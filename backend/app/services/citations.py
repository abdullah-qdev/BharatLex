import re
from dataclasses import dataclass, asdict


SECTION_PATTERNS = [
    re.compile(r"\b(?:section|sec\.?)\s+([0-9A-Za-z][0-9A-Za-z().-]*)", re.IGNORECASE),
    re.compile(r"\b(?:rule|regulation|article)\s+([0-9A-Za-z][0-9A-Za-z().-]*)", re.IGNORECASE),
]
CLAUSE_PATTERN = re.compile(r"\b(?:clause|sub-clause|subclause)\s+([0-9A-Za-z().-]+)", re.IGNORECASE)
DEADLINE_PATTERN = re.compile(
    r"\b(?:within|not later than|deadline|file(?:d)? within)\s+([^.;:]{0,80}?\b(?:days?|months?|years?|hours?)\b)",
    re.IGNORECASE,
)
FORUM_PATTERN = re.compile(
    r"\b((?:District|State|National|Consumer|Appellate|Grievance|Ombudsman|Tribunal|Commission|Authority|Forum)"
    r"(?:\s+[A-Z][A-Za-z&.-]+){0,8})\b"
)
ADDRESS_PATTERN = re.compile(
    r"\b(?:address|located at|office at|send to)\s*[:,-]?\s*([^.;\n]{8,180})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CitationMetadata:
    sections: list[str]
    clauses: list[str]
    forum_names: list[str]
    forum_addresses: list[str]
    filing_deadlines: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = " ".join(value.strip(" ,;:.-").split())
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def extract_citation_metadata(text: str) -> CitationMetadata:
    sections: list[str] = []
    for pattern in SECTION_PATTERNS:
        sections.extend(match.group(0) for match in pattern.finditer(text))

    return CitationMetadata(
        sections=_unique(sections),
        clauses=_unique([match.group(0) for match in CLAUSE_PATTERN.finditer(text)]),
        forum_names=_unique([match.group(1) for match in FORUM_PATTERN.finditer(text)]),
        forum_addresses=_unique([match.group(1) for match in ADDRESS_PATTERN.finditer(text)]),
        filing_deadlines=_unique([match.group(1) for match in DEADLINE_PATTERN.finditer(text)]),
    )
