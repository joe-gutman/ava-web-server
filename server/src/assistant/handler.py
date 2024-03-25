import uuid
import os
import torch
import time
import json
import importlib
from datetime import datetime
from utils.logger import logger
from transformers import AutoModelForCausalLM, AutoTokenizer, TextGenerationPipeline
from auto_gptq import AutoGPTQForCausalLM

class Assistant():
    def __init__(self):
        self.id = uuid.uuid4()
        self.modules = self.load_config()
        self.tools = self.load_tools()
        self.latest_task = None
        self.message_history = []
        self.text_generation_params = {
            'temperature': 0.7, 
            'do_sample': True, 
            'top_p': 0.95, 
            'top_k': 40
        }

        self.load_model(self.model_name)

    def __repr__(self):
        return f'<Assistant {self.name}:{self.id}>'
    
    def load_model(self, model_name, device=None):
        try:
            torch.cuda.empty_cache()
            loading_start = time.time()
            if device is None:
                device = "cuda:0" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading model: {model_name[:10]}... on device: {device}")
            model_dir = "src/assistant/models/" + model_name

            self.model = AutoModelForCausalLM.from_pretrained(model_dir,
                                             device_map=device,
                                             trust_remote_code=False,
                                             revision="main")
            self.tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=True)
            
            loading_time = round(time.time() - loading_start)
            logger.info(f"Model loaded ({loading_time} sec): {model_name[:10]}...")
        except Exception as e:
            logger.error(f"Error loading model: {e}")  # Print out the detailed error
            return None, None

    def load_config(self):
        try:
            with open('config.json') as json_file:
                config_data = json.load(json_file)
            
                logger.info("Loading assistant config...")
                logger.debug(config_data)
                
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
                    logger.debug(f"{key}: {config_data['modules'][key]['instructions']}")
                    instructions = config_data['modules'][key]['instructions']

                    instructions = instructions.replace("{self.name}", self.name)

                    
                    if 'examples' in config_data['modules'][key]:
                        examples = config_data['modules'][key]['examples']
                        examples_str = ""
                        for example in examples:
                            user_message = example['user_message']
                            response = example['response']

                            examples_str += f"\n USER: {user_message} \nASSISTANT: {response} \n"
                        modules[key] = f"{instructions} \n \nEXAMPLES: {examples_str}"""
                    else:
                        modules[key] = instructions


                logger.debug(f"Modules loaded: {modules}")
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
                        # Prepare the module spec
                        spec = importlib.util.spec_from_file_location(folder_name, main_path)

                        # Create the module
                        module = importlib.util.module_from_spec(spec)

                        # Execute the module
                        spec.loader.exec_module(module)

                        # Extract the necessary items
                        examples = module.examples if hasattr(module, 'examples') else None
                        call_format = module.call_format if hasattr(module, 'call_format') else None

                        function_name = folder_name
                        if call_format and examples and function_name:
                            tools[function_name] = {
                                'call_format': call_format,
                                'examples': examples,
                                'function': function_name
                            }

                        combined_examples = ""
                        logger.debug(f"Tool examples: {tools[function_name]['examples']}")
                        for example in tools[function_name]['examples']:
                            logger.debug(f"Single example: {example}")
                            combined_examples += f"\n{example['user_message']}\n{example['response']}\n"
                        tools[function_name]['examples'] = combined_examples

                    else:
                        raise FileNotFoundError(f"No 'main.py' file found in the '{folder_name}' folder.")

            logger.debug(f"Tools: {tools}")
            return tools
        except Exception as e: 
            logger.error(f"Error loading assistant tools: {e}")

    def interact(self, interaction, conversation_name=None):
        logger.info(f"New interaction: {interaction}")
        try:
            user = interaction['user']['first_name'].lower().capitalize()
            message = interaction['data']['text'].lower()

            # triggered = self.check_if_triggered(user, message)
            triggered = True
            message_type = self.get_message_type(user, message)

            if message_type.strip() == "" or "conversation" in message_type or "get_time" in message_type :
                pass

            logger.debug(f"Triggered: {triggered}")
            if triggered:
                response = self._generate_text(user, message, self.modules['assistant'])
                logger.info(f"Assistant response: {response}")

                if response is None:
                    error_message = "Assistant was not able to generate response"
                    logger.error(error_message)
                    return {
                        "type": "error",
                        "error": error_message
                    }
                
                else:
                    return {
                        "type": "text",
                        "text": response
                    }
            elif not triggered:
                return {
                    "type": "text",
                    "text": None
                }
        except Exception as e:
            error_message = "Assistant had a problem generating response"
            logger.error(f"{error_message}: {e}")
            return {
                "type": "error",
                "error": f"{error_message}"
            }
        
    def check_if_triggered(self, user, message):
        try:
            logger.debug(f"Generating response for: {message}")

            trigger_prompt = self.prompts['trigger']

            triggered = self._generate_text(message, trigger_prompt, user, 25)
            logger.debug(f"Triggered type: {type(triggered)}")

            if isinstance(triggered, bool):
                return triggered
            else:
                if "true" in triggered.lower() or "false" in triggered.lower():
                    logger.debug(f"Triggered.lower(): {triggered.lower()}")
                    return "true" in triggered.lower()
                else:
                    logger.debug(f"Unexpected response: {triggered}")
                    return None
        except Exception as e:
            logger.error(e)

    def get_message_type(self, user, message):
        logger.info("Getting message type.")

        type_names = list(self.tools.keys())
        for each in ['conversation', 'get_time']:
            type_names.append(each)

        logger.debug(f"Modules: {self.modules}")
        if 'message_types' not in self.modules:
            raise KeyError(f"Missing type config for checking message type.")
        else:    
            type_prompt = self.modules['message_types']
            logger.debug(f"Message type prompt: {type_prompt}")

            logger.debug(f"Type names: {type_names}")
            for i, type in enumerate(type_names):
                type_prompt += f"{i + 1}. {type}\n"
                logger.debug(f"Type: {type}")

            logger.debug(f"Type prompt: {type_prompt}")

            message_type = self._generate_text(user, message, type_prompt, max_tokens=5)

            logger.info(f"Message type: {message_type}")
            return message_type

    def _generate_text(self, username, message, instructions, response_marker="ASSISTANT", max_tokens=500):
        try:
            logger.debug(f"Generating response for: {message}")
            logger.debug(f"Instructions received: {instructions}")

            response_marker = f"{response_marker}:"            
            # formatted_datetime = datetime.now().strftime("%A %b %d, %Y")
            # prompt = f"{instructions} \n----\nUSERNAME: {username} USER:{message} \n{response_marker}"""
            prompt = f"USER: {message} \nASSISTANT:"
            
            logger.debug(f"Prompt: {prompt}")

            # input_ids = self.tokenizer(prompt, return_tensors='pt').input_ids.cuda()
            # output = self.model.generate(inputs=input_ids, max_new_tokens=max_tokens, **self.text_generation_params)
            # generated_text = self.tokenizer.decode(output[0])

            pipeline = TextGenerationPipeline(model=self.model, tokenizer=self.tokenizer)
            outputs = pipeline(prompt, max_new_tokens=max_tokens, **self.text_generation_params)
            generated_text = outputs[0]['generated_text']

            response_index = generated_text.rindex(response_marker)
            generated_text = generated_text[response_index + len(response_marker):].strip()
            logger.debug(f'USER: {message} \n ASSISTANT: {generated_text}')

            self.message_history.append({
                'user_message': message,
                response_marker.lower(): generated_text
            })

            formatted_response = generated_text.replace("\\n", "\n")
            return generated_text
        except Exception as e:
            logger.error(f"Error generating text: {e}")