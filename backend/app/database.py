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
