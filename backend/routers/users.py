from fastapi import APIRouter, Depends, HTTPException
from typing import List
from bson import ObjectId

import models
import database
from dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=models.UserPublic)
async def read_me(current_user: models.UserInDB = Depends(get_current_user)):
    return models.UserPublic(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        avatar_url=current_user.avatar_url,
    )


@router.get("/search", response_model=List[models.UserPublic])
async def search_users(
    q: str,
    current_user: models.UserInDB = Depends(get_current_user),
):
    if not q:
        return []
    db = database.db
    cursor = db.users.find(
        {"username": {"$regex": q, "$options": "i"}, "_id": {"$ne": ObjectId(current_user.id)}},
        limit=20,
    )
    results = []
    async for u in cursor:
        results.append(models.UserPublic(
            id=str(u["_id"]),
            username=u["username"],
            email=u["email"],
            avatar_url=u.get("avatar_url"),
        ))
    return results


@router.get("/{user_id}", response_model=models.UserPublic)
async def get_user(user_id: str, current_user: models.UserInDB = Depends(get_current_user)):
    db = database.db
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return models.UserPublic(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        avatar_url=user.get("avatar_url"),
    )
