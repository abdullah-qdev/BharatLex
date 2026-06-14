import re


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "but",
    "for",
    "from",
    "have",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "that",
    "the",
    "they",
    "this",
    "to",
    "was",
    "what",
    "with",
}


def _terms(text: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[A-Za-z0-9]{3,}", text.lower())
        if term not in STOPWORDS
    }


def compare_evidence_to_description(description: str | None, evidence_text: str) -> dict:
    if not description:
        return {
            "checked": False,
            "related": None,
            "score": None,
            "message": "No separate grievance description was provided to compare against the uploaded evidence.",
        }

    description_terms = _terms(description)
    evidence_terms = _terms(evidence_text)
    if not description_terms or not evidence_terms:
        return {
            "checked": True,
            "related": False,
            "score": 0.0,
            "message": "The uploaded evidence did not contain enough readable text to confirm it relates to the described grievance.",
        }

    overlap = description_terms & evidence_terms
    score = len(overlap) / max(1, min(len(description_terms), len(evidence_terms)))
    related = score >= 0.18 or len(overlap) >= 3
    weak_match = not related and (score >= 0.08 or len(overlap) >= 1)

    return {
        "checked": True,
        "related": related,
        "weak_match": weak_match,
        "score": round(score, 3),
        "matched_terms": sorted(overlap)[:12],
        "message": (
            "The uploaded evidence appears related to the described grievance."
            if related
            else (
                "The uploaded evidence has a weak connection to the described grievance. I can use it cautiously, but it should not be treated as strong proof yet."
                if weak_match
                else "The uploaded evidence does not clearly match the described grievance. I can still help with the grievance text, but this upload should not be treated as supporting evidence yet."
            )
        ),
    }
