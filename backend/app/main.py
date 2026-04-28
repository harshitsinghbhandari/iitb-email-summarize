import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from mail_fetch.config import validate_config
from mail_fetch.main import get_all_uids, get_email_by_uid, get_last_10_emails
from notify.main import send_to_discord
from summarize_mail.main import get_summary, load_summaries

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")

app = FastAPI(title="Inbox Broadcast API")

# The frontend (Vite + React) runs on a separate origin in development.
# Override via CORS_ALLOW_ORIGINS=https://prod.example.com,...
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
_allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", _default_origins).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OFFLINE_FIXTURE_PATH = REPO_ROOT / "mail_harvest" / "sanitized_emails.json"
OFFLINE_FIXTURE_COMMAND = "python backend/scripts/prepare_mail_fixture.py"


@app.get("/api/health")
async def healthcheck() -> dict:
    return {"status": "ok"}


def load_offline_fixture() -> dict:
    if not OFFLINE_FIXTURE_PATH.exists():
        raise FileNotFoundError(f"Offline fixture not found at {OFFLINE_FIXTURE_PATH}")

    with OFFLINE_FIXTURE_PATH.open("r", encoding="utf-8") as f:
        fixture = json.load(f)

    if not isinstance(fixture, dict) or not isinstance(fixture.get("emails"), list):
        raise ValueError(f"Offline fixture has an invalid shape: {OFFLINE_FIXTURE_PATH}")

    return fixture


def offline_fixture_error(message: str, status_code: int = 404) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "message": message,
            "command": OFFLINE_FIXTURE_COMMAND,
        },
    )


@app.get("/api/offline/emails")
async def api_get_offline_emails():
    """Return offline fixture email list data without full bodies."""
    try:
        fixture = load_offline_fixture()
    except FileNotFoundError:
        return offline_fixture_error(
            "Offline fixture not found. Run the fixture preparation command and refresh this page."
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        logger.exception("Offline fixture could not be loaded")
        return offline_fixture_error(f"Offline fixture could not be loaded: {exc}", status_code=500)

    emails = []
    for email in fixture["emails"]:
        if not isinstance(email, dict):
            continue
        emails.append({key: value for key, value in email.items() if key not in {"body", "html_body"}})

    return {
        "status": "success",
        "manifest": fixture.get("manifest", {}),
        "data": emails,
    }


@app.get("/api/offline/email/{uid}")
async def api_get_offline_email(uid: str):
    """Return a single offline fixture email including its normalized body."""
    try:
        fixture = load_offline_fixture()
    except FileNotFoundError:
        return offline_fixture_error(
            "Offline fixture not found. Run the fixture preparation command and refresh this page."
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        logger.exception("Offline fixture could not be loaded")
        return offline_fixture_error(f"Offline fixture could not be loaded: {exc}", status_code=500)

    for email in fixture["emails"]:
        if isinstance(email, dict) and str(email.get("uid")) == str(uid):
            return {"status": "success", "data": email}

    return JSONResponse(
        status_code=404,
        content={"status": "error", "message": f"Offline email UID {uid} not found."},
    )

@app.get("/api/emails")
async def api_get_emails():
    """Fetch and return the last 10 emails as JSON."""
    # Validate config first
    missing = validate_config()
    if missing:
        return {"status": "error", "message": f"Missing configuration: {', '.join(missing)}. Please check your .env file."}

    emails = get_last_10_emails()
    
    # If emails contains an error dictionary, return it
    if isinstance(emails, dict) and "error" in emails:
        return emails

    # Process emails for frontend viewing (limit snippet max length)
    for em in emails:
        clean_body = em.get("body", "").replace("\r", " ").replace("\n", " ").strip()
        em["snippet"] = clean_body[:120] + ("..." if len(clean_body) > 120 else "")

    return {"status": "success", "data": emails}

@app.get("/api/email/{uid}/summary")
async def api_get_summary(uid: str):
    """Fetch email, summarize it, and return summary."""
    email = get_email_by_uid(uid)
    
    if isinstance(email, dict) and "error" in email:
        return {"status": "error", "message": email["error"]}
    
    if email:
        summary = get_summary(uid, email['body'])
        # If summary is an error message (e.g., Ollama offline), it's still returned as a summary 
        # text to be rendered in the UI, rather than a 500 error.
        return {"status": "success", "summary": summary}
    
    return {"status": "error", "message": "Email not found"}

@app.get("/api/email/{uid}")
async def api_get_single_email(uid: str):
    """Fetch and return a single email by UID including summary."""
    email = get_email_by_uid(uid)
    
    if isinstance(email, dict) and "error" in email:
        return {"status": "error", "message": email["error"]}
        
    if email:
        email["summary"] = get_summary(uid, email['body'])
        return {"status": "success", "data": email}
    
    return {"status": "error", "message": "Email not found"}

@app.post("/api/email/{uid}/discord")
async def api_send_to_discord(uid: str):
    """Send an email summary to Discord."""
    email = get_email_by_uid(uid)
    if isinstance(email, dict) and "error" in email:
        return {"status": "error", "message": email["error"]}
        
    if not email:
        return {"status": "error", "message": "Email not found"}

    summary = get_summary(uid, email['body'])
    
    # Don't send summaries that are actually error messages
    if "offline" in summary.lower() or "error" in summary.lower():
        return {"status": "error", "message": f"Cannot send to Discord: {summary}"}

    success, message = send_to_discord(email, summary)

    if success:
        return {"status": "success", "message": message}
    return {"status": "error", "message": message}

@app.get("/api/summarize-pending")
async def api_summarize_pending():
    """Prioritized batch summarization of pending emails."""
    try:
        all_uids = get_all_uids()
        summaries = load_summaries()["summaries"]

        pending_uids = [uid for uid in all_uids if str(uid) not in summaries]
        pending_uids.sort(key=lambda x: int(x) if str(x).isdigit() else x)

        count = 0
        for uid in pending_uids:
            email = get_email_by_uid(uid)
            if email and not (isinstance(email, dict) and "error" in email):
                get_summary(uid, email['body'])
                count += 1

        return {"status": "success", "summarized_count": count, "total_pending_before": len(pending_uids)}
    except Exception as e:
        logger.exception("Batch summarization failed")
        return {"status": "error", "message": str(e)}
