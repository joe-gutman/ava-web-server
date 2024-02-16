import json
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from quart import current_app as app
from utils.logger import logger

class DeviceHandler:
    @staticmethod
    async def create_device(request, user_id):
        device = request['data']['content']['device']

        try:
            logger.info(f'Creating device: {device}')

            device_to_insert = device.copy()
            device_to_insert['user_id'] = ObjectId(user_id)

            try:
                result = await app.db.devices.insert_one(device_to_insert)
                logger.info(f'New device created: {result}')

                inserted_device = await app.db.devices.find_one({'_id': result.inserted_id})
                inserted_device['_id'] = str(inserted_device['_id'])
                inserted_device['user_id'] = str(inserted_device['user_id'])

                return {
                    'status': 'success',
                    'message': 'Device created', 
                    'user': {
                        '_id': user_id
                    },
                    'data': {
                        'type': 'device',
                        'content': {
                            'device': inserted_device
                        }
                    }
                }

            except DuplicateKeyError as e:
                logger.error(f'Device already exists: {device}')
                existing_device = await app.db.devices.find_one({'user_id': ObjectId(user_id), 'name': device['name']})
                if existing_device:
                    existing_device['_id'] = str(existing_device['_id'])
                    existing_device['user_id'] = str(existing_device['user_id'])
                return {
                    'status': 'error',
                    'message': 'Device already exists',
                    'user': {
                        '_id': user_id
                    },
                    'data': {
                        'content': {
                            'device': existing_device
                        },
                        'type': 'device'
                    }
                }, 400
        except Exception as e:
            logger.error(f'Error creating device: {e}')
            return {
                'status': 'error',
                'message': 'Error creating device',
                'user': {
                    '_id': user_id
                },
                'data': {
                    'content': {
                        'device': device
                    },
                    'type': 'device'
                }
            }, 500