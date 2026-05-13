from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        self.active_connections.append(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        print("Sending personal message")
        await websocket.send_json(message)

    async def broadcast(self, message: list):
        print("Broadcasting")
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                self.active_connections.remove(websocket)
                print(f"Removed Websocket connection from broadcast {websocket}")
    
    def disconnect(self, websocket: WebSocket):
        print("Disconnecting websocket")
        self.active_connections.remove(websocket)
    
    async def closeConnections(self):
        print("Disconnecting all websockets")
        for websocket in self.active_connections:
            self.active_connections.remove(websocket)