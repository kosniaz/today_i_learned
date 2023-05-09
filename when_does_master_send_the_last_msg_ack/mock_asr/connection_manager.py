from typing import Any, List, Tuple
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[Tuple[WebSocket, Any]] = []

    async def connect(self, websocket: WebSocket, data=None):
        await websocket.accept()
        self.active_connections.append((websocket, data))

    def retrieve_for_websocket(self, websocket: WebSocket):
        for i, (connection, data) in enumerate(self.active_connections):
            logger.info(f"Retrieving {i}")
            if connection is websocket:
                return data
        return None

    def is_active(self, ws: WebSocket):
        for active_ws, _ in self.active_connections:
            if ws is active_ws:
                return True
        return False

    async def disconnect(self, websocket: WebSocket):
        for i, (ws, data) in enumerate(self.active_connections):
            if ws is websocket:
                self.active_connections.pop(i)
                await ws.close()
                return data
        # self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection, _ in self.active_connections:
            await connection.send_text(message)
