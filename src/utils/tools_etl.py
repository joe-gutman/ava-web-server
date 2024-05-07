import asyncio
import json
from ..db_connection import initialize_client

async def main():
    
    # Load the JSON file
    with open('server/config/tool_params.json') as f:
        data = json.load(f)

    # Check if each tool has a location and a name
    for index, tool in enumerate(data):
        if 'device' not in tool or not tool['device']:
            raise ValueError(f'Tool at index {index} does not have a location')
        if 'name' not in tool['function'] or not tool['function']['name']:
            raise ValueError(f'Tool at index {index} does not have a name')

    db = await initialize_client()

    db['tools'].drop_index('tool_name_1_user_id_1')
    db['tools'].create_index(
        [("tool_name", 1), ("user_id", 1)],
        unique=True,
        sparse=True
    )

    collection = db['tools']

    await collection.insert_many(data)

# Run the main function inside an event loop
loop = asyncio.get_event_loop()
loop.run_until_complete(main())