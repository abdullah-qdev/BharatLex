import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.config import get_settings


class OllamaError(RuntimeError):
    pass


def _post_json(path: str, payload: dict, timeout: int = 120) -> dict:
    settings = get_settings()
    url = f"{settings.ollama_base_url.rstrip('/')}{path}"
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        raise OllamaError(f"Could not reach Ollama at {settings.ollama_base_url}") from exc


def embed_text(text: str) -> list[float]:
    settings = get_settings()
    payload = {"model": settings.ollama_embedding_model, "input": text}

    try:
        response = _post_json("/api/embed", payload, timeout=120)
        embeddings = response.get("embeddings") or []
        if embeddings:
            return [float(value) for value in embeddings[0]]
    except OllamaError:
        raise
    except Exception:
        pass

    legacy_response = _post_json(
        "/api/embeddings",
        {"model": settings.ollama_embedding_model, "prompt": text},
        timeout=120,
    )
    embedding = legacy_response.get("embedding")
    if not embedding:
        raise OllamaError("Ollama did not return an embedding.")

    return [float(value) for value in embedding]


def chat(system_prompt: str, user_prompt: str) -> str:
    settings = get_settings()
    payload = {
        "model": settings.ollama_chat_model,
        "stream": False,
        "options": {
            "num_predict": settings.ollama_num_predict,
            "temperature": settings.ollama_temperature,
        },
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if settings.ollama_disable_thinking:
        payload["think"] = False

    response = _post_json("/api/chat", payload, timeout=180)
    message = response.get("message") or {}
    content = message.get("content", "").strip()
    if not content:
        thinking = message.get("thinking", "").strip()
        if thinking:
            raise OllamaError("Ollama returned only thinking output. Disable thinking or use a non-thinking model.")
        raise OllamaError(f"Ollama did not return a chat response. done_reason={response.get('done_reason')}")
    return content
