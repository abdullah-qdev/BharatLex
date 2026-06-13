from fastapi import APIRouter, UploadFile, File, Form
from services import sarvam, gemini, rag
from utils.text_cleaner import clean_text, clean_stt_output

router = APIRouter()

@router.post("/analyze")
async def analyze_complaint(
    input_type: str = Form(...),   # "text" | "speech" | "ocr"
    text_input: str = Form(None),  # for typed text
    image_input: str = Form(None), # for OCR (base64)
    audio_file: UploadFile = File(None)  # for speech
):
    # STEP 1: get clean transcript regardless of input type
    if input_type == "text":
        transcript = clean_text(text_input)
    
    elif input_type == "speech":
        if not audio_file:
            return {"error": "No audio file provided"}
        audio_bytes = await audio_file.read()
        raw_transcript = await sarvam.transcribe_audio(audio_bytes, audio_file.filename)
        transcript = await clean_stt_output(raw_transcript, gemini)
    
    elif input_type == "ocr":
        if not image_input:
            return {"error": "No image provided"}
        transcript = await gemini.vision_extract(image_input)
    
    else:
        return {"error": "Invalid input_type"}
    
    # STEP 2: classify category
    category = await classify_category(transcript)
    
    # STEP 3: run RAG and return structured output
    result = await rag.retrieve_and_analyse(transcript, category)
    result["transcript"] = transcript   # pass forward to /draft
    result["category"] = category
    
    return result

async def classify_category(transcript: str) -> str:
    prompt = f"""Classify this legal complaint into exactly one category.
Return only the category word, nothing else.

Categories:
- consumer (Amazon, Flipkart, Zomato, telecom, product issues)
- cyber (online scam, fraud, data theft, fake website)  
- workplace (harassment, wrongful termination, wage theft)

Complaint: {transcript}"""
    
    result = await gemini.generate(prompt)
    category = result.strip().lower()
    
    if category not in ["consumer", "cyber", "workplace"]:
        return "consumer"  # safe default
    return category