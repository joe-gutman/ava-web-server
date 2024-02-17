import httpx
from quart import Quart, request
from utils.logger import logger
from utils.json_request_decorator import route_with_req as _
from tools.actions import  main_functions as actions

app = Quart(__name__)

@_(app, '/command', methods=['POST'])
async def forward_command(request):
    try: 
        # run functions from actions 
        function_name = request['tool']['name']
        function_args = request['tool']['arguments']
        function = actions.get(function_name)
        if function:
            result = await function(**function_args)
            response = {
                'status': 'success',
                'message': f'Tool {function_name} with args {function_args} executed successfully',
                'data':{
                    'type': 'command_result',
                    'content': result
                }
            }
            logger.info(response)
            return response, 200
        else:
            return {
                'status': 'error',
                'message': f'Tool {function_name} not found',
                'data':{
                    'type': 'command_result',
                    'content': f'Tool {function_name} not found'
                }
            }
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return {
            'status': 'error',
            'message': f'Error executing command: {e}',
            'data':{
                'type': 'command',
                'content': f'Error executing command: {function_name} with args {function_args}'
            }
        }


if __name__ == "__main__":
    app.run(port=5001, host="10.0.0.229")