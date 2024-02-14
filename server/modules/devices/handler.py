import json
from bson import ObjectId
from quart import current_app as app
from utils.logger import logger

class DeviceHandler:
    @staticmethod
    async def add_device(request, user_id):
        device = request['data']['content']['device']
        try:
            user_device = await app.db.users.find_one({'_id': ObjectId(user_id), 'devices._id': device['_id']}, {'devices.$': 1})

            logger.info(f'Device in request: {device}')
            if user_device is not None:
                logger.info(f'Updating Device: {user_device}')
                # Update the device
                result = await app.db.users.update_one({'_id': ObjectId(user_id), 'devices._id': device['_id']}, {'$set': {'devices.$': device}})

                if result.modified_count > 0:
                    # Fetch the updated device
                    updated_device = await app.db.users.find_one({'_id': ObjectId(user_id), 'devices._id': device['_id']}, {'devices.$': 1})
                    updated_device['_id'] = str(updated_device['_id'])
                    return {
                        'status': 'success',
                        'message': 'Device updated',
                        'user': {
                            '_id': user_id
                        },
                        'data': {
                            'content': {
                                'device': updated_device
                            },
                            'type': 'device'
                        }
                    }
                else:
                    return {
                        'status': 'success',
                        'message': 'Device is already up-to-date',
                        'user': {
                            '_id': user_id
                        },
                        'data': {
                            'content': {
                                'device': device
                            },
                            'type': 'device'
                        }
                    }, 200
            else:
                result = await app.db.users.update_one({'_id': ObjectId(user_id)}, {'$push': {'devices': device}})
                if result.modified_count > 0:
                    new_device = await app.db.users.find_one({'_id': ObjectId(user_id), 'devices._id': device['_id']}, {'devices.$': 1})
                    new_device['_id'] = str(new_device['_id'])
                    return {
                        'status': 'success',
                        'message': 'Device added',
                        'user': {
                            '_id': user_id
                        },
                        'data': {
                            'content': {
                                'device': new_device
                            },
                            'type': 'device'
                        }
                    }
                else: 
                    return {
                        'status': 'error',
                        'message': 'Error adding new device',
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
        except Exception as e:
            logger.error(f'Error adding device: {e}')
            return {
                'status': 'error',
                'message': 'Error adding device',
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
