import os
import logging
from dotenv import load_dotenv
import requests
from pathlib import Path

logger = logging.getLogger("notify")

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT_DIR = PACKAGE_DIR.parents[1]

# Load a repo-level .env first if present, then the notify-specific file.
load_dotenv(ROOT_DIR / ".env")
load_dotenv(PACKAGE_DIR / ".env", override=True)

# Discord Webhook URL from environment variables
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def send_to_discord(email_data, summary):
    """
    Sends an email summary to a Discord channel via webhook.
    """
    if not DISCORD_WEBHOOK_URL:
        logger.warning("Discord Webhook URL not configured in .env")
        return False, "Discord Webhook URL not configured. Please check your .env file."

    payload = {
        "embeds": [
            {
                "title": f"📧 New Email Summary: {email_data.get('subject', '(No Subject)')}",
                "color": 3447003,  # Blue color
                "fields": [
                    {"name": "From", "value": email_data.get("sender", "Unknown"), "inline": True},
                    {"name": "Date", "value": email_data.get("date", "Unknown"), "inline": True},
                    {
                        "name": "Summary",
                        "value": summary or "No summary available.",
                        "inline": False,
                    },
                ],
                "footer": {"text": "Inbox Broadcast AI"},
            }
        ]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        return True, "Successfully sent to Discord."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return False, "Discord Webhook URL is invalid (404 Not Found)."
        return False, f"Discord API Error: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Error sending to Discord: {e}")
        return False, f"Failed to send to Discord: {str(e)}"


def send_deadline_to_discord(deadline_data):
    """
    Sends an extracted email deadline to a Discord channel via webhook.
    """
    if not DISCORD_WEBHOOK_URL:
        logger.warning("Discord Webhook URL not configured in .env")
        return False, "Discord Webhook URL not configured. Please check your .env file."

    payload = {
        "embeds": [
            {
                "title": f"Deadline: {deadline_data.get('title', 'Untitled deadline')}",
                "color": 15158332,
                "fields": [
                    {
                        "name": "Due",
                        "value": deadline_data.get("due_date", "Unknown"),
                        "inline": True,
                    },
                    {
                        "name": "From",
                        "value": deadline_data.get("sender", "Unknown"),
                        "inline": True,
                    },
                    {
                        "name": "Email",
                        "value": deadline_data.get("subject", "(No Subject)"),
                        "inline": False,
                    },
                    {
                        "name": "Evidence",
                        "value": deadline_data.get("source_text", "No source text captured.")[
                            :1000
                        ],
                        "inline": False,
                    },
                ],
                "footer": {
                    "text": f"Inbox Broadcast Deadlines | UID {deadline_data.get('uid', 'unknown')}"
                },
            }
        ]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        return True, "Successfully sent deadline to Discord."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return False, "Discord Webhook URL is invalid (404 Not Found)."
        return False, f"Discord API Error: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Error sending deadline to Discord: {e}")
        return False, f"Failed to send deadline to Discord: {str(e)}"


if __name__ == "__main__":
    test_email = {"subject": "Test Subject", "sender": "test@example.com", "date": "Today"}
    test_summary = "This is a test summary."
    success, msg = send_to_discord(test_email, test_summary)
    print(f"Success: {success}, Message: {msg}")
