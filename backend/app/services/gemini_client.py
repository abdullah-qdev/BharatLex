import json
import os

from app.config import get_settings
from app.services.quad_polar_agents import AgentResponse
from app.services.retriever import RetrievedChunk


class GeminiError(RuntimeError):
    pass


SYSTEM_INSTRUCTION = """You are BharatLex's final synthesis layer.
Use only the retrieved RAG evidence and the supported parts of the four Ollama agent responses.
Reject any legal fact, deadline, forum, address, notice requirement, or remedy that is not grounded in retrieved chunks.
If the retrieved evidence is insufficient, say so directly.
Produce a practical workflow with conclusion, next steps, escalation timing, legal notice applicability, missing information, and citations."""


def synthesize_answer(
    query: str,
    chunks: list[RetrievedChunk],
    agent_responses: list[AgentResponse],
) -> str:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise GeminiError("Missing GEMINI_API_KEY in backend/.env")

    for proxy_key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        os.environ.pop(proxy_key, None)

    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise GeminiError("Install backend requirements to enable Gemini synthesis.") from exc

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        settings.gemini_model,
        system_instruction=SYSTEM_INSTRUCTION,
    )
    payload = {
        "user_question": query,
        "retrieved_evidence": [chunk.to_dict() for chunk in chunks],
        "ollama_agent_responses": [response.to_dict() for response in agent_responses],
    }
    response = model.generate_content(json.dumps(payload, ensure_ascii=False, indent=2))
    try:
        text = (response.text or "").strip()
    except Exception as exc:
        raise GeminiError(f"Gemini response could not be read: {exc}") from exc

    if not text:
        feedback = getattr(response, "prompt_feedback", None)
        raise GeminiError(f"Gemini did not return a final answer. prompt_feedback={feedback}")
    return text
