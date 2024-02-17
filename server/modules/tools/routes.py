from quart import Blueprint, jsonify
from modules.tools.handler import ToolHandler as tools
from utils.json_request_decorator import route_with_req as _
from utils.logger import logger

bp = Blueprint('tools', __name__)

# return tool response
@_(bp, '/user/<user_id>/tool/<tool_id>/response', methods=['POST'])
async def handle_tool(request, user_id, tool_id):
    logger.info('Received POST request on /tool/%s/response', tool_id)
    result, status_code = await tools.handle_tool(request, tool_id)
    if result is None or status_code is None:
        return jsonify({'message': 'Error handling tool'}), 500
    logger.info(f'Response status code: {status_code}, Response: {result}')
    return jsonify(result), status_code

# get all tools
@_(bp, '/user/<user_id>/device/<device_id>/tools', methods=['GET'])
async def get_tools(user_id, device_id):
    logger.info('Received GET request on /tools/%s', user_id)
    result, status_code = await tools.get_tools(user = user_id, device = device_id)
    if result is None or status_code is None:
        return jsonify({'message': 'Error getting tools'}), 500
    logger.info(f'Response status code: {status_code}, Response: {result}')
    return jsonify(result), status_code

# allow client to create one, or mutliple tools
@_(bp, '/user/<user_id>/device/<device_id>/tools', methods=['POST'])
async def create_tool(request, user_id, device_id):
    logger.info('Received POST request on /tools/%s', user_id)
    result, status_code = await tools.create_tool(request, user = user_id, device = device_id)
    if result is None or status_code is None:
        return jsonify({'message': 'Error creating tool'}), 500
    logger.info(f'Response status code: {status_code}, Response: {result}')
    return jsonify(result), status_code
    