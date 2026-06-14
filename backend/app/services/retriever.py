import math
import re
from dataclasses import dataclass, asdict
from typing import Any

from pymongo.database import Database

from app.config import get_settings
from app.services.legal_catalog import get_category
from app.services.ollama_client import embed_text


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_title: str
    category: str
    relative_path: str
    chunk_index: int
    text: str
    score: float
    page_start: int | None = None
    page_end: int | None = None
    citation: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0

    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0

    return dot / (left_norm * right_norm)


def _keyword_score(query: str, text: str) -> float:
    terms = set(re.findall(r"[A-Za-z0-9]+", query.lower()))
    if not terms:
        return 0.0

    haystack = text.lower()
    hits = sum(1 for term in terms if term in haystack)
    return hits / len(terms)


def _chunk_from_record(record: dict[str, Any], score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=record["chunk_id"],
        document_title=record.get("document_title", ""),
        category=record.get("category", ""),
        relative_path=record.get("relative_path", ""),
        chunk_index=record.get("chunk_index", 0),
        text=record.get("text", ""),
        score=round(score, 4),
        page_start=record.get("page_start"),
        page_end=record.get("page_end"),
        citation=record.get("citation") or {},
    )


def _mongo_filter(category_key: str | None = None) -> dict:
    category = get_category(category_key)
    if not category:
        return {}

    return {"document_title": {"$in": category.document_titles}}


def retrieve_chunks(
    db: Database,
    query: str,
    top_k: int | None = None,
    category_key: str | None = None,
) -> list[RetrievedChunk]:
    settings = get_settings()
    limit = top_k or settings.rag_top_k

    query_filter = _mongo_filter(category_key)
    records = list(
        db.legal_chunks.find(
            query_filter,
            {
                "_id": 0,
                "chunk_id": 1,
                "document_title": 1,
                "category": 1,
                "relative_path": 1,
                "chunk_index": 1,
                "text": 1,
                "embedding": 1,
                "page_start": 1,
                "page_end": 1,
                "citation": 1,
            },
        )
    )

    if category_key and not records:
        records = list(
            db.legal_chunks.find(
                {},
                {
                    "_id": 0,
                    "chunk_id": 1,
                    "document_title": 1,
                    "category": 1,
                    "relative_path": 1,
                    "chunk_index": 1,
                    "text": 1,
                    "embedding": 1,
                    "page_start": 1,
                    "page_end": 1,
                    "citation": 1,
                },
            )
        )

    if not records:
        return []

    embedded_records = [record for record in records if record.get("embedding")]
    scored: list[tuple[float, dict[str, Any]]] = []

    if embedded_records:
        query_embedding = embed_text(query)
        scored = [
            (_cosine_similarity(query_embedding, record["embedding"]), record)
            for record in embedded_records
        ]
    else:
        scored = [(_keyword_score(query, record.get("text", "")), record) for record in records]

    return [
        _chunk_from_record(record, score)
        for score, record in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]
        if score >= settings.rag_min_score
    ]
