# `Assistant` Class

The `Assistant` class represents a chatbot assistant, with features to send and receive messages from users. The assistant can also manage conversations and track interactions between the user and the chatbot.

## Attributes

- `id`: A unique identifier for the assistant. Generated using `uuid.uuid4()`.
- `name`: The name of the assistant.
- `initial_prompt`: The initial prompt that the assistant will use to guide each response to the user.
- `conversations`: A dictionary of `Conversation` objects managed by the assistant, keyed by conversation name.
- `active_conversation`: The `Conversation` object that the assistant is currently interacting with.
- `native_tools`: A dictionary of native tools that the assistant can use, keyed by tool name.
- `active_task`: The task that the assistant is currently performing.

## Methods

- `__init__(self, name, initial_prompt)`: Initializes a new `Assistant` instance.
- `__repr__(self)`: Returns a string representation of the `Assistant` instance.
- `start_conversation(self, name, age_limit=None)`: Starts a new conversation with the given name and age limit, and sets it as the active conversation.
- `get_conversation(self, name)`: Returns the `Conversation` object with the given name.
- `end_conversation(self, name)`: Ends the conversation with the given name and removes it from the `conversations` dictionary.
- `end_expired_conversations(self)`: Ends all conversations that have exceeded their age limit.
- `get_active_conversation(self)`: Returns the `Conversation` object that the assistant is currently interacting with.
- `set_activate_conversation(self, name)`: Sets the conversation with the given name as the active conversation.
- `remove_active_conversation(self)`: Removes the current active conversation.
- `get_native_tools(self)`: Returns the `native_tools` dictionary.
- `add_native_tool(self, tool_name, tool)`: Adds a new tool to the `native_tools` dictionary with the given name and tool object.
- `delete_native_tool(self, tool_name)`: Deletes the tool with the given name from the `native_tools` dictionary.
- `recieve_interaction(self, interaction, conversation_name=None)`: Receives a interaction from a user, adds it to the active conversation, ends any expired conversations, and returns a response.
  - interaction structure should be an object with the following attributes:
    - `user_id`: The user who sent the interaction.
    - `device_id`: The device from which the interaction was sent.
    - content: An object containing the content of the interaction.
      - `type`: The type of content: `text` or `tool_response`.

   
- `get_response(self, interaction)`: Returns a response to the given interaction. This method is not fully implemented in the provided code.



# `Conversation` Class

The `Conversation` class represents a conversation connected to a chatbot, with features to manage and track the conversation.

## Attributes

- `id`: A unique identifier for the conversation, generated using `uuid.uuid4()`.
- `name`: The name of the conversation.
- `interaction_history`: A list of interaction objects in the conversation. Interactions can be of two types: 'message' and 'command'.
- `start_time`: The time when the conversation was created, in seconds since the Epoch.
- `age`: The age of the conversation, in minutes.
- `age_limit`: The maximum age of the conversation, in minutes. If `None`, the conversation has no age limit.
- `last_active`: The time of the last interaction in the conversation, in seconds since the Epoch.

### Interaction Object

Each interaction object in `interaction_history` has the following attributes:

- `user_id`: The user who sent the interaction.
- `device_id`: The device from which the interaction was sent.
- `content`: An object containing the content of the interaction.
  - `type`: The type of interaction: 'message' or 'command'. 

#### Message Interaction

For 'message' interactions, the `content` attribute includes:

- `text`: The text of the message.

```json
{
    "user": { 
        "id": "user1",
        "name": "John Doe"
        // Additional properties may be included here...
    },
    "device": {
        "id": "device1",
        "name": "iPhone"
        // Additional properties may be included here...
    },
    "content": {
        "type": "text",
        "text": "Hello, how are you?"
        }
}
```

#### Command Interaction

For 'command' interactions, the `content` attribute includes:

- `name`: The name of the command.
- `kwargs`: The keyword arguments of the command.

```json
{
    "user": { 
        "id": "user1",
        "name": "John Doe"
        // Additional properties may be included here...
    },
    "device": {
        "id": "device1",
        "name": "iPhone"
        // Additional properties may be included here...
    },
    "content": {
        "type": "command",
        "name": "weather",
        "kwargs": {
            "location": "New York",
            "date": "2021-10-01",
            "time": "12:00",
            "units": "imperial"
        }
    }
}
```

## Methods

- `__init__(self, name, age_limit=None)`: Initializes a new `Conversation` instance. 
- `__repr__(self)`: Returns a string representation of the `Conversation` instance.
- `get_interactions(self)`: Returns a string of all interactions in the conversation, separated by newlines.
- `get_age(self)`: Returns the age of the conversation, in minutes.
- `add_interaction(self, interaction)`: Adds an interaction to the conversation and updates `last_active`.
- `is_expired(self)`: Returns `True` if the conversation has exceeded its age limit, `False` otherwise.