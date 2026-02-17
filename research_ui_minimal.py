# research_ui_minimal.py
import streamlit as st
from whisper_local import transcribe_audio_bytes
import pyttsx3
import os
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="AI Inventory — Minimal", layout="wide")

st.title("AI Inventory — Minimal voice demo")

st.markdown("Upload a short audio file (wav/mp3) or click *Record microphone* if you installed `streamlit-mic-recorder`.")

uploaded = st.file_uploader("Upload audio (wav/mp3) for transcription", type=["wav","mp3","m4a"])
if uploaded is not None:
    audio_bytes = uploaded.read()
    st.audio(audio_bytes)
    with st.spinner("Transcribing..."):
        res = transcribe_audio_bytes(audio_bytes)
        text = res.get("text","")
    st.success("Transcription:")
    st.write(text)

    if st.button("Speak (pyttsx3)"):
        engine = pyttsx3.init()
        engine.say(text or "No text to speak")
        engine.runAndWait()

# Optional: simple text input that responds with the same text (placeholder for LLM)
question = st.text_input("Type a question for the local demo (not a full LLM yet):")
if st.button("Answer (local stub)"):
    answer = f"(Local stub) I received: {question}"
    st.write(answer)
    # speak
    engine = pyttsx3.init()
    engine.say(answer)
    engine.runAndWait()
