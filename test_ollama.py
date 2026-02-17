import requests

url = "http://localhost:11434/api/generate"

data = {
    "model": "mistral",
    "prompt": "Explain invoice in one line",
    "stream": False
}

r = requests.post(url, json=data)

print(r.json()["response"])