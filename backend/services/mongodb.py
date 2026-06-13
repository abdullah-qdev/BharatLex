from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["bharatlex"]

legal_docs = db["legal_docs"]
users = db["users"]
complaints = db["complaints"]