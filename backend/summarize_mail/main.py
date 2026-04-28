import requests
import json
import os
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from .config import MODEL, OLLAMA_BASE_URL
from .PROMPT import SYSTEM_PROMPT

logger = logging.getLogger("summarize_mail")
ROOT_DIR = Path(__file__).resolve().parents[2]
SUMMARIES_FILE = Path(os.getenv("SUMMARIES_FILE", ROOT_DIR / "summaries.json"))


def get_prompt_hash():
    """Computes a hash of the current system prompt."""
    return hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()


def load_summaries():
    """
    Loads summaries from the JSON cache file.
    If the system prompt has changed, the cache is invalidated and reset.
    """
    if not SUMMARIES_FILE.exists():
        return {"prompt_hash": get_prompt_hash(), "summaries": {}}

    try:
        with SUMMARIES_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict) or "prompt_hash" not in data or "summaries" not in data:
            return {"prompt_hash": get_prompt_hash(), "summaries": {}}

        current_hash = get_prompt_hash()
        if data["prompt_hash"] != current_hash:
            logger.info("System prompt changed. Invalidating summary cache...")
            return {"prompt_hash": current_hash, "summaries": {}}

        return data
    except Exception as e:
        logger.error(f"Error loading summaries: {e}")
        return {"prompt_hash": get_prompt_hash(), "summaries": {}}


def save_summaries(data):
    """Saves the cache data (including prompt hash) to the JSON file."""
    try:
        data["prompt_hash"] = get_prompt_hash()
        SUMMARIES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with SUMMARIES_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving summaries: {e}")


def summarize_content(content):
    """
    Takes a string content and returns a summary using Ollama.
    """
    if not content or len(content.strip()) == 0:
        return "No content to summarize."

    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist).strftime("%H:%M:%S %d/%m/%y")

    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": MODEL,
        "prompt": f"Current Time: {now}\n\n{SYSTEM_PROMPT}\n\nContent to summarize:\n{content}\n\nSummary:",
        "stream": False,
        "think": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "Could not generate summary.").strip()
    except requests.exceptions.ConnectionError:
        return "AI Summarizer is offline. Please ensure Ollama is running."
    except requests.exceptions.HTTPError as e:
        return f"AI Summarizer error: {e.response.status_code}. Check if model {MODEL} is pulled."
    except Exception as e:
        logger.error(f"Unexpected error during summarization: {e}")
        return f"An unexpected error occurred: {str(e)}"


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

    # Only cache successful summaries, not error messages
    if "offline" not in summary.lower() and "error" not in summary.lower():
        summaries[uid_str] = summary
        save_summaries(data)

    return summary


if __name__ == "__main__":
    test_text = "The quick brown fox jumps over the lazy dog many times to demonstrate agility."
    print("Testing Summary:")
    print(summarize_content(test_text))
