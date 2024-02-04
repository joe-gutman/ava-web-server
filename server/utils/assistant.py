import asyncio
import os
import json
import logging
from pyaimanager import AssistantManager

from dotenv import load_dotenv
load_dotenv()

# import tools
from .tool_functions import functions

logging.basicConfig(level=logging.DEBUG)

class Assistant:
    """
    A simple assistant that can talk to you, and answer your questions.

    Initialization Parameters:
        api_key (str): An Open API key for the Assistant API.
        assistant_params (dict): A dictionary of parameters to create a new assistant.
    """
    def __init__(self):
        self.assistant_manager = None
        self.assistant = None
        self.trigger = None
        self.name = None

    async def initialize(self, assistant_params):
        print("assistant_name: ", assistant_params["name"]) 
        logging.info("Initializing Assistant")
        # create assistant manager 
        self.assistant_manager = await AssistantManager.create(os.getenv("OPENAI_API_KEY"))
        # check if assistant and trigger already exist
        assistants = await self.assistant_manager.get_assistants()
        for assistant in assistants:
            if assistant.name == assistant_params["name"]:
                self.assistant = assistant
                self.name = assistant.name
            if assistant.name == "Trigger":
                self.trigger = assistant
        # if assistant and trigger do not exist, create them
        if self.assistant is None:
            self.assistant = await self.assistant_manager.create_assistant(assistant_params)
        if self.trigger is None:
            self.trigger = await self.assistant_manager.create_assistant(self.load_params("assistant/trigger_params.json"))        
            
        assistant_names = [assistant.name for assistant in assistants]
        logging.info("Assistants: " + str(assistant_names))

    def load_params(self, filename):
        try:
            with open(filename) as f:
                assistant_params = json.load(f)
                return assistant_params
        except FileNotFoundError:
            raise Exception(f"{filename}' file not found")
        except json.JSONDecodeError:
            raise Exception(f"Error decoding JSON from {filename}")

    async def handle_tool_call(self, function_name, function_args):
        try:
            return functions[function_name](function_args)
        except Exception as e:
            logging.error("Error in handle_tool_call: " + str(e))    
            raise Exception("Error in handle_tool_call: " + str(e))
        
    async def is_assistant_triggered(self, message):
        """
        Check if the assistant is triggered by the message. Checks against the trigger assistant and local assistant name.

        Parameters:
            message (str): The message to check if the assistant is triggered.

        Returns:
            bool: True if the assistant is triggered, False otherwise.    
        """
        try: 
            response = await self.trigger.send_message(message)
            if response['status'] == 'requires_action':
                tool_id = response['tool_calls'][0]['tool_call_id'],
                tool_args = {
                    "attention_needed": response['tool_calls'][0]['arguments']['attention_needed'],
                    "user_message": response['tool_calls'][0]['arguments']['user_message'],
                    "assistant_name": response['tool_calls'][0]['arguments']['assistant_name']
                }

                if tool_args['attention_needed'] and tool_args['assistant_name'] == self.name:
                    return True
                else:
                    await self.trigger.submit_tool_output([{
                        "tool_call_id": tool_id,
                        "output": False
                    }])
                    return False
            else:
                return False
        except Exception as e:
            logging.error("Error checking if assistant is triggered: " + str(e))
            # raise Exception("Error checking if assistant is triggered: " + str(e))
                
    async def send_message(self, message):
        triggered = self.is_assistant_triggered(message)
        if triggered:
            try:
                response = await self.assistant.send_message(message)
                print(response)
                if response['status'] == 'requires_action':
                    tool_call_outputs = []

                    for tool in response['tool_calls']:
                        tool_call_id = tool['tool_call_id']
                        function_name = tool['function_name']
                        function_args = tool['arguments']
                        tool_output = self.handle_tool_call(function_name, function_args)

                        tool_call_outputs.append({
                            "tool_call_id": tool_call_id,
                            "output": tool_output
                        })

                    # Submit the tool output
                    try:
                        await self.assistant.submit_tool_output(tool_call_outputs)
                    except Exception as e:
                        logging.error("Error in submit_tool_output: " + str(e))
                        raise Exception("Error in submit_tool_output: " + str(e))
                elif response['status'] == 'completed':
                    # This is a regular message, handle it accordingly
                    return clean_complete_response(response[message])
            except Exception as e:
                logging.error("Error in send_message: " + str(e))
                # raise Exception("Error in send_message: " + str(e))
    
    # cleans the complete response, a complete response is a message object
    def clean_complete_response(self, message):
        return message['content'][0]['text']['value']