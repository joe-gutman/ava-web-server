import json
from bson import ObjectId
from quart import current_app as app
from pprint import pformat
from utils.logger import logger
from utils.request_builder import build_request as build_request
from modules.tools.handler import ToolHandler as tools

class MessageHandler:
    @staticmethod
    async def send_message(request, user_id, device_id):
        try: 
            message = request['data']['content']
            assistant = app.assistant
            logger.info(f'Handling message: "{message}" for user_id: {user_id}, device_id: {device_id}')

            user = await app.db.users.find_one({'_id': ObjectId(user_id)}, {'password': 0})
            logger.info(f'User found: {pformat(user)}')

            request = build_request(user, request)
            
            logger.info(f'Message: {pformat(request)}')

            assistant_response = await assistant.send_message(message)
            logger.info(f'Assistant response: {pformat(assistant_response)}')

            if isinstance(assistant_response, list):
                assistant_response = assistant_response[0]

            return await MessageHandler.handle_response(assistant_response, user_id, device_id)

        except Exception as e:
            logger.error(f'Error sending message: {e}')
            return {
                'status': 'error',
                'message': 'Error sending message',
                'user': {
                    '_id': user['_id']
                },
                'device': {
                    '_id': device_id
                },
                'data': {
                    "content": message,
                }
                }, 500
    
    @staticmethod
    async def handle_response(response, user_id, device_id):
        try:
            if response['status'] == 'requires_action':
                logger.info(f'Status: {response["status"]}')
                tool_call = build_request(tool_call, user_id, device_id)
                logger.info(f"Tool call detected: {pformat(tool_call)}")

                tool_output = await tools.handle_tool_call(response['data']['content'], user_id, device_id)
                logger.info(f"Tool output: {tool_output}")

                if (tool_output['status'] == 'requires_client_action'):
                    return tool_output['message'], 200
                else:
                    user = await app.db.users.find_one({'_id': ObjectId(user_id)}, {'password': 0})
                    response_to_ai = { 
                        'tool_call_id': tool_call['request']['tool_call_id'], 
                        'tool_outputs': [{
                            'tool_call_id': tool_call['request']['tool_call_id'],
                            'output': {
                                'status': 'completed',
                                'message': 'Tool output',
                                'user': {
                                    'username': user['username'],
                                    'name': user['name']
                                },
                                'data': {
                                    'content': tool_output['data']['content'],
                                    'type': tool_output['data']['type'],
                                    'tool': {
                                        'name': tool_output['data']['tool']['name'],
                                        'id': tool_output['data']['tool']['id']
                                    }
                                }
                            }                      
                        }]
                    }
                    logger.info(f"Submitting tool response: {pformat(response_to_ai)}")

                    response_from_ai = await app.assistant.send_tool_response(response_to_ai)
                    logger.info(f'AI response to tool output: {pformat(response_from_ai)}')
                    response_to_client = {
                        'status': 'success',
                        'user': {
                            '_id': str(user['_id']),
                        },
                        'data': {
                            'content': response_from_ai['message']['content'][0]['text']['value'],
                            'type': response_from_ai['message']['content'][0]['type']
                        }
                    }
                    logger.info(f'Message sent to client: {pformat(response_to_client)}')
                    return response_to_client, 200
            elif response['status'] == 'completed':
                logger.info(f'Status: {response["status"]}')
                response_to_client = {
                    'status': 'success',
                    'user': {
                        '_id': str(user['_id']),
                    },
                    'data': {
                        'content': response['message']['content'][0]['text']['value'],
                        'type': response['message']['content'][0]['type']
                    }
                }
                logger.info(f'Message sent to client: {pformat(response_to_client)}')
                return response_to_client, 200
        except Exception as e:
            logger.error(f'Error handling response: {e}')
            return {
                'status': 'error',
                'message': 'Error handling response',
                'user': {
                    '_id': user['_id']
                },
                'device': {
                    '_id': device_id
                },
                'data': {
                    "content": response['data']['content'],
                }
                }, 500

    @staticmethod
    async def get_message_history(user_id):
        logger.info(f'Getting message history for user_id: {user_id}')
        messages = await app.db.messages.find({'user_id': user_id})
        return {'messages': messages['message_history']},