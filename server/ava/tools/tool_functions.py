import sys

# The function that is called when the user tells the chatbot they want to quit, or something similar.
def quit():
    print("Chatbot: Goodbye!")
    sys.exit()

# We can add custom tools to the chatbot to make it more useful. These tools can be included in the chatbot parameters. The chatbot can then use these tools to perform certain actions.

# This tool sets up the chatbot to quit when the user tells it to. More specific OpenAI API references can be found at https://platform.openai.com/docs/assistants/tools
tools = [{
    "type": "function",
    "function": {
        "name": "quit",
        "description": "End the chat",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}]

# The tools require a dictionary of functions for the assistant to call when the tool is used. 
functions = {
    'quit': quit,
}
