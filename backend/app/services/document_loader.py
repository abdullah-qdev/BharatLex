from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from app.config import BACKEND_ROOT
from app.services.chunker import TextChunk, chunk_text


LEGAL_DOCS_ROOT = BACKEND_ROOT / "legal_docs"


@dataclass(frozen=True)
class LegalDocument:
    title: str
    category: str
    path: Path
    relative_path: str
    page_count: int
    text: str
    chunks: list[TextChunk]


def list_legal_pdf_paths(root: Path = LEGAL_DOCS_ROOT) -> list[Path]:
    if not root.exists():
        return []

    return sorted(root.glob("*/*.pdf"))


def extract_pdf_text(path: Path) -> tuple[str, int]:
    reader = PdfReader(str(path))
    page_text: list[str] = []

    for page in reader.pages:
        page_text.append(page.extract_text() or "")

    return "\n\n".join(page_text), len(reader.pages)


def load_legal_document(path: Path) -> LegalDocument:
    text, page_count = extract_pdf_text(path)
    category = path.parent.name
    title = path.stem
    relative_path = path.relative_to(BACKEND_ROOT).as_posix()

    return LegalDocument(
        title=title,
        category=category,
        path=path,
        relative_path=relative_path,
        page_count=page_count,
        text=text,
        chunks=chunk_text(text),
    )


def preview_legal_documents() -> list[dict]:
    previews: list[dict] = []

    for path in list_legal_pdf_paths():
        text, page_count = extract_pdf_text(path)
        chunks = chunk_text(text)
        previews.append(
            {
                "title": path.stem,
                "category": path.parent.name,
                "relative_path": path.relative_to(BACKEND_ROOT).as_posix(),
                "page_count": page_count,
                "character_count": len(text),
                "chunk_count": len(chunks),
            }
        )

    return previews
