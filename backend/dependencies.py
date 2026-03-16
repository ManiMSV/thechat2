from fastapi import Depends, HTTPException
from bson import ObjectId

import auth
import database
import models


async def get_current_user(token: str = Depends(auth.oauth2_scheme)) -> models.UserInDB:
    payload = auth.decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    user_id = payload.get("sub")
    try:
        user = await database.db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    user["id"] = str(user["_id"])
    return models.UserInDB(**user)
