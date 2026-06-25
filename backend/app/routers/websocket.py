from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
import asyncio

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, client_id: str = None):
        if client_id and client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                await connection.send_text(message)
        else:
            for connections in self.active_connections.values():
                for connection in connections:
                    await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong", "timestamp": str(asyncio.get_event_loop().time())}),
                    websocket
                )
            elif message.get("type") == "subscribe":
                channel = message.get("channel", "general")
                await manager.send_personal_message(
                    json.dumps({"type": "subscribed", "channel": channel}),
                    websocket
                )
            else:
                await manager.broadcast(
                    json.dumps({"type": "message", "data": message, "from": client_id}),
                    message.get("channel", client_id)
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception:
        manager.disconnect(websocket, client_id)

@router.post("/broadcast")
async def broadcast_message(message: dict):
    await manager.broadcast(json.dumps(message))
    return {"status": "sent"}

