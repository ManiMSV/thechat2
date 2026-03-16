from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern=r"^\w+$")
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserInDB(BaseModel):
    id: Optional[str] = None
    username: str
    email: EmailStr
    password_hash: str
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UserPublic(BaseModel):
    id: str
    username: str
    email: EmailStr
    avatar_url: Optional[str] = None


class ConversationCreate(BaseModel):
    participant_id: str


class ConversationInDB(BaseModel):
    id: Optional[str] = None
    participants: List[str]
    created_at: datetime
    last_message_at: datetime


class ConversationPublic(BaseModel):
    id: str
    participants: List[str]
    created_at: datetime
    last_message_at: datetime
    other_user: UserPublic
    last_message_preview: Optional[str] = None
    unread_count: int = 0


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)


class MessageInDB(BaseModel):
    id: Optional[str] = None
    conversation_id: str
    sender_id: str
    content: str
    created_at: datetime
    read_by: List[str] = []


class MessagePublic(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    content: str
    created_at: datetime
    read_by: List[str] = []
