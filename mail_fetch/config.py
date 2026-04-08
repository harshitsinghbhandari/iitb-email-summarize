import os
from dotenv import load_dotenv

load_dotenv()

# Configure your IMAP settings here or via environment variables
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
IMAP_USERNAME = os.getenv("IMAP_USERNAME", "your_email@gmail.com")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "your_app_password")
MAILBOX = os.getenv("MAILBOX", "INBOX")
IGNORE_EMAILS = os.getenv("IGNORE_EMAILS", "").split(",") if os.getenv("IGNORE_EMAILS") else []
EMAILS_TO_FETCH = 10
