from app.config import get_settings
from app.services.gemini_client import GeminiError
from app.services.groq_client import GroqError
from app.services.quad_polar_agents import AgentResponse
from app.services.retriever import RetrievedChunk


class FinalSynthesisError(RuntimeError):
    pass


def synthesize_final_answer(
    query: str,
    chunks: list[RetrievedChunk],
    agent_responses: list[AgentResponse],
) -> str:
    settings = get_settings()

    if settings.final_synthesis_provider == "groq":
        try:
            from app.services.groq_client import synthesize_answer

            return synthesize_answer(query, chunks, agent_responses)
        except GroqError as exc:
            raise FinalSynthesisError(str(exc)) from exc

    if settings.final_synthesis_provider == "gemini":
        try:
            from app.services.gemini_client import synthesize_answer

            return synthesize_answer(query, chunks, agent_responses)
        except GeminiError as exc:
            raise FinalSynthesisError(str(exc)) from exc

    raise FinalSynthesisError(
        "FINAL_SYNTHESIS_PROVIDER must be either 'groq' or 'gemini'."
    )
