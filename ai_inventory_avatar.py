import streamlit as st
import requests
import whisper
import tempfile
import soundfile as sf
from gtts import gTTS
from duckduckgo_search import DDGS
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import numpy as np
import os
import time

# =========================
# CONFIG
# =========================

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

st.set_page_config(page_title="Inventory AI Avatar", layout="wide")

# =========================
# LOAD WHISPER
# =========================

@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

whisper_model = load_whisper()

# =========================
# MEMORY
# =========================

if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = []

# =========================
# AVATAR THEME (KEEP)
# =========================

st.markdown("""
<style>
.big-avatar {
    width: 220px;
    height: 220px;
    border-radius: 50%;
    background: radial-gradient(circle, #3cf2d4, #0a1f2f);
    box-shadow: 0 0 40px #3cf2d4;
    animation: pulse 2s infinite;
    margin: auto;
}
.speaking {
    box-shadow: 0 0 70px #3cf2d4;
}
@keyframes pulse {
    0% { box-shadow: 0 0 20px #3cf2d4; }
    50% { box-shadow: 0 0 50px #3cf2d4; }
    100% { box-shadow: 0 0 20px #3cf2d4; }
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='big-avatar'></div>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center'>Inventory AI — Avatar Online</h3>", unsafe_allow_html=True)

# =========================
# LIVE WEB SEARCH
# =========================

def web_search(q):
    try:
        with DDGS() as ddgs:
            r = ddgs.text(q, max_results=3)
            return " ".join([x["body"] for x in r])
    except:
        return ""

# =========================
# AI BRAIN (ONLINE + FALLBACK)
# =========================

def ask_ai(q):

    context = web_search(q)

    prompt = f"""
Use latest info if available.

Web data:
{context}

User question:
{q}
"""

    if not OPENROUTER_KEY:
        return "No OpenRouter key found."

    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=60
        )

        data = r.json()
        return data["choices"][0]["message"]["content"]

    except:
        return offline_fallback(q)

# =========================
# OFFLINE FALLBACK
# =========================

def offline_fallback(q):
    q = q.lower()
    if "cm of andhra" in q:
        return "Current CM of Andhra Pradesh is N. Chandrababu Naidu (since June 2024)."
    if "time" in q:
        return time.ctime()
    return "Offline mode answer: I could not reach live model."

# =========================
# SPEAK (FREE VOICE)
# =========================

def speak(text):
    tts = gTTS(text=text, lang="en")
    f = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(f.name)
    audio = open(f.name, "rb").read()
    st.audio(audio)

# =========================
# TEXT MODE
# =========================

st.header("⌨️ Ask by Text")

q = st.text_input("Type and press Enter")

if q:
    reply = ask_ai(q)
    st.success(reply)
    st.session_state.chat_memory.append((q, reply))
    speak(reply)

# =========================
# LIVE VOICE CALL MODE
# =========================

st.header("📞 Live Avatar Call Mode")

ctx = webrtc_streamer(
    key="call",
    mode=WebRtcMode.SENDONLY,
    media_stream_constraints={"audio": True, "video": False},
)

if ctx.audio_receiver:

    st.info("🎙️ Avatar listening — speak")

    frames = ctx.audio_receiver.get_frames(timeout=1)

    if frames:
        audio = np.concatenate([
            f.to_ndarray().flatten().astype(np.float32)/32768.0
            for f in frames
        ])

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        sf.write(tmp.name, audio, 16000)

        result = whisper_model.transcribe(tmp.name)
        text = result["text"]

        if text.strip():
            st.write("🗣️ You:", text)

            reply = ask_ai(text)
            st.success(reply)
            speak(reply)

# =========================
# MEMORY VIEW
# =========================

if st.checkbox("Show memory"):
    for u,a in st.session_state.chat_memory:
        st.write("You:", u)
        st.write("AI:", a)