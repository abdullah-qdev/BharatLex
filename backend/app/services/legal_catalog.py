from dataclasses import dataclass, asdict
import json
import re

from app.services.ollama_client import OllamaError, chat


@dataclass(frozen=True)
class LegalCategory:
    key: str
    label: str
    document_titles: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


LEGAL_CATEGORIES = [
    LegalCategory(
        key="consumer",
        label="Consumer disputes",
        document_titles=[
            "Consumer Protection Act, 2019",
            "Consumer Protection (E-Commerce) Rules, 2020",
        ],
    ),
    LegalCategory(
        key="cyber",
        label="Cyber fraud and cheating",
        document_titles=[
            "IT Act, 2000 (Amendment 2008)",
            "BNS Section 318 (Cheating)",
            "BNS Section 316 (Criminal Breach of Trust)",
        ],
    ),
    LegalCategory(
        key="workplace",
        label="Workplace and employment",
        document_titles=[
            "POSH Act, 2013",
            "Industrial Dispute Provisions",
            "Code on Wages, 2019",
        ],
    ),
    LegalCategory(
        key="banking",
        label="Banking and payments",
        document_titles=[
            "RBI Integrated Ombudsman Scheme",
        ],
    ),
]


def get_category(key: str | None) -> LegalCategory | None:
    if not key:
        return None

    normalized = key.strip().lower()
    for category in LEGAL_CATEGORIES:
        if category.key == normalized:
            return category

    return None


def list_categories() -> list[dict]:
    return [category.to_dict() for category in LEGAL_CATEGORIES]


CATEGORY_KEYWORDS = {
    "consumer": [
        "refund",
        "replacement",
        "defective",
        "broken",
        "warranty",
        "seller",
        "shop",
        "product",
        "delivery",
        "e-commerce",
        "laptop",
        "phone",
    ],
    "cyber": [
        "fraud",
        "otp",
        "upi",
        "phishing",
        "hacked",
        "scam",
        "cyber",
        "account",
        "unauthorized",
        "transaction",
    ],
    "workplace": [
        "salary",
        "wages",
        "employer",
        "workplace",
        "harassment",
        "termination",
        "fired",
        "posh",
        "office",
        "employee",
    ],
    "banking": [
        "bank",
        "loan",
        "credit card",
        "debit card",
        "rbi",
        "ombudsman",
        "atm",
        "payment",
        "chargeback",
    ],
}


def _keyword_classify_category(text: str) -> dict:
    normalized = text.lower()
    scores: dict[str, int] = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", normalized):
                score += 1
        scores[category] = score

    best_key = max(scores, key=scores.get)
    best_score = scores[best_key]
    category = get_category(best_key) if best_score else None

    if best_score >= 2:
        confidence = "high"
    elif best_score == 1:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "category": category.to_dict() if category else None,
        "confidence": confidence,
        "scores": scores,
        "reason": (
            f"Matched {best_score} keyword(s) for {best_key}."
            if category
            else "No category-specific keywords matched; retrieval should search all documents."
        ),
        "method": "keyword",
    }


def _parse_classifier_json(raw_text: str) -> dict:
    cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)


def classify_category(text: str) -> dict:
    categories = [
        {
            "key": category.key,
            "label": category.label,
            "document_titles": category.document_titles,
        }
        for category in LEGAL_CATEGORIES
    ]
    system_prompt = """Classify an Indian legal grievance into exactly one category.
Allowed categories: consumer, cyber, workplace, banking, unknown.
Use consumer for defective products, refunds, replacement, warranties, sellers, shops, e-commerce, and services.
Use cyber for scams, OTP/UPI fraud, hacking, phishing, unauthorized digital transactions.
Use workplace for wages, termination, harassment, POSH, employer/employee disputes.
Use banking for bank services, RBI ombudsman, cards, loans, account complaints.
Return JSON only with keys: category, confidence, reason.
confidence must be high, medium, or low.
If unclear, use unknown with low confidence."""
    user_prompt = json.dumps(
        {
            "grievance": text,
            "available_categories": categories,
        },
        ensure_ascii=False,
    )

    keyword_result = _keyword_classify_category(text)
    try:
        raw = chat(system_prompt, user_prompt)
        parsed = _parse_classifier_json(raw)
    except (OllamaError, json.JSONDecodeError, TypeError, ValueError):
        return keyword_result

    key = str(parsed.get("category", "")).strip().lower()
    confidence = str(parsed.get("confidence", "low")).strip().lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"

    category = get_category(key)
    if not category:
        return {
            "category": None,
            "confidence": "low",
            "reason": parsed.get("reason", "Ollama could not match a supported category."),
            "method": "ollama",
            "fallback": keyword_result,
        }

    if confidence == "low" and keyword_result.get("category"):
        return {
            **keyword_result,
            "method": "keyword",
            "ollama_low_confidence": {
                "category": category.to_dict(),
                "reason": parsed.get("reason", ""),
            },
        }

    return {
        "category": category.to_dict(),
        "confidence": confidence,
        "reason": parsed.get("reason", ""),
        "method": "ollama",
        "fallback": keyword_result,
    }
