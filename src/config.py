import os

class Config:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    MONGO_URI = os.getenv("MONGO_URI")
    PORT = int(os.getenv("PORT", 8000))