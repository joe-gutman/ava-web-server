import sys

# Handles the decision whether a user message requires attention or not
# If the message does require attention, send the message back to the assistant to be handled
def handle_ava_response(attention_needed, user_message, tool_call_id):
    if attention_needed:
        return {
            'tool_call_id': tool_call_id,
            'output': {
                'user_message': user_message
            }
        }

# We can add custom tools to the chatbot to make it more useful. These tools can be included in the chatbot parameters. The chatbot can then use these tools to perform certain actions.

# This tool sets up the chatbot to quit when the user tells it to. More specific OpenAI API references can be found at https://platform.openai.com/docs/assistants/tools

# The tools require a dictionary of functions for the assistant to call when the tool is used. 
functions = {
    'handle_ava_response': handle_ava_response,
}
