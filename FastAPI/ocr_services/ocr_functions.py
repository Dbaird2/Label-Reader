
from models.OCR_Model import OCRResult
import logging
import base64
import cv2
import numpy as np
import re
import state
import asyncio
import easyocr
from services.AI_agent import agent

reader = easyocr.Reader(['en'], gpu=False)

logger = logging.getLogger(__name__)

# ocr_functions.py
def preprocess_label(img_bytes: bytes):
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 1. Upscale
    img = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    # 2. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Denoise — do this early, before any contrast work
    gray = cv2.fastNlMeansDenoising(gray, h=10)

    # 4. CLAHE — more conservative clip to avoid over-enhancing noise
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # 5. Deskew — straighten before thresholding
    gray = deskew(gray)

    # 6. Adaptive threshold — smaller block for tighter local adaptation
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 15, 8
    )

    # 7. Inversion check — EasyOCR expects dark text on light background
    if cv2.mean(thresh)[0] < 127:
        thresh = cv2.bitwise_not(thresh)

    # 8. Morphological closing — same as before, fine
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return thresh
    
def deskew(gray: np.ndarray) -> np.ndarray:
    coords = np.column_stack(np.where(gray < 128))
    if len(coords) < 50:
        return gray
    angle = cv2.minAreaRect(coords.astype(np.float32))[-1]
    # minAreaRect returns angles in [-90, 0); normalize to [-45, 45]
    if angle < -45:
        angle += 90
    (h, w) = gray.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)

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
        if conf > 0.5 and filterString(text)
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

    if not candidates:
        logger.info("No valid OCR candidates found after filtering.")
        return OCRResult() 

    best_match = await find_best_match(candidates)
    ocr_prompt = f"""
        From OCR candidates:
        {candidates}

        Extract the most likely person and insert into database if confidence > 0.8.
        Otherwise ask for clarification.
        """
    if not best_match:
        result = await agent.run(ocr_prompt)
        if "insert_person" in result:
             best_match = result["insert_person"]
    else:
        logger.info("Best match found: %s", best_match)


    return OCRResult(**(best_match or {}))