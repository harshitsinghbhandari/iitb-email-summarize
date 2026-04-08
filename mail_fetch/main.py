import ssl
from imap_tools import MailBox
from .config import IMAP_SERVER, IMAP_PORT, IMAP_USERNAME, IMAP_PASSWORD, MAILBOX

def get_last_10_emails():
    """Reads emails from the configured IMAP mailbox, filtering out ignored addresses, until 10 are found."""
    try:
        # Create a context that supports older TLS versions if needed
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        # Allow older ciphers and lower security levels often found in academic networks
        context.set_ciphers('DEFAULT@SECLEVEL=1')

        # Connect to the IMAP server and login with the SSL context
        from .config import IGNORE_EMAILS
        with MailBox(IMAP_SERVER, port=IMAP_PORT, ssl_context=context).login(IMAP_USERNAME, IMAP_PASSWORD, initial_folder=MAILBOX) as mailbox:
            emails = []
            # Fetch emails in reverse order (newest first).
            # Since fetch() returns an iterator, we can efficiently loop through all emails
            # and stop as soon as we collect 10 non-ignored ones.
            for msg in mailbox.fetch(reverse=True):
                if msg.from_ not in IGNORE_EMAILS:
                    emails.append({
                        "uid": msg.uid,
                        "subject": msg.subject or "(No Subject)",
                        "sender": msg.from_,
                        "date": msg.date.strftime("%b %d, %Y %I:%M %p"),
                        "body": msg.text or msg.html or ""
                    })
                    if len(emails) == 10:
                        break

            return emails
    except Exception as e:
        print(f"Error reading emails: {e}")
        return []

def get_all_uids():
    """Returns a list of all available email UIDs in the mailbox."""
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT@SECLEVEL=1')

        with MailBox(IMAP_SERVER, port=IMAP_PORT, ssl_context=context).login(IMAP_USERNAME, IMAP_PASSWORD, initial_folder=MAILBOX) as mailbox:
            # fetch() returns an iterator over messages. We just want the UIDs.
            # To get all, we can use mailbox.fetch() without limit
            return [msg.uid for msg in mailbox.fetch()]
    except Exception as e:
        print(f"Error fetching all UIDs: {e}")
        return []

def get_email_by_uid(uid):
    """Fetches a single email by its unique ID."""
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        
        with MailBox(IMAP_SERVER, port=IMAP_PORT, ssl_context=context).login(IMAP_USERNAME, IMAP_PASSWORD, initial_folder=MAILBOX) as mailbox:
            # Search for the specific email by UID
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
        print(f"Error fetching email {uid}: {e}")
        return None
