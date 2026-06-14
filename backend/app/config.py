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


@lru_cache
def get_settings() -> Settings:
    mongodb_uri = os.getenv("MONGODB_URI", "").strip()
    mongodb_db = os.getenv("MONGODB_DB", "bharatlex").strip()

    if not mongodb_uri:
        raise RuntimeError("Missing MONGODB_URI in backend/.env")

    return Settings(mongodb_uri=mongodb_uri, mongodb_db=mongodb_db)
