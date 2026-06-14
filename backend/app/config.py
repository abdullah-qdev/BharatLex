from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel
import os


BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env")


class Settings(BaseModel):
    mongodb_uri: str
    mongodb_db: str = "bharatlex"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_chat_model: str = "llama3.1"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_num_predict: int = 320
    ollama_temperature: float = 0.2
    ollama_disable_thinking: bool = True
    final_synthesis_provider: str = "groq"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    rag_top_k: int = 6
    rag_min_score: float = 0.2
    debate_rounds: int = 2


@lru_cache
def get_settings() -> Settings:
    mongodb_uri = os.getenv("MONGODB_URI", "").strip()
    mongodb_db = os.getenv("MONGODB_DB", "bharatlex").strip()

    if not mongodb_uri:
        raise RuntimeError("Missing MONGODB_URI in backend/.env")

    return Settings(
        mongodb_uri=mongodb_uri,
        mongodb_db=mongodb_db,
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip(),
        ollama_chat_model=os.getenv("OLLAMA_CHAT_MODEL", "llama3.1").strip(),
        ollama_embedding_model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text").strip(),
        ollama_num_predict=int(os.getenv("OLLAMA_NUM_PREDICT", "320")),
        ollama_temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.2")),
        ollama_disable_thinking=os.getenv("OLLAMA_DISABLE_THINKING", "true").strip().lower()
        in {"1", "true", "yes", "on"},
        final_synthesis_provider=os.getenv("FINAL_SYNTHESIS_PROVIDER", "groq").strip().lower(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip(),
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip(),
        rag_top_k=int(os.getenv("RAG_TOP_K", "6")),
        rag_min_score=float(os.getenv("RAG_MIN_SCORE", "0.2")),
        debate_rounds=int(os.getenv("DEBATE_ROUNDS", "2")),
    )
