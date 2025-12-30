# Load environment variables first
import dotenv
dotenv.load_dotenv()  # Must be at the top before using os.getenv

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from groq import Groq
import fitz
from textwrap import wrap
from supabase import create_client

# Import your blueprint after loading env
from routes.legal_professionals import legal_professionals_bp

# Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "https://law-pal.vercel.app"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-User-ID"],
    }
})

# Register blueprints
app.register_blueprint(legal_professionals_bp)

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase URL or Service Key")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1")
if not PINECONE_API_KEY:
    raise ValueError("Missing Pinecone API Key")
pc = Pinecone(api_key=PINECONE_API_KEY)

# Embedding model
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Groq client
GROQ_API_KEY = os.getenv("GROQ_API")
if not GROQ_API_KEY:
    raise ValueError("Missing Groq API Key")
groq_client = Groq(api_key=GROQ_API_KEY)

# Conversation history
conversation_histories = {
    "personal-and-family-legal-assistance": {},
    "business-consumer-and-criminal-legal-assistance": {},
    "consultation": {},
}

# -----------------------
# Form submission route
# -----------------------
@app.route("/submit-form", methods=["POST"])
def submit_form():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        required = ["firstName", "lastName", "email", "subject", "message"]
        if not all(data.get(f) for f in required):
            return jsonify({"error": "Missing fields"}), 400

        response = supabase.table("user_forms").insert(data).execute()
        if response.data:
            return jsonify({"message": "Form submitted successfully"}), 201
        else:
            return jsonify({"error": str(response.error)}), 500

    except Exception as e:
        logger.exception("Submit form failed")
        return jsonify({"error": str(e)}), 500

# -----------------------
# Helper functions
# -----------------------
def retrieve_context(index_name, query, top_k=3):
    try:
        index = pc.Index(index_name)
        embedding = model.encode(query).tolist()
        results = index.query(vector=embedding, top_k=top_k, include_metadata=True)
        return [m["metadata"]["text"] for m in results["matches"]]
    except Exception as e:
        print("Pinecone error:", e)
        return []

def generate_response(query, contexts, history, service):
    context = "\n\n".join(contexts) if contexts else "No context found"
    prompt = f"""
Indian {service.replace('-', ' ').title()} Law Assistant.

Context:
{context}

Question:
{query}

Answer:
"""
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=700,
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return str(e)

def handle_chat(service):
    if service not in conversation_histories:
        return jsonify({"error": "Invalid service category"}), 400

    data = request.get_json()
    query = data.get("query")
    user_id = request.headers.get("X-User-ID", "default")

    if not query:
        return jsonify({"error": "Query missing"}), 400

    history = conversation_histories[service].setdefault(user_id, [])
    contexts = retrieve_context("lawpal", query)
    response = generate_response(query, contexts, history, service)

    history.append({"role": "user", "content": query})
    history.append({"role": "bot", "content": response})

    return jsonify({"response": response})

# -----------------------
# Chat routes
# -----------------------
@app.route("/<service>/chat", methods=["POST", "OPTIONS"])
def chat(service):
    if request.method == "OPTIONS":
        return "", 200
    return handle_chat(service)

@app.route("/<service>/history", methods=["GET"])
def history(service):
    if service not in conversation_histories:
        return jsonify({"error": "Invalid service"}), 400
    user_id = request.headers.get("X-User-ID", "default")
    return jsonify({"history": conversation_histories[service].get(user_id, [])})

# -----------------------
# Run server
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
