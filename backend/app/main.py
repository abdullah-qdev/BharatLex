from fastapi import FastAPI, HTTPException

from app.database import check_mongodb_connection
from app.routes.ingest import router as ingest_router


app = FastAPI(
    title="BharatLex API",
    version="0.1.0",
    description="Backend API for legal grievance analysis, RAG, and agent workflows.",
)

app.include_router(ingest_router)


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
