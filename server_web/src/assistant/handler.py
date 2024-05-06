import cohere
import uuid
import os
import time
import json
import importlib
from quart import current_app as app
from datetime import datetime
from utils.logger import logger
from cohere import ChatMessage

class Assistant():
    def __init__(self):
        self.id = uuid.uuid4()
        self.modules = self.load_config()
        self.tools = self.load_tools()
        self.latest_task = None
        self.message_history = []
        self.conversation_id = str(uuid.uuid4())
        self.co = cohere.Client(os.environ.get('CO_API_KEY'))

    def __repr__(self):
        return f'<Assistant {self.name}:{self.id}>'

    def load_config(self):
        try:
            with open('config.json') as json_file:
                config_data = json.load(json_file)
            
                logger.info("Loading assistant config...")
                # logger.debug(config_data)
                
                if 'model_name' not in config_data:
                    logger.error("Missing model_name in config.")
                    raise SystemExit("Script terminated due to module missing model")
                else:
                    self.model_name = config_data['model_name']
                    logger.debug(f"Assistant model in config: {self.model_name}")

                if 'assistant_name' not in config_data:
                    logger.error("Missing assistant_name in config.")
                    raise SystemExit("Script terminated due to assistant_name")
                else:
                    self.name = config_data['assistant_name']
                    logger.debug(f"Assistant name in config: {self.name}")

                modules = {}
                for key in config_data['modules'].keys():
                    # logger.debug(f"{key}: {config_data['modules'][key]['instructions']}")
                    instructions = config_data['modules'][key]['instructions']

                    instructions = instructions.replace("{self.name}", self.name)

                    if 'examples' in config_data['modules'][key]:
                        examples = config_data['modules'][key]['examples']
                        examples_str = ""
                        for example in examples:
                            user_message = example['user_message']
                            response = example['response']
                            
                            user_message = user_message.replace("{self.name}", self.name)
                            response = response.replace("{self.name}", self.name)

                            examples_str += f"\n USER: {user_message} \nASSISTANT: {response} \n"
                        modules[key] = f"{instructions} \n \nEXAMPLES: {examples_str}"""
                    else:
                        modules[key] = instructions

                    modules[key] = instructions


                # logger.debug(f"Modules loaded: {modules}")
                return modules
        except Exception as e:
            logger.error(f"Error building prompts from config: {e}")

    def load_tools(self):
        try:
            tools = {}

            tools_dir = os.path.join(os.path.dirname(__file__), "tools")
            for folder_name in os.listdir(tools_dir):

                tool_folder = os.path.join(tools_dir, folder_name)
                
                if os.path.isdir(tool_folder):
                    logger.info(f"Loading tool: {folder_name}")
                    main_path = os.path.join(tool_folder, 'main.py')

                    # Check if main.py exists in the folder
                    if os.path.exists(main_path):
                        spec = importlib.util.spec_from_file_location(folder_name, main_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        call_format = getattr(module, 'call_format', None)
                        function = getattr(module, folder_name, None)
                        
                        if not call_format:
                            raise KeyError("Missing function call format in tools")
                        else:
                            call_format = json.loads(call_format)
                        
                        if not function:
                            raise KeyError("Missing function name in tools")
                        
                    
                        if call_format and folder_name:
                            tools[folder_name] = {
                                'call_format': call_format,
                                'function': function
                            }
                        all_call_formats = []
                        for tool in tools.values():
                            all_call_formats.append(tool['call_format']) 

                        tools['all_call_formats'] = all_call_formats

                        return tools                    
            
                    else:
                        raise FileNotFoundError(f"No 'main.py' file found in the '{folder_name}' folder.")

            # logger.debug(f"Tools: {tools}")
            return tools
        except Exception as e: 
            logger.error(f"Error loading assistant tools: {e}")

    # ---------------------------------------------------------------------------- #
    #                            Interact with Assistant                           #
    # ---------------------------------------------------------------------------- #
            
    async def interact(self, interaction):
        logger.info(f"New interaction: {interaction}")
        try:
            username = interaction['user']['first_name'].lower().capitalize()
            message = interaction['data']['text'].lower()

            # formatted_datetime = datetime.now().strftime("%A %b %d, %Y %I:%M:%S %p")
            # verbose_prompt = f"""{self.modules['assistant']} \n Current User: {username} \n Current Message DateTime: {formatted_datetime} \n Current Message: {message}"""
            prompt = f"""{self.modules['assistant']} \n Current Message: {message}"""
            logger.debug(f"Tool calls: {self.tools['all_call_formats']}")

            response = self.send_message(username, prompt)      

            tool_call_count = len(response.tool_calls) if response.tool_calls is not None else 0
            logger.debug(f"Tool call count: {tool_call_count}")
            tool_responses = []
            if response.text == "" and tool_call_count == 0:
                pass
            elif response.text == "" and tool_call_count > 0:
                for tool_call in response.tool_calls:
                    name = tool_call.name
                    parameters = tool_call.parameters

                    tool_response = await self.tools[name]['function'](interaction['user'], **parameters)
                    logger.debug(f"Tool response: {tool_response}")

                    tool_responses.append({
                        "call": tool_call,
                        "outputs": [
                            tool_response
                        ]
                    })
                    logger.debug(f"Tool Response: {tool_responses}")

            response = self.send_message(username, prompt, tool_responses)

            
            return self.format_response(response.text, "text")

        except Exception as e:
            error_message = f"Error interacting with assistant: {e}"
            logger.error(error_message)
            return self.format_response(error_message, "error")

    # ---------------------------------------------------------------------------- #
    #                   Send and Recieve Message from Cohere API                   #
    # ---------------------------------------------------------------------------- #
    def send_message(self, username, message, tool_responses = None):
        logger.debug(f"Sending Message: {message}")
        logger.debug(f"Sending Tool Responses: {tool_responses}")

        send_message_params = {
            'message': message,
            'tools': self.tools['all_call_formats'],
            "temperature": 0.9,
            "k": 10,
            "model": self.model_name,
            "seed": 156354544151,
            "conversation_id": self.conversation_id
            # "chat_history": self.message_history
        }

        if tool_responses is not None:
            send_message_params['tool_results'] = tool_responses

        response = self.co.chat(
            **send_message_params
        )
        
        # self.message_history.extend(
        #         [
        #             {'role':'USER', 'message':message},
        #             {'role':'CHATBOT', 'message':response.text},
        #         ]
        #     )
            
        
        logger.debug(f"Response: {response}")        
        return response

    # ---------------------------------------------------------------------------- #
    #                   Format Response to Send Back to Frontend                   #
    # ---------------------------------------------------------------------------- #
    def format_response(self, response, type):
        return {
            "type": type,
            type: response
        }
