from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

class Database:
    client: AsyncIOMotorClient = None

db = Database()

def get_database():
    if db.client is None:
        raise RuntimeError("Database client is not initialized")
    return db.client[settings.MONGO_DB]

def get_collection():
    return get_database()[settings.MONGO_COLLECTION]

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.MONGO_URI)

async def close_mongo_connection():
    if db.client:
        db.client.close()
