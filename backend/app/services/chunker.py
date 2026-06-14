from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    text: str
    char_start: int
    char_end: int
    page_start: int | None = None
    page_end: int | None = None


def _page_range_for_chunk(
    char_start: int, char_end: int, page_ranges: list[tuple[int, int, int]] | None
) -> tuple[int | None, int | None]:
    if not page_ranges:
        return None, None

    pages = [
        page_number
        for page_number, page_start, page_end in page_ranges
        if page_start < char_end and page_end > char_start
    ]
    if not pages:
        return None, None

    return min(pages), max(pages)


def chunk_text(
    text: str,
    chunk_size: int = 1800,
    overlap: int = 250,
    page_ranges: list[tuple[int, int, int]] | None = None,
) -> list[TextChunk]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    chunks: list[TextChunk] = []
    start = 0

    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunk = cleaned[start:end].strip()

        if chunk:
            page_start, page_end = _page_range_for_chunk(start, end, page_ranges)
            chunks.append(
                TextChunk(
                    chunk_index=len(chunks),
                    text=chunk,
                    char_start=start,
                    char_end=end,
                    page_start=page_start,
                    page_end=page_end,
                )
            )

        if end == len(cleaned):
            break

        start = max(end - overlap, start + 1)

    return chunks
