# research_tools.py (or utils.py) -- add/replace the ask_ollama_via_cli function

import subprocess
import os
import re
from typing import Tuple

ANSI_RE = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')  # remove ANSI escape sequences

def clean_text_bytes(b: bytes) -> str:
    """Decode bytes to string safely and strip ANSI codes."""
    # decode with replacement for invalid bytes
    s = b.decode('utf-8', errors='replace')
    # remove ANSI escape sequences
    s = ANSI_RE.sub('', s)
    # strip excessive whitespace at ends
    return s.strip()

def ask_ollama_via_cli(prompt: str, model: str = "phi3:mini", timeout: int = 120) -> Tuple[str, str]:
    """
    Ask a local Ollama model using the CLI and return (stdout_clean, stderr_clean).
    - prompt: the input text to the model
    - model: ollama model name
    - timeout: seconds to wait for completion
    """
    # build command
    cmd = ["ollama", "run", model]
    # copy environment and disable color / force dumb terminal so Ollama emits less control codes
    env = os.environ.copy()
    env["TERM"] = "dumb"
    env["FORCE_COLOR"] = "0"
    try:
        # pass prompt via stdin, capture stdout+stderr as bytes
        proc = subprocess.run(
            cmd,
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            timeout=timeout
        )
    except subprocess.TimeoutExpired as e:
        # return empty stdout and the timeout message in stderr
        return "", f"Ollama timed out after {timeout}s"

    stdout_clean = clean_text_bytes(proc.stdout)
    stderr_clean = clean_text_bytes(proc.stderr)

    return stdout_clean, stderr_clean