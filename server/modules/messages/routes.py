from quart import Blueprint, jsonify
from modules.messages.handler import MessageHandler as message
from utils.logger import logger
from utils.json_request_decorator import route_with_req as _

bp = Blueprint('messages', __name__)

# send a message, also saves the message in the database message history
@_(bp, '/messages/user/<user_id>/device/<device_id>', methods=['POST'])
async def send_message_route(request, user_id, device_id):
    logger.info(f'Received POST request on /messages/user/{user_id}/device/{device_id}')
    result, status_code = await message.send_message(request, user = user_id, device = device_id)
    if result is None or status_code is None:
        return jsonify({'message': 'Error handling message'}), 500
    logger.info('Response status code: %s, Response: %s', status_code, result)
    return jsonify(result), status_code

# get all messages
@_(bp,'/messages/<user_id>', methods=['GET'])
async def get_message_route(user_id):
    logger.info('Received GET request on /messages/%s', user_id)
    result, status_code = await message.get_messages(user_id)
    logger.info('Response status code: %s, Response: %s', status_code, result)
    return jsonify(result), status_code