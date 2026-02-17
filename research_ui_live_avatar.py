"""
research_ui_live_avatar.py
Drop this file into your project folder (next to whisper_local.py).
Run with: streamlit run research_ui_live_avatar.py
"""

import os
import io
import time
import json
import wave
import threading
import tempfile
import requests
import numpy as np
import streamlit as st
from typing import List, Optional

# streamlit-webrtc
from streamlit_webrtc import webrtc_streamer, WebRtcMode

# Use your whisper_local.py wrapper (must exist in same folder)
# whisper_local.transcribe_audio_bytes(audio_bytes, model_name="small") -> dict with "text"
from whisper_local import transcribe_audio_bytes

# TTS
import pyttsx3

# CONFIG (edit env vars or set them in .env / PowerShell / system)
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "").strip() or None
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "arcee-trinity-large-preview")
LOCALAI_URL = os.getenv("LOCALAI_URL", "").strip() or None
LOCALAI_MODEL = os.getenv("LOCALAI_MODEL", "gpt-4o-mini")

# Provide a STUN server to help WebRTC connect on restricted networks
DEFAULT_RTC_CONFIG = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}

st.set_page_config(page_title="Inventory AI — Avatar Call", layout="wide")
st.markdown(
    """
    <style>
    /* keep the avatar theme visuals consistent */
    .big-avatar { width: 280px; height: 280px; border-radius: 18px; background: radial-gradient(circle at 30% 30%, #39aaff 0%, #0070ff 45%, #002b5c 100%); margin: 20px auto; display:block; box-shadow: 0 20px 40px rgba(0,0,0,0.6); }
    .avatar-title { text-align:center; color:#dfefff; margin-bottom:30px; }
    .status-box { padding:10px 14px; border-radius:8px; background:#0b3; color:#011; }
    .err-box { padding:10px 14px; border-radius:8px; background:#300; color:#fee; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Inventory AI — Avatar Call Mode (Live mic)")

# top avatar area (keeps your theme/animation)
st.markdown('<div class="big-avatar"></div>', unsafe_allow_html=True)
st.markdown('<div class="avatar-title"><h3>Inventory AI — Avatar Online</h3></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.header("Talk to Inventory AI (Live)")
    st.info("Mode: Live Call. Click the gray *Start* button inside the WebRTC box. Allow microphone access when the browser asks. Speak naturally. The avatar will transcribe and reply with voice.")
    st.write("If OpenRouter API key is set (env OPENROUTER_API_KEY), the app will try it first and fall back to local.")

    # typed input (search/ask)
    typed = st.text_input("Or type a question and press Enter (press Enter to submit)", key="typed_input")
    if typed:
        st.write("You typed:", typed)

with col2:
    st.header("Status & Keys")
    st.write("- OpenRouter key loaded:", bool(OPENROUTER_KEY))
    st.write("- LocalAI URL:", LOCALAI_URL or "Not set")
    st.write("- STUN configuration:", "Using google STUN" if DEFAULT_RTC_CONFIG else "none")
    st.markdown("---")
    st.write("Notes: For best transcription ensure ffmpeg is installed and in PATH. For WebRTC issues try a different STUN/TURN server.")

# ---- helper utilities ----

def speak_text(text: str):
    """
    Speak asynchronously using pyttsx3 in a thread to avoid blocking Streamlit.
    """
    def tts_worker(text_inner):
        try:
            engine = pyttsx3.init()
            # Optional: pick a voice by language if installed (example)
            # voices = engine.getProperty('voices')
            # engine.setProperty('voice', voices[0].id)
            engine.say(text_inner)
            engine.runAndWait()
        except Exception as e:
            st.warning(f"TTS error: {e}")

    th = threading.Thread(target=tts_worker, args=(text,), daemon=True)
    th.start()


def frames_to_wav_bytes(frames) -> bytes:
    """
    Convert streamlit-webrtc audio frames to a valid WAV file bytes.
    This attempts to create a PCM16 WAV that ffmpeg/whisper can read.
    """
    if not frames:
        raise ValueError("No audio frames")

    # collect arrays
    arrays = []
    sample_rate = None
    nchannels = None

    for f in frames:
        try:
            arr = f.to_ndarray()  # frame -> numpy array
        except Exception:
            # fallback - try to read raw bytes
            data = f.planes[0].to_bytes()
            arr = np.frombuffer(data, dtype=np.int16)
        # arr may be (n_channels, n_samples) or (n_samples,)
        if arr.ndim == 2:
            # (channels, samples) -> interleave
            nchannels = arr.shape[0]
            interleaved = arr.T.reshape(-1)
            arrays.append(interleaved.astype(np.int16))
        else:
            # mono
            if nchannels is None:
                nchannels = 1
            arrays.append(arr.astype(np.int16))
        if sample_rate is None and hasattr(f, "sample_rate"):
            sample_rate = getattr(f, "sample_rate")

    if sample_rate is None:
        sample_rate = 16000  # sensible default

    final = np.concatenate(arrays).astype(np.int16)

    bio = io.BytesIO()
    with wave.open(bio, "wb") as wf:
        wf.setnchannels(nchannels or 1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(int(sample_rate))
        wf.writeframes(final.tobytes())
    return bio.getvalue()


def ask_openrouter(prompt: str, api_key: str, model: str = "arcee-trinity-large-preview"):
    if not api_key:
        return None, "(no openrouter key)"
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 500}
    try:
        r = requests.post(url, headers=headers, json=body, timeout=20)
        r.raise_for_status()
        j = r.json()
        # try common shapes
        if isinstance(j, dict):
            # openrouter style: choices -> message -> content
            if "choices" in j and isinstance(j["choices"], list) and len(j["choices"]) > 0:
                ch = j["choices"][0]
                msg = ch.get("message", {}).get("content") or ch.get("text")
                return msg, None
            # fallback: maybe an 'output' or 'text'
            if "output" in j:
                return str(j["output"]), None
        return str(j), None
    except Exception as e:
        return None, f"(OpenRouter error) {e}"


def ask_local_llm(prompt: str):
    """
    Very small local fallback. If you install LocalAI/ollama and expose HTTP,
    set LOCALAI_URL and LOCALAI_MODEL in env and this function will call it.
    """
    if LOCALAI_URL:
        payload = {"model": LOCALAI_MODEL, "prompt": prompt, "max_tokens": 400}
        try:
            r = requests.post(LOCALAI_URL, json=payload, timeout=12)
            if r.ok:
                data = r.json()
                # try common shapes
                if "choices" in data and isinstance(data["choices"], list):
                    return data["choices"][0].get("text") or data["choices"][0].get("message", {}).get("content")
                # try "output" or "completion"
                if "output" in data:
                    return str(data["output"])
                return str(data)
            else:
                return f"(local LLM returned status {r.status_code})"
        except Exception as e:
            return f"(local LLM error) {e}"
    # No local LLM available -> fallback canned reply
    return f"(offline local fallback) I heard: {prompt[:200]}"


def ask_ai(prompt: str):
    """
    Main ask function: OpenRouter -> Local -> canned fallback
    Returns: answer string and debug-info string (or None).
    """
    # prefer OpenRouter, if key present
    if OPENROUTER_KEY:
        out, err = ask_openrouter(prompt, OPENROUTER_KEY, OPENROUTER_MODEL)
        if out:
            return out, None
        # if openrouter failed try local
        if err:
            # continue to local
            local = ask_local_llm(prompt)
            return local, f"OpenRouter: {err}"
    else:
        local = ask_local_llm(prompt)
        return local, "(used local fallback, no openrouter key)"

# ---- WebRTC: live mic section ----

st.markdown("---")
st.subheader("Live Call Mode — Start microphone (WebRTC)")

webrtc_ctx = webrtc_streamer(
    key="avatar-call",
    mode=WebRtcMode.SENDONLY,
    rtc_configuration=DEFAULT_RTC_CONFIG,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=False,
    audio_receiver_size=1024,
)

if webrtc_ctx.state.playing:
    st.success("Avatar listening — speak naturally")
else:
    st.info("Click Start in the box above to allow the mic and begin live call.")

# Process audio frames on each rerun
if webrtc_ctx.audio_receiver:
    try:
        frames = webrtc_ctx.audio_receiver.get_frames(timeout=0.5)
    except Exception as e:
        frames = []
        # on first runs it may be empty; that's fine

    if frames:
        st.info("Processing audio...")
        try:
            wav_bytes = frames_to_wav_bytes(frames)
        except Exception as e:
            st.error(f"Error converting frames -> wav: {e}")
            wav_bytes = None

        if wav_bytes:
            # transcribe using your whisper_local wrapper which handles ffmpeg
            try:
                with st.spinner("Transcribing (Whisper)..."):
                    whisper_res = transcribe_audio_bytes(wav_bytes, model_name="small")
                    user_text = whisper_res.get("text") if isinstance(whisper_res, dict) else str(whisper_res)
                    if not user_text:
                        st.warning("Whisper returned no text.")
                        user_text = ""
                    st.write("🗣️ You said:", user_text)
            except Exception as e:
                st.error(f"Whisper error: {e}")
                user_text = ""

            # If got text -> ask AI
            if user_text.strip():
                answer, debug = ask_ai(user_text)
                if not answer:
                    answer = "(No answer)"
                st.write("🤖 Avatar:", answer)
                if debug:
                    st.write("Debug:", debug)
                # speak async
                try:
                    speak_text(answer)
                except Exception as e:
                    st.warning(f"TTS call error: {e}")

# Also allow typed questions to run query
if typed:
    with st.spinner("Querying AI..."):
        try:
            ans, dbg = ask_ai(typed)
            st.write("🤖 Avatar:", ans)
            if dbg:
                st.write("Debug:", dbg)
            speak_text(ans)
        except Exception as e:
            st.error(f"Ask error: {e}")

st.markdown("---")
st.write("Troubleshooting & Quick fixes:")
st.write(
    """
- If you see **ffmpeg not found**: install ffmpeg (download Windows static build) and add `.../ffmpeg/bin` to PATH, then restart the terminal and run `ffmpeg -version` to verify.
- If whisper complains about tensor types: ensure we used a **valid WAV file** (this script writes 16-bit PCM WAV). If you still see `RuntimeError: expected floating point`, update your `whisper_local.py` to call the model's transcribe(path) only with file paths (not arrays).
- If OpenRouter gives model ID errors (like `perplexity/sonar-small-online is not a valid model ID`) change `OPENROUTER_MODEL` env variable to a valid model string or remove the key to use local fallback.
- WebRTC may need STUN/TURN if `Connection is taking longer than expected`. Try a different stun server or a TURN server for strict networks.
"""
)

st.caption("If something still breaks, copy the red traceback and send it — I'll read and fix the exact lines.")