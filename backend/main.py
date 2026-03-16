from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from routers import auth as auth_router
from routers import users as users_router
from routers import conversations as conversations_router
from routers import messages as messages_router
from routers import websocket as websocket_router
import database

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.create_indexes()
    yield


app = FastAPI(title="ChatApp API", lifespan=lifespan)

_extra = os.getenv("CORS_ORIGINS", "")
origins = ["http://localhost:4200", "http://127.0.0.1:4200"] + [
    o.strip() for o in _extra.split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(conversations_router.router)
app.include_router(messages_router.router)
app.include_router(websocket_router.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
