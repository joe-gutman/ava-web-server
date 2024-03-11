import uuid
import torch
import time
import json
from utils.logger import logger
from transformers import AutoTokenizer, TextGenerationPipeline
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig

class Assistant():
    def __init__(self, assistant_params):
        self.id = uuid.uuid4()
        self.name = assistant_params["name"] or "assistant"
        self.instructions = assistant_params["instructions"]
        self.model_name = assistant_params["model"]
        self.conversations = {}
        self.active_conversation = None
        self.native_tools = {}
        self.active_task = None
        self.max_response_tokens = 500
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

        if self.model_name is None:
            logger.error("MISSING MODEL NAME: Text generation model must be provided")
            raise SystemExit("Script terminated due to missing model name.")
        if not self.name:
            logger.warning("ASSISTANT NAME MISSING: Defaulting to 'assistant'")
        if not self.instructions:
            logger.error(f"MISSING ASSISTANT INSTRUCTIONS: Instructions must be provided.")
            raise SystemExit("Script terminated due to missing assistant instructions.")
        logger.info(f"Creating assistant '{self.name}' with LLM model: '{self.model_name}' and instructions: '{self.instructions[:25]}...'")

        self.load_model(self.model_name)



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
        new_conversation = Conversation(name, self.instructions, self.model, self.tokenizer, self.text_generation_params, age_limit)
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
            triggered = self.check_if_triggered(interaction)
            logger.debug(f"Triggered: {triggered}")
            if triggered:
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
        
    def check_if_triggered(self, interaction):

        user = interaction['user']['first_name']
        message = interaction['data']['text']
        
        #percent that trigger rating has to be to count as a trigger for the assistant
        trigger_rating_min = 70 

        try:
            prompt = f"""
            <<SYS>>
            You are an AI assistant for another AI assistant named {self.name}. Your task is to analyze user messages and determine if they are requesting assistance. Rate the likelihood on a scale of 0 to 100, where 0 means no request and 100 means a definite request. A message directly addressed to the assistant with a clear request should generally receive a higher rating, even if the task is not typical. Respond with a trigger rating and a rationale.

            Examples:
            Message: "Ava, what's the weather?"
            Assistant: {{"trigger_rating": "95", "rationale": "The user directly addresses the assistant and asks a question, indicating they are talking to the AI."}}

            Message: "Can you take a look at this, I'm not sure what John wants."
            Assistant: {{"trigger_rating": "40", "rationale": "The message suggests a request for help but is unclear if it's directed at the AI or a person."}}

            Message: "Just finished reading a great book on gardening!"
            Assistant: {{"trigger_rating": "0", "rationale": "This is a statement with no indication of talking to the AI."}}

            Message: "Can you help me find a good recipe for lasagna?"
            Assistant: {{"trigger_rating": "85", "rationale": "The user is asking for help, which suggests they are talking to the AI."}}

            Message: "I'm thinking of making pasta for dinner."
            Assistant: {{"trigger_rating": "10", "rationale": "A personal statement with no clear indication of talking to the AI."}}

            Message: "Ava, remind me to call Mom tomorrow."
            Assistant: {{"trigger_rating": "95", "rationale": "The user directly addresses the assistant with a request, indicating they are talking to the AI."}}

            Message: "I wonder what the capital of France is."
            Assistant: {{"trigger_rating": "50", "rationale": "A question that an AI can answer, but it's phrased as a personal musing rather than directly talking to the AI."}}

            Message: "I'm not sure what to do about this issue at work."
            Assistant: {{"trigger_rating": "30", "rationale": "Expresses uncertainty but it's unclear if the user is talking to the AI."}}

            Message: "Please turn off the lights."
            Assistant: {{"trigger_rating": "85", "rationale": "A command that could be directed at a smart home assistant, suggesting the user is talking to the AI."}}

            Message: "Ava, how do I fix a leaky faucet?"
            Assistant: {{"trigger_rating": "90", "rationale": "The user directly addresses the AI and asks for assistance, indicating they are talking to the AI."}}

            Message: "What do you think about the latest AI advancements?"
            Assistant: {{"trigger_rating": "90", "rationale": "The user poses a question likely aimed at engaging in conversation with the AI, indicating direct communication."}}

            Message: "Do you get tired of answering questions?"
            Assistant: {{"trigger_rating": "90", "rationale": "A direct question to the AI about its experiences, indicating the user is talking to the AI."}}

            Message: "How's your day going, Ava?"
            Assistant: {{"trigger_rating": "98", "rationale": "The user directly addresses the AI in a conversational manner, clearly indicating they are talking to the AI."}}


            <</SYS>>


            Message: "{message}"
            Assistant:"""
            logger.debug(f"Generating response for: {message}")

            pipeline = TextGenerationPipeline(self.model, self.tokenizer)
            outputs = pipeline(prompt, **self.text_generation_params)

            # Split the generated text at the stop tokens and take the first part
            generated_text = outputs[0]['generated_text']
            logger.debug(f"Generated text: {generated_text}")
            response_index = generated_text.rindex("Assistant:")
            generated_text = json.loads(generated_text[response_index + len("Assistant:"):])
            logger.debug(f'Message: {message} \n Response: {generated_text}')

            if int(generated_text["trigger_rating"]) >= trigger_rating_min:
                return True
            return False
        except Exception as e:
            logger.error(e)
        
        
class Conversation:
    def __init__(self, name, prompt, model, tokenizer, text_generation_params, age_limit=None):
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
        self.text_generation_params = text_generation_params

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







    
    

