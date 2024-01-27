import aiohttp
import asyncio
import json
import logging
import signal
import speech_recognition as sr
from utils.text_to_speech import text_to_speech

logging.basicConfig(level=logging.DEBUG)

# This flag will be used to stop the script
stop_flag = False


# Replace 'MICROPHONE_INDEX' with the index of your microphone
MICROPHONE_INDEX = 1

key_phrase = 'ava'
suitable_voices = ['Rachel', 'Sarah', 'Matilda', 'Nicole']

def signal_handler(signal, frame):
    global stop_flag
    stop_flag = True
    logging.info('Stopping...')

async def speech_to_text(recognizer, audio):
    try:
        text = recognizer.recognize_google(audio).lower()
        logging.info('Recognized: ' + text)
        if key_phrase in text:
            response = await handle_request(text.split(key_phrase, 1)[1])
            print(response)
            # text_to_speech(response['response']['content'], suitable_voices[1])

    except Exception as e:
        logging.error('Speech not recognized... ' + str(e))

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
        
def listen_callback(recognizer, audio):
    # This function will be called in a separate thread once the audio is recorded
    asyncio.run(speech_to_text(recognizer, audio))
        
async def get_speech():
    r = sr.Recognizer()
    r.energy_threshold = 2000
    source = sr.Microphone()
    logging.info('Listening...')
    r.listen_in_background(source, listen_callback)
    while not stop_flag:  # Stop the loop when a termination signal is received
        await asyncio.sleep(1)  # Add a delay to prevent high CPU usage

async def main():
    await get_speech()

# Set the signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
        
# Run the main function
asyncio.run(main())