from quart import Blueprint, jsonify
from modules.users.handler import UserHandler as users
from utils.json_request_decorator import route_with_req as _
from utils.logger import logger

bp = Blueprint('users', __name__)

# update a specific tool
@_(bp, '/user/<user_id>/device/<device_id>/tools', methods=['PUT'])
async def update_tool(request, user_id, device_id):
    logger.info('Received PUT request on /tools/%s', user_id)
    result, status_code = await tools.update_tool(request, user_id, device_id)
    if result is None or status_code is None:
        return jsonify({'message': 'Error updating tool'}), 500
    logger.info(f'Response status code: {status_code}, Response: {result}')
    return jsonify(result), status_code

# login user
@_(bp, '/user/login', methods=['POST'])
async def login_user(data):
    logger.info('Received POST request on /user/login')
    result, status_code = await users.login_user(data)
    if result is None or status_code is None:
        return jsonify({'message': 'Error logging in user'}), 500
    logger.debug(f'Response status code: {status_code}, Response: {result}')
    return jsonify(result), status_code

@_(bp, '/user/register', methods=['POST'])
async def register_user(data):
    logger.info('Received POST request on /user/register')
    result, status_code = await users.register_user(data)
    if result is None or status_code is None:
        return jsonify({'message': 'Error registering user'}), 500
    logger.debug(f'Response status code: {status_code}, Response: {result}')
   