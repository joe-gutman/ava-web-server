import uuid
import torch
import time
from utils.logger import logger
from transformers import AutoTokenizer, TextGenerationPipeline
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig

class Assistant():
    def __init__(self, name, model_name, instructions=""):
        if model_name is None:
            raise Exception("MISSING MODEL NAME: Text generation model must be provided")
        if not name:
            logger.warning("Assistant name not provided. Defaulting to 'assistant'")
        if not instructions:
            logger.warning("Initial prompt not provided. Defaulting to no instructions.")

        self.id = uuid.uuid4()
        self.name = name or "assistant"
        self.instructions = instructions
        self.conversations = {}
        self.active_conversation = None
        self.native_tools = {}
        self.active_task = None

        self.max_response_tokens = 500

        logger.info(f"Create assistant '{self.name}' with LLM model: '{model_name}' and instructions: '{self.instructions[:25]}...'")
        self.load_model(model_name)

    def __repr__(self):
        return f'<Assistant {self.name}:{self.id}>'
    
    def load_model(self, model_name):
        try:
            torch.cuda.empty_cache()
            loading_start = time.time()
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            logger.debug(f"Loading model: {model_name[:10]}... on device: {device}")
            model_dir = "src/assistant/models/" + model_name

            self.model = AutoGPTQForCausalLM.from_quantized(model_dir)
            self.tokenizer = AutoTokenizer.from_pretrained(model_dir)

            self.model = self.model.to(device)

            loading_time = round(time.time() - loading_start)
            logger.info(f"Model loaded ({loading_time} sec): {model_name[:10]}...")
        except Exception as e:
            logger.error(e)
            return None, None

    def start_conversation(self, name="default", age_limit=None):
        new_conversation = Conversation(name, self.instructions, self.model, self.tokenizer, age_limit)
        self.conversations[name] = new_conversation
        self.active_conversation = new_conversation
        return self.conversations[name]
    
    def get_conversation(self, name):
        return self.conversations.get(name)
    
    def end_conversation(self, name):
        if self.active_conversation == self.get_conversation(name):
            self.remove_active_conversation()
        del self.conversations[name]

    def end_expired_conversations(self):
        for conversation in self.conversations.values():
            if conversation.is_expired():
                self.end_conversation(conversation.name)
                logger.info(f'Conversation {conversation.name} expired')

    def get_active_conversation(self):
        return self.active_conversation
    
    def set_activate_conversation(self, name):
        self.active_conversation = self.get_conversation(name)

    def remove_active_conversation(self):
        self.active_conversation = None

    def get_native_tools(self):
        return self.native_tools

    def add_native_tool(self, tool_name, tool):
        self.native_tools[tool_name] = tool

    def delete_native_tool(self, tool_name):
        del self.native_tools[tool_name]

    def interact(self, interaction, conversation_name=None):
        logger.info(f"New interaction: {interaction}")
        if self.active_conversation is None and conversation_name is not None:
            self.set_activate_conversation(conversation_name)
            logger.debug(f"Starting new conversation: {conversation_name}")
        elif self.active_conversation is None and conversation_name is None:
            self.start_conversation('default')
            logger.debug(f"No conversation, starting new 'default' conversation")

        try:
            response = self.active_conversation.handle_interaction(interaction)
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
        except Exception as e:
            error_message = "Assistant had a problem generating response"
            logger.error(f"{error_message}: {e}")
            return {
                "type": "error",
                "error": f"{error_message}"
            }
        
        
class Conversation:
    def __init__(self, name, prompt, model, tokenizer, age_limit=None):
        self.id = uuid.uuid4()
        self.name = name
        self.conversation_prompt = prompt
        self.model = model
        self.tokenizer = tokenizer
        self.interaction_history = []
        self.start_time = time.time()
        self.age = 0
        self.age_limit = None #minutes
        self.last_active = time.time()
        # Text Generation Settings
        self.text_generation_params = {
            "max_new_tokens": 500,
            # "temperature": 0.5,
            # "top_k": 40,
            # "top_p": 0.7,
            "repetition_penalty": 1.2,
            # "no_repeat_ngram_size": 1,
            # "length_penalty": 0.75,
            # "diversity_penalty": 0.6,
            # "num_beams": 1,
            # "num_beam_groups": 1,
        }

    def __repr__(self):
        return f'<Conversation {self.name}:{self.id} >'

    def get_interactions(self):
        interactions = '''{}'''.format('\n'.join(self.interaction_history))
        return interactions
    
    def get_age(self):
        self.age = (time.time() - self.start_time) / 60  # Convert age to minutes
        return self.age
    
    def handle_interaction(self, interaction):
        if interaction['data']['type'] == 'text':
            message = interaction['data']['text']
            user = interaction['user']['first_name']
            response = self._generate_response(message, user)
            self.add_interaction(f"User: {message}")
            self.add_interaction(f"Assistant: {response}")
            if response is not None:
                return response


    def is_expired(self):
        if self.age_limit is None or self.get_age() <= self.age_limit:
            return False
        else:
            return True
        
    def add_interaction(self, interaction):
        self.interaction_history.append(interaction)
        self.last_active = time.time()

    def _generate_response(self, message, user):
        try:
            prompt = f"""
            <<SYS>>
            {self.conversation_prompt}
            <</SYS>>
            {self.get_interactions()}
            {user}: {message}
            Assistant:"""

            logger.debug(f'Generating text with prompt: {prompt}')
            
            generate_start = time.time()
            logger.debug(f"Generating response for: {message}")

            pipeline = TextGenerationPipeline(self.model, self.tokenizer)
            outputs = pipeline(prompt, **self.text_generation_params)

            # Split the generated text at the stop tokens and take the first part
            generated_text = outputs[0]['generated_text']
            logger.debug(f"Generated text: {generated_text}")
            response_index = generated_text.rindex("Assistant:")
            generated_text = generated_text[response_index + len("Assistant:"):]

            logger.debug(f"Generated in: {round(time.time() - generate_start)} seconds")

            return generated_text
        except Exception as e:
            logger.error(e) 







    
    

