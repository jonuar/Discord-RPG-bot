from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from config import Config

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client[Config.DB_NAME]

    async def close(self):
        self.client.close()

    async def create_user(self, user_id: int, race: str = None, user_class: str = None):
        collection = self.db["players"]
        user_doc = {
            "user_id": user_id,
            "race": race,
            "class": user_class,
            "coins": 0,
            "inventory": []
        }
        result = await collection.insert_one(user_doc)
        return result.inserted_id

    async def read_user(self, user_id: int):
        collection = self.db["players"]
        return await collection.find_one({"user_id": user_id})

    async def update_user(self, user_id: int, update: dict):
        collection = self.db["players"]
        updated_document = await collection.find_one_and_update(
            {"user_id": user_id},
            {'$set': update},
            return_document=ReturnDocument.AFTER
        )
        return updated_document

    async def delete_user(self, user_id: int):
        collection = self.db["players"]
        result = await collection.delete_one({"user_id": user_id})
        return result.deleted_count

def get_database():
    return Database()