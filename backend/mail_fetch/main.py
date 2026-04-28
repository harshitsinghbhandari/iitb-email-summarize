import ssl
import logging
from imap_tools import MailBox
from db.store import append_mail_record, utc_now_iso
from .config import (
    IMAP_SERVER,
    IMAP_PORT,
    IMAP_USERNAME,
    IMAP_PASSWORD,
    MAILBOX,
    IGNORE_EMAILS,
    EMAILS_TO_FETCH,
    IMAP_ALLOW_INSECURE_SSL,
)

logger = logging.getLogger("mail_fetch")


def _get_imap_context():
    """Create an SSL context for IMAP connections."""
    context = ssl.create_default_context()
    if IMAP_ALLOW_INSECURE_SSL:
        logger.warning("IMAP_ALLOW_INSECURE_SSL is enabled; certificate verification is disabled.")
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers("DEFAULT@SECLEVEL=1")
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


def _normalize_headers(headers):
    normalized = {}
    if not isinstance(headers, dict):
        return normalized

    for key, value in headers.items():
        if isinstance(value, (list, tuple)):
            normalized[str(key)] = [str(item) for item in value]
        elif value is None:
            normalized[str(key)] = []
        else:
            normalized[str(key)] = [str(value)]
    return normalized


def _attachment_metadata(message):
    metadata = []
    for attachment in message.attachments:
        metadata.append(
            {
                "filename": getattr(attachment, "filename", None),
                "content_type": getattr(attachment, "content_type", None),
                "size": getattr(attachment, "size", None),
                "content_id": getattr(attachment, "content_id", None),
            }
        )
    return metadata


def message_to_db_record(message):
    """Return the full DB record shape for a fetched IMAP message."""
    return {
        "uid": str(message.uid),
        "mailbox": MAILBOX,
        "fetched_at": utc_now_iso(),
        "subject": message.subject or "(No Subject)",
        "sender": message.from_,
        "to": message.to,
        "cc": message.cc,
        "bcc": message.bcc,
        "reply_to": message.reply_to,
        "date": message.date.isoformat() if message.date else None,
        "date_raw": message.date_str,
        "flags": list(message.flags or []),
        "size": message.size,
        "size_rfc822": message.size_rfc822,
        "headers": _normalize_headers(message.headers),
        "text": message.text or "",
        "html": message.html or "",
        "attachments": _attachment_metadata(message),
    }


def persist_message(message) -> None:
    """Persist a fetched message to the DB-backed mail JSONL store."""
    try:
        append_mail_record(message_to_db_record(message))
    except Exception:
        logger.exception("Failed to persist fetched email UID %s", getattr(message, "uid", "?"))


def get_last_10_emails():
    """Reads emails from the configured IMAP mailbox, filtering out ignored addresses."""
    try:
        context = _get_imap_context()
        with MailBox(IMAP_SERVER, port=IMAP_PORT, ssl_context=context).login(
            IMAP_USERNAME, IMAP_PASSWORD, initial_folder=MAILBOX
        ) as mailbox:
            emails = []
            for msg in mailbox.fetch(reverse=True):
                if msg.from_.lower() not in IGNORE_EMAILS:
                    persist_message(msg)
                    emails.append(
                        {
                            "uid": msg.uid,
                            "subject": msg.subject or "(No Subject)",
                            "sender": msg.from_,
                            "date": msg.date.strftime("%b %d, %Y %I:%M %p"),
                            "body": msg.text or msg.html or "",
                        }
                    )
                    if len(emails) == EMAILS_TO_FETCH:
                        break
            return emails
    except Exception as e:
        return {"error": _handle_imap_error(e, "While fetching latest emails:")}


def get_all_uids():
    """Returns a list of all available email UIDs in the mailbox."""
    try:
        context = _get_imap_context()
        with MailBox(IMAP_SERVER, port=IMAP_PORT, ssl_context=context).login(
            IMAP_USERNAME, IMAP_PASSWORD, initial_folder=MAILBOX
        ) as mailbox:
            return [msg.uid for msg in mailbox.fetch()]
    except Exception as e:
        logger.error(f"Error fetching all UIDs: {e}")
        return []


def get_email_by_uid(uid):
    """Fetches a single email by its unique ID."""
    try:
        context = _get_imap_context()
        with MailBox(IMAP_SERVER, port=IMAP_PORT, ssl_context=context).login(
            IMAP_USERNAME, IMAP_PASSWORD, initial_folder=MAILBOX
        ) as mailbox:
            for msg in mailbox.fetch(f"UID {uid}", limit=1):
                persist_message(msg)
                return {
                    "uid": msg.uid,
                    "subject": msg.subject or "(No Subject)",
                    "sender": msg.from_,
                    "date": msg.date.strftime("%b %d, %Y %I:%M %p"),
                    "body": msg.text or "No content.",
                }
        return None
    except Exception as e:
        err = _handle_imap_error(e, f"While fetching email UID {uid}:")
        return {"error": err}
