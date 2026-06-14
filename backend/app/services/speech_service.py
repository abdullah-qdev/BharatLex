import os
import shutil
import uuid
from pathlib import Path


class SpeechError(RuntimeError):
    pass


UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"


def temporary_audio_path(filename: str) -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename).suffix or ".ogg"
    return UPLOAD_DIR / f"{uuid.uuid4()}{suffix}"


def save_upload_to_path(file, destination: Path) -> None:
    with destination.open("wb") as output:
        shutil.copyfileobj(file, output)


async def transcribe_audio_file(file_path: str) -> str:
    api_key = os.getenv("SARVAM_API_KEY", "").strip()
    if not api_key:
        raise SpeechError("Missing SARVAM_API_KEY in backend/.env")

    try:
        from sarvamai import AsyncSarvamAI
    except ImportError as exc:
        raise SpeechError("Missing sarvamai. Install backend requirements.") from exc

    client = AsyncSarvamAI(api_subscription_key=api_key)
    try:
        with open(file_path, "rb") as audio:
            response = await client.speech_to_text.transcribe(
                file=audio,
                model=os.getenv("SARVAM_STT_MODEL", "saaras:v3"),
                language_code=os.getenv("SARVAM_LANGUAGE_CODE", "unknown"),
            )
    except Exception as exc:
        raise SpeechError(f"Sarvam transcription failed: {exc}") from exc

    transcript = getattr(response, "transcript", None)
    if not transcript or not transcript.strip():
        raise SpeechError("Sarvam returned an empty transcript.")

    return transcript.strip()
