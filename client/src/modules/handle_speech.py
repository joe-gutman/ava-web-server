import os
import re
import time
import pyaudio
import numpy as np
import speech_recognition as sr
import whisper
import torch
import webrtcvad
import traceback
from datetime import datetime, timedelta
from queue import Queue
from dotenv import load_dotenv
from elevenlabs import generate, stream, set_api_key, VoiceSettings, Voice, voices
from utils.logger import logger

class SpeechHandler:
    def __init__(self, model_name="medium", energy_threshold=1000):
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
        self.energy_threshold = energy_threshold
        self.load_model(model_name)
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(3)  # Aggressive mode for VAD

        load_dotenv('../.env')
        set_api_key(os.getenv('ELEVENLABS_API_KEY'))

    def setup_audio(self):
        torch.cuda.empty_cache()
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

    def real_time_transcription(self, record_timeout=2):
        self.setup_audio()

        incoming_audio = []
        translated_text = ""
        
        is_speaking = False
        speech_start_time = None
        silence_threshold = 3  # seconds of silence to consider speech ended

        import numpy as np

        def record_callback(_, audio: sr.AudioData):
            # ADD NOISE REDUCTION
            # 
            # 
            # 
            nonlocal is_speaking, speech_start_time
            raw_audio = audio.get_raw_data()
            has_speech = False

            sample_rate = 16000
            frame_duration = 20 # ms
            num_samples_per_frame = int(sample_rate * frame_duration / 1000)

            try:
                raw_audio_np = np.frombuffer(raw_audio, dtype=np.int16)
                logger.debug(f"Raw audio length: {len(raw_audio_np)}")
                for i in range(0, len(raw_audio_np), num_samples_per_frame):
                    frame = raw_audio_np[i:i + num_samples_per_frame]
                    if len(frame) < num_samples_per_frame:
                        frame = np.pad(frame, (0, num_samples_per_frame - len(frame)), mode='constant')
                    logger.debug(f"Frame length: {len(frame)}")
                    has_speech = self.vad.is_speech(frame, sample_rate)
                    if has_speech:
                        break
            except Exception as e:
                logger.error(f"Error in VAD processing: {e}")

            if has_speech:
                incoming_audio.append(raw_audio)
                is_speaking = True
                speech_start_time = time.time()


        self.recorder.listen_in_background(self.source, record_callback, phrase_time_limit=2)

        try:
            while True:
                if len(incoming_audio) > 0:
                    combined_audio = b''.join(incoming_audio)
                    incoming_audio = []

                    audio_np = np.frombuffer(combined_audio, dtype=np.int16)
                    result = self.audio_model.transcribe(audio_np.astype(np.float32) / 32768.0, fp16=torch.cuda.is_available())
                    text = result['text'].strip()
                    logger.debug(f"STT Chunk: {text}")
                    translated_text += " " + text

                elif is_speaking is True and time.time() - speech_start_time > silence_threshold: 
                    is_speaking = False
                    logger.debug(f"Full STT: {translated_text}")
                    return translated_text
                    # check for keyword
                    # if any(key_phrase in translated_text.lower() for key_phrase in self.key_phrases):
                    #     return translated_text
                    # else:
                    #     return None 

                time.sleep(0.1)

        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(f"Error handling speech: {e}")





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