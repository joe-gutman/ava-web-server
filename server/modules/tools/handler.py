from bson import ObjectId
from modules.tools.actions import main_functions as actions
from quart import current_app as app
from utils.logger import logger
from utils.to_lowercase import to_lowercase

class ToolHandler:
    @staticmethod
    async def create_tool(request, user_id):
        tool = request['data']['content']['tool']

        try:
            logger.info(f'Creating tool: {tool}')

            tool_to_insert = tool.copy()
            tool_to_insert['user_id'] = ObjectId(user_id)

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
                        '_id': user_id
                    },
                    'device': {
                        '_id': device_id
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
                existing_tool = await app.db.tools.find_one({'user_id': ObjectId(user_id), 'device_id': ObjectId(device_id), 'name': tool['name']})
                if existing_tool:
                    existing_tool['_id'] = str(existing_tool['_id'])
                    existing_tool['user_id'] = str(existing_tool['user_id'])
                    existing_tool['device_id'] = str(existing_tool['device_id'])
                return {
                    'status': 'error',
                    'message': 'Tool already exists',
                    'user': {
                        '_id': user_id
                    },
                    'device': {
                        '_id': device_id
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
                    '_id': user_id
                },
                'device': {
                    '_id': device_id
                },
                'data': {
                    'content': {
                        'tool': tool
                    },
                    'type': 'tool'
                }
            }, 500
        
        
    @staticmethod
    async def update_tool(request, user_id, device_id, tool_id):
        try:
            tool = request['data']['content']['tool']
            logger.info(f'Updating tool: {tool}')

            device = await app.db.devices.find_one({'_id': ObjectId(device_id), 'user_id': ObjectId(user_id)})

            if device is None:
                return {
                    'status': 'error',
                    'message': 'Device not found',
                    'user': {
                        '_id': user_id
                    },
                    'device': {
                        '_id': device_id
                    }
                }, 404

            tool['device_id'] = device_id
            tool['user_id'] = user_id
            result = await app.db.tools.update_one({'_id': ObjectId(tool_id)}, {'$set': to_lowercase(tool)})

            if result.modified_count == 1:
                updated_tool = await app.db.tools.find_one({'_id': ObjectId(tool_id)})
                updated_tool['_id'] = str(updated_tool['_id'])
                updated_tool['user_id'] = str(updated_tool['user_id'])
                updated_tool['device_id'] = str(updated_tool['device_id'])

                return {
                    'status': 'success',
                    'message': 'Tool updated', 
                    'user': {
                        '_id': user_id
                    },
                    'device': {
                        '_id': device_id
                    },
                    'data': {
                        'type': 'tool',
                        'content': {
                            'tool': updated_tool
                        }
                    }
                }
            else:
                return {'message': 'Error updating tool'}, 500
        except Exception as e:
            logger.error(f'Error updating tool: {e}')
            return {
                'status': 'error',
                'message': 'Error updating tool',
                'user': {
                    '_id': user_id
                },
                'device': {
                    '_id': device_id
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
    async def get_tool_by_name(user_id, device_name, tool_name):
        try:
            tool = await app.db.tools.find_one({'user_id': ObjectId(user_id), 'device': device_name, 'function.name': tool_name})

            if tool is not None:
                return {
                    'status': 'success',
                    'message': 'Tool found',
                    'user': {
                        '_id': user_id
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
                            '_id': user_id
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
                            '_id': user_id
                        }
                    }, 404
        except Exception as e:
            logger.error(f'Error getting tool: {e}')
            return {
                'status': 'error',
                'message': 'Error getting tool',
                'user': {
                    '_id': user_id
                }
            }, 500



        
    # get users tools
    @staticmethod
    async def get_user_tools(user_id):
        try:
            tools = await app.db.tools.find({'user_id': ObjectId(user_id)}).to_list(length=None)

            for tool in tools:
                tool['_id'] = str(tool['_id'])
                tool['user_id'] = str(tool['user_id'])
                tool['device_id'] = str(tool['device_id'])

            return {
                'status': 'success',
                'message': 'User tools',
                'user': {
                    '_id': user_id
                },
                'data': {
                    'type': 'tools',
                    'content': {
                        'tools': tools
                    }
                }
            }
        except Exception as e:
            logger.error(f'Error getting user tools: {e}')
            return {
                'status': 'error',
                'message': 'Error getting user tools',
                'user': {
                    '_id': user_id
                }
            }, 500
        
    # get device tools
    @staticmethod
    async def get_device_tools(user_id, device_id):
        try:
            tools = await app.db.tools.find({'user_id': ObjectId(user_id), 'device_id': ObjectId(device_id)}).to_list(length=None)

            for tool in tools:
                tool['_id'] = str(tool['_id'])
                tool['user_id'] = str(tool['user_id'])
                tool['device_id'] = str(tool['device_id'])

            return {
                'status': 'success',
                'message': 'Device tools',
                'user': {
                    '_id': user_id
                },
                'device': {
                    '_id': device_id
                },
                'data': {
                    'type': 'tools',
                    'content': {
                        'tools': tools
                    }
                }
            }
        
        except Exception as e:
            logger.error(f'Error getting device tools: {e}')
            return {
                'status': 'error',
                'message': 'Error getting device tools',
                'user': {
                    '_id': user_id
                },
                'device': {
                    '_id': device_id
                }
            }, 500
        
    # get all tools
    @staticmethod
    async def get_all_tools(user_id, device_id):
        try:
            user_tools = await app.db.tools.find({'user_id': ObjectId(user_id)}).to_list(length=None)

            server_tools = await app.db.tools.find({'device': 'server'}).to_list(length=None)

            device = await app.db.devices.find_one({'_id': ObjectId(device_id), 'user_id': ObjectId(user_id)})
            if device is not None:
                device_tools = await app.db.tools.find({'device': device['name']}).to_list(length=None)


            all_tools = user_tools + server_tools + device_tools

            for tool in all_tools:
                tool['_id'] = str(tool['_id'])
                if('user_id' in tool):
                    tool['user_id'] = str(tool['user_id'])
                if('device_id' in tool):
                    tool['device_id'] = str(tool['device_id'])

            return {
                'status': 'success',
                'message': 'All tools',
                'user': {
                    '_id': user_id
                },
                'data': {
                    'type': 'tools',
                    'content': {
                        'tools': all_tools
                    }
                }
            }
        except Exception as e:
            logger.error(f'Error getting all tools: {e}')
            return {
                'status': 'error',
                'message': 'Error getting all tools',
                'user': {
                    '_id': user_id
                }
            }, 500

    @staticmethod
    async def handle_tool_call(tool_call, user_id, device_id):
        try:
            device = await app.db.devices.find_one({'_id': ObjectId(device_id), 'user_id': ObjectId(user_id)})
            logger.info('Handling tool call...')
            try: 
                tool = ToolHandler.get_tool_by_name(user_id, device['name'], tool_call['function']['name'])
                tool_name = tool['function']['name']
                tool_arguments = tool['function']['arguments']

                if tool['device'] == 'server':
                    response = await actions.get(tool_name)(tool_arguments)
                    # run tool from dictionary 'function name': function
                    return {
                        'status': 'success',
                        'message': 'Tool output',
                        'user': {
                            '_id': user_id
                        },
                        'device': {
                            '_id': device_id
                        },
                        'data': {
                            'type': 'tool',
                            'content': {
                                'tool_output': response
                            }
                        }
                    }
                elif tool['device'] == device['name']:
                    return {
                        'status': 'requires_client_action',
                        'message': 'Tool requires action from client',
                        'user': {
                            '_id': user_id
                        },
                        'device': {
                            '_id': device_id
                        },
                        'data': {
                            'type': 'tool',
                            'content': {
                                'tool': { 'name': tool_name, 'arguments': tool_arguments }
                            }
                        }
                    }
                else: 
                    return {
                        'status': 'error',
                        'message': 'Tool not found',
                        'user': {
                            '_id': user_id
                        },
                        'device': {
                            '_id': device_id
                        }
                    }, 404
            except Exception as e:
                logger.error(f'Error handling tool call: {e}')
                return {
                    'status': 'error',
                    'message': 'Error handling tool call',
                    'user': {
                        '_id': user_id
                    },
                    'device': {
                        '_id': device_id
                    }
                }, 500
        except Exception as e:
            logger.error(f'Error getting device for tool call: {e}')
            return {
                'status': 'error',
                'message': 'Error getting device for tool call',
                'user': {
                    '_id': user_id
                },
                'device': {
                    '_id': device_id
                }
            }, 500
    