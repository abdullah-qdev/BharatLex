import shutil

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.ocr_service import (
    OcrError,
    available_languages,
    extract_text_from_image,
    temporary_image_path,
)
from app.routes.rag import AskRequest, run_rag_pipeline
from app.services.evidence_matcher import compare_evidence_to_description


router = APIRouter(prefix="/api/ocr", tags=["ocr"])


def _normalize_lang(lang: str) -> str:
    return "+".join(part for part in lang.replace(" ", "+").split("+") if part)


@router.get("/languages")
def ocr_languages() -> dict:
    try:
        languages = available_languages()
    except OcrError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "ok": True,
        "languages": languages,
        "hindi_available": "hin" in languages,
    }


@router.post("/image")
async def ocr_image(
    file: UploadFile = File(...),
    lang: str = "eng+hin",
    preprocess: bool = True,
) -> dict:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload an image file.")

    temp_path = temporary_image_path(file.filename or "upload.png")
    try:
        with temp_path.open("wb") as output:
            shutil.copyfileobj(file.file, output)

        normalized_lang = _normalize_lang(lang)
        text = extract_text_from_image(str(temp_path), lang=normalized_lang, preprocess=preprocess)
    except OcrError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        temp_path.unlink(missing_ok=True)

    return {
        "ok": True,
        "filename": file.filename,
        "language": normalized_lang,
        "preprocessed": preprocess,
        "text": text,
        "character_count": len(text),
    }


@router.post("/ask")
async def ocr_ask(
    file: UploadFile = File(...),
    lang: str = "eng",
    preprocess: bool = True,
    description: str | None = None,
    include_final: bool = True,
    debug: bool = False,
    save_conversation: bool = True,
) -> dict:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload an image file.")

    temp_path = temporary_image_path(file.filename or "upload.png")
    try:
        with temp_path.open("wb") as output:
            shutil.copyfileobj(file.file, output)

        normalized_lang = _normalize_lang(lang)
        text = extract_text_from_image(str(temp_path), lang=normalized_lang, preprocess=preprocess)
    except OcrError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        temp_path.unlink(missing_ok=True)

    if len(text.strip()) < 10:
        raise HTTPException(
            status_code=422,
            detail="OCR did not extract enough text to analyze. Upload a clearer image.",
        )

    evidence_match = compare_evidence_to_description(description, text)
    question = description.strip() if description else text
    if description and (evidence_match.get("related") or evidence_match.get("weak_match")):
        question = (
            f"{description.strip()}\n\n"
            f"Uploaded evidence OCR text. Evidence relation: {evidence_match['message']}\n{text}"
        )

    result = run_rag_pipeline(
        AskRequest(
            question=question,
            category=None,
            include_final=include_final,
            debug=debug,
            save_conversation=save_conversation,
        )
    )
    result["input_source"] = {
        "type": "ocr_image",
        "filename": file.filename,
        "language": normalized_lang,
        "preprocessed": preprocess,
        "ocr_text": text,
        "ocr_character_count": len(text),
        "evidence_match": evidence_match,
    }
    return result
