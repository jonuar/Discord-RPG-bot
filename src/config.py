import os
from dotenv import load_dotenv


ENV = os.getenv("BOT_ENV", "development")
dotenv_path = f".env.{ENV}"
load_dotenv(dotenv_path)

print(f"[CONFIG] Loaded environment: {ENV}")

class Config:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("RPGBOT_DB_NAME")
    COLLECTION_NAME = os.getenv("RPGBOT_COLLECTION_NAME")
