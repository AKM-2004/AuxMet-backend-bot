from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from logs import ModuleLogger

logger = ModuleLogger("mongodbconnection")
load_dotenv()
import os

uri = os.getenv("MONGODB_URI")

_client = None
_is_connected = None


async def connectDB():
    global _client, _is_connected

    if _is_connected:
        logger.INFO("MongoDB already connected")
        return _client

    try:
        _client =  AsyncIOMotorClient(uri)
        # Test the connection
        _client.admin.command("ping")
        _is_connected = True
        logger.INFO("MongoDB connected successfully")
        print("DB is connected")
        return _is_connected
    except Exception as e:
        logger.ERROR(f"Error connecting to MongoDB: {e}")
        _is_connected = False
        _client = None
        raise e


def get_mongodb_client():
    if not _is_connected or not _client:
        raise RuntimeError(
            "MongoDB not connected. Call connect_mongodb() first in your main application."
        )
    return _client


async def disconnect_mongodb():
    global _client, _is_connected
    if _client:
        _client.close()
        _client = None
        _is_connected = False
        logger.INFO("MongoDB disconnected")
