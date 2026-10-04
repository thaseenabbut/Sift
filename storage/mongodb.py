import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from rich import print

from schemas import DOCUMENT_MODELS

_ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(_ENV_PATH)

MONGODB_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

class DatabaseManager:
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db = None

    async def connect_and_init(self):
        print("[bold green][CONNECTING][/bold green] Connecting to MongoDB...")

        self.client = AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,  # fail after 5s if no server found
            connectTimeoutMS=5000,          # fail after 5s if connection hangs
        )
        self.db = self.client[DATABASE_NAME]

        await self.client.admin.command("ping")

        await init_beanie(
            database=self.db,
            document_models=DOCUMENT_MODELS
        )
        print("[bold green][CONNECTED][/bold green] MongoDB connection established and Beanie initialized.")

    async def close_connection(self):
        if self.client:
            self.client.close()
            print("[bold red][DISCONNECTED][/bold red] MongoDB connection closed.")

db_manager = DatabaseManager()
