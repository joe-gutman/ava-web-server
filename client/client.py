import aiohttp
import asyncio
import json
import logging
import speech_recognition as sr
from utils.text_to_speech import text_to_speech
from threading import Lock

logging.basicConfig(level=logging.DEBUG)

# Replace 'MICROPHONE_INDEX' with the index of your microphone
MICROPHONE_INDEX = 1

key_phrase = 'hey ava'
suitable_voices = ['Rachel', 'Sarah', 'Matilda', 'Nicole']

async def speech_to_text(recognizer, audio):
    try:
        text = recognizer.recognize_google(audio).lower()
        logging.info('Recognized: ' + text)
        if key_phrase in text:
            response = await handle_request(text.split(key_phrase, 1)[1])
            text_to_speech(response['response']['content'], suitable_voices[1])

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
        
async def get_speech():
    try:
        with sr.Microphone() as source:
            r = sr.Recognizer()
            audio = r.listen(source)
            await speech_to_text(r, audio)
    except sr.UnknownValueError:
        print("No clue what you said, listening again... \n")
        await get_speech()

async def main():
    await get_speech()
    
        
# Run the main function
asyncio.run(main())