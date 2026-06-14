import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import get_settings
from app.services.quad_polar_agents import AgentResponse
from app.services.retriever import RetrievedChunk


class GroqError(RuntimeError):
    pass


SYSTEM_PROMPT = """You are BharatLex's final customer-facing synthesis layer.
Use only the retrieved RAG evidence and the supported parts of the four Ollama agent responses.
Reject any legal fact, deadline, forum, address, notice requirement, or remedy that is not grounded in retrieved chunks.
If the retrieved evidence is insufficient, say so directly.

Write for a normal person, not a lawyer. Do not start with generic phrases like "you can file a product liability claim".
Start with the user's immediate practical position in plain language.
Be specific about what the evidence supports: replacement, refund/return of price, compensation, forum, missing proof, and uncertainty.
Do not say legal notice is required or "may be needed" unless the retrieved evidence explicitly says so.

Use this exact structure:
1. Short Answer
2. What You Should Do Now
3. What To Prepare
4. What Is Still Unclear
5. Legal Notice
6. Citations

Citation style:
- Put citations only in section 6 at the bottom.
- Use numbered citations like [1], [2], [3].
- In earlier sections, refer to those citation numbers only.
- Each citation must include chunk_id, document title, page range if available, and the specific supported point.
Keep the full answer concise and non-overwhelming."""


def synthesize_answer(
    query: str,
    chunks: list[RetrievedChunk],
    agent_responses: list[AgentResponse],
) -> str:
    settings = get_settings()
    if not settings.groq_api_key:
        raise GroqError("Missing GROQ_API_KEY in backend/.env")

    for proxy_key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        os.environ.pop(proxy_key, None)

    payload = {
        "model": settings.groq_model,
        "temperature": 0.2,
        "max_tokens": 900,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "user_question": query,
                        "retrieved_evidence": [chunk.to_dict() for chunk in chunks],
                        "ollama_agent_responses": [
                            response.to_dict() for response in agent_responses
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            },
        ],
    }

    request = Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "BharatLex/0.1",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise GroqError(f"Groq API error {exc.code}: {detail}") from exc
    except URLError as exc:
        raise GroqError(f"Could not reach Groq API: {exc}") from exc

    choices = data.get("choices") or []
    if not choices:
        raise GroqError(f"Groq returned no choices: {data}")

    content = ((choices[0].get("message") or {}).get("content") or "").strip()
    if not content:
        raise GroqError(f"Groq returned an empty final answer: {data}")

    return content
