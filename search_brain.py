# search_brain.py
import os, textwrap, subprocess, shlex, requests
from duckduckgo_search import ddg

OLLAMA_CLI = shutil = None
try:
    import shutil
except:
    pass

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "arcee-trinity-large-preview")
LOCALAI_URL = os.getenv("LOCALAI_URL", "http://localhost:8080/v1/completions")
LOCALAI_MODEL = os.getenv("LOCALAI_MODEL", "gpt-4o-mini")

def web_search(query, k=4):
    try:
        res = ddg(query, max_results=k)
        return res or []
    except Exception as e:
        print("Web search failed:", e)
        return []

def build_research_prompt(query, results):
    lines = []
    lines.append("You are a concise research assistant. Answer using the web results and cite them.")
    lines.append(f"User: {query}")
    lines.append("")
    lines.append("Results:")
    for i,r in enumerate(results,1):
        title = r.get("title","")
        body = r.get("body","")
        href = r.get("href","")
        snippet = textwrap.shorten(body or "", width=220, placeholder="...")
        lines.append(f"{i}. {title}\n{snippet}\n{href}")
    lines.append("")
    lines.append("Tasks:\n1) Give a short answer (4-8 sentences). 2) Mention which results support the claims in [1],[2] format.\n3) Give 2 recommended next steps.")
    return "\n".join(lines)

def call_openrouter(prompt):
    if not OPENROUTER_API_KEY:
        return None
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    body = {"model": OPENROUTER_MODEL, "messages":[{"role":"user","content":prompt}], "max_tokens":600}
    try:
        r = requests.post(url, headers=headers, json=body, timeout=20)
        r.raise_for_status()
        j = r.json()
        choice = j.get("choices",[{}])[0]
        return choice.get("message", {}).get("content") or choice.get("text") or str(j)
    except Exception as e:
        return f"(OpenRouter error) {e}"

def call_localai(prompt):
    # best-effort call to LocalAI/other local endpoints
    payload = {"model": LOCALAI_MODEL, "prompt": prompt, "max_tokens": 500}
    try:
        r = requests.post(LOCALAI_URL, json=payload, timeout=15)
        j = r.json()
        if "choices" in j and j["choices"]:
            return j["choices"][0].get("text") or j["choices"][0].get("message", {}).get("content")
        return str(j)
    except Exception as e:
        return f"(LocalAI error) {e}"

def ask_brain(query):
    results = web_search(query, k=4)
    if not results:
        return "No web results found. Try different keywords."
    prompt = build_research_prompt(query, results)
    # prefer OpenRouter
    if OPENROUTER_API_KEY:
        out = call_openrouter(prompt)
        if out and not out.lower().startswith("(openrouter error)"):
            return out
    # fallback local
    out = call_localai(prompt)
    return out or "No answer."
