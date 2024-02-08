import logging
from quart import Blueprint, jsonify
from modules.users import handler as users
from utils.json_request_decorator import route_with_req as _

bp = Blueprint('users', __name__)
users = users.UserHandler()

@_(bp, '/user/login', methods=['POST'])
async def login_user(data):
    logging.info("received login request")
    result, status_code = await users.login_user(data)
    return jsonify(result), status_code

@_(bp, '/user/register', methods=['POST'])
async def register_user(data):
    logging.info("received register request")
    result, status_code = await users.register_user(data)
    return jsonify(result), status_code