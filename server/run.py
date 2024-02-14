import sys
import json
import signal
import motor.motor_asyncio as motor
from quart import Quart
from dotenv import load_dotenv
from utils.logger import logger
from modules.assistant.handler import Assistant
from modules.users import bp as users_bp
from modules.messages import bp as messages_bp
from modules.devices import bp as devices_bp
from db_connection import get_db_client

app = Quart(__name__)
load_dotenv()


@app.before_serving
async def startup():
    logger.info("Starting up server...")
    try:
        app.db = await get_db_client()
    except Exception as e:
        logger.error(f'Error connecting to database: {e}')
        sys.exit(1)
    app.register_blueprint(users_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(devices_bp)
    try:
        params = json.load(open('config/ava_params.json'))
        app.assistant = await Assistant.initialize(params)
    except Exception as e:
        logger.error(f'Error initializing assistant: {e}')
        sys.exit(1)

@app.after_serving
async def shutdown():
    logger.info("Shutting down server...")

def signal_handler(sig, frame):
    logger.info("Crtl+C pressed...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    app.run()