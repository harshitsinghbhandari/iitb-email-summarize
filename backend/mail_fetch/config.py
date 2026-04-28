import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# Setup basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mail_fetch_config")

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT_DIR = PACKAGE_DIR.parents[1]

# Load a repo-level .env first if present, then the mail_fetch-specific file
# documented in README.md.
load_dotenv(ROOT_DIR / ".env")
load_dotenv(PACKAGE_DIR / ".env", override=True)


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
IGNORE_EMAILS = [
    email.strip().lower() for email in os.getenv("IGNORE_EMAILS", "").split(",") if email.strip()
]
EMAILS_TO_FETCH = 10
IMAP_ALLOW_INSECURE_SSL = os.getenv("IMAP_ALLOW_INSECURE_SSL", "").lower() in {"1", "true", "yes"}
