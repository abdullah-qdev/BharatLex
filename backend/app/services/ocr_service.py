import os
import subprocess
import tempfile
from pathlib import Path


class OcrError(RuntimeError):
    pass


def _configure_tesseract() -> None:
    tesseract_cmd = os.getenv("TESSERACT_CMD", "").strip()
    if not tesseract_cmd:
        return

    try:
        import pytesseract
    except ImportError as exc:
        raise OcrError("Missing pytesseract. Install backend requirements.") from exc

    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


def _tesseract_command() -> str:
    return os.getenv("TESSERACT_CMD", "").strip() or "tesseract"


def _tessdata_config() -> str:
    tessdata_dir = os.getenv("TESSDATA_DIR", "").strip()
    if not tessdata_dir:
        return ""

    return f" --tessdata-dir {tessdata_dir}"


def available_languages() -> list[str]:
    env = os.environ.copy()
    tessdata_dir = os.getenv("TESSDATA_DIR", "").strip()
    if tessdata_dir:
        env["TESSDATA_PREFIX"] = tessdata_dir

    try:
        result = subprocess.run(
            [_tesseract_command(), "--list-langs"],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise OcrError(
            "Tesseract executable was not found or could not list languages. "
            "Install Tesseract OCR and set TESSERACT_CMD if needed."
        ) from exc

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return [line for line in lines if not line.lower().startswith("list of available languages")]


def preprocess_image(image_path: str):
    try:
        import cv2
    except ImportError as exc:
        raise OcrError("Missing OpenCV. Install opencv-python-headless from backend requirements.") from exc

    image = cv2.imread(image_path)
    if image is None:
        raise OcrError(f"Could not read image: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    return cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        10,
    )


def normalize_text(text: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFC", text)
    lines = [line.rstrip() for line in normalized.splitlines()]
    return "\n".join(lines).strip()


def extract_text_from_image(
    image_path: str,
    lang: str = "eng+hin",
    preprocess: bool = True,
) -> str:
    _configure_tesseract()

    try:
        import cv2
        import pytesseract
    except ImportError as exc:
        raise OcrError("Missing OCR dependencies. Install opencv-python-headless and pytesseract.") from exc

    image = preprocess_image(image_path) if preprocess else cv2.imread(image_path)
    if image is None:
        raise OcrError(f"Could not read image: {image_path}")

    try:
        raw_text = pytesseract.image_to_string(
            image,
            lang=lang,
            config=f"--oem 3 --psm 3{_tessdata_config()}",
        )
    except pytesseract.TesseractNotFoundError as exc:
        raise OcrError(
            "Tesseract executable was not found. Install Tesseract OCR and set TESSERACT_CMD if needed."
        ) from exc
    except pytesseract.TesseractError as exc:
        raise OcrError(f"Tesseract OCR failed: {exc}") from exc

    return normalize_text(raw_text)


def temporary_image_path(filename: str) -> Path:
    suffix = Path(filename).suffix or ".png"
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    handle.close()
    return Path(handle.name)
