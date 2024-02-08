from modules.tools.handler import ToolHandler as tools
from utils.json_request_decorator import route_with_req as _


@_('user/<user_id>/tool/<tool_id>/response', methods=['POST'])
async def handle_tool(data, tool_id):
    return await tools.handle_tool(data, tool_id) 

@_('user/<user_id>/tools', methods=['GET'])
async def get_tools(data, user_id):
    return await tools.get_tools(data, user_id)