
import logging
import pytesseract
import cv2
import numpy as np
import re
import state

logger = logging.getLogger(__name__)

# ocr_functions.py
def preprocess_label(img_bytes: bytes):
    arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    blurred = cv2.GaussianBlur(enhanced, (0, 0), 3)
    sharpened = cv2.addWeighted(enhanced, 1.5, blurred, -0.5, 0)
    _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def filterString(string):
    if re.search(r'\d', string) is not None:
        return False
    if re.search(r'colorado', string.lower()) is not None:
        return False
    # if re.search(r'ship|shlp\sto|shipto', string.lower()) is not None:
    #     return 'Next'
    return True

async def get_results(img_bytes: bytes) -> dict:
    img = preprocess_label(img_bytes)
    raw = pytesseract.image_to_string(img, config='--psm 6')

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    text = [line for line in lines if filterString(line)]
    logger.debug(f"Extracted text: {text}")
    candidate = " ".join(text[:2])

    match = await state.db.lookupName(candidate)

    return {
        "name": match['name'] if match else None,
        "building": match['building'] if match else None,
        "room": match['room'] if match else None,
        "confidence": match['confidence'] if match else None
    }


