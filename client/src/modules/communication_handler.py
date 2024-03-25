import os
import re
import time
import pyaudio
import asyncio
import string
import numpy as np
import speech_recognition as sr
import whisper
import torch
import webrtcvad
import torch
import glob
from random import randrange
from utils.logger import logger
from TTS.api import TTS
from threading import Lock
# from .tts import generate_audio


class ListenHandler:
    def __init__(self, model_name="medium", energy_threshold=1550):
        self.key_phrases = ['ava', 'eva']
        self.energy_threshold = energy_threshold
        self.load_model(model_name)
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(3)  # Aggressive mode for VAD

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
            self.source = sr.Microphone(sample_rate=24000, device_index=mic_index)
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

    def realtime_stt(self, record_timeout=2):
        self.setup_audio()

        incoming_audio = []
        translated_text = ""
        
        is_speaking = False
        speech_start_time = None
        silence_threshold = 3  # seconds of silence to consider speech ended

        import numpy as np

        def record_callback(_, audio: sr.AudioData):

            # ADD BUILT IN NOISE REDUCTION
            # - noise reduction currently relies on 3rd party software (Nvidia Broadcast)
            
            nonlocal is_speaking, speech_start_time
            raw_audio = audio.get_raw_data()
            has_speech = False

            sample_rate = 16000
            frame_duration = 20 # ms
            num_samples_per_frame = int(sample_rate * frame_duration / 1000)

            try:
                raw_audio_np = np.frombuffer(raw_audio, dtype=np.int16)
                # logger.debug(f"Raw audio length: {len(raw_audio_np)}")
                for i in range(0, len(raw_audio_np), num_samples_per_frame):
                    frame = raw_audio_np[i:i + num_samples_per_frame]
                    if len(frame) < num_samples_per_frame:
                        frame = np.pad(frame, (0, num_samples_per_frame - len(frame)), mode='constant')
                    # logger.debug(f"Frame length: {len(frame)}")
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
                    if len(translated_text) > 0:
                        if 'eva' in translated_text.lower():
                            translated_text.replace('eva', 'ava')
                        # return translated_text
                        # check for keyword
                        if any(key_phrase in translated_text.lower() for key_phrase in self.key_phrases):
                            return translated_text
                        else:
                            return None 

                time.sleep(0.1)

        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(f"Error handling speech: {e}")

class SpeechHandler_TTS:
    def __init__(self):
        self.script_dir = os.path.dirname(__file__)
        self.save_dir = os.path.join(self.script_dir, "..", "outputs")
        self.audio_samples = self.get_voice_samples()
        self.audio_rate = 24000
        self.queue = []
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        self.device = "cuda"
        self.all_sentences_processed = False
        self.lock = Lock()

        self.tts.to(self.device)

        # if wav_opt:
        #     # Save the converted WAV
        #     with open(output_wav_path, 'wb') as f:
        #         f.write(wav_opt[1][0])
        # else:
        #     raise RuntimeError("Failed to perform voice conversion")

    async def convert_tts(self, text):
        sentences = self.split_text_sentences(text)
        # temp_wav_path = os.path.join(self.script_dir, self.save_dir, 'temp', f"temp_output_{randrange(0, 123456789)}.wav")

        for sentence in sentences:
            if len(re.sub(r'[^a-zA-Z0-9]', '', string)) > 1:
                audio = await asyncio.to_thread(
                    self.tts.tts,
                    text=sentence,
                    speaker_wav=self.get_voice_samples(filename=""),
                    language="en",
                    split_sentences=False
                )

                with self.lock:
                    self.queue.append(audio)

        self.all_sentences_processed = True

        # ------------------ Experimental nonworking RVC integration ----------------- #
        # Error: Audio is played at a slower rate than the audio file specifies
        # Error: Played audio reflects XTTS model instead of the expected RVC model 
        # 
        # audio = generate_audio(
        #     text=sentences[0],
        #     tts_output_dir=os.path.join(self.script_dir, self.save_dir,'temp'),
        #     speaker_name="speaker2",
        #     emotion="Surprise",
        #     speed=1.0
        # )

        # self.queue.append(audio)

    def is_punctuation(self, word):
        # Check if the word consists only of punctuation characters
        return all(char in string.punctuation for char in word)
        
    def split_text_words(self, text, max_length=25):
        # Split text into words along with punctuation
        words_with_punctuation = re.findall(r'\w+|[^\w\s]', text)
        print(f"Words: {words_with_punctuation}")
        
        chunks = []
        current_chunk = []
        word_count = 0
        
        for word in words_with_punctuation:
            if self.is_punctuation(word) and word_count <= max_length :
                if current_chunk:
                    current_chunk[-1] = current_chunk[-1].strip()
                current_chunk.append(word + ' ')
            else: 
                current_chunk.append(word +' ')
                word_count += 1
                if word_count == max_length:
                    chunks.append(''.join(current_chunk))
                    current_chunk = []
                    word_count = 0
        if current_chunk:
            chunks.append(''.join(current_chunk))
        return chunks
    
    def split_text_sentences(self, text):
        return re.split(r'(?<=[.!?])\s+', text)
    
    def get_voice_samples(self, filename = ""):
        voice_samples_path = os.path.join(self.script_dir, "..", "..", "voice_samples")
        voice_samples = []
        if filename != "":
            matching_files = glob.glob(os.path.join(voice_samples_path, f"{filename}.*"))
            voice_samples.extend(matching_files)
        else:
            for filename in os.listdir(voice_samples_path):
                voice_samples.append(os.path.join(voice_samples_path, filename))

        return voice_samples 


    async def play_audio_loop(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=22050,
                        output=True)
        
        while True:
            if len(self.queue) > 0:
                audio = self.queue.pop(0)
                audio_np = np.array(audio, dtype=np.float32)
                audio_bytes = (audio_np * 32767).astype(np.int16).tobytes()
                stream.write(audio_bytes)
            else:
                if self.all_sentences_processed:
                    print("Done")
                    break
                await asyncio.sleep(0.1)

    async def run(self, text):
        self.all_sentences_processed = False
        await asyncio.gather(
            self.convert_tts(text),
            self.play_audio_loop()
        )