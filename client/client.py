import aiohttp
import asyncio
import json
import logging
import speech_recognition as sr
from utils.text_to_speech import text_to_speech
from threading import Lock
git
logging.basicConfig(level=logging.DEBUG)

# Replace 'MICROPHONE_INDEX' with the index of your microphone
MICROPHONE_INDEX = 1

key_phrase = 'hey ava'
suitable_voices = ['Rachel', 'Sarah', 'Matilda', 'Nicole']

# Create a lock
lock = Lock()

def speech_to_text(recognizer, audio):
    with lock:
        try:
            text = recognizer.recognize_google(audio).lower()
            logging.info('Recognized: ' + text)
            if key_phrase in text:
                response = asyncio.run(handle_request(text.split(key_phrase, 1)[1]))
                text_to_speech(response['response']['content'], suitable_voices[0])

        except Exception as e:
            logging.error('Voice not recognized: ' + str(e))

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
        
def get_audio():
    r = sr.Recognizer()
    mic = sr.Microphone(device_index=MICROPHONE_INDEX)
    print("Listening...")
    try:
        stop_listening = r.listen_in_background(mic, speech_to_text)
    except:
        print('please say that again')
        return get_audio()
    return stop_listening

async def main():
    stop_listening = get_audio()
    while True:
        if stop_listening is not None:
            await asyncio.sleep(1)
        
# Run the main function
asyncio.run(main())