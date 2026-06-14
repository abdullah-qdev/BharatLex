from datetime import datetime, timezone

from fastapi import APIRouter, Query
from pymongo import UpdateOne

from app.database import get_database
from app.services.citations import extract_citation_metadata
from app.services.document_loader import (
    list_legal_pdf_paths,
    load_legal_document,
    preview_legal_documents,
)
from app.services.ollama_client import embed_text


router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


@router.get("/legal-docs/preview")
def preview_legal_docs() -> dict:
    documents = preview_legal_documents()
    return {
        "document_count": len(documents),
        "chunk_count": sum(document["chunk_count"] for document in documents),
        "documents": documents,
    }


@router.post("/legal-docs")
def ingest_legal_docs(
    embed: bool = Query(default=False, description="Generate Ollama embeddings for RAG retrieval.")
) -> dict:
    db = get_database()
    now = datetime.now(timezone.utc)
    paths = list_legal_pdf_paths()

    document_operations = []
    chunk_operations = []

    for path in paths:
        document = load_legal_document(path)

        document_operations.append(
            UpdateOne(
                {"relative_path": document.relative_path},
                {
                    "$set": {
                        "title": document.title,
                        "category": document.category,
                        "relative_path": document.relative_path,
                        "page_count": document.page_count,
                        "character_count": len(document.text),
                        "chunk_count": len(document.chunks),
                        "updated_at": now,
                    },
                    "$setOnInsert": {"created_at": now},
                },
                upsert=True,
            )
        )

        for chunk in document.chunks:
            chunk_id = f"{document.relative_path}::chunk-{chunk.chunk_index}"
            chunk_payload = {
                "chunk_id": chunk_id,
                "document_title": document.title,
                "category": document.category,
                "relative_path": document.relative_path,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "char_start": chunk.char_start,
                "char_end": chunk.char_end,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "citation": extract_citation_metadata(chunk.text).to_dict(),
                "updated_at": now,
            }
            if embed:
                chunk_payload["embedding"] = embed_text(chunk.text)

            chunk_operations.append(
                UpdateOne(
                    {"chunk_id": chunk_id},
                    {
                        "$set": chunk_payload,
                        "$setOnInsert": {"created_at": now},
                    },
                    upsert=True,
                )
            )

    if document_operations:
        db.legal_documents.bulk_write(document_operations, ordered=False)

    if chunk_operations:
        db.legal_chunks.bulk_write(chunk_operations, ordered=False)

    return {
        "ok": True,
        "documents_found": len(paths),
        "chunks_written": len(chunk_operations),
        "embedded": embed,
        "collections": ["legal_documents", "legal_chunks"],
    }
