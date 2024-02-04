from handlers import tools
from auto_request_json import route_with_req

# get all tools
@route_with_req('/tool/get_tools', methods=['GET'])
async def get_tools(data):
    return await tools.get_tools(data)

# get a tool by name
@route_with_req('tool/get_tool/<tool_name>', methods=['GET'])
async def get_tool(tool_name):
    return await tools.get_tool(tool_name)

# create a new tool
@route_with_req('/tool/create', methods=['POST'])
async def create_tool(tool):
    return await tools.create_tool(tool)

# delete the tool
@route_with_req('/tool/delete/<tool_name>', methods=['DELETE'])
async def delete_tool(tool):
    return await tools.delete_tool(tool)

# update the tool
@route_with_req('/tool/update/<tool_name>', methods=['POST'])
async def update_tool(tool):
    return await tools.update_tool(tool)

# # save the request of a tool call to use as training data
# @route_with_req('/tool/tool_call', methods=['POST'])
# async def tool_call(tool):
#     return await tools.tool_call(tool)

# # save the response of a tool call to use as training data
# @route_with_req('/tool/tool_call_response/<tool_name>', methods=['POST'])
# async def tool_call_response(response, tool_id):
#     return await tools.tool_call_response(response, tool_id)
