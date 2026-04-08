from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from mail_fetch.main import get_last_10_emails, get_email_by_uid, get_all_uids
from summarize_mail.main import get_summary, load_summaries
from notify.main import send_to_discord
from mail_fetch.config import validate_config
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("app")

app = FastAPI(title="Live Mail Viewer")

# Setup Jinja2 templates directory
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    """Serve the stunning frontend web interface."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/email/{uid}", response_class=HTMLResponse)
async def email_detail(request: Request, uid: str):
    """Serve the detail page for a specific email."""
    return templates.TemplateResponse(request=request, name="detail.html", context={"uid": uid})

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
        summaries = load_summaries()

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
