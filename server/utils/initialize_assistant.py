import json
import asyncio
from modules.assistant.handler import Assistant
from utils.logger import logger


async def _initialize_assistant(params):
    try:
        logger.info('No assistant found, initializing assistant')
        assistant = await Assistant.initialize(params)
        logger.info(f'Assistant initialized: {assistant}')
    except Exception as e:
        logger.error(f'Error initializing assistant: {e}')
        return {'message': 'Error initializing assistant'}, 500
    
async def _build_params():
    ava_params = json.load(open('config/ava_params.json'))
       
assistant = asyncio.run(_initialize_assistant(asyncio.run(_build_params())))