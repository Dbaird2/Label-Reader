from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from models.OCR_Model import OCRResult, AddPersonModel, EditPersonModel, SearchPersonModel
from main import app
import os
import base64
import state

client = TestClient(app)

def get_test_image(filename):
    path = os.path.join("tests", "fixtures", filename)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

async def test_websocket_ocr():
    fake_ocr = [(None, "Seth Alison", 0.95)]
    fake_db = (
        {"name": "Seth Alison", "department": "Theatreworks", "building": "Arts Center", "confidence": 1.0},
        'Seth Alison'
    )

    with patch("ocr_services.ocr_functions.reader.readtext", return_value=fake_ocr), \
        patch.object(state.db, "lookupName", new=AsyncMock(return_value=fake_db)):
        
        with client.websocket_connect("/ws/ocr") as websocket:
            websocket.send_json({"ocr": True, "image": get_test_image("test_png.jpg")})
            response = websocket.receive_json()
            assert "department" in response
            assert "name" in response
            assert response["department"] == "Theatreworks"
            assert response["name"] == "Seth Alison"