from quart import Blueprint, request, jsonify

bp = Blueprint('messages', __name__)

# send a message, also saves the message in the database message history
@bp.route('/messages/<user_id>', methods=['POST'])
async def send_messages_route(user_id):
    data = await request.get_json()
    result, status_code = await chat.handle_message(data, user_id)
    return jsonify(result), status_code

# get all messages
@bp.route('/messages/<user_id>', methods=['GET'])
async def get_messages_route(user_id):
    result, status_code = await chat.get_messages(user_id)
    return jsonify(result), status_code
