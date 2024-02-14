from bson import ObjectId
from modules.tools.actions import main_functions as actions
from quart import current_app as app
from utils.logger import logger

class ToolHandler:
    @staticmethod
    async def create_tool(data, user_id, device_id):
        try:
            tools = data['request']['tools']
            logger.info(f'Creating tools: {tools}')
            devices = await app.db.users.find_one({'_id': ObjectId(user_id)}, {'devices': 1})

            tool_update_count = 0
            tool_create_count = 0

            if devices is not None:
                device = next((device for device in devices['devices'] if device['_id'] == device_id), None)

                if device is None:
                    logger.error(f'Device not found: {device_id}')
                    return {'message': 'Device not found'}, 404

                for tool in tools:
                    for user_tool in device['tools']:
                        if tool['name'] == user_tool['name']:
                            logger.info(f'Updating tool: {tool}')
                            user_tool.update(tool)  # Assuming update is a method of the tool object
                            tool_update_count += 1
                            break
                    else:
                        logger.info(f'Creating tool: {tool}')
                        device['tools'].append(tool)
                        tool_create_count += 1

                await app.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'devices': devices['devices']}})
                return {
                    'status': 'success',
                    'status_message': f'Tools created: {tool_create_count}, Tools updated: {tool_update_count}',
                    'user': {
                        '_id': user_id
                    },
                    'data': {
                        'content': {
                            'tools': devices['tools']
                        },
                        'type': 'tools'   
                    }
                }
                    
            else:
                logger.error(f'User not found: {user_id}')
                return {'message': 'User not found'}, 404
        except Exception as e:
            logger.error(f'Error creating tools: {e}')
            return {'message': 'Error creating tools'}, 500
        
    @staticmethod
    async def get_tools(data, user_id, device_id):
        try:
            devices = await app.db.users.find_one({'_id': ObjectId(user_id)}, {'devices': 1})
            if devices is not None:
                device = next((device for device in devices if device['_id'] == device_id), None)

                if device is not None:
                    return {
                        'status': 'success',
                        'user': {
                            '_id': user_id
                        },
                        'data': {
                            'content': {
                                'tools': devices['tools']
                            },
                            'type': 'tools'   
                        }
                    }, 200
                else:
                    logger.error(f'Device not found: {device_id}')
                    return {'message': 'Device not found'}, 404
        except Exception as e:
            logger.error(f'Error getting tools: {e}')
            return {'message': 'Error getting tools'}, 500

    @staticmethod
    async def update_tool(data, user_id, device_id):
        try:
            devices = await app.db.users.find_one({'_id': ObjectId(user_id)}, {'devices': 1})

            if devices is not None:
                device = next((device for device in devices if device['_id'] == device_id), None)

                if device is None:
                    logger.error(f'Device not found: {device_id}')
                    return {'message': 'Device not found'}, 404

                for tool in device['tools']:
                    if tool['_id'] == data['request']['tool']['_id']:
                        tool.update(data['request']['tool'])
                        await app.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'devices': devices}})
                        return {'message': f'Tool updated {tool}'}, 200

                return {'message': 'Tool not found'}, 404

            else:
                return {'message': 'User not found'}, 404

        except Exception as e:
            logger.error(f'Error updating tool: {e}')
            return {'message': 'Error updating tool'}, 500

            


    @staticmethod
    async def run_local_tool(data, user_id):
        logger.info('Running local tool...')
        try:
            tool = actions.get(data['tool']['tool_name'])
            if tool is not None:
                logger.info(f'Tool found: {data["tool"]["tool_name"]}')
                return {'tool': tool}
            else:
                logger.error(f'Tool not found: {data["tool"]["tool_name"]}')
                return {'message': 'Tool not found'}
                
        except Exception as e:
            logger.error(f'Error running tool: {e}')
            return {'message': 'Error running tool'}

    @staticmethod
    async def handle_tool_call(tool_call):
        try:
            logger.info('Handling tool call...')
            user = tool_call['user']
            tool_name = tool_call['request']['function_name']
            tool_arguments = tool_call['request']['arguments']
            logger.info(f'Tool name: {tool_name}, Arguments: {tool_arguments}')
            remote_tool = await ToolHandler.get_remote_tool(tool_name, user['_id']) #check if tool is remote
            if remote_tool is not None:
                logger.info(f'Tool is remote: {remote_tool}')   
                return tool_call
            else:
                logger.info('Tool is not remote.')
                logger.info(f'Actions: {actions}')
                if tool_name in actions:
                    tool_response = await actions[tool_name](user, **tool_arguments)
                    logger.info(f'Tool response: {tool_response}')
                    return tool_response
                else:
                    logger.error('Tool not found in actions.')
                    return {'message': 'Tool not found in actions'} 
        except Exception as e:
            logger.error(f'Error handling tool call: {e}')
            return {'message': 'Error handling tool call'}

    @staticmethod    
    async def get_remote_tool(tool_name, user_id):
        logger.info('Getting remote tool...')
        try:
            user = await app.db.users.find_one({'_id': ObjectId(user_id)})
            if user is None:
                logger.error(f'User not found: {user_id}')
                raise Exception(f'Error checking user tools: {user_id}')
            else: 
                for tool in user['tools']:
                    logger.info(f'Checking tool: {tool}')
                    if tool['name'] == tool_name:
                        logger.info(f'Found tool: {tool_name}')
                        return tool
                logger.info(f'Tool not found: {tool_name}')
                return None
        except Exception as e:
            logger.error(f'Error getting tools: {e}')
            return {'message': 'Error getting tools'}, 500
    