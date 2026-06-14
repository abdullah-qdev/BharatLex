from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from app.config import BACKEND_ROOT
from app.services.chunker import TextChunk, chunk_text


LEGAL_DOCS_ROOT = BACKEND_ROOT / "legal_docs"
STATUTES_ROOT = BACKEND_ROOT / "statutes"
LEGAL_SOURCE_ROOTS = [LEGAL_DOCS_ROOT, STATUTES_ROOT]


@dataclass(frozen=True)
class LegalDocument:
    title: str
    category: str
    path: Path
    relative_path: str
    page_count: int
    text: str
    chunks: list[TextChunk]


def list_legal_pdf_paths(roots: list[Path] | None = None) -> list[Path]:
    pdf_paths: list[Path] = []

    for root in roots or LEGAL_SOURCE_ROOTS:
        if root.exists():
            pdf_paths.extend(root.rglob("*.pdf"))

    return sorted(pdf_paths)


def _category_for_path(path: Path) -> str:
    if STATUTES_ROOT in path.parents:
        return "statutes"
    if path.parent == LEGAL_DOCS_ROOT:
        return "general"
    return path.parent.name


def _clean_text(text: str) -> str:
    return " ".join(text.split())


def extract_pdf_text(path: Path) -> tuple[str, int, list[tuple[int, int, int]]]:
    reader = PdfReader(str(path))
    page_text: list[str] = []
    page_ranges: list[tuple[int, int, int]] = []
    cursor = 0

    for page_number, page in enumerate(reader.pages, start=1):
        cleaned = _clean_text(page.extract_text() or "")
        start = cursor
        end = start + len(cleaned)
        page_text.append(cleaned)
        page_ranges.append((page_number, start, end))
        cursor = end + 1

    return " ".join(page_text), len(reader.pages), page_ranges


def load_legal_document(path: Path) -> LegalDocument:
    text, page_count, page_ranges = extract_pdf_text(path)
    category = _category_for_path(path)
    title = path.stem
    relative_path = path.relative_to(BACKEND_ROOT).as_posix()

    return LegalDocument(
        title=title,
        category=category,
        path=path,
        relative_path=relative_path,
        page_count=page_count,
        text=text,
        chunks=chunk_text(text, page_ranges=page_ranges),
    )


def preview_legal_documents() -> list[dict]:
    previews: list[dict] = []

    for path in list_legal_pdf_paths():
        text, page_count, page_ranges = extract_pdf_text(path)
        chunks = chunk_text(text, page_ranges=page_ranges)
        previews.append(
            {
                "title": path.stem,
                "category": _category_for_path(path),
                "relative_path": path.relative_to(BACKEND_ROOT).as_posix(),
                "page_count": page_count,
                "character_count": len(text),
                "chunk_count": len(chunks),
            }
        )

    return previews
