import re
import unicodedata

def clean_text(raw: str) -> str:
    """
    Cleans typed input. Fixes Hindi unicode, removes noise.
    """
    text = unicodedata.normalize("NFKC", raw)       # fixes Hindi devanagari issues
    text = re.sub(r'\s+', ' ', text).strip()         # collapse extra whitespace
    text = re.sub(r'[^\w\s\.\,\!\?\-\u0900-\u097F]', '', text)  # keep Hindi range
    return text

async def clean_stt_output(raw_transcript: str, gemini_service) -> str:
    """
    Passes noisy STT output through Gemini for cleanup before RAG.
    Only call this for speech path, not typed text.
    """
    prompt = f"""This is a speech-to-text transcript of a legal complaint in Hindi or English.
Fix any transcription errors only.
Preserve all names, company names, amounts, dates, and order IDs exactly as spoken.
Return only the corrected text, nothing else, no explanation.

Transcript: {raw_transcript}"""

    return await gemini_service.generate(prompt)