"""
This module contains a decorator that automatically parses the request body as JSON and sends it to the decorated function as an argument.

"""
from functools import wraps
from quart import request, Quart

app = Quart(__name__)

def route_with_req(path, methods=None):
    def decorator(f):
        @app.route(path, methods=methods)
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            json_data = await request.get_json()
            return await f(json_data, *args, **kwargs)
        return decorated_function
    return decorator