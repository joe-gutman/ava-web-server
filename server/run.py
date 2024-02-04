import signal
import sys
import os
import motor.motor_asyncio as motor
from quart import Quart
from dotenv import load_dotenv
from utils.logger import get_logger
from modules.users import bp as users_bp
from db_connection import get_db_client

app = Quart(__name__)
load_dotenv()

# Set up logging
logger = get_logger(__name__)

@app.before_serving
async def startup():
    logger.info("Starting up server...")
    app.db = await get_db_client()
    app.register_blueprint(users_bp)

@app.after_serving
async def shutdown():
    logger.info("Shutting down server...")

def signal_handler(sig, frame):
    logger.info("Crtl+C pressed...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    app.run()