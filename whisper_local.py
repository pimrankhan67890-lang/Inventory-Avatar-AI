import whisper
import tempfile
import os

_model = None

def load_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model

def transcribe_audio_bytes(audio_bytes):
    model = load_model()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_bytes)
        path = f.name

    try:
        result = model.transcribe(path)
        return result["text"]
    finally:
        try:
            os.remove(path)
        except:
            pass

