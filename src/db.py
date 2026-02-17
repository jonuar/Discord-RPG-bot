from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from config import Config

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client[Config.DB_NAME]

    async def close(self):
        self.client.close()

    async def create_document(self, collection_name: str, document: dict):
        collection = self.db[collection_name]
        result = await collection.insert_one(document)
        return result.inserted_id

    async def read_document(self, collection_name: str, query: dict):
        collection = self.db[collection_name]
        document = await collection.find_one(query)
        return document

    async def update_document(self, collection_name: str, query: dict, update: dict):
        collection = self.db[collection_name]
        updated_document = await collection.find_one_and_update(
            query,
            {'$set': update},
            return_document=ReturnDocument.AFTER
        )
        return updated_document

    async def delete_document(self, collection_name: str, query: dict):
        collection = self.db[collection_name]
        result = await collection.delete_one(query)
        return result.deleted_count

def get_database():
    return Database()