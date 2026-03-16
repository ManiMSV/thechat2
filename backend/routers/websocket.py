from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from bson import ObjectId
from datetime import datetime

import auth
import database
from connection_manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str, token: str):
    payload = auth.decode_access_token(token)
    if not payload or "sub" not in payload:
        await websocket.close(code=1008)
        return

    try:
        user = await database.db.users.find_one({"_id": ObjectId(payload["sub"])})
    except Exception:
        await websocket.close(code=1008)
        return
    if not user:
        await websocket.close(code=1008)
        return

    user_id = str(user["_id"])

    try:
        conv = await database.db.conversations.find_one(
            {"_id": ObjectId(conversation_id), "participants": user_id}
        )
    except Exception:
        await websocket.close(code=1008)
        return
    if not conv:
        await websocket.close(code=1008)
        return

    await manager.connect(conversation_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "message":
                content = (data.get("content") or "").strip()
                if not content:
                    continue
                now = datetime.utcnow()
                doc = {
                    "conversation_id": conversation_id,
                    "sender_id": user_id,
                    "content": content,
                    "created_at": now,
                    "read_by": [user_id],
                }
                result = await database.db.messages.insert_one(doc)
                await database.db.conversations.update_one(
                    {"_id": ObjectId(conversation_id)},
                    {"$set": {"last_message_at": now}},
                )
                await manager.broadcast(conversation_id, {
                    "type": "message",
                    "id": str(result.inserted_id),
                    "conversation_id": conversation_id,
                    "sender_id": user_id,
                    "content": content,
                    "created_at": now.isoformat(),
                    "read_by": [user_id],
                })
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        manager.disconnect(conversation_id, websocket)
