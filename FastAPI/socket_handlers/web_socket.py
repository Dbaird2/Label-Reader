from fastapi import WebSocket, WebSocketDisconnect, APIRouter
import state
from ocr_services.ocr_functions import get_results
import base64
# from routers.auth import checkJWT
import logging 

router = APIRouter(tags=["ocr"], prefix="/ws")
logger = logging.getLogger(__name__)

@router.websocket("/ocr")
async def ocr_ws(websocket: WebSocket):
    logger.debug("/ocr_ws called")
    await websocket.accept()
    await state.ws.connect(websocket)
    try:
        while True:
            try:
                data = await websocket.receive_json()
            except WebSocketDisconnect as e:
                logger.warning("Client disconnected: code=%s", e.code)
                break
            except Exception as e:
                logger.error("Failed to receive JSON: %s", e)
                await websocket.send_json({"error": f"Invalid data: {str(e)}"})
                continue

            logger.info("Total data size: %d chars", len(str(data)))  # ADD THIS
            logger.info("Received keys: %s", list(data.keys()))
            frame_b64 = data.get("image")

            if not frame_b64:
                await websocket.send_json({"error": "No frame provided"})
                continue

            logger.info("Decoding base64...")
            try:
                img_bytes = base64.b64decode(frame_b64)
                logger.info("Decoded: %d bytes", len(img_bytes))
            except Exception as e:
                logger.error("Base64 decode failed: %s", e)
                await websocket.send_json({"error": "Invalid base64"})
                continue

            logger.info("Calling get_results...")
            try:
                result = await get_results(img_bytes)
                logger.info("Result: %s", result)
            except Exception as e:
                logger.exception("get_results failed: %s", e)
                await websocket.send_json({"error": "Processing failed"})
                continue

            await websocket.send_json(result)
    except WebSocketDisconnect:
        state.ws.disconnect(websocket)
    
@router.get("/ocr-test")
async def ocr_test():
    return {"status": "router is registered"}