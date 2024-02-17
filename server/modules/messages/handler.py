import json
from datetime import datetime
from bson import ObjectId
from quart import current_app as app
from pprint import pformat
from utils.logger import logger
from utils.request_builder import build_request as build_request
from utils.fetch_entities import fetch_entities
from modules.tools.handler import ToolHandler as tools
from modules.devices.handler import DeviceHandler as devices
from modules.users.handler import UserHandler as users


class MessageHandler:
    @staticmethod
    @fetch_entities
    async def send_message(request, user, device):
        logger.info(f'User: {user}\n Device: {device}')
        try: 
            message = request['data']['content']
            assistant = app.assistant


            logger.info(f'Handling message: "{message}" for user: {user["_id"]}, device: {device["_id"]}')
            request = {
                'status': 'in_progress',
                'message': 'Message being sent',
                'user': user,
                'device': device,
                'data': {
                    'type': 'text',
                    'content': message
                }
            }
            
            logger.info(pformat(request))

            assistant_response = await assistant.send_message(request)
            logger.info(f'Assistant response: {pformat(assistant_response)}')

            if isinstance(assistant_response, list):
                assistant_response = assistant_response[0]

            return await MessageHandler.handle_response(assistant_response, user, device)

        except Exception as e:
            logger.error(f'Error sending message: {e}')
            return {
                'status': 'error',
                'message': 'Error sending message',
                'user': {
                    '_id': user['_id']
                },
                'device': {
                    '_id': device['_id']
                },
                'data': {
                    "content": message,
                }
            }, 500
    
    @staticmethod
    async def handle_response(response, user, device):    
        try:
            if response['status'] == 'requires_action':
                logger.info(f'Status: {response["status"]}')
                tool_call = response['data']['content']
                logger.info(f"Tool call detected: {pformat(response)}")

                tool_output = await tools.handle_tool_call(tool_call, user, device)
                logger.info(f'Tool call connected to output: {pformat(tool_call)}')
                logger.info(f"Tool output: {pformat(tool_output)}")

                if (tool_output['status'] == 'requires_client_action'):
                    return tool_output['message'], 200
                else:
                    response_to_ai = { 
                        'tool_outputs': [{
                            'tool_call_id': tool_call['tool_call_id'],
                            'output': json.dumps({
                                'status': 'completed',
                                'message': 'Tool output',
                                'user': {
                                    'name': user['first_name']
                                },
                                'data': {
                                    'content': tool_output['data']['content'],
                                }
                            })                      
                        }]
                    }
                    logger.info(f"Submitting tool response to AI: {pformat(response_to_ai)}")

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
                        '_id': user['_id'],
                    },
                    'device': {
                        '_id': device['_id'],
                    },
                    'data': {
                        'content': response['data']['content']['message']['content'][0]['text']['value'],
                        'type': response['data']['content']['message']['content'][0]['type']
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
                    '_id': device['_id']
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