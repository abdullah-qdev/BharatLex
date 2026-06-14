from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import uuid
import os
import time

from app.services.pipeline import process_audio
app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):
    # generate request id for tracing
    request_id = str(uuid.uuid4())

    start_time = time.time()

    # preserve original extension (helps choose correct codec)
    orig_name = getattr(file, 'filename', '') or ''
    _, ext = os.path.splitext(orig_name)
    if not ext:
        ext = '.ogg'
    file_path = f"{UPLOAD_DIR}/{request_id}{ext}"

    try:
        # save incoming upload to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # process audio - this can raise errors from downstream services
        result = await process_audio(file_path)

        end_time = time.time()

        return {
            "request_id": request_id,
            "status": "success",
            "processing_time": round(end_time - start_time, 2),
            "data": result
        }

    except Exception as exc:
        # log exception server-side for debugging
        import traceback
        tb = traceback.format_exc()
        print(f"Error processing request {request_id}:", exc)
        print(tb)

        # attempt to remove the file if it exists
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

        # return a JSON error (helps the frontend avoid HTML error pages)
        return {
            "request_id": request_id,
            "status": "error",
            "message": str(exc),
            "trace": tb
        }


@app.get('/ping')
async def ping():
    return {"status": "ok", "message": "BharatLex backend alive"}


@app.get('/demo-analyze')
async def demo_analyze():
    """Returns a demo/mock response for testing frontend without real audio."""
    return {
        "request_id": "demo-12345",
        "status": "success",
        "processing_time": 2.5,
        "data": {
            "transcript": "[DEMO MODE] I ordered a laptop from Amazon 2 weeks ago. It arrived damaged with a broken screen. Customer support is not responding to my emails. I want a refund or replacement immediately.",
            "category": "consumer",
            "analysis": {
                "summary": "Damaged product received from e-commerce platform with unresponsive customer support",
                "issue_type": "product defect and service failure",
                "applicable_laws": [
                    "Consumer Protection Act 2019 - Section 2(7)",
                    "Indian Penal Code - Section 406 (criminal breach of trust)"
                ],
                "possible_actions": [
                    "File complaint with District Consumer Redressal Commission",
                    "Send legal notice to the seller",
                    "File complaint with National Consumer Helpline"
                ],
                "evidence_needed": [
                    "Order receipt and delivery proof",
                    "Photographs of damaged laptop",
                    "Email communications with support",
                    "Warranty documents"
                ]
            },
            "opponent": {
                "opponent_argument": "The product damage claim lacks substantiation. Our delivery partner followed proper protocols, and the complainant has not provided photographic evidence taken at the time of delivery. Our terms clearly state that the receiver must inspect within 24 hours.",
                "counter_points": [
                    "No inspection report filed at time of delivery",
                    "Unilateral claim of damage without supporting documentation",
                    "Complainant's failure to follow dispute resolution procedure"
                ],
                "likely_defense_strategy": "Challenge the timeline and demand contemporaneous proof. Assert that any damage occurred post-delivery due to mishandling by the recipient."
            }
        }
    }
