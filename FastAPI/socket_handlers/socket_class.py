from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    """Class defining socket events"""
    def __init__(self):
        """init method, keeping track of connections"""
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        """connect event"""
        # await websocket.accept()
        self.active_connections.append(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Direct Message"""
        print("Sending personal message")
        await websocket.send_json(message)

    async def broadcast(self, message: list):
        """Broadcast Message"""
        print("Broadcasting")
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                self.active_connections.remove(websocket)
                print(f"Removed Websocket connection from broadcast {websocket}")
    
    def disconnect(self, websocket: WebSocket):
        """disconnect event"""
        print("Disconnecting websocket")
        self.active_connections.remove(websocket)
    
    async def closeConnections(self):
        """disconnect event"""
        print("Disconnecting all websockets")
        for websocket in self.active_connections:
            self.active_connections.remove(websocket)