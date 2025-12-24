import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("LOCALAI_BASE_URL", "http://localhost:8080").rstrip("/")
MODEL = os.getenv("LOCALAI_MODEL", "ggml-gpt4all-j")
FORCE_JSON = os.getenv("FORCE_JSON", "0")


def chat_completion(system_prompt, user_prompt, temperature=0.0):
    url = f"{BASE_URL}/v1/chat/completions"
    payload = {
        "model": MODEL,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if FORCE_JSON == "1":
        payload["response_format"] = {"type": "json_object"}

    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
