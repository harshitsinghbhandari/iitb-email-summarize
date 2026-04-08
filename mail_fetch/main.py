import ssl
import logging
from imap_tools import MailBox
from .config import IMAP_SERVER, IMAP_PORT, IMAP_USERNAME, IMAP_PASSWORD, MAILBOX, IGNORE_EMAILS, EMAILS_TO_FETCH

logger = logging.getLogger("mail_fetch")

def _get_imap_context():
    """Helper to create a consistent SSL context for academic networks."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.set_ciphers('DEFAULT@SECLEVEL=1')
    return context

def _handle_imap_error(e, context_msg=""):
    """Centralized IMAP error handling with helpful messages."""
    err_str = str(e).lower()
    if "authenticate" in err_str or "login failed" in err_str:
        msg = "Authentication failed: Please check your IMAP credentials or SSO token."
    elif "connection" in err_str or "timeout" in err_str:
        msg = "Connection failed: Could not reach the IMAP server. Check your internet or VPN."
    else:
        msg = f"IMAP Error: {str(e)}"
    
    logger.error(f"{context_msg} {msg}")
    return msg

def get_last_10_emails():
    """Reads emails from the configured IMAP mailbox, filtering out ignored addresses."""
    try:
        context = _get_imap_context()
        with MailBox(IMAP_SERVER, port=IMAP_PORT, ssl_context=context).login(IMAP_USERNAME, IMAP_PASSWORD, initial_folder=MAILBOX) as mailbox:
            emails = []
            for msg in mailbox.fetch(reverse=True):
                if msg.from_ not in IGNORE_EMAILS:
                    emails.append({
                        "uid": msg.uid,
                        "subject": msg.subject or "(No Subject)",
                        "sender": msg.from_,
                        "date": msg.date.strftime("%b %d, %Y %I:%M %p"),
                        "body": msg.text or msg.html or ""
                    })
                    if len(emails) == EMAILS_TO_FETCH:
                        break
            return emails
    except Exception as e:
        return {"error": _handle_imap_error(e, "While fetching latest emails:")}

def get_all_uids():
    """Returns a list of all available email UIDs in the mailbox."""
    try:
        context = _get_imap_context()
        with MailBox(IMAP_SERVER, port=IMAP_PORT, ssl_context=context).login(IMAP_USERNAME, IMAP_PASSWORD, initial_folder=MAILBOX) as mailbox:
            return [msg.uid for msg in mailbox.fetch()]
    except Exception as e:
        logger.error(f"Error fetching all UIDs: {e}")
        return []

def get_email_by_uid(uid):
    """Fetches a single email by its unique ID."""
    try:
        context = _get_imap_context()
        with MailBox(IMAP_SERVER, port=IMAP_PORT, ssl_context=context).login(IMAP_USERNAME, IMAP_PASSWORD, initial_folder=MAILBOX) as mailbox:
            for msg in mailbox.fetch(f'UID {uid}', limit=1):
                return {
                    "uid": msg.uid,
                    "subject": msg.subject or "(No Subject)",
                    "sender": msg.from_,
                    "date": msg.date.strftime("%b %d, %Y %I:%M %p"),
                    "body": msg.html or msg.text or "No content."
                }
        return None
    except Exception as e:
        err = _handle_imap_error(e, f"While fetching email UID {uid}:")
        return {"error": err}
