"""
This module contains a decorator, `route_with_req`, which is designed for use with Flask or Quart routes. 
The decorator automatically parses the request body as JSON and passes it as the first argument to the decorated route handler function. 
It also allows for the specification of the route path and HTTP methods directly in the decorator, providing a streamlined way to define routes.

Example usage:

my_bp = Blueprint('my_bp', __name__)

@route_with_req(my_bp, '/my_route', methods=['POST'])
async def my_route_handler(json_data):
    # Handle the route
    pass
"""
from functools import wraps
from quart import request

def route_with_req(bp, path, methods=None):
    def decorator(f):
        @bp.route(path, methods=methods)
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            json_data = await request.get_json()
            return await f(json_data, *args, **kwargs)
        return decorated_function
    return decorator