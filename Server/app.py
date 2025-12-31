# Load environment variables FIRST (local dev only)
import dotenv
dotenv.load_dotenv()

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from pinecone import Pinecone
from groq import Groq
from supabase import create_client

# Import blueprint
from routes.legal_professionals import legal_professionals_bp

# -----------------------
# Logging
# -----------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------
# Flask App
# -----------------------
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:5173",
            "https://law-pal.vercel.app"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-User-ID"],
    }
})

app.register_blueprint(legal_professionals_bp)

# -----------------------
# Supabase
# -----------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase credentials missing")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------
# Pinecone
# -----------------------
PINECONE_API_KEY = os.getenv("PINECONE_API")
PINECONE_INDEX = "lawpal"

if not PINECONE_API_KEY:
    raise RuntimeError("Pinecone API key missing")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

# -----------------------
# Groq
# -----------------------
GROQ_API_KEY = os.getenv("GROQ_API")
if not GROQ_API_KEY:
    raise RuntimeError("Groq API key missing")

groq_client = Groq(api_key=GROQ_API_KEY)

# -----------------------
# In-memory conversation history
# -----------------------
conversation_histories = {
    "personal-and-family-legal-assistance": {},
    "business-consumer-and-criminal-legal-assistance": {},
    "consultation": {},
}

# -----------------------
# Health check (IMPORTANT)
# -----------------------
@app.route("/")
def health():
    return jsonify({"status": "ok"}), 200

# -----------------------
# Submit Form
# -----------------------
@app.route("/submit-form", methods=["POST"])
def submit_form():
    try:
        data = request.get_json(force=True)
        required = ["firstName", "lastName", "email", "subject", "message"]

        if not all(data.get(f) for f in required):
            return jsonify({"error": "Missing fields"}), 400

        result = supabase.table("user_forms").insert(data).execute()

        if result.data:
            return jsonify({"message": "Form submitted"}), 201

        return jsonify({"error": "Insert failed"}), 500

    except Exception as e:
        logger.exception("Form submission failed")
        return jsonify({"error": str(e)}), 500

# -----------------------
# Retrieve Context (Pinecone text search)
# -----------------------
def retrieve_context(query, top_k=3):
    try:
        results = index.query(
            top_k=top_k,
            include_metadata=True,
            query={"text": query}
        )

        logger.info(f"Pinecone matches: {len(results.get('matches', []))}")

        return [
            m["metadata"].get("text", "")
            for m in results.get("matches", [])
        ]

    except Exception as e:
        logger.error(f"Pinecone error: {e}")
        return []

# -----------------------
# Generate Answer
# -----------------------
def generate_response(query, contexts, service):
    context_block = "\n\n".join(contexts) if contexts else "No legal context found."

    prompt = f"""
You are an Indian {service.replace('-', ' ')} law assistant.

Use ONLY the context below.
If unsure, say you are not certain.

Context:
{context_block}

Question:
{query}

Answer:
"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=600,
    )

    return response.choices[0].message.content.strip()

# -----------------------
# Chat Handler
# -----------------------
def handle_chat(service):
    if service not in conversation_histories:
        return jsonify({"error": "Invalid service"}), 400

    data = request.get_json(force=True)
    query = data.get("query")
    user_id = request.headers.get("X-User-ID", "default")

    if not query:
        return jsonify({"error": "Query missing"}), 400

    contexts = retrieve_context(query)
    answer = generate_response(query, contexts, service)

    history = conversation_histories[service].setdefault(user_id, [])
    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": answer})

    return jsonify({"response": answer})

# -----------------------
# Routes
# -----------------------
@app.route("/<service>/chat", methods=["POST", "OPTIONS"])
def chat(service):
    if request.method == "OPTIONS":
        return "", 200
    return handle_chat(service)

@app.route("/<service>/history", methods=["GET"])
def history(service):
    user_id = request.headers.get("X-User-ID", "default")
    return jsonify({
        "history": conversation_histories.get(service, {}).get(user_id, [])
    })

# -----------------------
# Run (Render-compatible)
# -----------------------
##if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
