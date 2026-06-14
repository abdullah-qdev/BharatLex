import json
import re

from app.core.groq_client import client

SYSTEM_PROMPT = """
You are a professional legal opponent in Indian dispute scenarios.

Your job is to argue AGAINST the user’s claim as if you are:
- a company lawyer
- employer HR/legal team
- or accused party defense counsel

You MUST be realistic, strategic, and legally grounded.

DO NOT be emotional. DO NOT be vague.

INPUT:
You will receive a legal case summary.

OUTPUT FORMAT (STRICT JSON):

{
  "opponent_argument": "strong structured legal defense",
  "counter_points": [
    "legal or factual challenge 1",
    "legal or procedural challenge 2",
    "evidence weakness or inconsistency"
  ],
  "likely_defense_strategy": "overall legal strategy used by opponent",
  "pressure_points": [
    "what weakens the user's case most",
    "what evidence would destroy their claim"
  ]
}

RULES:

- Always assume opponent is rational and defensive, not malicious.
- Focus on:
  - lack of evidence
  - procedural gaps
  - contractual loopholes
  - jurisdiction/legal ambiguity
- NEVER agree with user claim.
- NEVER give advice to user.
- ALWAYS build a defendable opposing case.

Be realistic like an Indian corporate lawyer or defendant advocate.
"""


def safe_parse(text):
    try:
        return json.loads(text)

    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)

        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass

        return {
            "opponent_argument": "Unable to generate defense",
            "counter_points": [],
            "likely_defense_strategy": ""
        }


def generate_opponent(transcript, category, analysis):
    try:
        prompt = SYSTEM_PROMPT + f"""

Category:
{category}

Complaint:
{transcript}

Analysis:
{analysis}
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        text = response.choices[0].message.content

        return safe_parse(text)

    except Exception as e:
        return {
            "opponent_argument": str(e),
            "counter_points": [],
            "likely_defense_strategy": ""
        }