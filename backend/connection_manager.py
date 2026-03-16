from fastapi import WebSocket
from typing import Dict, List


class ConnectionManager:
    def __init__(self):
        # mapping conversation_id -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, conversation_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(conversation_id, []).append(websocket)

    def disconnect(self, conversation_id: str, websocket: WebSocket):
        conns = self.active_connections.get(conversation_id, [])
        if websocket in conns:
            conns.remove(websocket)
            if not conns:
                self.active_connections.pop(conversation_id, None)

    async def broadcast(self, conversation_id: str, message: dict):
        dead = []
        for connection in list(self.active_connections.get(conversation_id, [])):
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self.disconnect(conversation_id, connection)


manager = ConnectionManager()
