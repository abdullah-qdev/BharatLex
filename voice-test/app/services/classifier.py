import json
from app.core.groq_client import client


SYSTEM_PROMPT = """
You are a STRICT legal issue classifier for Indian law.

You MUST choose exactly ONE category:

consumer:
- refunds, shopping issues, defective products, e-commerce, banking complaints, seller fraud

cyber:
- UPI fraud, OTP scam, phishing, hacking, account theft, online harassment, identity theft

workplace:
- salary delay, termination, firing, workplace harassment, internships, contract disputes, PF/HR issues

CRITICAL RULES:
- salary/employment = ALWAYS workplace
- digital money fraud = ALWAYS cyber
- product/service purchase = ONLY consumer

OUTPUT FORMAT:
{
  "category": "consumer" | "cyber" | "workplace"
}
"""


def safe_parse(text: str):
    try:
        return json.loads(text)
    except Exception:
        print("❌ JSON PARSE FAILED:", text)
        return {
            "category": "unknown",
            "raw_output": text
        }


def classify_text(transcript: str):
    try:
        # 🚨 HARD GUARD: prevent garbage input
        if not transcript or len(transcript.strip()) < 3:
            return {
                "category": "unknown",
                "error": "empty_or_invalid_transcript"
            }

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": transcript}
            ],
            temperature=0.1,
            max_tokens=80,
            top_p=0.9
        )

        text = response.choices[0].message.content.strip()

        print("🧠 RAW GROQ OUTPUT:", text)

        return safe_parse(text)

    except Exception as e:
        print("❌ CLASSIFIER ERROR:", str(e))
        return {
            "category": "unknown",
            "error": str(e)
        }