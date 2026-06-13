import json
from services.mongodb import legal_docs
from services import gemini

async def retrieve_and_analyse(clean_transcript: str, category: str) -> dict:
    
    # 1. embed the complaint
    query_vector = await gemini.embed(clean_transcript)
    
    # 2. vector search filtered by category
    pipeline = [
        {
            "$vectorSearch": {
                "index": "legal_docs_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 50,
                "limit": 5,
                "filter": {"category": category}
            }
        },
        {
            "$project": {
                "section_number": 1,
                "section_text": 1,
                "act_name": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    
    sections = list(legal_docs.aggregate(pipeline))
    
    if not sections:
        return {"error": "No relevant law found for this complaint category."}
    
    # 3. build context string
    context = "\n\n".join([
        f"{s['act_name']} — {s['section_number']}:\n{s['section_text']}"
        for s in sections
    ])
    
    # 4. structured output prompt
    prompt = f"""You are a legal analysis engine for Indian consumer law.
Given the complaint and law sections below, return ONLY valid JSON with no extra text, 
no markdown, no explanation.

Complaint: {clean_transcript}

Relevant Law:
{context}

Return exactly this JSON:
{{
    "applicable_act": "",
    "section_number": "",
    "section_text": "",
    "violation_type": "",
    "forum": "",
    "forum_address": "",
    "filing_deadline": "",
    "recommended_action": "",
    "citations": []
}}"""
    
    raw = await gemini.generate(prompt)
    
    # 5. safe parse — Gemini sometimes wraps in backticks
    clean = raw.strip().replace("```json", "").replace("```", "").strip()
    
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        # fallback: ask Gemini to fix its own output
        fix_prompt = f"The following is malformed JSON. Fix it and return only valid JSON:\n{clean}"
        fixed = await gemini.generate(fix_prompt)
        return json.loads(fixed.strip().replace("```json","").replace("```","").strip())