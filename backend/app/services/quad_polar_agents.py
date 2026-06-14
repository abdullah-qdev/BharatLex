import json
from dataclasses import dataclass, asdict

from app.config import get_settings
from app.services.ollama_client import chat
from app.services.retriever import RetrievedChunk


@dataclass(frozen=True)
class AgentProfile:
    key: str
    name: str
    role: str


@dataclass(frozen=True)
class AgentResponse:
    round_number: int
    agent_key: str
    agent_name: str
    role: str
    response: str

    def to_dict(self) -> dict:
        return asdict(self)


AGENTS = [
    AgentProfile(
        key="statutory_purist",
        name="Statutory Purist",
        role="State the strict legal position supported by the retrieved statute excerpts, sections, clauses, forums, and deadlines.",
    ),
    AgentProfile(
        key="aggressive_advocate",
        name="Aggressive Advocate",
        role="Build the strongest user-side claim and remedy path that remains grounded in the retrieved evidence.",
    ),
    AgentProfile(
        key="skeptic",
        name="Skeptic",
        role="Find missing facts, weak claims, unsupported assumptions, and places where the evidence is insufficient.",
    ),
    AgentProfile(
        key="pragmatist",
        name="Pragmatist",
        role="Turn the retrieved evidence into the cheapest, fastest, realistic workflow, including escalation timing and notice or filing steps only when supported.",
    ),
]


SYSTEM_PROMPT = """You are one constrained BharatLex debate agent.
You must use only the retrieved RAG evidence supplied by the backend.
Do not add legal sections, deadlines, forums, addresses, remedies, or procedures unless they appear in the evidence.
If the evidence is insufficient, say exactly what cannot be concluded.
Cite chunk IDs for every legal or procedural claim.
Do not reveal chain-of-thought or private reasoning. Give only the final concise analysis.
Stay under 180 words.
Return concise plain text with exactly these labels:
Position:
Evidence Used:
Missing Information:
Unsupported/Unsafe Claims:
Confidence:"""


def _context_block(chunks: list[RetrievedChunk]) -> str:
    records = []
    for chunk in chunks:
        records.append(
            {
                "chunk_id": chunk.chunk_id,
                "document_title": chunk.document_title,
                "category": chunk.category,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "citation": chunk.citation or {},
                "text": chunk.text,
            }
        )
    return json.dumps(records, ensure_ascii=False, indent=2)


def _prior_block(responses: list[AgentResponse]) -> str:
    if not responses:
        return ""

    return "\n\n".join(
        f"[Round {response.round_number}] {response.agent_name}:\n{response.response}"
        for response in responses
    )


def run_agents(query: str, chunks: list[RetrievedChunk]) -> list[AgentResponse]:
    settings = get_settings()
    evidence = _context_block(chunks)
    responses: list[AgentResponse] = []
    rounds = max(1, min(settings.debate_rounds, 3))

    for round_number in range(1, rounds + 1):
        prior = _prior_block(responses)
        round_instruction = (
            "Give your first evidence-bound position."
            if round_number == 1
            else (
                "Review the prior debate. Name one point you agree with, one point you challenge, "
                "and your revised evidence-bound position. Do not repeat points unless necessary."
            )
        )

        for agent in AGENTS:
            user_prompt = f"""User question:
{query}

Debate round:
{round_number}

Your debate role:
{agent.role}

Retrieved evidence:
{evidence}

Prior debate:
{prior or "None"}

Instruction:
{round_instruction}"""
            responses.append(
                AgentResponse(
                    round_number=round_number,
                    agent_key=agent.key,
                    agent_name=agent.name,
                    role=agent.role,
                    response=chat(SYSTEM_PROMPT, user_prompt),
                )
            )

    return responses
