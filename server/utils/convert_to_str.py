# converts most all data types to string
# may not work on custom classes
def convert_to_str(data):
    if isinstance(data, dict):
        return {k: convert_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_to_str(item) for item in data]
    else:
        return str(data)