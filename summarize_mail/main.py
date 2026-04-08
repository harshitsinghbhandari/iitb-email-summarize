import requests
import json
import os
from .config import MODEL, OLLAMA_BASE_URL
from .PROMPT import SYSTEM_PROMPT

SUMMARIES_FILE = "summaries.json"

def load_summaries():
    """Loads summaries from the JSON cache file."""
    if not os.path.exists(SUMMARIES_FILE):
        return {}
    try:
        with open(SUMMARIES_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading summaries: {e}")
        return {}

def save_summaries(summaries):
    """Saves summaries to the JSON cache file."""
    try:
        with open(SUMMARIES_FILE, "w") as f:
            json.dump(summaries, f, indent=2)
    except Exception as e:
        print(f"Error saving summaries: {e}")

def summarize_content(content):
    """
    Takes a string content and returns a summary using Ollama.
    The model is unaware that the content is an email.
    """
    if not content or len(content.strip()) == 0:
        return "No content to summarize."

    url = f"{OLLAMA_BASE_URL}/api/generate"

    payload = {
        "model": MODEL,
        "prompt": f"{SYSTEM_PROMPT}\n\nContent to summarize:\n{content}\n\nSummary:",
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
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
    summaries = load_summaries()
    uid_str = str(uid)

    if uid_str in summaries:
        return summaries[uid_str]

    summary = summarize_content(body)
    summaries[uid_str] = summary
    save_summaries(summaries)
    return summary

if __name__ == "__main__":
    # Quick test
    test_text = "The quick brown fox jumps over the lazy dog many times to demonstrate agility."
    print("Testing Summary:")
    print(summarize_content(test_text))
