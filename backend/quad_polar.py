"""
quad_polar.py — the engine.

  RAG (your folder)  ->  4 local Ollama personalities debate (N rounds)
                      ->  Gemini reads the whole debate and renders the verdict.

Run order:
    1. python corpus.py     # builds the RAG index from ./statutes
    2. python run.py        # temporary command-line input (see run.py)
"""

from __future__ import annotations
import os
import json
import asyncio

from ollama import AsyncClient
from google import genai
from google.genai import types

from corpus import search as retrieve_statutes   # local numpy RAG (corpus.py)

# ======================= CONFIG — change these ===========================
# >>> PUT YOUR GEMINI API KEY HERE (from https://aistudio.google.com/apikey)
# Either export GEMINI_API_KEY in your shell, or paste it inside the quotes.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "PASTE-YOUR-GEMINI-KEY-HERE")

OLLAMA_MODEL = "llama3.1"            # the 4 debaters. Lighter+faster: "qwen2.5:7b"
GEMINI_MODEL = "gemini-3.5-flash"   # the judge. For deeper reasoning use a pro tier.
DEBATE_ROUNDS = 2                   # round 2+ = agents react to each other
# =========================================================================

ollama = AsyncClient()
gemini = genai.Client(api_key=GEMINI_API_KEY)

# Categories -> which laws retrieval should pull. Keep filenames in ./statutes
# matching these strings (see corpus.py).
CATEGORY_LAWS = {
    "consumer":  ["Consumer Protection Act 2019", "Consumer Protection (E-Commerce) Rules 2020"],
    "cyber":     ["IT Act 2000 (Amendment 2008)", "BNS Section 318", "BNS Section 316"],
    "workplace": ["POSH Act 2013", "Industrial Disputes provisions", "Code on Wages 2019"],
    "banking":   ["RBI Integrated Ombudsman Scheme"],
    "insurance": ["IRDAI Bima Bharosa (IGMS)", "Insurance Ombudsman"],
}

# >>> THE FOUR POLES. Edit names / system prompts freely to change personalities.
PERSONALITIES = [
    {"name": "Statutory Purist",
     "system": "You are a strict Indian legal analyst. Use ONLY the provided statute "
               "excerpts. Cite specific sections. If the law does not clearly cover a "
               "point, say so plainly. Never invent a section."},
    {"name": "Aggressive Advocate",
     "system": "You fight for the aggrieved person's maximum remedy. Identify the "
               "strongest claims, the highest relief available, and the most assertive "
               "(but lawful) path. Push hard, but stay grounded in the excerpts."},
    {"name": "Skeptic",
     "system": "You are the devil's advocate. Attack the case: weak or missing evidence, "
               "limitation/time bars, jurisdiction problems, procedural traps, anything a "
               "defendant or authority would use to defeat it. Be specific."},
    {"name": "Pragmatist",
     "system": "You optimise for the cheapest, fastest, realistic route to a result. "
               "Weigh effort vs payoff. Prefer ombudsman/mediation/online portals over "
               "litigation where sensible. Note costs, time, and practical friction."},
]

JUDGE_SYSTEM = (
    "You are the presiding judge over a four-way advisory debate about an Indian legal "
    "grievance. You did not participate; you now read the full debate and the statute "
    "excerpts and produce the final answer for the user. Weigh the advocate's ambition "
    "against the skeptic's warnings and the pragmatist's realism, anchored by the "
    "purist's citations. Output JSON only with this shape: "
    '{"summary": "", "applicable_law": [{"law":"","section":"","why":""}], '
    '"forum": "", "tasks": [{"step":"","detail":"","deadline":""}], '
    '"documents": [], "relief": "", "needs_notice": true, '
    '"confidence": "low|medium|high"}'
)


def parse(text, fallback):
    try:
        return json.loads(text.replace("```json", "").replace("```", "").strip())
    except Exception:
        return fallback


async def ollama_say(system: str, user: str, fmt: str | None = None) -> str:
    resp = await ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        format=fmt or "",                    # "json" constrains output to valid JSON
    )
    return resp["message"]["content"]


async def intake(grievance_text: str, user_facts: dict) -> dict:
    sys = ('Extract a structured fact set from this Indian grievance. Respond with a '
           'JSON object having exactly two keys: "facts" (an object of key facts) and '
           '"missing_info" (a list of strings naming essential facts that are missing).')
    out = parse(await ollama_say(sys,
        f"Grievance: {grievance_text}\nKnown: {json.dumps(user_facts)}",
        fmt="json"), {})
    if not isinstance(out, dict):
        out = {}
    # Normalize: some local models put the facts at the top level instead of under "facts".
    facts = out.get("facts")
    if not isinstance(facts, dict):
        facts = {k: v for k, v in out.items() if k not in ("facts", "missing_info")}
    missing = out.get("missing_info")
    if not isinstance(missing, list):
        missing = []
    return {"facts": facts, "missing_info": missing}


async def debate(grievance: str, facts: dict, statutes: list) -> list:
    """N rounds. Each round all four speak in parallel; later rounds see prior ones."""
    transcript, prior = [], ""
    base = (f"Grievance: {grievance}\n"
            f"Facts: {json.dumps(facts)}\n"
            f"Statute excerpts:\n{json.dumps(statutes, indent=2)}\n")

    for r in range(DEBATE_ROUNDS):
        ctx = base
        if prior:
            ctx += (f"\nWhat the other advisors argued last round:\n{prior}\n"
                    "Respond to them — agree, refine, or push back. Be concise.")
        replies = await asyncio.gather(*[
            ollama_say(p["system"], ctx + f"\n(You are the {p['name']}.)")
            for p in PERSONALITIES
        ])
        turn = [{"round": r + 1, "name": p["name"], "text": t}
                for p, t in zip(PERSONALITIES, replies)]
        transcript += turn
        prior = "\n\n".join(f"{m['name']}: {m['text']}" for m in turn)

    return transcript


async def judge(grievance: str, facts: dict, statutes: list, transcript: list) -> dict:
    convo = "\n\n".join(f"[Round {m['round']}] {m['name']}:\n{m['text']}" for m in transcript)
    contents = (f"Grievance: {grievance}\nFacts: {json.dumps(facts)}\n\n"
                f"Statute excerpts:\n{json.dumps(statutes, indent=2)}\n\n"
                f"The debate:\n{convo}")
    # google-genai client is sync; run it off the event loop.
    resp = await asyncio.to_thread(
        gemini.models.generate_content,
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=JUDGE_SYSTEM,
            response_mime_type="application/json",
        ),
    )
    return parse(resp.text, {"summary": resp.text, "tasks": [], "needs_notice": False})


async def draft_notice(grievance: str, verdict: dict, statutes: list) -> str:
    contents = ("Draft a formal legal notice under Indian law from the aggrieved party. "
                "Include parties, facts, the provisions relied on, the demand, a compliance "
                "period, and consequences. Mark every user-supplied blank as [SQUARE BRACKETS].\n\n"
                f"Grievance: {grievance}\nVerdict: {json.dumps(verdict)}\n"
                f"Statutes: {json.dumps(statutes)}")
    resp = await asyncio.to_thread(
        gemini.models.generate_content, model=GEMINI_MODEL, contents=contents)
    return resp.text


# ===========================================================================
# >>> INTEGRATION POINT — your real input UI calls this one function.
# ===========================================================================
async def run_grievance_pipeline(grievance_text: str, category: str,
                                 user_facts: dict | None = None) -> dict:
    intake_out = await intake(grievance_text, user_facts or {})
    if intake_out.get("missing_info"):
        return {"status": "needs_input", "questions": intake_out["missing_info"]}

    facts = intake_out.get("facts", {})
    statutes = await retrieve_statutes(grievance_text, CATEGORY_LAWS.get(category, []))
    transcript = await debate(grievance_text, facts, statutes)
    verdict = await judge(grievance_text, facts, statutes, transcript)

    if verdict.get("needs_notice"):
        verdict["notice_draft"] = await draft_notice(grievance_text, verdict, statutes)

    verdict["status"] = "done"
    verdict["transcript"] = transcript      # so your UI can show the debate
    return verdict
