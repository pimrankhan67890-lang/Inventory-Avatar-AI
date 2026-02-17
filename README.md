# AI Inventory — Beta

## Quick local test (Windows PowerShell)

1. Create & activate venv
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

2. Install requirements
   python -m pip install --upgrade pip
   pip install -r requirements.txt

3. Install FFmpeg and add to PATH (required for Whisper)

4. Create .env from .env.example and set OPENROUTER_API_KEY if you have it.

5. Run minimal test:
   streamlit run ai_inventory_optimizer.py

## Optional: Local LLM
- Install Ollama or LocalAI (recommended) for offline answers.
- Set LOCALAI_URL in .env.

## Deploy
- Push to GitHub.
- Connect repository to Streamlit Cloud (add secrets in app settings).
