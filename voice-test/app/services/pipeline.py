from app.services.classifier import classify_text
from app.services.analyzer import analyze_case
from app.services.opponent import generate_opponent
from app.services.sarvam import transcribe_audio


async def process_audio(file):

    transcript = await transcribe_audio(file)
    print("✅ STT completed")

    category_obj = classify_text(transcript)
    category = category_obj.get("category", "consumer")
    print("✅ Classification completed")

    analysis = analyze_case(transcript, category)
    print("✅ Analysis completed")

    opponent = generate_opponent(
        transcript,
        category,
        analysis
    )
    print("✅ Opponent simulation completed")

    return {
    "status": "success",
    "transcript": transcript,
    "category": category,
    "analysis": analysis,
    "opponent": opponent,
}
