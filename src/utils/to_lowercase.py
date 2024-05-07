def to_lowercase(data):
    if isinstance(data, str):
        return data.lower()
    elif isinstance(data, dict):
        lowercase_dict = {}
        for key, value in data.items():
            lowercase_dict[key] = to_lowercase(value)
        return lowercase_dict
    elif isinstance(data, list):
        lowercase_list = []
        for item in data:
            lowercase_list.append(to_lowercase(item))
        return lowercase_list
    else:
        return data
    