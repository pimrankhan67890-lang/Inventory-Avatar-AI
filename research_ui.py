import streamlit as st
import requests
import os
import pyttsx3
from whisper_local import transcribe_audio_bytes
from reporter import make_pdf
from dotenv import load_dotenv
import streamlit.components.v1 as components

load_dotenv()

st.set_page_config(page_title="Inventory AI — Beta", layout="wide")

# -------------------------
# CONFIG
# -------------------------

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

def speak(text):
    try:
        engine = pyttsx3.init()
        engine.say(text[:500])
        engine.runAndWait()
    except:
        pass

# -------------------------
# OPENROUTER CALL
# -------------------------

def ask_ai(prompt):
    if not OPENROUTER_KEY:
        return "No OpenRouter key set. Using local fallback answer."

    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "arcee-ai/arcee-trinity-large-preview",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=20
        )

        data = r.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"AI request failed → {e}"

# -------------------------
# AVATAR HTML
# -------------------------

avatar_html = """
<div style="text-align:center">
<img src="https://i.imgur.com/6qK0F1k.gif" width="320">
<h2>🤖 Inventory AI — Beta</h2>
</div>
"""

# -------------------------
# UI
# -------------------------

st.title("Inventory AI — Beta")
components.html(avatar_html, height=380)

st.subheader("🎤 Talk to AI")

audio = st.file_uploader("Upload voice (wav/mp3)", type=["wav","mp3","m4a"])

if audio:
    bytes_data = audio.read()
    st.audio(bytes_data)

    with st.spinner("Listening..."):
        text = transcribe_audio_bytes(bytes_data)

    st.success("You said:")
    st.write(text)

    if st.button("🧠 Ask AI"):
        with st.spinner("Thinking..."):
            answer = ask_ai(text)

        st.subheader("AI Response")
        st.write(answer)

        speak(answer)

        st.session_state["last_answer"] = answer

# -------------------------
# TEXT CHAT ALSO
# -------------------------

q = st.text_input("Or type your question")

if st.button("Ask (text)"):
    answer = ask_ai(q)
    st.write(answer)
    speak(answer)
    st.session_state["last_answer"] = answer

# -------------------------
# EXPORT
# -------------------------

if "last_answer" in st.session_state:
    if st.button("📄 Export PDF"):
        file = make_pdf(st.session_state["last_answer"])
        with open(file, "rb") as f:
            st.download_button("Download", f, "ai_answer.pdf")
