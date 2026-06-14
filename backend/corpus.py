"""
corpus.py — local RAG index over a folder of statute files.

No database needed. It embeds your law files with Ollama and saves a numpy
index to disk. quad_polar.py imports search() from here.

==========================================================================
>>> WHERE TO PUT YOUR RAG DATA <<<
Drop your law / act files into the folder named by STATUTE_DIR below
(default: ./statutes). One file per law. The file NAME (without extension)
MUST match a law name used in CATEGORY_LAWS in quad_polar.py. Examples:
    statutes/Consumer Protection Act 2019.txt
    statutes/IT Act 2000 (Amendment 2008).txt
    statutes/POSH Act 2013.pdf
Supported file types: .txt  .md  .pdf

Then build the index (re-run whenever you add or change files):
    python corpus.py
==========================================================================
"""

from __future__ import annotations
import re
import pickle
from pathlib import Path

import numpy as np
import ollama

# ===================== CONFIG — change these ==============================
STATUTE_DIR = "./statutes"           # >>> your RAG data folder
INDEX_PATH  = "./corpus_index.pkl"   # generated file; leave as is
EMBED_MODEL = "nomic-embed-text"     # run once: ollama pull nomic-embed-text
# =========================================================================


def embed(texts: list[str]) -> np.ndarray:
    """Local embeddings via Ollama, L2-normalized so cosine == dot product."""
    vecs = [ollama.embeddings(model=EMBED_MODEL, prompt=t)["embedding"] for t in texts]
    arr = np.array(vecs, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return arr / norms


def read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader          # pip install pypdf
        return "\n".join(p.extract_text() or "" for p in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="ignore")


SECTION_RE = re.compile(r"^\s*(?:Section\s+)?(\d+[A-Z]?)\.?\s", re.MULTILINE)


def chunk_text(text: str, size: int = 1200, overlap: int = 150) -> list[dict]:
    """Paragraph-aware chunking, tagging a section number when detectable."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, buf = [], ""
    for p in paras:
        if len(buf) + len(p) > size and buf:
            chunks.append(buf)
            buf = buf[-overlap:] + "\n\n" + p
        else:
            buf = (buf + "\n\n" + p).strip()
    if buf:
        chunks.append(buf)

    out = []
    for c in chunks:
        m = SECTION_RE.search(c)
        out.append({"section": m.group(1) if m else None, "text": c})
    return out


def build_index():
    folder = Path(STATUTE_DIR)
    if not folder.exists():
        print(f"Folder '{STATUTE_DIR}' not found. Create it and add your law files.")
        return
    files = [p for p in folder.iterdir() if p.suffix.lower() in (".txt", ".md", ".pdf")]
    if not files:
        print(f"No .txt/.md/.pdf files found in '{STATUTE_DIR}'.")
        return

    chunks = []
    for path in files:
        law = path.stem                      # filename == law_name
        print(f"Indexing: {law}")
        for c in chunk_text(read_file(path)):
            chunks.append({"law_name": law, "section": c["section"], "text": c["text"]})

    embeddings = embed([c["text"] for c in chunks])
    with open(INDEX_PATH, "wb") as f:
        pickle.dump({"chunks": chunks, "embeddings": embeddings}, f)
    print(f"Done. Indexed {len(chunks)} chunks from {len(files)} files -> {INDEX_PATH}")


_INDEX = None


def _load():
    global _INDEX
    if _INDEX is None:
        if not Path(INDEX_PATH).exists():
            raise FileNotFoundError(
                f"No index at '{INDEX_PATH}'. Add files to '{STATUTE_DIR}' "
                f"and run: python corpus.py")
        with open(INDEX_PATH, "rb") as f:
            _INDEX = pickle.load(f)
    return _INDEX


async def search(query: str, law_names: list[str] | None = None, k: int = 6) -> list[dict]:
    """Top-k statute chunks for a query. Filters by law_names; falls back to
    searching all chunks if the filter matches nothing (e.g. filenames differ)."""
    idx = _load()
    chunks, embs = idx["chunks"], idx["embeddings"]
    q = embed([query])[0]
    sims = embs @ q                          # cosine similarity (both normalized)
    order = np.argsort(-sims)

    flt = law_names or []
    out = []
    for i in order:
        c = chunks[int(i)]
        if flt and c["law_name"] not in flt:
            continue
        out.append({"law_name": c["law_name"], "section": c["section"], "text": c["text"]})
        if len(out) >= k:
            break

    if not out and flt:                      # filter matched nothing -> search all
        for i in order[:k]:
            c = chunks[int(i)]
            out.append({"law_name": c["law_name"], "section": c["section"], "text": c["text"]})
    return out


if __name__ == "__main__":
    build_index()
