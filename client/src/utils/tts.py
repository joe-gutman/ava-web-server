import os
import pyaudio
import asyncio
import numpy as np
import re
import string
from TTS.api import TTS
from threading import Lock

class Text_To_Speech:
    def __init__(self, voice):
        self.script_dir = os.path.dirname(__file__)
        self.save_folder = os.path.join(self.script_dir, "..", "..", "outputs")
        self.audio_sample = os.path.join(self.script_dir, "..", "..", "models", f"{voice}.wav")
        # self.tts = TTS("tts_models/en/multi-dataset/tortoise-v2")
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        self.queue = []
        self.all_sentences_processed = False
        self.lock = Lock()
        self.tts.to('cuda')

    # def split_text(self, text, max_length=10):
    #     words = re.findall(r"[\w']+", text)
    #     chunks = []
    #     for i in range(0, len(words), max_length):
    #         chunk = ' '.join(words[i:i+max_length])
    #         chunks.append(chunk)
    #     return chunks
        
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

    async def convert_tts(self, text):
        sentences = self.split_text_sentences(text)
        for sentence in sentences:
            # audio = await asyncio.to_thread(self.tts.tts, text=sentence, num_autoregressive_samples=8, diffusion_iterations=15) # for tortoise tts model
            audio = await asyncio.to_thread(self.tts.tts, text=sentence, speaker_wav=self.audio_sample, language="en") # for xtts model
            with self.lock:
                self.queue.append(audio)

        self.all_sentences_processed = True

    async def process_sentence(self, sentence):
        audio = await asyncio.to_thread(
            self.tts.tts, 
            text=sentence, 
            speaker_wav=self.audio_sample, 
            language="en"
        )
        self.queue.append(audio)

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
        await asyncio.gather(
            self.convert_tts(text),
            self.play_audio_loop()
        )

def main():
    tts = Text_To_Speech("upbeat_female")
    # asyncio.run(stt.run("In a hole in the ground there lived a hobbit. Not a nasty, dirty, wet hole, filled with the ends of worms and an oozy smell, nor yet a dry, bare, sandy hole with nothing in it to sit down on or to eat: it was a hobbit-hole, and that means comfort."))
    asyncio.run(tts.run("Hello, I'm Ava, your virtual assistant. How can I assist you today? Would you like me to check your schedule, set a reminder, or search the web for you?"))

if __name__ == "__main__":
    main()