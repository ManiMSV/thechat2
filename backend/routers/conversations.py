from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from bson import ObjectId
from typing import List, Optional

import models
import database
from dependencies import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])


async def _enrich(conv: dict, current_user_id: str, db) -> models.ConversationPublic:
    other_id = next((p for p in conv["participants"] if p != current_user_id), None)
    other_doc = await db.users.find_one({"_id": ObjectId(other_id)}) if other_id else None
    other_user = (
        models.UserPublic(
            id=str(other_doc["_id"]),
            username=other_doc["username"],
            email=other_doc["email"],
            avatar_url=other_doc.get("avatar_url"),
        )
        if other_doc
        else models.UserPublic(id=other_id or "", username="Deleted user", email="")
    )

    conv_id = str(conv["_id"])
    last_msg = await db.messages.find_one(
        {"conversation_id": conv_id}, sort=[("created_at", -1)]
    )
    preview: Optional[str] = None
    if last_msg:
        body = last_msg.get("content", "")
        preview = body[:40] + ("\u2026" if len(body) > 40 else "")

    unread = await db.messages.count_documents(
        {"conversation_id": conv_id, "read_by": {"$nin": [current_user_id]}}
    )

    return models.ConversationPublic(
        id=conv_id,
        participants=conv["participants"],
        created_at=conv["created_at"],
        last_message_at=conv["last_message_at"],
        other_user=other_user,
        last_message_preview=preview,
        unread_count=unread,
    )


@router.get("", response_model=List[models.ConversationPublic])
async def list_conversations(current_user: models.UserInDB = Depends(get_current_user)):
    db = database.db
    cursor = db.conversations.find(
        {"participants": current_user.id}, sort=[("last_message_at", -1)]
    )
    return [await _enrich(conv, current_user.id, db) async for conv in cursor]


@router.post("", response_model=models.ConversationPublic)
async def create_or_get_conversation(
    payload: models.ConversationCreate,
    current_user: models.UserInDB = Depends(get_current_user),
):
    db = database.db
    if payload.participant_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot start a conversation with yourself")
    try:
        other = await db.users.find_one({"_id": ObjectId(payload.participant_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid participant ID")
    if not other:
        raise HTTPException(status_code=404, detail="User not found")

    participants = sorted([current_user.id, payload.participant_id])
    conv = await db.conversations.find_one({"participants": participants})
    if not conv:
        now = datetime.utcnow()
        doc = {"participants": participants, "created_at": now, "last_message_at": now}
        result = await db.conversations.insert_one(doc)
        conv = await db.conversations.find_one({"_id": result.inserted_id})
    return await _enrich(conv, current_user.id, db)
