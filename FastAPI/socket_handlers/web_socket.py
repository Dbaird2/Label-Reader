from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from models.OCR_Model import AddPersonModel, EditPersonModel, OCRModel, OCRResult, SearchPersonModel
from ocr_services.ocr_functions import get_results
from pydantic import ValidationError
from pathlib import Path
import logging 
import base64
import state

DEBUG_DIR = Path("debug_frames")
DEBUG_DIR.mkdir(exist_ok=True)

router = APIRouter(tags=["ocr"], prefix="/ws")
logger = logging.getLogger(__name__)

@router.websocket("/ocr")
async def ocr_ws(websocket: WebSocket):
    try:
        await websocket.accept()
        logger.info("Client connected: %s", websocket.client)
        await state.ws.connect(websocket)
    except Exception as e:
        logger.error("WebSocket connection error: %s", e)
        return
    try:
        while True:
            try:
                data = await websocket.receive_json()
                if data.get("addPerson"):
                    logger.info("Handling addPerson request")
                    await handle_add_person(websocket, data)
                elif data.get("ocr"):
                    logger.info("Handling OCR request")
                    await handle_ocr(websocket, data)
                elif data.get("searchPerson"):
                    logger.info("Handling searchPerson request")
                    await search_person(websocket, data)
                else:
                    logger.warning("Unknown message type: %s", data)
                    await websocket.send_json({"error": "Unknown message type"})

            except WebSocketDisconnect as e:
                logger.warning("Client disconnected: code=%s", e.code)
                break
            except Exception as e:
                logger.error("Unexpected error: %s", e)
                await websocket.send_json({"error": f"Invalid data: {str(e)}"})

    finally:
        state.ws.disconnect(websocket)


async def decode_base64(data: str) -> bytes | None:
    try:
        return base64.b64decode(data)
    except Exception:
        return None

async def run_ocr(img_bytes: bytes) -> dict | None:
    try:
        return await get_results(img_bytes)
    except Exception as e:
        logger.exception("OCR processing failed: %s", e)
        return None

async def upsert_person(person: AddPersonModel) -> bool:
    try:
        await state.db.upsertPerson(person)
        return True
    except Exception as e:
        logger.error("Failed to add person upsert_person: %s", e)
        return False
    
async def edit_person(person: EditPersonModel) -> bool:
    try:
        await state.db.editPerson(person)
        return True
    except Exception as e:
        logger.error("Failed to edit person edit_person: %s", e)
        return False


async def handle_ocr(websocket: WebSocket, data: dict):
    try:
        message = OCRModel(**data)
    except ValidationError as e:
        await websocket.send_json({"error": f"Invalid OCR data: {str(e)}"})
        return

    img_bytes = await decode_base64(message.image)
    if not img_bytes:
        await websocket.send_json({"error": "Invalid base64"})
        return

    result = await run_ocr(img_bytes)
    if not result:
        await websocket.send_json({"error": "Processing failed"})
        return

    await websocket.send_json(result.model_dump())


async def handle_add_person(websocket: WebSocket, data: dict):
    try:
        person = EditPersonModel(**data)
    except ValidationError as e:
        await websocket.send_json({"error": f"Invalid person data: {str(e)}"})
        return

    success = await edit_person(person)
    if not success:
        await websocket.send_json({"error": "Failed to edit person"})
        return

    await websocket.send_json({"status": "Person edited successfully"})
    
async def search_person(websocket: WebSocket, data: dict):
    try:
        search_model = SearchPersonModel(**data)
        logger.info("Searching for: %s", search_model.search)
    except ValidationError as e:
        await websocket.send_json({"error": f"Invalid search data: {str(e)}"})
        return

    result = await state.db.lookupName(search_model.search)
    if result:
        await websocket.send_json(result)
    else:
        await websocket.send_json({'status': 'Person Not Found'})


@router.get("/ocr-test")
async def ocr_test():
    return {"status": "router is registered"}