import json
from aiohttp import ClientSession
from quart import Quart
from tools.actions import  main_functions as actions
from utils.logger import logger
from utils.json_request_decorator import route_with_req as _

app = Quart(__name__)
current_user = None

@_(app, '/command', methods=['POST'])
async def forward_command(request):
    try: 
        # run functions from actions 
        function_name = request['tool']['name']
        function_args = request['tool']['arguments']
        logger.info(f'Received command: {function_name} with args {function_args}')
        function = actions.get(function_name)
        if function:
            logger.info(f'Executing command: {function_name} with args {function_args}')
            result = await function(**function_args)
            response = {
                'status': 'success',
                'message': f'Tool {function_name} with args {function_args} executed successfully',
                'data':{
                    'type': 'command_result',
                    'content': result
                }
            }
            logger.info(f'Successfully executed command: {response}')
            return response, 200
        else:
            logger.error(f'Tool {function_name} not found')
            return {
                'status': 'error',
                'message': f'Tool {function_name} not found',
                'data':{
                    'type': 'command_result',
                    'content': f'Tool {function_name} not found'
                }
            }, 404
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return {
            'status': 'error',
            'message': f'Error executing command: {e}',
            'data':{
                'type': 'command',
                'content': f'Error executing command: {function_name} with args {function_args}'
            }
        }, 500
    
@_(app, '/send_message/<user_id>', methods=['POST'])
async def send_message(request, user_id):
    global current_user
    try:
        with open('config/device.json') as f:
            device = json.load(f)
            logger.debug(f"Device: {device}") 
        logger.info(f"Sending message: {request['data']['text']}")
        logger.info(f"User: {request['user']}")
        logger.info(f"Device: {device}")
        logger.info(f"Current user: {current_user}")
        if current_user['_id'] == user_id:
            logger.info('Current user is the same as the request user')
            async with ClientSession() as session:
                request_data = {
                    "type": "text",
                    "text": request['data']['text']
                }
                logger.info(f'Sending request {request_data}')
                async with session.post(f"http://localhost:5000/messages/user/{current_user['_id']}/device/{device['_id']}", json=request_data) as response:
                    response = await response.json()
                    logger.debug(f"Response: {response}")

                    type = response['data']['type']
                    if type == 'text':
                        response_text = response['data']['text']
                        logger.info(f'Response: {response_text}')
                        return {
                            'user': current_user,
                            'data': {
                                'type': 'text',
                                'text': response_text
                            }
                        }, 200
                    else:
                        logger.error(f'Error in response: {response["message"]}')
                        return {
                            'type': 'error',
                            'error': response['message']
                        }, 500
        else:
            logger.error('Current user is not the same as the request user')
            return {
                'status': 'error',
                'message': 'Current user is not the same as the request user'
            }, 500
    except Exception as e:
        logger.error(f'Error in send_request: {e}')
        return {"status": "error", "message": str(e)}, 500

@_(app, '/user/login', methods=['POST'])
async def login(request):
    global current_user
    try: 
        async with ClientSession() as session:
            async with session.post('http://localhost:5000/user/login', json=request) as response:
                logger.info('Sending login request...')
                response = await response.json()
                logger.debug(f"Response: {response}")

                if response['status'] == 'success':
                    current_user = response['user']
                    logger.info(f'Logged in as: {current_user}')
                    
                return response
    except Exception as e:
        logger.error(f'Error in login request: {e}')
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    app.run(port=5001, host="10.0.0.229")