import os
import json
from bson import ObjectId
from datetime import datetime
from pprint import pformat
from pyaimanager import AssistantManager
from utils.logger import logger
from dotenv import load_dotenv

load_dotenv()

def handle_non_serializable(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

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

    @classmethod
    async def initialize(cls, assistant_params):
        instance = cls()
        logger.info("Initializing Assistant")
        # create assistant manager 
        instance.assistant_manager = await AssistantManager.create(os.getenv("OPENAI_API_KEY"))
        # check if assistant and trigger already exist
        assistants = await instance.assistant_manager.get_assistants()
        for assistant in assistants:
            if assistant.name == assistant_params["name"]:
                instance.assistant = assistant
                instance.name = assistant.name
            if assistant.name == "Trigger":
                instance.trigger = assistant
        # if assistant and trigger do not exist, create them
        if instance.assistant is None:
            instance.assistant = await instance.assistant_manager.create_assistant(assistant_params)
        if instance.trigger is None:
            instance.trigger = await instance.assistant_manager.create_assistant(instance.load_params("trigger_params.json"))      
        return instance  

    def load_params(self, filename):
        try:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            filepath = os.path.join(script_dir, f'config/{filename}')
            with open(filepath) as f:
                assistant_params = json.load(f)
                return assistant_params
        except FileNotFoundError:
            raise Exception(f"{filename}' file not found")
        except json.JSONDecodeError:
            raise Exception(f"Error decoding JSON from {filename}")

    async def is_triggered(self, message):
        try: 
            logger.info(f"Message: {pformat(message)}")
            response = (await self.trigger.send_message(message))[0]
            logger.info(f"Response: {pformat(response)}") 
            
            if response['status'] == 'requires_action':
                tool_id = response['tool_calls']['tool_call_id']
                logger.info(f"tool_id: {tool_id}, type: {type(tool_id)}")
                
                function_call = response['tool_calls']
                logger.info(f"function_call: {pformat(function_call)}")  
                logger.info(f"Assistant triggered: {function_call['arguments']['attention_needed']}")

                if function_call['arguments']['attention_needed']:
                    # await self.trigger.submit_tool_output([{
                    #     "tool_call_id": tool_id,
                    #     "output": True
                    # }])
                    return True
                else:
                    # await self.trigger.submit_tool_output([{
                    #     "tool_call_id": tool_id,
                    #     "output": False
                    # }])
                    return False
            else:
                return False
        except Exception as e:
            logger.error("Error checking if assistant is triggered: " + str(e))
                
    async def send_message(self, message):
        if type(message) is dict:
            message = json.dumps(message, default=handle_non_serializable)
        triggered = await self.is_triggered(message) 
        logger.info(f"Assistant triggered: {triggered}")           
        if triggered:
            try:
                response = await self.assistant.send_message(message)
                logger.info(f"Request: {pformat(message)}")
                logger.info(f"Response: {pformat(response)}")
                if isinstance(response, list):
                    response = response[0]
                    return {
                        'status': response['status'],
                        'message': 'Assistant response',
                        'data': {
                            'type': 'tool_call',
                            'content': response['tool_calls']
                        }
                    }
                else:
                    return {
                        'status': response['status'],
                        'message': 'Assistant response',
                        'data': {
                            'type': 'ai_response',
                            'content': response
                        }
                    }
            except Exception as e:
                logger.error(f'Error in send_message: {str(e)}')
                raise Exception(f"Error in send_message: {str(e)}")
        else:
            logger.info("Assistant not triggered")
            return None
        
    async def send_tool_response(self, tool_call_output):
        try:
            return await self.assistant.submit_tool_outputs(tool_call_output)
        except Exception as e:
            logger.error(f"Error in submit_tool_output: {str(e)}")
            raise Exception(f'Error in submit_tool_output: {str(e)}')

    
    # cleans the complete response, a complete response is a message object
    def get_message_from_response(self, message):
        return message['message']['content'][0]['text']['value']