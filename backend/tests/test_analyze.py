import pytest
import httpx

BASE_URL = "http://localhost:8000"

# TEST 1: typed text path
def test_typed_text():
    response = httpx.post(f"{BASE_URL}/analyze", data={
        "input_type": "text",
        "text_input": "I ordered a phone from Amazon for Rs 15000. It never arrived and they are refusing to refund."
    })
    assert response.status_code == 200
    data = response.json()
    assert "applicable_act" in data
    assert "forum" in data
    assert data["category"] == "consumer"
    print("TYPED TEXT RESULT:", data)

# TEST 2: speech path (needs a real audio file)
def test_speech_path():
    with open("tests/sample_hindi_complaint.wav", "rb") as f:
        response = httpx.post(f"{BASE_URL}/analyze", 
            data={"input_type": "speech"},
            files={"audio_file": ("complaint.wav", f, "audio/wav")}
        )
    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data
    assert "applicable_act" in data
    print("SPEECH RESULT:", data)

# TEST 3: OCR path (needs a base64 image)
def test_ocr_path():
    import base64
    with open("tests/sample_receipt.jpg", "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    response = httpx.post(f"{BASE_URL}/analyze", data={
        "input_type": "ocr",
        "image_input": img_b64
    })
    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data
    print("OCR RESULT:", data)