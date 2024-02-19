import os
import time
import speech_recognition as sr
import asyncio
from elevenlabs import generate, stream, set_api_key, VoiceSettings, Voice, voices
from dotenv import load_dotenv
from utils.logger import logger



class SpeechHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.source = sr.Microphone(chunk_size=10240)
        self.chosen_voice = 'Maya'
        self.voice_ids = {
            'Rachel':'21m00Tcm4TlvDq8ikWAM', 
            'Sarah':'EXAVITQu4vr4xnSDxMaL', 
            'Matilda':'XrExE9yKIg1WjnnlVkGX', 
            'Nicole':'piTKgcLEGmPE4e6mEKli',
            'Maya':'SeF28OCtyrmtk1Z29z6b',
            'Julia':'yssiWZPp27siJ0howQ4z',
            'Joanne': 'xYksD5PsEyPnJJEqJsMC'
        }
        self.key_phrases = ['ava', 'eva']


        load_dotenv('../.env')
        set_api_key(os.getenv('ELEVENLABS_API_KEY'))


    def text_to_speech(self, text):
        load_dotenv('../.env')
        logger.debug(f'API Key: {os.getenv("ELEVENLABS_API_KEY")}')
        set_api_key(os.getenv('ELEVENLABS_API_KEY'))
        all_voices = voices()


        try:
            logger.info(f'Converting text to speech: {text}')

            logger.info(f'Voice: {self.chosen_voice}, ID: {self.voice_ids[self.chosen_voice]}')
            audio_stream = generate(
                text=text,
                voice= Voice(
                    voice_id=self.voice_ids[self.chosen_voice],
                    name=self.chosen_voice,
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

    async def start_listening(self):
        logger.info('Listening...')
        while True:
            with self.source as source:
                audio = self.recognizer.listen(source)
                text = self._listen_callback(audio)
                if text:
                    return text

    def _listen_callback(self, audio):
        logger.info('Received audio data')
        try:
            text = self.recognizer.recognize_google(audio).lower()
            logger.info(f'Recognized: {text}')
            if any(phrase in text for phrase in self.key_phrases):
                logger.info(f'Key phrase detected; Returning: {text}')
                return text
            else:
                return None
        except Exception as e:
            logger.error(f'Speech not recognized: {str(e)}')