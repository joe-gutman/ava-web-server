import os
import motor.motor_asyncio as motor
from dotenv import load_dotenv

load_dotenv()

async def initialize_client():
    db_username = os.getenv('DB_USERNAME')
    db_password = os.getenv('DB_PASSWORD')
    client = motor.AsyncIOMotorClient(f"mongodb://{db_username}:{db_password}@localhost:27017")
    db = client['ava_dev_db']

    # Create collections and unique indexes
    collections = {
        'devices': [("device_name", 1), ("user_id", 1)],
        'messages': [("message_id", 1)],
        'tools': [("tool_name", 1), ("user_id", 1)],
        'users': [("email", 1)]
    }

    for collection, indexes in collections.items():
        existing_indexes = await db[collection].index_information()
        for index in indexes:
            index_name = '_'.join([str(part) for part in index])
            if index_name not in existing_indexes:
                await db[collection].create_index([index], unique=True, sparse=True)

    return db