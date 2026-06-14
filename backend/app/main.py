from datetime import datetime

from fastapi import FastAPI, HTTPException

from app.database import check_mongodb_connection
from app.routes.ingest import router as ingest_router
from app.routes.rag import router as rag_router
from app.utils.hashing import generate_integrity_hash


app = FastAPI(
    title="BharatLex API",
    version="0.1.0",
    description="Backend API for legal grievance analysis, RAG, and agent workflows.",
)

app.include_router(ingest_router)
app.include_router(rag_router)


@app.get("/")
def root() -> dict:
    return {
        "service": "BharatLex API",
        "status": "running",
        "next": "Use /health/db to verify MongoDB Atlas connectivity.",
    }


@app.get("/health/db")
def health_db() -> dict:
    try:
        return check_mongodb_connection()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/complaint")
async def submit_complaint(request: dict):
    clerk_id = request.get("clerk_id")
    complaint_text = request.get("complaint_text")
    
    timestamp = datetime.utcnow().isoformat()
    integrity_hash = generate_integrity_hash(clerk_id, complaint_text, timestamp)
    
    return {
        "status": "received",
        "integrity_hash": integrity_hash,
        "timestamp": timestamp,
        "message": "Complaint secured with SHA-256"
    }
