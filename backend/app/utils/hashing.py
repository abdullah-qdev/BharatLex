import hashlib
import json
from datetime import datetime

def generate_integrity_hash(clerk_id: str, complaint_text: str, timestamp: str) -> str:
    payload = json.dumps({
        "clerk_id": clerk_id,
        "complaint": complaint_text,
        "timestamp": timestamp
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()

def verify_integrity_hash(clerk_id: str, complaint_text: str, timestamp: str, stored_hash: str) -> bool:
    recomputed = generate_integrity_hash(clerk_id, complaint_text, timestamp)
    return recomputed == stored_hash
