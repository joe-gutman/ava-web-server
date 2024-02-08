import aiohttp
import asyncio
import json
import signal
import os
import time
import speech_recognition as sr
from pprint import pformat
from dotenv import load_dotenv
from utils.text_to_speech import text_to_speech
from utils.logger import logger
from modules.users import User

# This flag will be used to stop the script
stop_flag = False

# Replace 'MICROPHONE_INDEX' with the index of your microphone
MICROPHONE_INDEX = 1

load_dotenv()

key_phrases = ['ava', 'eva']
current_user = None

def signal_handler(signal, frame):
    global stop_flag
    stop_flag = True
    logger.info('Stopping...')

def listen_callback(recognizer, audio):
    global current_user
    start_time = time.time()
    logger.info('Received audio data')
    try:
        text = recognizer.recognize_google(audio).lower()
        recognize_time = time.time()
        logger.debug(f'Time taken for recognition: {recognize_time - start_time}')
        logger.info(f'Recognized: {text}')
        if any(phrase in text for phrase in key_phrases):
            response = asyncio.run(handle_request(text))
            if response:
                logger.debug(f'Response received')
                status = response['status']
                type = response['data']['type']
                if status == 'success' and type == 'text':
                    response_text = response['data']['response']
                    logger.info(f'Response: {response_text}')
                    try:
                        text_to_speech(response_text)
                    except Exception as e:
                        logger.error(f'Error in text_to_speech: {e}')
                else:
                    logger.error(f'Error in response: {response["message"]}')
    except Exception as e:
        logger.error(f'Speech not recognized: {str(e)}')

async def handle_request(text):
    global current_user
    data = {
        'user': {
            '_id': current_user.id,
            'name': current_user.first_name
        },
        'request': {
            'type': 'text',
            'content': text
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f'http://localhost:5000/messages/{current_user.id}', json=data) as response:
            logger.info('Sending request...')
            response = json.loads(await response.text())
            logger.debug(f"Response: {pformat(response)}")
            return response

async def start_listening():
    r = sr.Recognizer()
    source = sr.Microphone(chunk_size=10240)

    logger.info('Listening...')
    r.listen_in_background(source, listen_callback)
    while not stop_flag:  # Stop the loop when a termination signal is received
        await asyncio.sleep(1)  # Add a delay to prevent high CPU usage

async def main():
    global stop_flag
    # Rest of your main function...
    await start_listening()

async def main():
    global stop_flag    
    global current_user

    # login on the server
    try:
        username = os.getenv('SERVER_USERNAME')
        password = os.getenv('SERVER_PASSWORD')
        logger.debug(f'Logging in with {username} and {password}...')
        current_user = await User.login(username, password)
        if  current_user:
            try:
                await start_listening()
            except Exception as e:
                logger.error(f'Error getting speech: {e}')
                stop_flag = True
        else:
            stop_flag = True
    except Exception as e:
        logger.error(f'NOT AUTHORIZED: Error logging in: {e}')
        current_user = None
        stop_flag = True

# Set the signal handler
signal.signal(signal.SIGINT, signal_handler)

signal.signal(signal.SIGTERM, signal_handler)
        
# Run the main function
asyncio.run(main())