import re
import json
from quart import current_app as app
from datetime import datetime
from bson import ObjectId
from functools import wraps
from utils.logger import logger
from utils.convert_to_str import convert_to_str as to_str

def is_valid_objectid(id):
    return bool(re.match('^[a-f0-9]{24}$', id))

def fetch_entities(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger.info(f'Fetching entities for {func.__name__}')
        logger.info(f'Args: {args}, Kwargs: {kwargs}')
        entities = {k: v for k, v in kwargs.items() if k in ['user', 'device']}
        logger.info(f'Entities: {entities}')
        if (len(entities) == 0):
            return await func(*args, **kwargs)

        fetched_entities = {}
    


        for entity_name, entity_id in entities.items():
            fetch_entity = None
            try: 
                if is_valid_objectid(entity_id):
                    fetched_entity = await app.db[entity_name + 's'].find_one({'_id': ObjectId(entity_id)}, {'password': 0})
                    logger.info(f' Fetched {entity_name} with id {entity_id}: {fetched_entity}')
                else:
                    logger.error(f'Invalid id for {entity_name}: {entity_id}')
            except Exception as e:
                logger.error(f'Error fetching {entity_name} with id {entity_id}: {e}')
            if fetched_entity is not None:
                if isinstance(fetched_entity, dict):
                    fetched_entity = {k: to_str(v) for k, v in fetched_entity.items()}
                fetched_entities[entity_name] = fetched_entity
            
            logger.info(f'Fetched entities: {fetched_entities}')

        kwargs.update(fetched_entities)
        return await func(*args, **kwargs)
    return wrapper