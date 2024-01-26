import asyncio
import os
import json
from pyaimanager import AssistantManager

from dotenv import load_dotenv
load_dotenv()

# import tools
from .tools.tool_functions import tools, functions

# Create a new chatbot class
class Ava:
    """
    A simple chatbot that can talk to you, and answer your questions.

    Initialization Parameters:
        api_key (str): An Open API key for the Assistant API.
        assistant_params (dict): A dictionary of parameters to create a new assistant.
    """
    def __init__(self):
        self.assistant_params = None
        self.assistant = None

    async def initialize(self):
        with open('./ava/ava_parameters.json', 'r') as f:
            self.assistant_params = json.load(f)
        self.assistant = await AssistantManager(os.getenv("OPENAI_API_KEY")).create_assistant(self.assistant_params)

    async def send_message(self, message):
        response = await self.assistant.send_message(message)
        return self.clean_message_response(response) 
    
    def clean_message_response(self, response):
        print(response)
        return response['content'][0]['text']['value']