"""
This is a text to speech module using ElevenLab's Voice API. It is used to convert text to speech and play the audio stream.

Input: text string
"""

from elevenlabs import generate, stream, set_api_key
from dotenv import load_dotenv
import os

load_dotenv()
set_api_key(os.getenv('ELEVENLABS_API_KEY'))

def text_to_speech(text, voice):
    try:
        audio_stream = generate(
            text=text,
            voice=voice,
            model='eleven_monolingual_v1',
            stream=True
        )
        stream(audio_stream)
    except Exception as e:
        raise Exception("Error in text_to_speech: " + str(e))
