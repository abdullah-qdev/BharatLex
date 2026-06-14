#!/usr/bin/env python3
"""
OCR pipeline for printed English + Hindi (Devanagari) text.

Stages:
  1. Image preprocessing (grayscale, denoise, binarize) for cleaner OCR input
  2. Tesseract OCR with combined eng+hin language models
  3. Unicode NFC normalization of the recognized text

Usage:
    python ocr_normalize.py <image_path> [--lang eng+hin] [--no-preprocess]
"""

import argparse
import os
import sys
import unicodedata

import cv2
import pytesseract

# On Windows, if tesseract isn't on PATH, set the TESSERACT_CMD environment
# variable to the full path of tesseract.exe, e.g.:
#   set TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
_tesseract_cmd = os.environ.get("TESSERACT_CMD")
if _tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd


def preprocess_image(image_path: str):
    """Load an image and apply preprocessing to improve OCR accuracy.

    Steps: grayscale -> denoise -> adaptive threshold (binarization).
    Returns a binarized image array ready for Tesseract.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Remove sensor/scan noise while keeping edges reasonably sharp
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Adaptive threshold handles uneven lighting better than a global threshold
    binary = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        10,
    )

    return binary


def run_ocr(image, lang: str = "eng+hin") -> str:
    """Run Tesseract OCR on a preprocessed image array.

    lang="eng+hin" tells Tesseract to use both language models together,
    which works well for documents that mix English and Hindi text.
    """
    # --oem 3: default LSTM engine
    # --psm 3: fully automatic page segmentation (good default for notes/docs)
    config = "--oem 3 --psm 3"
    return pytesseract.image_to_string(image, lang=lang, config=config)


def normalize_text(text: str) -> str:
    """Apply Unicode NFC normalization plus light whitespace cleanup.

    NFC ensures Devanagari characters that can be represented in multiple
    byte sequences (e.g. a consonant + combining matra/nukta vs. a
    precomposed form) end up in a single canonical form. This matters for
    downstream search, comparison, and storage consistency.
    """
    normalized = unicodedata.normalize("NFC", text)

    # Strip trailing whitespace per line and surrounding blank lines,
    # without collapsing intentional paragraph breaks.
    lines = [line.rstrip() for line in normalized.splitlines()]
    return "\n".join(lines).strip()


def process(image_path: str, lang: str = "eng+hin", preprocess: bool = True) -> str:
    """Full pipeline: preprocess -> OCR -> normalize. Returns final text."""
    if preprocess:
        image = preprocess_image(image_path)
    else:
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Could not read image: {image_path}")

    raw_text = run_ocr(image, lang=lang)
    return normalize_text(raw_text)


def main():
    parser = argparse.ArgumentParser(description="OCR + NFC normalization for English/Hindi documents")
    parser.add_argument("image_path", help="Path to the input image")
    parser.add_argument("--lang", default="eng+hin", help="Tesseract language string (default: eng+hin)")
    parser.add_argument("--no-preprocess", action="store_true", help="Skip image preprocessing")
    args = parser.parse_args()

    try:
        result = process(args.image_path, lang=args.lang, preprocess=not args.no_preprocess)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(result)


if __name__ == "__main__":
    main()