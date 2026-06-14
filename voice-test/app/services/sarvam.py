import os
from dotenv import load_dotenv
from sarvamai import AsyncSarvamAI

load_dotenv()

_SARVAM_KEY = os.getenv("SARVAM_API_KEY")
client = None

if _SARVAM_KEY:
    try:
        client = AsyncSarvamAI(api_subscription_key=_SARVAM_KEY)
    except Exception as e:
        print("❌ Failed to initialize Sarvam client:", e)


async def transcribe_audio(file_path: str):
    """
    Transcribe audio file using Sarvam STT.
    No codec hinting — let Sarvam auto-detect from file content.
    Returns transcript string, or None if STT fails.
    """
    if not client:
        print("❌ Sarvam client not initialized — check SARVAM_API_KEY in .env")
        return None

    file_size = os.path.getsize(file_path)
    print(f"🎙️  Transcribing: {file_path} ({file_size} bytes)")

    try:
        with open(file_path, "rb") as audio:
            response = await client.speech_to_text.transcribe(
                file=audio,
                model="saaras:v3",
                language_code="unknown",  # auto-detect language
            )

        transcript = response.transcript.strip() if response and response.transcript else None
        print(f"✅ STT SUCCESS: {transcript}")
        return transcript if transcript else None

    except Exception as e:
        print(f"⚠️ STT FAILED: {str(e)[:200]}")
        return None
