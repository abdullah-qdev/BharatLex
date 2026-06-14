from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    text: str
    char_start: int
    char_end: int


def chunk_text(text: str, chunk_size: int = 1800, overlap: int = 250) -> list[TextChunk]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    chunks: list[TextChunk] = []
    start = 0

    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunk = cleaned[start:end].strip()

        if chunk:
            chunks.append(
                TextChunk(
                    chunk_index=len(chunks),
                    text=chunk,
                    char_start=start,
                    char_end=end,
                )
            )

        if end == len(cleaned):
            break

        start = max(end - overlap, start + 1)

    return chunks
