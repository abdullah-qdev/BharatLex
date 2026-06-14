from dataclasses import dataclass, asdict


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
