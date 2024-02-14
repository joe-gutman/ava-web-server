from quart import Blueprint, jsonify
from modules.devices.handler import DeviceHandler as devices
from utils.json_request_decorator import route_with_req as _

bp = Blueprint('devices', __name__)

# add device
@_(bp, '/user/<user_id>/devices/<device_id>', methods=['POST'])
async def add_device(request, user_id, device_id):
    return await devices.add_device(request, user_id, device_id)