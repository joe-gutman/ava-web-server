from aiohttp import ClientSession
import asyncio
import signal
import os
import pygame
import traceback
from dotenv import load_dotenv
from utils.logger import logger
from modules.communication_handler import SpeechHandler_TTS as SpeechHandler
from modules.communication_handler import ListenHandler



# This flag will be used to stop the script
stop_flag = False

load_dotenv()

def play_startup_sound():
    pygame.mixer.init()
    pygame.mixer.music.load("startup.mp3")
    pygame.mixer.music.play()

def signal_handler(signal, frame):
    global stop_flag
    stop_flag = True
    logger.info("Stopping...")
    exit(0)

async def main():
    global stop_flag
    client_server_route = "http://10.0.0.229:5001/"
    speech = SpeechHandler()
    listen = ListenHandler()

    # login on the server
    try:
        username = os.getenv("SERVER_USERNAME")
        password = os.getenv("SERVER_PASSWORD")
        current_user = None

        try: 
            # Login
            async with ClientSession() as client:
                response = await client.post(f"{client_server_route}/user/login", json={"username": username, "password": password})
                response_data = await response.json()
                current_user = response_data["user"]
                logger.info(f"Logged in as: {current_user['username']}")
        except Exception as e:
            logger.error(f"Error in login: {e}")
            stop_flag = True

        if current_user:
            # Start listening
            logger.info("Starting to listen...")
            try:
                # play_startup_sound()
                while not stop_flag:
                    speech_text = listen.realtime_stt()

                    if speech_text:
                        logger.info(f"Sending message: {speech_text}")
                        async with ClientSession() as client:
                            formated_request = {
                                "status": "request",
                                "user": current_user,
                                "data": {
                                    "type": "text",
                                    "text": speech_text
                                }
                            }
                            logger.info(f"Sending request: {formated_request}")
                            response = await client.post(f"{client_server_route}/send_message/{current_user['_id']}", json=formated_request)
                            if response is not None:
                                response_data = await response.json()
                                if response_data['data']['type'] == "text":
                                    response_text = response_data['data']['text']
                                    logger.debug(f"Response text: {response_text}")
                                    
                                    if response_text is not None and response_text.lower() != "none":
                                        await speech.run(response_data["data"]["text"])

            except Exception as e:
                logger.error(f"Error getting speech: {e}")
                stop_flag = True
        else:
            stop_flag = True
    except Exception as e:
        logger.error(f"Error in main: {e}")
        stop_flag = True

# Set the signal handler
signal.signal(signal.SIGINT, signal_handler)



signal.signal(signal.SIGTERM, signal_handler)
        
# Run the main function
asyncio.run(main())