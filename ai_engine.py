import os
import json
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv not installed; proceed and rely on environment variables
    pass

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

API_URL = "https://api.deepseek.com/v1/chat/completions"


def call_ai(prompt, temperature=0.3, max_tokens=1500):
    """Call the DeepSeek API. Imports `requests` lazily so the module can be imported even if
    `requests` isn't installed; a clear RuntimeError is raised only when the function is used.
    """
    if not DEEPSEEK_API_KEY:
        raise ValueError("Missing API key")

    try:
        import requests
    except Exception as e:
        raise RuntimeError("The 'requests' package is required to call the AI API. Install it with 'pip install requests'.") from e

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]

    content = content.replace("```json", "").replace("```", "").strip()

    return content