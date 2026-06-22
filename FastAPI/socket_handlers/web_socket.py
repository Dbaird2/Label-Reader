from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from models.OCR_Model import AddPersonModel, EditPersonModel, OCRModel, OCRResult, SearchPersonModel
from ocr_services.ocr_functions import get_results
from services.AI_agent import agent
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
                    res = await handle_add_person(data)
                elif data.get("ocr"):
                    logger.info("Handling OCR request")
                    res = await handle_ocr(data)
                elif data.get("searchPerson"):
                    logger.info("Handling searchPerson request")
                    res = await search_person(data)
                elif data.get("editPerson"):
                    logger.info("Handling editPerson request")
                    res = await handle_edit_person(data)
                else:
                    logger.warning("Unknown message type: %s", data)
                    res = {"error": "Unknown message type"}
                if res:
                    await websocket.send_json(res)
                else:
                    logger.warning("No response generated for message: %s", data)
                    await websocket.send_json({"error": "No response generated"})

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


async def handle_ocr(data: dict):
    try:
        message = OCRModel(**data)
    except ValidationError as e:
        return {"error": f"Invalid OCR data: {str(e)}"}

    img_bytes = await decode_base64(message.image)
    if not img_bytes:
        return {"error": "Invalid base64"}
        

    result = await run_ocr(img_bytes)
    if not result:
        return {"error": "Processing failed"}
        
    if "error" in result:
        return result

    logger.info("Results: %s", result)
    if not result.department and not result.name:
        return {"status": "No result found"}
    return result.model_dump()


async def handle_add_person(data: dict):
    try:
        person = AddPersonModel(**data)
    except ValidationError as e:
        return {"error": f"Invalid person data: {str(e)}"}

    success = await upsert_person(person)
    if not success:
        return {"error": "Failed to add person"}

    return {"status": "Person added successfully"}

async def handle_edit_person(data: dict):
    try:
        person = EditPersonModel(**data)
    except ValidationError as e:
        return {"error": f"Invalid person data: {str(e)}"}

    success = await edit_person(person)
    if not success:
        return {"error": "Failed to edit person"}

    return {"status": "Person edited successfully"}

async def search_person(data: dict):
    try:
        search_model = SearchPersonModel(**data)
        logger.info("Searching for: %s", search_model.search)
    except ValidationError as e:
        return {"error": f"Invalid search"}

    result = await state.db.lookupName(search_model.search)
    logger.info("Database search result: %s", result)
    if result and result['confidence'] > 0.35:
        return result
    else:
        logger.info("No DB match above confidence threshold, returning best candidate")
        result = await agent.run(search_model.search)
        logger.info("AI agent corrected '%s' to '%s'", search_model.search, result)
    
        if result and result != search_model.search:
            ai_match, _ = await state.db.lookupName(result)
            if ai_match and ai_match["confidence"] > 0.4:
                logger.info("AI-corrected name '%s' has a good DB match, returning AI-corrected result", result)
                return ai_match
            else:
                logger.info("AI-corrected name '%s' does not have a good DB match, returning original candidate", result)
                return {"error": f"No valid match found for '{search_model.search}' after AI correction"}
        else:
            logger.info("AI agent did not provide a correction, returning original candidate")
            return {"error": f"No valid match found for '{search_model.search}' after AI correction"}


@router.get("/ocr-test")
async def ocr_test():
    return {"status": "router is registered"}