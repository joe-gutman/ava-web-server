from aiohttp import ClientSession
import asyncio
import signal
import os
import pygame
from transformers import AutoTokenizer
from dotenv import load_dotenv
from utils.logger import logger
from modules.communication_handler import ListenHandler_Google
from modules.communication_handler import ListenHandler_Whisper
from modules.communication_handler import ListenHandler_Deepgram
from modules.communication_handler import SpeechHandler_XTTS
from modules.communication_handler import SpeechHandler_Polly
from modules.communication_handler import SpeechHandler_ElevenLabs



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
    # listen = ListenHandler_Deepgram()
    listen = ListenHandler_Deepgram()
    speech_elevenlabs = SpeechHandler_ElevenLabs()
    speech_polly = SpeechHandler_Polly()
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-cased")

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

        while current_user:
            # Start listening
            logger.info("Starting to listen...")
            try:
                speech_text = await listen.start()            
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
                                logger.info(f"Response text: {response_text}")
                                if response_text is not None and response_text.lower() != "none":
                                    text_token_count = len(tokenizer.tokenize(response_text))

                                    logger.debug(f"Text token count: {text_token_count}")
                                    if text_token_count > 35:
                                        await speech_polly.run(response_text)
                                    else:
                                        await speech_elevenlabs.run(response_text)
            except KeyboardInterrupt:
                pass
            except Exception as e:
                logger.error(f"Error getting speech: {e}")
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