import logging
from quart import Blueprint, request, jsonify
from modules.users import handler as users

bp = Blueprint('users', __name__)
users = users.UserHandler()

@bp.route('/user/login', methods=['POST'])
async def login_user():
    logging.info("received login request")
    data = await request.get_json()
    result, status_code = await users.login_user(data)
    return jsonify(result), status_code

@bp.route('/user/register', methods=['POST'])
async def register_user():
    logging.info("received register request")
    data = await request.get_json()
    result, status_code = await users.register_user(data)
    return jsonify(result), status_code