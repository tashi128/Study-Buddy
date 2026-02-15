import re
import json
from datetime import datetime

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def calculate_progress_score(correct, total):
    return round((correct / total) * 100, 1) if total else 0

def safe_json_loads(text, default=None):
    try:
        return json.loads(text)
    except:
        return default or {}
def extract_json_from_text(text: str):
    """
    Extract valid JSON from AI responses
    Handles ```json blocks and raw JSON
    """
    if not text:
        return []

    # Remove markdown code fences
    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    # Try to locate JSON array
    start = text.find("[")
    end = text.rfind("]") + 1

    if start != -1 and end != -1:
        text = text[start:end]

    try:
        return json.loads(text)
    except Exception:
        return []
