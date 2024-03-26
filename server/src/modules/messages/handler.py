import json
import asyncio
from bson import ObjectId
from concurrent.futures import ThreadPoolExecutor
from quart import current_app as app
from pprint import pformat
from utils.logger import logger
from utils.request_builder import build_request as build_request
from utils.fetch_entities import fetch_entities
from modules.tools.handler import ToolHandler as tools

executor = ThreadPoolExecutor(max_workers=5)

class MessageHandler:
    @staticmethod
    @fetch_entities
    async def receive_user_message(request, user_id, device_id):
        try: 
            # -------------------- Check if message exists in request -------------------- #
            if request['type'] == 'text':
                message = request['text']
                if message is None or message == "":
                    return {
                        "type": "error",
                        "error": "Bad Request: No message was sent to the assistant."

                    }, 400
                assistant = app.assistant
            else:
                return {
                    "type": "error",
                    "error": f"Bad Request: Message request is {request['type']} but should be text."
                }, 400
            
            # -------------- Check if user and device ids exist in database -------------- #
            user = await app.db['users'].find_one({'_id': ObjectId(user_id)}, {'password': 0})
            device = await app.db['devices'].find_one({'_id': ObjectId(device_id)}, {'password': 0})
            if user is None: 
                error_message = f"User not found with id: {user_id}"
                logger.error(error_message)
                return {
                    "type": "error",
                    "error": error_message
                }, 404
            if device is None: 
                error_message = f"Device not found with id: {device_id}"
                logger.error(error_message)
                return {
                    "type": "error",
                    "error": error_message
                }, 404
            else:
                logger.info(f'Handling message: "{message}" for user: {user_id}, device: {device_id}')

            # # -------------------- Build request to send to assistant -------------------- #
            request = {
                "user": user,
                "device": device,
                "data": {
                    "type": "text",
                    "text": message
                }
            }

            # -------------- Send request to assistant and wait for response -------------- #
            assistant_response = await assistant.interact(request)
            logger.info(f'Assistant response: {pformat(assistant_response)}')
            
            # ------------------------- Build response for client ------------------------ #
            response = {
                "user": user,
                "device": device,
                "data": assistant_response
            }
            error_code = 0
        
            # ---------------------- Handle response from assistant ---------------------- #
            if assistant_response is None:
                response["data"] = {
                    "type": "error",
                    "error": "Assistant failed to respond to request. Please try again later."
                }
                error_code = 500
            
            if assistant_response["type"] == "text" or assistant_response["type"] == None:
                error_code = 200
            
            if assistant_response["type"] == "error":
                error_code = 500
                
            logger.debug(f"Response: {response}")    
            return response, error_code
            

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {
                "status": "error",
                "message": "Error sending message",
                "user": {
                    "_id": user["_id"]
                },
                "device": {
                    "_id": device["_id"]
                },
                "data": {
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
                logger.info(f'Tool call: {pformat(tool_call)}')
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