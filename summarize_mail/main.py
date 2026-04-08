import requests
import json
import os
import hashlib
from datetime import datetime, timedelta, timezone
from .config import MODEL, OLLAMA_BASE_URL
from .PROMPT import SYSTEM_PROMPT

SUMMARIES_FILE = "summaries.json"

def get_prompt_hash():
    """Computes a hash of the current system prompt."""
    return hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()

def load_summaries():
    """
    Loads summaries from the JSON cache file.
    If the system prompt has changed, the cache is invalidated and reset.
    """
    if not os.path.exists(SUMMARIES_FILE):
        return {"prompt_hash": get_prompt_hash(), "summaries": {}}

    try:
        with open(SUMMARIES_FILE, "r") as f:
            data = json.load(f)

        # Ensure data is in the expected format
        if not isinstance(data, dict) or "prompt_hash" not in data or "summaries" not in data:
            return {"prompt_hash": get_prompt_hash(), "summaries": {}}

        # Check if the system prompt has changed
        current_hash = get_prompt_hash()
        if data["prompt_hash"] != current_hash:
            print("System prompt changed. Invalidating summary cache...")
            return {"prompt_hash": current_hash, "summaries": {}}

        return data
    except Exception as e:
        print(f"Error loading summaries: {e}")
        return {"prompt_hash": get_prompt_hash(), "summaries": {}}

def save_summaries(data):
    """Saves the cache data (including prompt hash) to the JSON file."""
    try:
        # Always ensure the current prompt hash is saved
        data["prompt_hash"] = get_prompt_hash()
        with open(SUMMARIES_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving summaries: {e}")

def summarize_content(content):
    """
    Takes a string content and returns a summary using Ollama.
    The model is unaware that the content is an email.
    """
    if not content or len(content.strip()) == 0:
        return "No content to summarize."

    # Get current time in GMT+5:30
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist).strftime("%H:%M:%S %d/%m/%y")

    url = f"{OLLAMA_BASE_URL}/api/generate"

    payload = {
        "model": MODEL,
        "prompt": f"Current Time: {now}\n\n{SYSTEM_PROMPT}\n\nContent to summarize:\n{content}\n\nSummary:",
        "stream": False,
        "think": False
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "Could not generate summary.").strip()
    except Exception as e:
        return f"Error connecting to Ollama: {str(e)}"

def get_summary(uid, body):
    """
    Returns the summary for a given email UID.
    Uses cache if available, otherwise generates a new summary and caches it.
    """
    data = load_summaries()
    summaries = data["summaries"]
    uid_str = str(uid)

    if uid_str in summaries:
        return summaries[uid_str]

    summary = summarize_content(body)
    summaries[uid_str] = summary
    save_summaries(data)
    return summary

if __name__ == "__main__":
    # Quick test
    test_text = "The quick brown fox jumps over the lazy dog many times to demonstrate agility."
    print("Testing Summary:")
    print(summarize_content(test_text))
