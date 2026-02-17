# ai_avatar_only.py
# Avatar-only Phase-1 demo (local-first)
import streamlit as st
import os, requests, base64, tempfile, time, json
from dotenv import load_dotenv
from whisper_local import transcribe_audio_bytes
import pyttsx3

load_dotenv()

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
# Hide streamlit default header/footer for clean avatar-only look
hide_streamlit_style = """
    <style>
      header {visibility: hidden;}
      footer {visibility: hidden;}
      .stMarkdown {color: #fff;}
      .css-18e3th9 {padding-top: 1rem;}
      .css-1v3fvcr {padding: 0rem;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ENV
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "arcee-trinity-large-preview")
LOCALAI_URL = os.getenv("LOCALAI_URL", "").strip()  # optional

# Page layout: only one big column for avatar UI
st.markdown("<div style='background:#071029;padding:16px;border-radius:10px; height:100vh;'>", unsafe_allow_html=True)

# Title text minimal and centered
st.markdown("<h1 style='text-align:center;color:#e6eef8;margin-top:12px'>Inventory AI — Beta</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#aebfd0;margin-top:-10px'>Just the avatar. Speak to it.</p>", unsafe_allow_html=True)

# Hidden controls for debug (if you press 'd' key or set SHOW_DEBUG env it will show)
SHOW_DEBUG = os.getenv("SHOW_DEBUG","").lower() in ("1","true","yes")

# UI: the avatar area and mic/upload controls
col1, col2, col3 = st.columns([1,0.5,1])
with col1:
    st.write("")  # left gap

with col2:
    # Avatar + audio playback area will be embedded as a single HTML component below
    st.write("")  # placeholder

    # Upload or record controls
    uploaded = st.file_uploader("Upload short audio (wav/mp3) — or use mic recorders if installed", type=["wav","mp3","m4a"], label_visibility="hidden")
    # Quick text box hidden by default (for debugging)
    typed = st.text_input("", placeholder="(hidden) debug text input", label_visibility="collapsed")

    if st.button("Talk (send)"):
        user_audio = None
        if uploaded:
            user_audio = uploaded.read()

        # if no audio and debug typed text present use typed
        user_text = ""
        if not user_audio and typed:
            user_text = typed

        if not user_audio and not user_text:
            st.warning("Please upload an audio file (or set debug text).")
            st.stop()

        # 1) If we have audio, transcribe with whisper_local behind the scenes (no UI transcript)
        if user_audio:
            st.info("Listening... (local Whisper)")
            try:
                whisper_res = transcribe_audio_bytes(user_audio)
                user_text = whisper_res.get("text","").strip()
            except Exception as e:
                st.error(f"Transcription error: {e}")
                user_text = ""

        # If we still have no text -> reply fallback
        if not user_text:
            answer_text = "Sorry, I didn't catch that. Please speak more clearly."
        else:
            # 2) Query LLM: try OpenRouter (if key present & reachable), else try LOCALAI_URL, else fallback
            answer_text = None
            if OPENROUTER_API_KEY:
                try:
                    url = "https://openrouter.ai/api/v1/chat/completions"
                    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
                    body = {"model": OPENROUTER_MODEL, "messages":[{"role":"user","content": user_text}], "max_tokens":300}
                    r = requests.post(url, headers=headers, json=body, timeout=20)
                    if r.ok:
                        j = r.json()
                        if "choices" in j and len(j["choices"])>0:
                            ch = j["choices"][0]
                            answer_text = ch.get("message", {}).get("content") or ch.get("text") or str(ch)
                        else:
                            answer_text = str(j)
                    else:
                        # OpenRouter returned error -> try local fallback
                        st.info(f"OpenRouter error {r.status_code}; using local fallback.")
                except Exception as e:
                    st.info(f"OpenRouter connection failed: {e} (using local fallback)")

            if not answer_text and LOCALAI_URL:
                try:
                    payload = {"model":"local","prompt":user_text,"max_tokens":300}
                    rr = requests.post(LOCALAI_URL, json=payload, timeout=12)
                    if rr.ok:
                        data = rr.json()
                        if "choices" in data and len(data["choices"])>0:
                            answer_text = data["choices"][0].get("text") or data["choices"][0].get("message",{}).get("content")
                        else:
                            answer_text = str(data)
                    else:
                        st.info("LocalAI returned non-200; using fallback.")
                except Exception as e:
                    st.info(f"LocalAI error: {e}")

            if not answer_text:
                # Final offline fallback: short polite response (you will replace with better local LLM)
                answer_text = f"(offline) I heard: {user_text[:200]}. Install LocalAI or set OPENROUTER_API_KEY for smarter replies."

        # 3) Create TTS audio file (pyttsx3 saves to a wav file), then embed audio+avatar in HTML so mouth animates while audio plays
        try:
            engine = pyttsx3.init()
            # save to temp wav
            fd, wav_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            engine.save_to_file(answer_text, wav_path)
            engine.runAndWait()
            # read bytes and base64 encode
            with open(wav_path, "rb") as f:
                audio_bytes = f.read()
            b64 = base64.b64encode(audio_bytes).decode("utf-8")
            # remove temp file
            try:
                os.remove(wav_path)
            except:
                pass

            # 4) Build minimal avatar HTML + audio tag (audio autoplay). The JS will animate mouth while audio is playing.
            avatar_html = f"""
            <div style="display:flex;align-items:center;justify-content:center;flex-direction:column;height:480px;">
              <div id="avatarArea" style="width:420px;height:420px;display:flex;align-items:center;justify-content:center;">
                <!-- simple SVG humanoid face -->
                <svg id="face" width="380" height="380" viewBox="0 0 380 380">
                  <rect x="0" y="0" width="380" height="380" rx="20" fill="#071029" />
                  <circle cx="190" cy="140" r="85" fill="#ffd9b3" stroke="#00000011" stroke-width="2"/>
                  <circle cx="160" cy="125" r="9" fill="#111"/>
                  <circle cx="220" cy="125" r="9" fill="#111"/>
                  <g id="mouth" transform="translate(190,200)">
                    <ellipse id="mouthEllipse" rx="38" ry="8" fill="#5b0b0b"></ellipse>
                  </g>
                </svg>
              </div>
              <!-- hidden audio (autoplay) -->
              <audio id="respAudio" src="data:audio/wav;base64,{b64}" autoplay></audio>
            </div>

            <script>
            const audio = document.getElementById('respAudio');
            const mouth = document.getElementById('mouthEllipse');
            // simple random-ish mouth animation while audio is playing
            let anim = null;
            function startAnimating() {{
                let last = performance.now();
                anim = setInterval(()=>{{
                    // random intensity while audio plays
                    let intensity = 8 + Math.abs(Math.sin(performance.now()/80))*30 * (Math.random()*0.9 + 0.1);
                    mouth.setAttribute('ry', intensity);
                }}, 60);
            }}
            function stopAnimating() {{
                if (anim) clearInterval(anim);
                mouth.setAttribute('ry', 8);
            }}
            audio.onplay = ()=>{{ startAnimating(); }};
            audio.onended = ()=>{{ stopAnimating(); }};
            audio.onerror = ()=>{{ stopAnimating(); }};
            </script>
            """
            # Render HTML (large)
            st.components.v1.html(avatar_html, height=520)
        except Exception as e:
            st.error(f"TTS/Avatar error: {e}")

with col3:
    st.write("")  # right gap

st.markdown("</div>", unsafe_allow_html=True)

if SHOW_DEBUG:
    st.markdown("---")
    st.write("DEBUG")
    st.write("OPENROUTER_KEY:", "Yes" if OPENROUTER_API_KEY else "No")
    st.write("LOCALAI_URL:", LOCALAI_URL or "(not set)")
