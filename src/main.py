import cohere
import os
import sys
import json
import signal
from quart import Quart
from dotenv import load_dotenv
from utils.logger import logger
from assistant.handler import Assistant
from modules.users.routes import bp as users_bp
from modules.messages.routes import bp as messages_bp
from modules.devices.routes import bp as devices_bp
from modules.tools.routes import bp as tools_bp
from db_connection import connect_to_db

app = Quart(__name__)
app.config['DEBUG'] = True
host_ip = os.environ.get('QUART_APP_HOST', '0.0.0.0')

load_dotenv()

@app.before_serving
async def startup():
    logger.info("Starting up server...")
    app.register_blueprint(users_bp)
    app.register_blueprint(messages_bp)
    # app.register_blueprint(devices_bp)
    # app.register_blueprint(tools_bp)


    try:
        app.db = await connect_to_db()
        logger.info("Connected to database: " + app.db.name)
    except Exception as e:
        logger.error(f'Error connecting to database: {e}')
        sys.exit(1)

    try:
        app.assistant = Assistant()
    except Exception as e:
        logger.error(f'Error initializing assistant: {e}')
        sys.exit(1)

@app.after_serving
async def shutdown():
    logger.info("Shutting down server...")

def signal_handler(sig, frame):
    logger.debug("Crtl+C pressed...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    app.run(host=host_ip)