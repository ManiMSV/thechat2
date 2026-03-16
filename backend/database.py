from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_URI = os.getenv("MONGODB_URL")

client = AsyncIOMotorClient(MONGO_URI)
db = client.thechat


async def create_indexes():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.messages.create_index("conversation_id")
    await db.messages.create_index([("conversation_id", 1), ("created_at", 1)])
    await db.conversations.create_index("participants")


async def get_db():
    return db
