from modules.tools.handler import ToolHandler as tools
from utils.json_request_decorator import route_with_req as _

# return tool response
@_('user/<user_id>/tool/<tool_id>/response', methods=['POST'])
async def handle_tool(data, tool_id):
    return await tools.handle_tool(data, tool_id)

# get all tools
@_('user/<user_id>/device/<device_id>/tools', methods=['GET'])
async def get_tools(data, user_id, device_id):
    return await tools.get_tools(data, user_id, device_id)

# allow client to create one, or mutliple tools
@_('user/<user_id>/device/<device_id>/tools', methods=['POST'])
async def create_tool(data, user_id):
    return await tools.create_tool(data, user_id, tools)

# update a specific tool
@_('user/<user_id>/device/<device_id>/tools', methods=['PUT'])
async def update_tool(data, user_id, device_id):
    return await tools.update_tool(data, user_id,device_id)