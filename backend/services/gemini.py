import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")
embedding_model = "models/gemini-embedding-001"

async def generate(prompt: str) -> str:
    response = model.generate_content(prompt)
    return response.text

async def embed(text: str) -> list[float]:
    result = genai.embed_content(
        model=embedding_model,
        content=text,
        task_type="retrieval_query",  # use retrieval_query for complaint queries
        output_dimensionality=768
    )
    return result["embedding"]        # returns 768-dim vector

async def vision_extract(image_base64: str) -> str:
    """For OCR path: extract complaint text from uploaded screenshot/bill."""
    import base64
    image_data = base64.b64decode(image_base64)
    
    prompt = """Extract all text from this image that describes a consumer complaint, 
    online scam, or workplace issue.
    Focus on: order IDs, amounts, dates, company names, what went wrong.
    Ignore watermarks, ads, unrelated UI elements.
    Return clean plain text only."""
    
    response = model.generate_content([
        {"mime_type": "image/jpeg", "data": image_data},
        prompt
    ])
    return response.text
