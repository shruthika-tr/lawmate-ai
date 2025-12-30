from flask import Blueprint, request, jsonify
from supabase import create_client
import os

legal_professionals_bp = Blueprint("legal_professionals", __name__)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

@legal_professionals_bp.route("/legal_professionals", methods=["GET"])
def get_legal_professionals():
    service = request.args.get("service")
    city = request.args.get("city")

    if not service:
        return jsonify({"error": "service is required"}), 400

    query = supabase.table("legal_professionals").select("*").eq("service_category", service)

    if city:
        query = query.eq("city", city)

    result = query.execute()
    return jsonify(result.data)
