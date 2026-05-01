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
            data = await websocket.receive_json()
            frame_b64 = data.get("frame")
            if not frame_b64:
                await websocket.send_json({"error": "No frame provided"})
                continue

            try:
                img_bytes = base64.b64decode(frame_b64)
            except Exception:
                await websocket.send_json({"error": "Invalid base64"})
                continue

            result = await get_results(img_bytes)
            await websocket.send_json(result)
    except WebSocketDisconnect:
        await state.ws.disconnect(websocket)