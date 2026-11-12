from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import settings


client = MongoClient(
    settings.MONGODB_URL,
    serverSelectionTimeoutMS=5000,
    tz_aware=True,
)
database: Database = client[settings.MONGODB_DATABASE]


def get_db():
    """Provides the configured MongoDB database to API endpoints."""
    yield database