from pprint import pformat
from quart import Blueprint, jsonify
from modules.messages.handler import MessageHandler as message
from utils.logger import logger
from utils.json_request_decorator import route_with_req as _
from utils.convert_to_str import convert_to_str

bp = Blueprint('messages', __name__)

# send a message, also saves the message in the database message history
@_(bp, '/messages/user/<user_id>/device/<device_id>', methods=['POST'])
async def receive_user_message(request, user_id, device_id):
    logger.info(f'Received POST request on /messages/user/{user_id}/device/{device_id}')
    result, status_code = await message.receive_user_message(request, user_id, device_id)
    if result is None or status_code is None:
        result, status_code = {
            "type": "error",
            "error": "There was an error handling the message. Please try again later."
            }, 500
        
    result = convert_to_str(result)
    logger.info(f'Status code: {status_code}, Response: \n {pformat(result)}')
    return jsonify(result), status_code

# get all messages
@_(bp,'/messages/<user_id>', methods=['GET'])
async def get_messages_route(user_id):
    logger.info('Received GET request on /messages/%s', user_id)
    result, status_code = await message.get_messages(user_id)
    logger.info('Response status code: %s, Response: %s', status_code, result)
    return jsonify(result), status_code