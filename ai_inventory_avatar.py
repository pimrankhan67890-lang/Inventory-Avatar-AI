import streamlit as st
from gtts import gTTS
import base64
import os

st.set_page_config(page_title="Inventory AI Avatar", layout="centered")

st.title("📦 Inventory AI — Avatar Online")

# ---------- TEXT INPUT ----------
user_text = st.text_input("Ask by Text")

# ---------- SIMPLE AI RESPONSE (replace with your real model later) ----------
def get_ai_reply(text):
    if not text:
        return ""
    return f"I received your message: {text}. I am ready to help you."

# ---------- AUDIO FUNCTION ----------
def speak_text(text):
    tts = gTTS(text)
    tts.save("reply.mp3")

    with open("reply.mp3", "rb") as f:
        audio_bytes = f.read()

    audio_base64 = base64.b64encode(audio_bytes).decode()

    audio_html = f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
    </audio>
    """

    st.markdown(audio_html, unsafe_allow_html=True)


# ---------- RUN ----------
if user_text:
    reply = get_ai_reply(user_text)

    st.success(reply)

    speak_text(reply)

    st.write("🔊 If autoplay blocked, click below:")
    st.audio("reply.mp3")
