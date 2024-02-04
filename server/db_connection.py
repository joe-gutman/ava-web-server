import os
import motor.motor_asyncio as motor
from dotenv import load_dotenv

load_dotenv()

async def get_db_client():
    db_username = os.getenv('DB_USERNAME')
    db_password = os.getenv('DB_PASSWORD')
    client = motor.AsyncIOMotorClient(f"mongodb://{db_username}:{db_password}@localhost:27017")
    return client['ava_dev_db']