import httpx
from pprint import pformat
from bson import ObjectId
from quart import current_app as app
from utils.logger import logger
from utils.fetch_entities import fetch_entities
from utils.to_lowercase import to_lowercase

class ToolHandler:
    @staticmethod
    @fetch_entities
    async def handle_tool_call(tool_call, user, device):
        try: 
            logger.info(f'Handling tool call: {tool_call}')
            tool_name = tool_call['function_name']
            tool_arguments = tool_call['arguments']
            tool_arguments['user'] = user

            tool_location = (await ToolHandler.get_tool_by_name(user, device, tool_call['function_name']))['data']['content']['tool']['device']
            logger.info(f'Tool location: {tool_location}')
            logger.info(f'Device: {pformat(device)}')
            logger.info(f'tool_name: {tool_name}') 
            logger.info(f'tool_arguments: {tool_arguments}')
            logger.info(f'tool_call: {pformat(tool_call)}')
            if tool_location == 'server':
                response = await actions.get(tool_name)(**tool_arguments)
                # run tool from dictionary 'function name': function
                return {
                    'status': 'success',
                    'message': 'Tool output',
                    'user': {
                        '_id': user['_id']
                    },
                    'device': {
                        '_id': device['_id']
                    },
                    'data': {
                        'type': 'tool',
                        'content': {
                            'tool_output': response
                        }
                    }
                }
            elif tool_location == 'client':
                logger.info(f'Running tool on client: {tool_name}')
                logger.info(f'Client: {pformat(device)}')
                address = device['location']['server_address']
                port = device['location']['server_port']
                logger.info(f'Client address: {address}:{port}')
                request = {
                    'user': user,
                    'device': device,
                    'tool': {
                        'name': tool_name, 
                        'arguments': tool_arguments
                    }
                }
                logger.info(f'Request: {pformat(request)}')    
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f'http://{address}:{port}/command', 
                        json=request
                    )
                if response.status_code == 200:
                    formated_response = {
                        'status': 'success',
                        'message': 'Tool output',
                        'user': {
                            '_id': user['_id']
                        },
                        'device': {
                            '_id': device['_id']
                        },
                        'data': {
                            'type': 'tool',
                            'content': {
                                'tool_output': response.json()['data']['content']
                            }
                        }
                    }
                    logger.info(f'Tool output: {pformat(formated_response)}')
                    return formated_response
                else:
                    return {'status': 'error', 'message': 'Failed to run tool on client'}, 500
            else: 
                return {
                    'status': 'error',
                    'message': 'Tool not found',
                    'user': {
                        '_id': user['_id']
                    },
                    'device': {
                        '_id': device['_id']
                    }
                }, 404
        except Exception as e:
            logger.error(f'Error handling tool call: {e}')
            return {
                'status': 'error',
                'message': f'Error handling tool call: {e}',
                'user': {
                    '_id': user['_id']
                },
                'device': {
                    '_id': device['_id']
                }
            }, 500
    
    @staticmethod
    @fetch_entities
    async def create_tool(request, user, device = None):
        tool = request['data']['content']['tool']

        try:
            logger.info(f'Creating tool: {tool}')

            tool_to_insert = tool.copy()
            tool_to_insert['user_id'] = ObjectId(user['_id'])
            if device:
                tool_to_insert['device_id'] = ObjectId(device['_id'])

            try:
                result = await app.db.tools.insert_one(to_lowercase(tool_to_insert))
                logger.info(f'New tool created: {result}')

                inserted_tool = await app.db.tools.find_one({'_id': result.inserted_id})
                inserted_tool['_id'] = str(inserted_tool['_id'])
                inserted_tool['user_id'] = str(inserted_tool['user_id'])
                inserted_tool['device_id'] = str(inserted_tool['device_id'])

                return {
                    'status': 'success',
                    'message': 'Tool created', 
                    'user': {
                        '_id': user['_id']
                    },
                    'data': {
                        'type': 'tool',
                        'content': {
                            'tool': inserted_tool
                        }
                    }
                }

            except DuplicateKeyError as e:
                logger.error(f'Tool already exists: {tool}')
                existing_tool = await app.db.tools.find_one({'user_id': ObjectId(user['_id']), 'device_id': ObjectId(device_id), 'name': tool['name']})
                if existing_tool:
                    existing_tool['_id'] = str(existing_tool['_id'])
                    existing_tool['user_id'] = str(existing_tool['user_id'])
                    existing_tool['device_id'] = str(existing_tool['device_id'])
                return {
                    'status': 'error',
                    'message': 'Tool already exists',
                    'user': {
                        '_id': user['_id']
                    },
                    'data': {
                        'content': {
                            'tool': existing_tool
                        },
                        'type': 'tool'
                    }
                }, 400
        except Exception as e:
            logger.error(f'Error creating tool: {e}')
            return {
                'status': 'error',
                'message': 'Error creating tool',
                'user': {
                    '_id': user['_id']
                },
                'data': {
                    'content': {
                        'tool': tool
                    },
                    'type': 'tool'
                }
            }, 500     
  
    # get tool by name
    @staticmethod
    @fetch_entities
    async def get_tool_by_name(user, device, tool_name):
        try:
            logger.info(f'Getting tool: {tool_name}')
            tool = await app.db.tools.find_one({
                '$or': [
                    {'user_id': ObjectId(user['_id']), 'device_id': ObjectId(device['_id']), 'function.name': tool_name},
                    {'user_id': {'$exists': False}, 'device_id': {'$exists': False}, 'function.name': tool_name},
                ]
            })

            if tool is not None:
                return {
                    'status': 'success',
                    'message': 'Tool found',
                    'user': {
                        '_id': user['_id']
                    },
                    'data': {
                        'type': 'tool',
                        'content': {
                            'tool': tool
                        }
                    }
                }
            else:
                tool = await app.db.tools.find_one({'name': tool_name})
                if tool is not None:
                    return {
                        'status': 'success',
                        'message': 'Tool found',
                        'user': {
                            '_id': user['_id']
                        },
                        'data': {
                            'type': 'tool',
                            'content': {
                                'tool': tool
                            }
                        }
                    }
                else:
                    return {
                        'status': 'error',
                        'message': 'Tool not found',
                        'user': {
                            '_id': user['_id']
                        }
                    }, 404
        except Exception as e:
            logger.error(f'Error getting tool: {e}')
            return {
                'status': 'error',
                'message': 'Error getting tool',
                'user': {
                    '_id': user['_id']
                }
            }, 500
