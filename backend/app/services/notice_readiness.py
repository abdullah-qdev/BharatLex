import re


NOTICE_REQUIRED_FIELDS = {
    "name": [
        r"\bmy name is\b",
        r"\bi am\b",
        r"\bfrom\b",
    ],
    "opposite_party": [
        r"\bshop\b",
        r"\bseller\b",
        r"\bcompany\b",
        r"\bemployer\b",
        r"\bbank\b",
    ],
    "date_or_timeline": [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\byesterday\b",
        r"\btoday\b",
        r"\blast week\b",
        r"\b\d+\s+(day|days|week|weeks|month|months)\s+ago\b",
    ],
    "desired_remedy": [
        r"\brefund\b",
        r"\breplace\b",
        r"\breplacement\b",
        r"\bcompensation\b",
        r"\brepair\b",
    ],
}


def assess_notice_readiness(question: str, final_answer: str | None) -> dict:
    text = f"{question}\n{final_answer or ''}".lower()
    missing: list[str] = []

    for field, patterns in NOTICE_REQUIRED_FIELDS.items():
        if not any(re.search(pattern, text) for pattern in patterns):
            missing.append(field)

    unsupported_phrases = [
        "cannot be confirmed",
        "not confirmed",
        "not required",
        "no specific legal notice",
        "not supported",
        "insufficient evidence",
    ]
    notice_supported = (
        bool(final_answer)
        and "legal notice" in final_answer.lower()
        and not any(phrase in final_answer.lower() for phrase in unsupported_phrases)
    )
    can_draft = notice_supported and not missing

    questions = []
    labels = {
        "name": "your full name",
        "opposite_party": "the shop/company/person you want to send the notice to",
        "date_or_timeline": "the purchase date and when you discovered the issue",
        "desired_remedy": "what you want: refund, replacement, repair, or compensation",
    }
    if notice_supported and missing:
        questions = [f"Please provide {labels[field]}." for field in missing]

    return {
        "notice_supported_by_answer": notice_supported,
        "can_draft_notice": can_draft,
        "missing_fields": missing,
        "questions": questions,
    }
