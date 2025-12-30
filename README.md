# Lawmate – AI-Powered Legal Assistance Platform

## Overview

Lawmate is a full-stack AI-powered legal assistance platform that helps users understand legal queries, analyze legal documents, retrieve relevant case laws, and connect with legal professionals through natural language interaction.

This project integrates large language models, semantic vector search, and secure authentication to make legal information more accessible.

⚠️ This application is developed for academic and demonstration purposes only and does not constitute legal advice.

---

## Key Features

- AI-powered legal chatbot for natural language legal queries
- Legal document upload and AI-based analysis
- Semantic case law retrieval using vector embeddings
- Legal professionals directory categorized by legal services
- Voice-based interaction (speech-to-text and text-to-speech)
- Multi-language support
- Secure authentication using Supabase

---

## Legal Professionals Module

- Categorized legal services (Family, Property, Business, Criminal, Consumer, Civil)
- Dynamic professional listings fetched from the backend
- Filtering based on selected legal service
- Designed to assist users in identifying relevant legal experts

---

## Tech Stack

### Frontend

- React (Vite)
- Tailwind CSS
- React Router
- Web Speech API

### Backend

- Flask (REST API)
- Pinecone (Vector Database)
- Groq (LLM Inference)

### Authentication & Services

- Supabase Authentication
- Environment-based configuration

---

## Setup & Installation

### Clone the Repository

git clone https://github.com/<your-username>/Lawmate.git
cd Lawmate

### Backend Setup

cd Server
pip install -r requirements.txt

Create a `.env` file inside the `Server` folder:

PINECONE_API_KEY=your_pinecone_key
PINECONE_ENV=your_pinecone_environment
GROQ_API_KEY=your_groq_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key

Run the backend server:

python app.py

### Frontend Setup

cd App
npm install
npm run dev

---

## Usage

- Register or log in to the platform
- Interact with the AI legal chatbot using text or voice
- Upload legal documents for automated analysis
- Browse legal professionals by service category
- Retrieve relevant case laws using semantic search

---

## License

MIT License

## Author

Shruthika T R
GitHub: [https://github.com/shruthika-tr](https://github.com/shruthika-tr)
