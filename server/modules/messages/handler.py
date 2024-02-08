import json
from bson import ObjectId
from quart import current_app as app
from pprint import pformat
from utils.logger import logger
from utils.request_builder import build_request as build_request
from modules.tools.handler import ToolHandler as tools
from modules.assistant.assistant import Assistant

class MessageHandler:
    @staticmethod
    async def send_message(request, user_id):
        try: 
            logger.info(f'Handling message for user_id: {user_id}')
            
            ava_params = json.load(open('config/ava_params.json'))
            assistant = await Assistant.initialize(ava_params)

            user = await app.db.users.find_one({'_id': ObjectId(user_id)}, {'password': 0})
            logger.info(f'User found: {pformat(user)}')

            request = build_request(user, request)
            
            logger.info(f'Message: {pformat(request)}')

            assistant_response = await assistant.send_message(request)
            logger.info(f'Assistant response: {pformat(assistant_response)}')

            if isinstance(assistant_response, list):
                assistant_response = assistant_response[0]


            # 'status': 'requires_action', means that the assistant has triggered a tool and is waiting for a response with the tool output.
            # If the response requires action, the appropriate tool will be called and the output will be returned.
            if assistant_response['status'] == 'requires_action':
                logger.info(f'Status: {assistant_response["status"]}')
                tool_call = build_request(user, assistant_response['tool_calls'])
                logger.info(f"Tool call detected: {pformat(tool_call)}")

                tool_output = await tools.handle_tool_call(tool_call)
                logger.info(f"Tool output: {tool_output}")

                response_to_ai = { 
                    'tool_call_id': tool_call['request']['tool_call_id'], 
                    'tool_outputs': [{
                        'tool_call_id': tool_call['request']['tool_call_id'],
                        'output':json.dumps(build_request(user, tool_output))
                    }]}
                logger.info(f"Submitting tool response: {pformat(response_to_ai)}")

                response_from_ai = await assistant.send_tool_response(response_to_ai)
                logger.info(f'AI response to tool output: {pformat(response_from_ai)}')
                response_to_client = {
                    'status': 'success',
                    'user': {
                        '_id': user_id,
                    },
                    'data': {
                        'response': response_from_ai['message']['content'][0]['text']['value'],
                        'type': response_from_ai['message']['content'][0]['type']
                    }
                }
                logger.info(f'Message sent to client: {pformat(response_to_client)}')
                return response_to_client, 200
            elif assistant_response['status'] == 'completed':
                logger.info(f'Status: {assistant_response["status"]}')
                response_to_client = {
                    'status': 'success',
                    'user': {
                        '_id': user_id,
                    },
                    'data': {
                        'response': assistant_response['message']['content'][0]['text']['value'],
                        'type': assistant_response['message']['content'][0]['type']
                    }
                }
                logger.info(f'Message sent to client: {pformat(response_to_client)}')
                return response_to_client, 200

        except Exception as e:
            logger.error(f'Error sending message: {e}')
            return {'message': 'Error sending message'}, 500

    @staticmethod
    async def get_message_history(user_id):
        logger.info(f'Getting message history for user_id: {user_id}')
        messages = await app.db.messages.find({'user_id': user_id})
        return {'messages': messages['message_history']}, 200