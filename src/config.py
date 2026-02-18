import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("RPGBOT_DB_NAME")
    COLLECTION_NAME = os.getenv("RPGBOT_COLLECTION_NAME")
    PORT = int(os.getenv("PORT", 8000))
    print(f"class Config DB_NAME: {DB_NAME}")