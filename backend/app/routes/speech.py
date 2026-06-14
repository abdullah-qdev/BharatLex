from fastapi import APIRouter, File, HTTPException, UploadFile

from app.routes.rag import AskRequest, run_rag_pipeline
from app.services.speech_service import (
    SpeechError,
    save_upload_to_path,
    temporary_audio_path,
    transcribe_audio_file,
)


router = APIRouter(prefix="/api/speech", tags=["speech"])


@router.post("/ask")
async def speech_ask(
    file: UploadFile = File(...),
    include_final: bool = True,
    debug: bool = False,
    save_conversation: bool = True,
) -> dict:
    if file.content_type and not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Upload an audio file.")

    temp_path = temporary_audio_path(file.filename or "recording.ogg")
    try:
        save_upload_to_path(file.file, temp_path)
        transcript = await transcribe_audio_file(str(temp_path))
    except SpeechError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        temp_path.unlink(missing_ok=True)

    if len(transcript.strip()) < 5:
        raise HTTPException(
            status_code=422,
            detail="Speech transcription did not contain enough text to analyze.",
        )

    result = run_rag_pipeline(
        AskRequest(
            question=transcript,
            category=None,
            include_final=include_final,
            debug=debug,
            save_conversation=save_conversation,
        )
    )
    result["input_source"] = {
        "type": "speech",
        "filename": file.filename,
        "transcript": transcript,
        "transcript_character_count": len(transcript),
    }
    return result
