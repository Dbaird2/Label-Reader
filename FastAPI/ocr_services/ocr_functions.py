
from models.OCR_Model import OCRResult
import logging
import base64
import cv2
import numpy as np
import re
import state
import asyncio
import easyocr

reader = easyocr.Reader(['en'], gpu=False)

logger = logging.getLogger(__name__)

# ocr_functions.py
def preprocess_label(img_bytes: bytes):
    # Decode
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 1. Upscale first — EasyOCR struggles under ~150 DPI equivalent
    img = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    # 2. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Denoise before thresholding (kills JPEG compression artifacts)
    gray = cv2.fastNlMeansDenoising(gray, h=10)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    # 4. Sharpen
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    gray = cv2.filter2D(gray, -1, kernel)

    # 5. Adaptive threshold (better than global for uneven lighting)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )

    # 6. Morphological closing — connects broken letter strokes
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return thresh

def filterString(string: str) -> bool:
    if len(string) < 3:
        return False
    if re.search(r'\d', string):
        return False
    # if 'colorado' in string.lower():
    #     return False
    alpha_ratio = sum(c.isalpha() for c in string) / len(string)
    if alpha_ratio < 0.6:
        return False
    tokens = string.split()
    single_chars = sum(1 for t in tokens if len(t) <= 2)
    if single_chars > len(tokens) * 0.4:
        return False
    return True

def get_candidates(tokens: list[str]) -> list[str]:
    if not tokens:
        return []
    singles = tokens
    bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
    trigrams = [f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}" for i in range(len(tokens) - 2)]
    return singles + bigrams + trigrams

async def run_easy_ocr(img_bytes: bytes) -> list:
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(
            None,
            lambda: reader.readtext(img_bytes, detail=1, paragraph=False)
        )
    except Exception as e:
        logger.error("EasyOCR failed: %s", e)
        return []


def filter_ocr_results(results: list) -> list:
    return [
        text for (_, text, conf) in results
        if conf > 0.4 and filterString(text)
    ]


async def find_best_match(candidates: list) -> dict | None:
    if not candidates:
        return None
    best_match = None
    for candidate in candidates:
        match = await state.db.lookupName(candidate)
        if match and (not best_match or match["confidence"] > best_match["confidence"]):
            best_match = match
        if best_match and best_match["confidence"] == 1.0:
            break
    return best_match


async def get_results(img_bytes: bytes) -> OCRResult:
    img_bytes = preprocess_label(img_bytes) 
    raw = await run_easy_ocr(img_bytes)
    for bbox, text, conf in raw:
        logger.info("OCR candidate: '%s' with confidence %.2f", text, conf)
    filtered = filter_ocr_results(raw)
    logger.info("OCR candidates: %s", filtered)
    candidates = get_candidates(filtered)
    best_match = await find_best_match(candidates)

    return OCRResult(**(best_match or {}))