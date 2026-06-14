import json
import re
from app.core.groq_client import client


SYSTEM_PROMPT = """
You are BharatLex, an AI legal assistant for Indian law.

You analyze user complaints and convert them into structured legal guidance.

STRICT RULES:
- Use ONLY the information present in the transcript.
- Do NOT assume or invent details (no laptops, no prices, no fake scenarios).
- If information is missing, leave it as unknown.
- Do NOT create a story.

Focus on Indian legal system:
- Consumer Protection Act 2019
- IT Act 2000
- Indian Penal Code (IPC) where relevant
- Labour laws for workplace cases

Return ONLY valid JSON:

{
  "summary": "short explanation of issue",
  "issue_type": "string",
  "applicable_laws": ["law1", "law2"],
  "possible_actions": ["action1", "action2"],
  "evidence_needed": ["evidence1", "evidence2"]
}

Do not include explanations or extra text.
"""


def safe_parse(text):
    try:
        return json.loads(text)

    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)

        if match:
            return json.loads(match.group())

        return {
            "summary": "Unable to analyze",
            "issue_type": "unknown",
            "applicable_laws": [],
            "possible_actions": [],
            "evidence_needed": []
        }


def analyze_case(transcript, category):
    try:
        prompt = SYSTEM_PROMPT + f"""

Category:
{category}

Transcript:
{transcript}
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )

        text = response.choices[0].message.content

        return safe_parse(text)

    except Exception as e:
        return {
            "summary": str(e),
            "issue_type": category,
            "applicable_laws": [],
            "possible_actions": [],
            "evidence_needed": []
        }