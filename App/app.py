from pinecone import Pinecone
from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from groq import Groq
from tqdm import tqdm
import os
import dotenv
import fitz
from textwrap import wrap
from supabase import create_client, Client
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": ["https://law-pal.vercel.app", "http://localhost:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-User-ID"],
    }
})

dotenv.load_dotenv()

# Initialize Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1")
if not PINECONE_API_KEY:
    raise ValueError("Missing Pinecone API Key.")
pc = Pinecone(api_key=PINECONE_API_KEY)

# Initialize Sentence Transformer Model
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Initialize Groq
GROQ_API_KEY = os.getenv("GROQ_API")
if not GROQ_API_KEY:
    raise ValueError("Missing Groq API Key.")
groq_client = Groq(api_key=GROQ_API_KEY)

# ✅ Initialize Supabase (SERVER MUST USE SERVICE ROLE KEY)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase URL or Service Role Key.")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Store conversation history
conversation_histories = {
    "personal-and-family-legal-assistance": {},
    "business-consumer-and-criminal-legal-assistance": {},
    "consultation": {},
}

@app.route('/submit-form', methods=['POST'])
def submit_form():
    try:
        logger.debug("Received form data: %s", request.get_data())

        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        logger.debug("Parsed JSON data: %s", data)

        required_fields = ["firstName", "lastName", "email", "subject", "message"]
        if not all(field in data and data[field] for field in required_fields):
            return jsonify({"error": "Missing or empty required fields"}), 400

        response = supabase.table("user_forms").insert(data).execute()
        logger.debug("Supabase response: %s", response)

        # ✅ Correct supabase-py success check
        if response.data:
            return jsonify({"message": "Form submitted successfully!"}), 201
        else:
            return jsonify({"error": str(response.error)}), 500

    except Exception as e:
        logger.error("Error in submit_form: %s", str(e), exc_info=True)
        return jsonify({"error": str(e)}), 500

# (REST OF FILE UNCHANGED)

if __name__ == "__main__":
    BUCKET_NAME = "pdfs"
    if os.getenv("CREATE_PINECONE_INDEX", "false").lower() == "true":
        create_pinecone_index(BUCKET_NAME)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
