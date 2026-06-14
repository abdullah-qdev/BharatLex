from pymongo import MongoClient
from pymongo.database import Database

from app.config import get_settings


def get_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)


def get_database() -> Database:
    settings = get_settings()
    client = get_client()
    return client[settings.mongodb_db]


def check_mongodb_connection() -> dict:
    client = get_client()
    client.admin.command("ping")
    settings = get_settings()
    return {"ok": True, "database": settings.mongodb_db}


from datetime import datetime
from app.utils.hashing import generate_integrity_hash

def save_complaint(db, clerk_id: str, complaint_text: str, analysis: dict):
    timestamp = datetime.utcnow().isoformat()
    integrity_hash = generate_integrity_hash(clerk_id, complaint_text, timestamp)
    
    complaint_doc = {
        "clerk_id": clerk_id,
        "transcript": complaint_text,
        "analysis": analysis,
        "integrity_hash": integrity_hash,
        "created_at": timestamp
    }
    
    result = db.complaints.insert_one(complaint_doc)
    return str(result.inserted_id), integrity_hash
