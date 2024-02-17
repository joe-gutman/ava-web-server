import uuid
import json

config = { 
    "device":{
        "name": "Main PC",
        "type": "computer",
        "specifications": {
            "type":"desktop",
            "os": "Windows",
            "version": "11",
            "architecture": "64-bit",
        },
        "location": {
            "city": "Battle Ground",
            "state": "Washington",
            "country": "United States",
            "building": "home",
            "room": "bedroom",
        }
    }
}


# generate a new config file
def generate_config():
    try:
        device_id = str(uuid.uuid4())
        config['device']['_id'] = device_id
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        return config
    except Exception as e:
        print(f'Error in generate_config: {e}')
        return None
    
# Load config
def load_config():
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        return generate_config()