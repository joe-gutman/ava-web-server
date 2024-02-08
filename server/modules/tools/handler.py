from bson import ObjectId
from modules.tools.actions import main_functions as actions
from quart import current_app as app
from utils.logger import logger

class ToolHandler:
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
    