# English + Hindi OCR with NFC Normalization

OCR pipeline for printed documents/notes containing English and/or Hindi
(Devanagari) text. Applies image preprocessing before OCR and Unicode NFC
normalization to the recognized text.

## System requirements

Install Tesseract with English and Hindi language data:

```bash
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin
```

## Python requirements

```bash
pip install -r requirements.txt
```

## Usage

```bash
python ocr_normalize.py notes.png
```

Options:

```bash
# Use a different language combination (e.g. Hindi only)
python ocr_normalize.py notes.png --lang hin

# Skip preprocessing (useful for already-clean, high-contrast scans)
python ocr_normalize.py notes.png --no-preprocess
```

Output is printed to stdout. Redirect to a file if needed:

```bash
python ocr_normalize.py notes.png > output.txt
```

## What each stage does

1. **Preprocessing** — grayscale conversion, denoising, and adaptive
   thresholding (binarization) to make text stand out from the background
   regardless of lighting/scan quality.
2. **OCR** — Tesseract LSTM engine (`--oem 3`) with automatic page
   segmentation (`--psm 3`), using the combined `eng+hin` language models so
   English and Hindi lines in the same document are both recognized.
3. **Normalization** — Unicode NFC normalization on the output text, plus
   trimming of trailing whitespace and surrounding blank lines. NFC ensures
   Devanagari characters that can be encoded multiple ways (e.g. a
   precomposed character vs. base + combining matra) end up in one
   canonical form, so the output text is consistent for storage,
   search, and comparison.

## Known limitation

A handful of Devanagari nukta letters (क़ ख़ ग़ ज़ ड़ ढ़ फ़ य़) are excluded
from NFC's recomposition rules, so a precomposed nukta letter and its
decomposed "consonant + nukta" form can still differ after NFC. This is
rarely an issue with OCR output but if it ever matters for your use case
(e.g. exact-match search), the Indic NLP Library's normalizer handles it.

## Notes

- Works on printed/typed text (not handwriting).
- For best accuracy, input images should be reasonably high resolution
  (~300 DPI equivalent) and roughly upright (small skew is fine; large
  rotations should be corrected first).
