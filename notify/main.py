import os
from dotenv import load_dotenv
import requests

# Load .env from the notify directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# Discord Webhook URL from environment variables
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_to_discord(email_data, summary):
    """
    Sends an email summary to a Discord channel via webhook.

    :param email_data: Dictionary containing email metadata (subject, sender, date)
    :param summary: The AI-generated summary text
    :return: Tuple (success: bool, message: str)
    """
    if not DISCORD_WEBHOOK_URL:
        return False, "Discord Webhook URL not configured."

    # Construct a clean embed for Discord
    payload = {
        "embeds": [
            {
                "title": f"📧 New Email Summary: {email_data.get('subject', '(No Subject)')}",
                "color": 3447003, # Blue color
                "fields": [
                    {
                        "name": "From",
                        "value": email_data.get('sender', 'Unknown'),
                        "inline": True
                    },
                    {
                        "name": "Date",
                        "value": email_data.get('date', 'Unknown'),
                        "inline": True
                    },
                    {
                        "name": "Summary",
                        "value": summary or "No summary available.",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "Inbox Broadcast AI"
                }
            }
        ]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        return True, "Successfully sent to Discord."
    except Exception as e:
        return False, f"Error sending to Discord: {str(e)}"

if __name__ == "__main__":
    # Quick manual test
    test_email = {"subject": "Test Subject", "sender": "test@example.com", "date": "Today"}
    test_summary = "This is a test summary."
    success, msg = send_to_discord(test_email, test_summary)
    print(f"Success: {success}, Message: {msg}")
