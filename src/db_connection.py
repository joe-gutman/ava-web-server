import os
import motor.motor_asyncio as motor
from utils.logger import logger


async def connect_to_db():
    db_url = os.environ.get('MONGODB_URL')
    if db_url == None or db_url.strip() == '':
        logger.error("Error connecting to database: MONGODB_URL environment variable is missing or empty")
        raise ValueError("Error connecting to database: MONGODB_URL missing or empty")
        

    logger.debug(f"Connecting to database at {db_url}")
    client = motor.AsyncIOMotorClient(f"{db_url}")
    db = client['ava_dev_db']

    # # Create collections and unique indexes
    # collections = {
    #     'devices': [("device_name", 1), ("user_id", 1)],
    #     'messages': [("message_id", 1)],
    #     'tools': [("tool_name", 1)],
    #     'users': [("email", 1)]
    # }

    # for collection, indexes in collections.items():
    #     existing_indexes = await db[collection].index_information()
    #     for index in indexes:
    #         index_name = '_'.join([str(part) for part in index])
    #         if index_name not in existing_indexes:
    #             await db[collection].create_index([index], unique=True, sparse=True)

    return db