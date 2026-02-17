# voice_tools.py
import pyttsx3
from whisper_local import transcribe_audio_bytes

def speak_text(text):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("TTS error:", e)

def transcribe_from_bytes(audio_bytes):
    return transcribe_audio_bytes(audio_bytes)
