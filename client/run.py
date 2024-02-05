import aiohttp
import asyncio
import json
import signal
import os
import speech_recognition as sr
from dotenv import load_dotenv
from utils.text_to_speech import text_to_speech
from utils.logger import logger

# This flag will be used to stop the script
stop_flag = False

# Replace 'MICROPHONE_INDEX' with the index of your microphone
MICROPHONE_INDEX = 1

load_dotenv()

key_phrase = 'ava'
suitable_voices = ['Rachel', 'Sarah', 'Matilda', 'Nicole']

def signal_handler(signal, frame):
    global stop_flag
    stop_flag = True
    logger.info('Stopping...')

async def speech_to_text(recognizer, audio):
    try:
        text = recognizer.recognize_google(audio).lower()
        logger.info('Recognized: ' + text)
        print('Recognized: ' + text)
        if key_phrase in text:
            try:
                response = await handle_request(text)
                # text_to_speech(response['response']['content'], suitable_voices[1])
                print(response)
            except Exception as e:
                logger.error('Error handling request... ' + str(e))
    except Exception as e:
        logger.error('Speech not recognized... ' + str(e))

async def handle_request(text):
    data = {
        'user': {
            '_id': 'placeholder',
            'name': 'placeholder'
        },
        'request': {
            'type': 'text',
            'content': text
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:5000/chat', json=data) as response:
            response = json.loads(await response.text())
            return response
        
async def login(username, password):
    data = {
        'username': username,
        'password': password
    }
    logger.info('Logging in...')
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:5000/user/login', json=data) as response:
            response = json.loads(await response.text())
            logger.debug(response)
            return response
        
# Impliment logout
# async def logout():

        
def listen_callback(recognizer, audio):
    # This function will be called in a separate thread once the audio is recorded
    asyncio.run(speech_to_text(recognizer, audio))
        
async def get_speech():
    r = sr.Recognizer()
    source = sr.Microphone()

    with sr.Microphone() as source:
        logger.info('Adjusting for ambient noise...')
        r.adjust_for_ambient_noise(source, duration=1)  # Adjust for ambient noise

    logger.info('Listening...')
    r.listen_in_background(source, listen_callback)
    while not stop_flag:  # Stop the loop when a termination signal is received
        await asyncio.sleep(1)  # Add a delay to prevent high CPU usage

async def main():
    # login on the server
    try:
        username = os.getenv('SERVER_USERNAME')
        password = os.getenv('SERVER_PASSWORD')
        logger.debug(f'Logging in with {username} and {password}...')
        login_result = await login(username, password)
        if login_result['status'] == 'success':
            logger.info(login_result['message'])
        else:
            logger.error('Error logging in...')
            raise Exception(login_result['status'],': ', login_result['message'])
        await get_speech()
    except Exception as e:
        logger.error(f'NOT AUTHORIZED: Error logging in: {e}')
        stop_flag = True

# Set the signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
        
# Run the main function
asyncio.run(main())