import os
from dotenv import load_dotenv
import logging

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mail_fetch_config")

load_dotenv()

def validate_config():
    """
    Validates that all required IMAP configurations are present.
    Returns a list of missing variables.
    """
    required = ["IMAP_SERVER", "IMAP_USERNAME", "IMAP_PASSWORD"]
    missing = [var for var in required if not os.getenv(var)]
    return missing

IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.iitb.ac.in")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
IMAP_USERNAME = os.getenv("IMAP_USERNAME")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")
MAILBOX = os.getenv("MAILBOX", "INBOX")
IGNORE_EMAILS = os.getenv("IGNORE_EMAILS", "").split(",") if os.getenv("IGNORE_EMAILS") else []
EMAILS_TO_FETCH = 10
