class Tool:
    def __init__(self, type, parameter_names, parameter_count, user_id, client_ids):
        self.type = type
        self.parameter_names = parameter_names
        self.parameter_count = parameter_count
        self.user_id = user_id
        self.client_ids = client_ids

class ToolHandler:
    @staticmethod
    async def get_tools():
        tools = []
        cursor = collection.find({})
        async for document in cursor:
            tools.append(document)
        return tools

    @staticmethod
    async def get_tool(tool_name):
        tool = await collection.find_one({'name': tool_name})
        return tool

    @staticmethod
    async def create_tool(tool):
        result = await collection.insert_one(tool.__dict__)
        return result.inserted_id

    @staticmethod
    async def delete_tool(tool_name):
        await collection.delete_one({'name': tool_name})

    @staticmethod
    async def update_tool(tool):
        await collection.replace_one({'name': tool.name}, tool.__dict__)

    # @staticmethod
    # async def tool_call(tool):
    #     # Save the request of a tool call
    #     pass

    # @staticmethod
    # async def tool_call_response(response, tool_id):
    #     # Save the response of a tool call
    #     pass