# -----------------------
# Load environment variables FIRST
# -----------------------
import dotenv
dotenv.load_dotenv()

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from groq import Groq
from supabase import create_client

# -----------------------
# Logging
# -----------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------
# Flask App
# -----------------------
app = Flask(__name__)

# -----------------------
# CORS (CORRECT)
# -----------------------
CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "http://localhost:5173",
                "https://lawmate-ai-pi.vercel.app",
            ],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-User-ID"],
        }
    },
)

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
# Embedding Model
# -----------------------
embedding_model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# -----------------------
# Groq
# -----------------------
GROQ_API_KEY = os.getenv("GROQ_API")
if not GROQ_API_KEY:
    raise RuntimeError("Groq API key missing")

groq_client = Groq(api_key=GROQ_API_KEY)

# -----------------------
# In-memory history
# -----------------------
conversation_histories = {
    "personal-and-family-legal-assistance": {},
    "business-consumer-and-criminal-legal-assistance": {},
    "consultation": {},
}

# -----------------------
# Health check
# -----------------------
@app.route("/")
def health():
    return jsonify({"status": "ok"}), 200

# =====================================================
# 🔍 CONFIRMATION ROUTES (FIXED)
# =====================================================

# 1️⃣ Pinecone index status (SAFE)
@app.route("/pinecone-status")
def pinecone_status():
    stats = index.describe_index_stats()

    return jsonify({
        "dimension": stats.dimension,
        "total_vector_count": stats.total_vector_count,
        "namespaces": stats.namespaces,
    })

# 2️⃣ Manual Pinecone test query (SAFE)
@app.route("/test-pinecone")
def test_pinecone():
    query = "Indian Penal Code theft"
    vector = embedding_model.encode(query).tolist()

    logger.info(f"Test embedding length: {len(vector)}")

    res = index.query(
        vector=vector,
        top_k=1,
        include_metadata=True,
    )

    matches = []
    for m in res.matches:
        matches.append({
            "id": m.id,
            "score": m.score,
            "metadata": m.metadata,
        })

    return jsonify({
        "query": query,
        "matches_found": len(matches),
        "matches": matches,
    })

# -----------------------
# Retrieve Context (FIXED)
# -----------------------
def retrieve_context(query, top_k=3):
    try:
        vector = embedding_model.encode(query).tolist()
        logger.info(f"Query embedding length: {len(vector)}")

        res = index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
        )

        matches = res.matches
        logger.info(f"Pinecone matches: {len(matches)}")

        return [m.metadata.get("text", "") for m in matches]

    except Exception as e:
        logger.error(f"Pinecone error: {e}")
        return []

# -----------------------
# Generate Response
# -----------------------
def generate_response(query, contexts, service):
    if contexts:
        system_prompt = (
            "You are an Indian legal assistant. "
            "Use the provided legal context to answer accurately."
        )
        context_block = "\n\n".join(contexts)
    else:
        system_prompt = (
            "You are an Indian legal assistant. "
            "Answer clearly even if no documents are available."
        )
        context_block = "No retrieved documents."

    prompt = f"""
{system_prompt}

Service Area: {service.replace('-', ' ')}

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
# Run (Render compatible)
# -----------------------
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
