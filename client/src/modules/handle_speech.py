import os
import re
import time
import pyaudio
import numpy as np
import speech_recognition as sr
import whisper
import torch
import webrtcvad
from datetime import datetime, timedelta
from queue import Queue
from dotenv import load_dotenv
from elevenlabs import generate, stream, set_api_key, VoiceSettings, Voice, voices
from utils.logger import logger

class SpeechHandler:
    def __init__(self, model_name="medium", energy_threshold=1000):
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
        self.key_phrase_pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, self.key_phrases)) + r')\b', re.IGNORECASE)
        self.energy_threshold = energy_threshold
        self.load_model(model_name)

        load_dotenv('../.env')
        set_api_key(os.getenv('ELEVENLABS_API_KEY'))

    def setup_audio(self):
        audio = pyaudio.PyAudio()
        mic_index = None
        for i in range(audio.get_device_count()):
            dev_info = audio.get_device_info_by_index(i)
            if 'Microphone' in dev_info['name']:
                mic_index = i
                break
        if mic_index is not None:
            self.source = sr.Microphone(sample_rate=16000, device_index=mic_index)
            self.recorder = sr.Recognizer()
            self.recorder.energy_threshold = self.energy_threshold
            self.recorder.dynamic_energy_threshold = False

            with self.source as source:
                self.recorder.adjust_for_ambient_noise(source)
        else:
            print("No microphone found.")

    def load_model(self, model_name):
        if model_name != "large":
            model_name += ".en"
        self.audio_model = whisper.load_model(model_name)
        logger.debug(f"Cuda is available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logger.debug("Moved whisper model to cuda")
            self.audio_model.cuda() 

    def real_time_transcription(self, record_timeout=2, phrase_timeout=3):
        self.setup_audio()

        data_queue = Queue()
        transcription = ['']

        def record_callback(_, audio: sr.AudioData):
            data = audio.get_raw_data()
            data_queue.put(data)

        self.recorder.listen_in_background(self.source, record_callback, phrase_time_limit=record_timeout)

        transcription = ['']

        queue_empty_flag = False

        while True:
            try:
                if not data_queue.empty():
                    queue_empty_flag = False

                    audio_data = b''.join(data_queue.queue)
                    data_queue.queue.clear()

                    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                    result = self.audio_model.transcribe(audio_np, fp16=torch.cuda.is_available())
                    text = result['text'].strip()

                    transcription.append(text)

                    # os.system('cls' if os.name == 'nt' else 'clear')
                    logger.debug(f"STT: {transcription[-1]}")
                    print(transcription[-1])

                elif not queue_empty_flag:
                    combined_transcript = ' '. join(transcription)
                    logger.debug(f"Entire Transcription: {combined_transcript}")
                    match = self.key_phrase_pattern.search(combined_transcript)
                    if match:
                        logger.debug(combined_transcript)
                        return combined_transcript 
                    transcription = ['']
                    queue_empty_flag = True

                time.sleep(0.1)
            except KeyboardInterrupt:
                break

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
                        similarity_boost=0.75,
                        style=0.1,
                        use_speaker_boost=True
                    )
                ),
                model='eleven_turbo_v2',
                stream=True,
            )

            stream(audio_stream)
            logger.info(f'Speech generated')
        except Exception as e:
            logger.error(f'Error in text_to_speech: {e}')