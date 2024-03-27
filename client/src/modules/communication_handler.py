import os, re, time, asyncio
from threading import Lock
from dotenv import load_dotenv
from signal import SIGTERM, SIGINT

import numpy as np, pyaudio, boto3
import speech_recognition as sr, webrtcvad, glob, torch

from utils.logger import logger
from TTS.api import TTS
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
)
import whisper

load_dotenv()

class ListenHandler_Google:
    def __init__(self, energy_threshold=1550):
        self.key_phrases = ['ava', 'eva']
        self.energy_threshold = energy_threshold
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(3)  # Aggressive mode for VAD

    def setup_audio(self):
        self.source = sr.Microphone(sample_rate=24000)
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = self.energy_threshold
        self.recorder.dynamic_energy_threshold = False

        with self.source as source:
            self.recorder.adjust_for_ambient_noise(source)

    def start_transcription(self, record_timeout=2):
        self.setup_audio()

        incoming_audio = []
        translated_text = ""
        
        is_speaking = False
        speech_start_time = None
        silence_threshold = 3  # seconds of silence to consider speech ended

        def record_callback(_, audio: sr.AudioData):
            nonlocal is_speaking, speech_start_time
            raw_audio = audio.get_raw_data()
            has_speech = False

            sample_rate = 16000
            frame_duration = 20  # ms
            num_samples_per_frame = int(sample_rate * frame_duration / 1000)

            try:
                raw_audio_np = np.frombuffer(raw_audio, dtype=np.int16)
                for i in range(0, len(raw_audio_np), num_samples_per_frame):
                    frame = raw_audio_np[i:i + num_samples_per_frame]
                    if len(frame) < num_samples_per_frame:
                        frame = np.pad(frame, (0, num_samples_per_frame - len(frame)), mode='constant')
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

                    audio = sr.AudioData(combined_audio, 24000, 2)
                    try:
                        text = self.recorder.recognize_google(audio)
                    except sr.UnknownValueError:
                        text = ""
                    logger.debug(f"STT Chunk: {text}")
                    translated_text += " " + text

                elif is_speaking is True and time.time() - speech_start_time > silence_threshold: 
                    is_speaking = False
                    logger.debug(f"Full STT: {translated_text}")
                    if len(translated_text) > 0:
                        if 'eva' in translated_text.lower():
                            translated_text.replace('eva', 'ava')
                        if any(key_phrase in translated_text.lower() for key_phrase in self.key_phrases):
                            return translated_text
                        else:
                            return None 

                time.sleep(0.1)

        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(f"Error handling speech: {e}")

class ListenHandler_Whisper:
    def __init__(self, model_name="medium", energy_threshold=1550):
        self.key_phrases = ['ava']
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

    def start_transcription(self, record_timeout=2):
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
                    translated_text_filtered = ''.join(char for char in translated_text if char.isalpha())

                    if len(translated_text_filtered) > 0:
                        if 'eva' in translated_text.lower():
                            translated_text = translated_text.replace('eva', 'ava')
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


class ListenHandler_Deepgram:
    def __init__(self):
        self.deepgram = DeepgramClient()
        self.dg_connection = self.deepgram.listen.live.v("1")
        self.current_transcript = ""
        self.options = LiveOptions(
                model="nova-2",
                punctuate=True,
                language="en-US",
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                interim_results=True,
                utterance_end_ms="1000",
                vad_events=True,
            )
        self.setup_listeners()

    def setup_listeners(self):
        # Define event handlers
        def on_open(self, event, **kwargs):
            print(f"\n\n{event}\n\n")

        def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            else:
                self.current_transcript += f" {sentence}"
            print(f"speaker: {sentence}")

        def on_metadata(self, metadata, **kwargs):
            print(f"\n\n{metadata}\n\n")

        def on_speech_started(self, speech_started, **kwargs):
            print(f"\n\n{speech_started}\n\n")
            # Reset the current transcript when speech starts
            self.current_transcript = ""

        def on_error(self, error, **kwargs):
            print(f"\n\n{error}\n\n")

        def on_close(self, close, **kwargs):
            print(f"\n\n{close}\n\n")

        # Assign event handlers
        self.dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        self.dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        self.dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
        self.dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
        self.dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        self.dg_connection.on(LiveTranscriptionEvents.Close, on_close)

    async def detect_speech_with_vad(self):
        vad = webrtcvad.Vad()
        vad.set_mode(3)  # Aggressive mode
        chunk = 320  # 20ms audio chunks for VAD

        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        input=True,
                        frames_per_buffer=chunk)

        is_speech = False
        silence_frames_threshold = int(0.5 * 16000)  # Number of frames for 0.5 seconds
        silence_frames_count = 0

        try:
            async for data in self.audio_data_generator(stream, chunk):
                if vad.is_speech(data, sample_rate=16000):
                    # Speech detected
                    if not is_speech:
                        print("--- SPEECH DETECTED ---")
                        is_speech = True
                        self.dg_connection.start(self.options)
                        # Reset the silence frames count
                        silence_frames_count = 0
                else:
                    # Silence detected
                    if is_speech:
                        silence_frames_count += 1
                        if silence_frames_count >= silence_frames_threshold:
                            print("--- SPEECH ENDED ---")
                            is_speech = False
                            silence_frames_count = 0
                            self.dg_connection.finish()
                            # Reset the silence frames count

        except asyncio.CancelledError:
            raise  # Re-raise the CancelledError to propagate the cancellation

        finally:
            # Cleanup
            stream.stop_stream()
            stream.close()
            p.terminate()

    async def audio_data_generator(self, stream, chunk):
        while True:
            data = await self.async_stream_read(stream, chunk)
            if not data:
                break
            yield data

    async def async_stream_read(self, stream, chunk):
        return stream.read(chunk)

    async def start_transcription(self):
        await self.detect_speech_with_vad()




class SpeechHandler_XTTS:
    def __init__(self):
        self.script_dir = os.path.dirname(__file__)
        self.save_dir = os.path.join(self.script_dir, "..", "outputs")
        self.audio_samples = self.get_voice_samples(filename="tests_data_ljspeech_wavs_LJ001-0031.wav")
        self.audio_rate = 24000
        self.queue = []
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        self.device = "cuda"
        self.all_sentences_processed = False
        self.lock = Lock()

        self.tts.to(self.device)

    async def convert_tts(self, text):
        sentences = self.split_text_sentences(text)

        logger.debug(f"Text to convert: {text}")

        for sentence in sentences:
            audio = await asyncio.to_thread(
                self.tts.tts,
                text=sentence,
                speaker_wav=self.get_voice_samples(),
                # speaker = "emma", 
                language="en",
                split_sentences=False
            )

            with self.lock:
                self.queue.append(audio)

        self.all_sentences_processed = True

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

class SpeechHandler_Polly:
    def __init__(self, region_name='us-east-1'):
        self.script_dir = os.path.dirname(__file__)
        self.polly_client = boto3.client('polly', 
                                         region_name=region_name, 
                                         aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'), 
                                         aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=16000,
                                      output=True)
        self.lock = asyncio.Lock()

    async def convert_tts(self, text, voice_id='Salli'):
        response = self.polly_client.synthesize_speech(
            Text=text,
            OutputFormat='pcm',
            VoiceId=voice_id,
            Engine='neural'
        )
        async with self.lock:
            while True:
                data = response['AudioStream'].read(1024)
                if not data:
                    break
                self.stream.write(data)

    async def run(self, text):
        await self.convert_tts(text)