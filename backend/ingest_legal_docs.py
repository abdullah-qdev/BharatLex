"""
BharatLex — Legal Document Ingest Script
-----------------------------------------
Place this file at: bharatlex/backend/scripts/ingest_legal_docs.py

What this script does:
1. Reads all PDFs from your 4 category folders
2. Extracts text using PyMuPDF (fastest library, 8-12x faster than pdfplumber)
3. Splits text into sections (chunks of ~500 words)
4. Embeds each section using Gemini gemini-embedding-001 (768 dimensions)
5. Stores text + embedding in MongoDB legal_docs collection
6. Creates vector search index if it doesn't exist yet

Run once before hackathon. Never needs to run again unless laws update.

Usage:
    cd bharatlex/backend
    python scripts/ingest_legal_docs.py
"""

import os
import sys
import time
import fitz  # PyMuPDF
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv
import google.generativeai as genai

# ─────────────────────────────────────────────
# CONFIGURATION — edit these paths if needed
# ─────────────────────────────────────────────

# Path to your unzipped folder on Windows
# Change this to your actual path
DOCS_BASE_PATH = r"C:\Users\abdul\Downloads\drive-download-20260613T120442Z-3-001"

# Folder name → MongoDB category mapping
# Must match exactly what's in your folder
CATEGORY_MAP = {
    "Banking & Payments": "banking",
    "Consumer Rights":    "consumer",
    "Cyber Fraud":        "cyber",
    "Workplace Rights":   "workplace",
}

# Chunk size in words — 500 is optimal for RAG
# Too small = loses context. Too large = dilutes relevance.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50  # words overlap between chunks to avoid cutting mid-sentence

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────

load_dotenv()  # loads MONGODB_URI and GEMINI_API_KEY from .env

MONGODB_URI = os.getenv("MONGODB_URI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not MONGODB_URI:
    print("ERROR: MONGODB_URI not found in .env file")
    sys.exit(1)

if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY not found in .env file")
    sys.exit(1)

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client["bharatlex"]
collection = db["legal_docs"]

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


# ─────────────────────────────────────────────
# STEP 1: CREATE VECTOR SEARCH INDEX
# ─────────────────────────────────────────────

def create_vector_search_index():
    """
    Creates the vector search index on legal_docs collection.
    Safe to call multiple times — skips if already exists.
    NOTE: On M0 free tier, this may fail programmatically.
    If it fails, create manually in Atlas UI using the JSON below.
    """
    index_definition = {
        "name": "legal_docs_index",
        "type": "vectorSearch",
        "definition": {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": 768,
                    "similarity": "cosine"
                },
                {
                    "type": "filter",
                    "path": "category"
                }
            ]
        }
    }

    try:
        collection.create_search_index(index_definition)
        print("✓ Vector search index created successfully")
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            print("✓ Vector search index already exists, skipping")
        else:
            print(f"⚠ Could not create index programmatically: {e}")
            print("→ Create it manually in Atlas UI with this JSON:")
            print("""
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 768,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "category"
    }
  ]
}
            """)


# ─────────────────────────────────────────────
# STEP 2: EXTRACT TEXT FROM PDF
# ─────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts all text from a PDF using PyMuPDF.
    PyMuPDF is 8-12x faster than pdfplumber for plain text.
    Handles multi-column layouts better than PyPDF2.
    """
    try:
        doc = fitz.open(pdf_path)
        full_text = []

        for page in doc:
            text = page.get_text("text")  # plain text mode
            # clean up excessive newlines
            text = "\n".join(
                line.strip() for line in text.splitlines() if line.strip()
            )
            full_text.append(text)

        doc.close()
        return "\n\n".join(full_text)

    except Exception as e:
        print(f"  ✗ Failed to extract text from {pdf_path}: {e}")
        return ""


# ─────────────────────────────────────────────
# STEP 3: SPLIT TEXT INTO CHUNKS
# ─────────────────────────────────────────────

def split_into_chunks(text: str, pdf_name: str, chunk_size: int = CHUNK_SIZE) -> list[dict]:
    """
    Splits extracted text into overlapping word chunks.
    Each chunk becomes one MongoDB document.

    Why chunk by words not characters:
    - Gemini embedding model has a token limit
    - 500 words ≈ 650 tokens, safely under the 2048 token limit
    - Overlapping chunks prevent cutting legal clauses mid-sentence
    """
    words = text.split()

    if not words:
        return []

    chunks = []
    start = 0
    chunk_number = 1

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)

        # Only store chunks with meaningful content (more than 50 words)
        if len(chunk_words) > 50:
            chunks.append({
                "chunk_number": chunk_number,
                "section_text": chunk_text,
                "source_file": pdf_name,
                "word_count": len(chunk_words)
            })
            chunk_number += 1

        # Move forward by chunk_size minus overlap
        start += chunk_size - CHUNK_OVERLAP

    return chunks


# ─────────────────────────────────────────────
# STEP 4: EMBED TEXT WITH GEMINI
# ─────────────────────────────────────────────

def embed_text(text: str) -> list[float] | None:
    """
    Generates 768-dimension embedding using Gemini gemini-embedding-001.
    Uses task_type=RETRIEVAL_DOCUMENT for legal doc storage.
    (Use RETRIEVAL_QUERY when embedding user complaints at query time)

    Rate limit: Gemini free tier allows 1500 requests/day.
    With 11 docs and ~500 word chunks, expect ~50-100 total chunks.
    Well within limits.
    """
    try:
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_document",
            output_dimensionality=768
        )
        return result["embedding"]
    except Exception as e:
        print(f"  ✗ Embedding failed: {e}")
        # Wait and retry once on rate limit
        if "quota" in str(e).lower() or "rate" in str(e).lower():
            print("  → Rate limited, waiting 60 seconds...")
            time.sleep(60)
            try:
                result = genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=text,
                    task_type="retrieval_document",
                    output_dimensionality=768
                )
                return result["embedding"]
            except Exception as e2:
                print(f"  ✗ Retry also failed: {e2}")
        return None


# ─────────────────────────────────────────────
# STEP 5: STORE IN MONGODB
# ─────────────────────────────────────────────

def store_chunk(chunk: dict, category: str, act_name: str, embedding: list[float]):
    """
    Stores one chunk with its embedding in MongoDB.
    Skips if this exact chunk already exists (safe to re-run).
    """
    # Check if already ingested
    existing = collection.find_one({
        "source_file": chunk["source_file"],
        "chunk_number": chunk["chunk_number"]
    })

    if existing:
        return False  # already exists, skip

    doc = {
        "act_name": act_name,
        "category": category,
        "source_file": chunk["source_file"],
        "chunk_number": chunk["chunk_number"],
        "section_text": chunk["section_text"],
        "word_count": chunk["word_count"],
        "embedding": embedding
    }

    collection.insert_one(doc)
    return True


# ─────────────────────────────────────────────
# MAIN: PROCESS ALL FOLDERS
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("BharatLex Legal Document Ingest Script")
    print("=" * 60)

    # Step 1: Create vector search index
    print("\n[1/5] Setting up vector search index...")
    create_vector_search_index()

    # Step 2: Verify docs folder exists
    base_path = Path(DOCS_BASE_PATH)
    if not base_path.exists():
        print(f"\nERROR: Folder not found: {DOCS_BASE_PATH}")
        print("Check the DOCS_BASE_PATH variable at the top of this script")
        sys.exit(1)

    total_chunks = 0
    total_stored = 0
    total_skipped = 0

    # Step 3: Process each category folder
    for folder_name, category in CATEGORY_MAP.items():
        folder_path = base_path / folder_name

        if not folder_path.exists():
            print(f"\n⚠ Folder not found, skipping: {folder_name}")
            continue

        pdf_files = list(folder_path.glob("*.pdf"))

        if not pdf_files:
            print(f"\n⚠ No PDFs found in: {folder_name}")
            continue

        print(f"\n[{category.upper()}] Processing {len(pdf_files)} PDF(s) in '{folder_name}'")
        print("-" * 40)

        for pdf_path in pdf_files:
            pdf_name = pdf_path.stem  # filename without .pdf
            act_name = pdf_name.replace("_", " ").replace("-", " ").title()

            print(f"\n  → {pdf_path.name}")

            # Extract text
            print(f"     Extracting text...")
            text = extract_text_from_pdf(str(pdf_path))

            if not text or len(text.strip()) < 100:
                print(f"     ✗ Too little text extracted, skipping")
                continue

            print(f"     ✓ Extracted {len(text.split())} words")

            # Split into chunks
            chunks = split_into_chunks(text, pdf_name)
            print(f"     ✓ Split into {len(chunks)} chunks")
            total_chunks += len(chunks)

            # Embed and store each chunk
            for i, chunk in enumerate(chunks):
                print(f"     Embedding chunk {i+1}/{len(chunks)}...", end="\r")

                embedding = embed_text(chunk["section_text"])

                if embedding is None:
                    print(f"     ✗ Chunk {i+1} embedding failed, skipping")
                    continue

                stored = store_chunk(chunk, category, act_name, embedding)

                if stored:
                    total_stored += 1
                else:
                    total_skipped += 1

                # Small delay to respect Gemini rate limits
                time.sleep(0.1)

            print(f"     ✓ Done: {len(chunks)} chunks embedded and stored")

    # Summary
    print("\n" + "=" * 60)
    print("INGEST COMPLETE")
    print(f"  Total chunks processed : {total_chunks}")
    print(f"  Newly stored in MongoDB: {total_stored}")
    print(f"  Skipped (already exist): {total_skipped}")
    print("=" * 60)

    if total_stored > 0:
        print("\n✓ MongoDB legal_docs collection is ready")
        print("✓ You can now create the vector search index in Atlas UI")
        print("  (if programmatic creation failed above)")
    else:
        print("\n⚠ Nothing was stored. Check errors above.")

    # Verify count
    count = collection.count_documents({})
    print(f"\n✓ Total documents in legal_docs collection: {count}")

    client.close()


if __name__ == "__main__":
    main()
