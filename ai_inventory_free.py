import streamlit as st
import streamlit.components.v1 as components
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import whisper
import tempfile
import os
import pyttsx3
import requests

# ---------------- CONFIG ----------------

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")

# ---------------- LOAD MODELS ----------------

@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

model = load_whisper()

# ---------------- AI CALL ----------------

def ask_ai(text):
    if not OPENROUTER_KEY:
        return "Hello! I am your Inventory AI Avatar. API key not set, running in demo mode."

    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "arcee-ai/trinity-large-preview",
                "messages": [{"role": "user", "content": text}],
                "max_tokens": 300,
            },
            timeout=20
        )
        j = r.json()
        return j["choices"][0]["message"]["content"]

    except Exception as e:
        return f"AI error fallback: {str(e)}"

# ---------------- TTS ----------------

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# ---------------- AVATAR HTML ----------------

avatar_html = """
<div style="display:flex;justify-content:center;">
<model-viewer src="https://modelviewer.dev/shared-assets/models/Astronaut.glb"
auto-rotate camera-controls style="width:400px;height:400px;">
</model-viewer>
<script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
</div>
"""

# ---------------- AUDIO PROCESSOR ----------------

class MicProcessor(AudioProcessorBase):
    def __init__(self):
        self.buffer = b""

    def recv(self, frame):
        self.buffer += frame.to_ndarray().tobytes()
        return frame

# ---------------- UI ----------------

st.set_page_config(layout="wide")
st.title("🤖 Inventory AI — Beta Avatar")

components.html(avatar_html, height=420)

st.markdown("### 🎤 Speak to Avatar")

ctx = webrtc_streamer(
    key="mic",
    mode=WebRtcMode.SENDONLY,
    audio_processor_factory=MicProcessor,
    media_stream_constraints={"audio": True, "video": False},
)

if st.button("🧠 Process Speech"):
    if ctx.audio_processor:
        audio_bytes = ctx.audio_processor.buffer

        if len(audio_bytes) < 1000:
            st.warning("No speech captured")
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                f.write(audio_bytes)
                path = f.name

            result = model.transcribe(path)
            user_text = result["text"]

            st.success(f"You said: {user_text}")

            answer = ask_ai(user_text)

            st.markdown("### 🤖 Avatar says:")
            st.write(answer)

            speak(answer)

            os.remove(path)
