from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

import models
import auth
import database

router = APIRouter(prefix="/auth", tags=["auth"])


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/register", response_model=models.UserPublic, status_code=201)
async def register(user: models.UserCreate):
    db = database.db
    if await db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    if await db.users.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already taken")
    now = datetime.utcnow()
    user_dict = user.dict()
    user_dict["password_hash"] = auth.hash_password(user_dict.pop("password"))
    user_dict["created_at"] = now
    user_dict["updated_at"] = now
    result = await db.users.insert_one(user_dict)
    return models.UserPublic(
        id=str(result.inserted_id),
        username=user_dict["username"],
        email=user_dict["email"],
        avatar_url=None,
    )


@router.post("/login", response_model=Token)
async def login(form_data: models.LoginRequest):
    db = database.db
    user = await db.users.find_one({"email": form_data.email})
    if not user or not auth.verify_password(form_data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = auth.create_access_token({"sub": str(user["_id"])})
    return {"access_token": token, "token_type": "bearer"}
