"""
This is a text to speech module using ElevenLab's Voice API. It is used to convert text to speech and play the audio stream.

Input:
    text: (str) - The text to be converted to speech
    voice: (str) - The name of the voice to be used for the speech
"""
import os
import traceback
from elevenlabs import generate, stream, set_api_key, VoiceSettings, Voice, voices
from dotenv import load_dotenv
from utils.logger import logger

def text_to_speech(text):
    load_dotenv('../.env')
    logger.debug(f'API Key: {os.getenv("ELEVENLABS_API_KEY")}')
    set_api_key(os.getenv('ELEVENLABS_API_KEY'))
    all_voices = voices()

    favorite_voices = {
        'Rachel':'21m00Tcm4TlvDq8ikWAM', 
        'Sarah':'EXAVITQu4vr4xnSDxMaL', 
        'Matilda':'XrExE9yKIg1WjnnlVkGX', 
        'Nicole':'piTKgcLEGmPE4e6mEKli',
        'Maya':'SeF28OCtyrmtk1Z29z6b',
        'Julia':'yssiWZPp27siJ0howQ4z',
        'Joanne': 'xYksD5PsEyPnJJEqJsMC'
    }

    chosen_voice = 'Maya'
    try:
        logger.info(f'Converting text to speech: {text}')

        logger.info(f'Voice: {favorite_voices[chosen_voice]}, ID: {chosen_voice}')
        audio_stream = generate(
            text=text,
            voice= Voice(
                voice_id=favorite_voices[chosen_voice],
                name=chosen_voice,
                category='premade',
                settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.5,
                    style=0.0,
                    use_speaker_boost=False
                )
            ),
            model='eleven_monolingual_v1',
            stream=True,
        )

        stream(audio_stream)
        logger.info(f'Speech generated')
    except Exception as e:
        logger.error(f'Error in text_to_speech: {e}')
        logger.error(traceback.format_exc())