from datetime import datetime

def build_request(user, request, metadata = {}):
    current_time = {
        'date': datetime.now().strftime('%Y-%m-%d') + ' (Y/M/D)',
        'time': datetime.now().strftime('%H:%M:%S'),
        'day': datetime.now().strftime('%A')
    }


    user_dict = {
        '_id': str(user['_id']),
        'name': user['first_name'],
        'settings': user['settings'] 
    }

    complete_request = {
        'current_time': current_time,
        'user': user_dict,
        'request': request,
        'metadata': metadata
    }

    return complete_request