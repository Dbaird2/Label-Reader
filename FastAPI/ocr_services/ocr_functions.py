
import asyncio
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
    arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Invalid image bytes")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Resize up if image is small — helps OCR significantly
    h, w = gray.shape
    if w < 800:
        scale = 800 / w
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # Denoise before sharpening
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def filterString(string: str) -> bool:
    if len(string) < 3:
        return False
    if re.search(r'\d', string):
        return False
    if 'colorado' in string.lower():
        return False
    alpha_ratio = sum(c.isalpha() for c in string) / len(string)
    if alpha_ratio < 0.6:
        return False
    tokens = string.split()
    single_chars = sum(1 for t in tokens if len(t) <= 2)
    if single_chars > len(tokens) * 0.4:
        return False
    return True

async def get_results(img_bytes: bytes) -> dict:
    loop = asyncio.get_event_loop()

    logger.info("Running EasyOCR...")
    results = await loop.run_in_executor(
        None,
        lambda: reader.readtext(img_bytes, detail=1, paragraph=False)
    )

    logger.info("Raw EasyOCR results: %s", results)

    # results = [(bbox, text, confidence), ...]
    lines = [
        text for (_, text, conf) in results
        if conf > 0.4 and filterString(text)
    ]

    logger.info("Filtered lines: %s", lines)
    # candidate = " ".join(lines[:2])
    # logger.info("Candidate: %r", candidate)

    # if not candidate.strip():
    #     logger.warning("No candidate extracted")
    #     return {"name": None, "building": None, "room": None, "confidence": None}
    highest_match = None
    for line in lines:
        match = await state.db.lookupName(line)
        if match and (not highest_match or match["confidence"] > highest_match["confidence"]):
            highest_match = match
    logger.info("DB result: %s", highest_match)

    return {
        "name": highest_match["name"] if highest_match else None,
        "building": highest_match["building"] if highest_match else None,
        "room": highest_match["room"] if highest_match else None,
        "department": highest_match["department"] if highest_match else None,
        "confidence": highest_match["confidence"] if highest_match else None
    }

