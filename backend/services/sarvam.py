import httpx
import os

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """
    Sends audio to Sarvam STT, returns raw transcript text.
    Supports WAV, MP3, WebM (browser recording default).
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.sarvam.ai/speech-to-text",
            headers={"api-subscription-key": SARVAM_API_KEY},
            files={"file": (filename, audio_bytes, "audio/wav")},
            data={
                "model": "saaras:v3",
                "mode": "transcribe",  # keeps original language
                "language_code": "hi-IN"  # handles Hindi + English both
            },
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()
        return result.get("transcript", "")