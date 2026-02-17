import streamlit as st
import requests
import os
from whisper_local import transcribe_audio_bytes
import pyttsx3

st.set_page_config(page_title="Inventory AI — Beta", layout="wide")

# ---------------- AVATAR UI ---------------- #

avatar_html = """
<style>
body {background:#0e1117;}
.avatar-wrap {
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  margin-top:40px;
}
.avatar {
  width:220px;
  height:220px;
  border-radius:50%;
  background:linear-gradient(135deg,#5ef,#09f);
  box-shadow:0 0 40px #09f;
  animation: breathe 2.5s infinite;
}
@keyframes breathe {
  0%{transform:scale(1)}
  50%{transform:scale(1.08)}
  100%{transform:scale(1)}
}
.status {
  margin-top:20px;
  font-size:22px;
  color:#9cf;
}
</style>

<div class="avatar-wrap">
  <div class="avatar"></div>
  <div class="status">Inventory AI — Avatar Online</div>
</div>
"""

st.components.v1.html(avatar_html, height=360)

st.title("📞 Talk With Inventory AI")

# ---------------- VOICE INPUT ---------------- #

audio = st.file_uploader("Upload voice (wav/mp3/m4a)", type=["wav","mp3","m4a"])

user_text = ""

if audio:
    audio_bytes = audio.read()
    st.audio(audio_bytes)

    with st.spinner("Listening..."):
        result = transcribe_audio_bytes(audio_bytes)
        user_text = result["text"]

    st.success("You said:")
    st.write(user_text)

# ---------------- TEXT INPUT BACKUP ---------------- #

typed = st.text_input("Or type message")

if typed:
    user_text = typed

# ---------------- AI BRAIN ---------------- #

def ask_openrouter(prompt):
    key = os.getenv("OPENROUTER_API_KEY","")

    if not key:
        return "API key missing — using local fallback reply."

    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type":"application/json"
            },
            json={
                "model":"openai/gpt-4o-mini",
                "messages":[{"role":"user","content":prompt}]
            },
            timeout=25
        )
        j = r.json()
        return j["choices"][0]["message"]["content"]

    except:
        return "Network error — local fallback answer."

# ---------------- RESPONSE ---------------- #

if st.button("Call AI") and user_text:

    with st.spinner("Thinking..."):
        answer = ask_openrouter(user_text)

    st.markdown("### 🤖 Avatar says:")
    st.write(answer)

    # speak
    engine = pyttsx3.init()
    engine.say(answer)
    engine.runAndWait()
