from fastapi import APIRouter, Depends, HTTPException, Query, Response
from datetime import datetime
from bson import ObjectId
from typing import List

import models
import database
from dependencies import get_current_user
from connection_manager import manager

router = APIRouter(
    prefix="/conversations/{conversation_id}/messages", tags=["messages"]
)


async def _verify_membership(conversation_id: str, user_id: str, db):
    try:
        conv = await db.conversations.find_one(
            {"_id": ObjectId(conversation_id), "participants": user_id}
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.get("", response_model=List[models.MessagePublic])
async def get_messages(
    conversation_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: models.UserInDB = Depends(get_current_user),
):
    db = database.db
    await _verify_membership(conversation_id, current_user.id, db)
    cursor = (
        db.messages.find({"conversation_id": conversation_id})
        .sort("created_at", 1)
        .skip(skip)
        .limit(limit)
    )
    results = []
    async for m in cursor:
        m["id"] = str(m["_id"])
        results.append(models.MessagePublic(**m))
    return results


@router.post("", response_model=models.MessagePublic, status_code=201)
async def send_message(
    conversation_id: str,
    payload: models.MessageCreate,
    current_user: models.UserInDB = Depends(get_current_user),
):
    db = database.db
    await _verify_membership(conversation_id, current_user.id, db)
    now = datetime.utcnow()
    doc = {
        "conversation_id": conversation_id,
        "sender_id": current_user.id,
        "content": payload.content,
        "created_at": now,
        "read_by": [current_user.id],
    }
    result = await db.messages.insert_one(doc)
    message_id = str(result.inserted_id)
    await db.conversations.update_one(
        {"_id": ObjectId(conversation_id)}, {"$set": {"last_message_at": now}}
    )
    await manager.broadcast(conversation_id, {
        "type": "message",
        "id": message_id,
        "conversation_id": conversation_id,
        "sender_id": current_user.id,
        "content": payload.content,
        "created_at": now.isoformat(),
        "read_by": [current_user.id],
    })
    return models.MessagePublic(
        id=message_id,
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=payload.content,
        created_at=now,
        read_by=[current_user.id],
    )


@router.post("/read", status_code=204)
async def mark_as_read(
    conversation_id: str,
    current_user: models.UserInDB = Depends(get_current_user),
):
    db = database.db
    await _verify_membership(conversation_id, current_user.id, db)
    result = await db.messages.update_many(
        {"conversation_id": conversation_id, "read_by": {"$nin": [current_user.id]}},
        {"$addToSet": {"read_by": current_user.id}},
    )
    if result.modified_count > 0:
        await manager.broadcast(conversation_id, {
            "type": "read",
            "conversation_id": conversation_id,
            "reader_id": current_user.id,
        })
    return Response(status_code=204)
