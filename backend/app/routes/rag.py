from datetime import datetime, timezone
import traceback

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.database import get_database
from app.services.final_synthesizer import FinalSynthesisError, synthesize_final_answer
from app.services.legal_catalog import classify_category, get_category, list_categories
from app.services.notice_readiness import assess_notice_readiness
from app.services.ollama_client import OllamaError
from app.services.quad_polar_agents import run_agents
from app.services.retriever import retrieve_chunks


router = APIRouter(prefix="/api/rag", tags=["rag"])


def _debug_500(stage: str, exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=500,
        detail={
            "stage": stage,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(limit=5),
        },
    )


def _debate_by_round(agents: list) -> list[dict]:
    rounds: dict[int, list[dict]] = {}
    for agent in agents:
        rounds.setdefault(agent.round_number, []).append(
            {
                "agent_key": agent.agent_key,
                "agent_name": agent.agent_name,
                "role": agent.role,
                "response": agent.response,
            }
        )

    return [
        {
            "round_number": round_number,
            "turns": turns,
        }
        for round_number, turns in sorted(rounds.items())
    ]


def _debate_transcript(agents: list) -> str:
    lines: list[str] = []
    current_round = None

    for agent in sorted(agents, key=lambda item: (item.round_number, item.agent_name)):
        if agent.round_number != current_round:
            current_round = agent.round_number
            lines.append(f"Round {current_round}")
        lines.append(f"{agent.agent_name}: {agent.response}")
        lines.append("")

    return "\n".join(lines).strip()


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    category: str | None = Field(default=None, description="Optional legal category key.")
    top_k: int | None = Field(default=None, ge=1, le=20)
    include_final: bool = Field(default=True, description="Set false to test RAG + Ollama agents without Gemini.")
    debug: bool = Field(default=False, description="Return a compact response for backend testing.")
    save_conversation: bool = True


def run_rag_pipeline(request: AskRequest) -> dict:
    db = get_database()
    question = request.question.strip()
    selected_category = get_category(request.category)
    classification = None
    if not selected_category:
        classification = classify_category(question)
        detected = classification.get("category")
        if detected and classification.get("confidence") in {"high", "medium"}:
            selected_category = get_category(detected["key"])

    try:
        chunks = retrieve_chunks(
            db,
            question,
            top_k=request.top_k,
            category_key=selected_category.key if selected_category else None,
        )
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise _debug_500("retrieve_chunks", exc) from exc

    if not chunks:
        result = {
            "ok": False,
            "status": "no_relevant_evidence",
            "message": "I could not find relevant information in the available legal documents.",
            "question": question,
            "category": selected_category.to_dict() if selected_category else None,
            "category_detection": classification,
            "retrieved_chunks": [],
            "agents": [],
            "final_answer": None,
            "final_error": None,
            "notice_readiness": assess_notice_readiness(question, None),
        }
        if request.save_conversation:
            db.rag_conversations.insert_one({**result, "created_at": datetime.now(timezone.utc)})
        return result

    try:
        agents = run_agents(question, chunks)
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise _debug_500("run_agents", exc) from exc

    final_answer = None
    final_error = None
    if request.include_final:
        try:
            final_answer = synthesize_final_answer(question, chunks, agents)
        except FinalSynthesisError as exc:
            final_error = str(exc)
        except Exception as exc:
            final_error = f"{type(exc).__name__}: {exc}"

    retrieved_chunks = [chunk.to_dict() for chunk in chunks]
    agents_payload = [agent.to_dict() for agent in agents]

    if request.debug:
        retrieved_chunks = [
            {
                "chunk_id": chunk.chunk_id,
                "document_title": chunk.document_title,
                "score": chunk.score,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "citation": chunk.citation or {},
                "text_preview": chunk.text[:500],
            }
            for chunk in chunks
        ]
        agents_payload = [
            {
                "round_number": agent.round_number,
                "agent_name": agent.agent_name,
                "response_preview": agent.response[:800],
            }
            for agent in agents
        ]

    result = {
        "ok": True,
        "status": "answered" if request.include_final else "agents_complete",
        "question": question,
        "category": selected_category.to_dict() if selected_category else None,
        "category_detection": classification,
        "retrieved_chunks": retrieved_chunks,
        "agents": agents_payload,
        "debate_rounds": _debate_by_round(agents),
        "debate_transcript": _debate_transcript(agents),
        "final_answer": final_answer,
        "final_error": final_error,
        "notice_readiness": assess_notice_readiness(question, final_answer),
    }
    if request.save_conversation:
        try:
            db.rag_conversations.insert_one({**result, "created_at": datetime.now(timezone.utc)})
        except Exception as exc:
            raise _debug_500("save_conversation", exc) from exc

    return result


@router.get("/categories")
def categories() -> dict:
    return {"categories": list_categories()}


@router.post("/ask")
def ask_rag(request: AskRequest) -> dict:
    return run_rag_pipeline(request)
