"""JSON persistence for Inbox Broadcast runtime state."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = Path(os.getenv("DB_RUNTIME_DIR", ROOT_DIR / "db" / "runtime"))
MAIL_HARVEST_DIR = Path(os.getenv("MAIL_HARVEST_DIR", RUNTIME_DIR / "mail_harvest"))
MAIL_RECORDS_FILE = Path(os.getenv("MAIL_RECORDS_FILE", MAIL_HARVEST_DIR / "emails.jsonl"))
MAIL_HARVEST_STATE_FILE = Path(
    os.getenv("MAIL_HARVEST_STATE_FILE", MAIL_HARVEST_DIR / "state.json")
)
OFFLINE_FIXTURE_FILE = Path(
    os.getenv("OFFLINE_FIXTURE_FILE", MAIL_HARVEST_DIR / "sanitized_emails.json")
)
DEADLINES_FILE = Path(os.getenv("DEADLINES_FILE", RUNTIME_DIR / "deadlines.json"))
SUMMARIES_FILE = Path(os.getenv("SUMMARIES_FILE", RUNTIME_DIR / "summaries.json"))
LEGACY_DEADLINES_FILE = ROOT_DIR / "deadlines.json"
LEGACY_SUMMARIES_FILE = ROOT_DIR / "summaries.json"
LEGACY_MAIL_RECORDS_FILE = ROOT_DIR / "mail_harvest" / "emails.jsonl"


def utc_now_iso() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def append_mail_record(record: dict[str, Any], path: Path = MAIL_RECORDS_FILE) -> None:
    """Append one fetched mail record to the mail JSONL store."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        f.write("\n")


def write_mail_harvest_state(
    state: dict[str, Any], path: Path = MAIL_HARVEST_STATE_FILE
) -> None:
    """Persist mail harvest state."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def empty_store() -> dict[str, Any]:
    """Return an empty deadline store."""
    return {
        "version": 1,
        "updated_at": None,
        "processed": {},
        "deadlines": [],
    }


def load_deadline_store(path: Path = DEADLINES_FILE) -> dict[str, Any]:
    """Load the deadline store, tolerating missing or malformed files."""
    if path == DEADLINES_FILE and not path.exists() and LEGACY_DEADLINES_FILE.exists():
        path = LEGACY_DEADLINES_FILE

    if not path.exists():
        return empty_store()

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return empty_store()

    if not isinstance(data, dict):
        return empty_store()

    store = empty_store()
    store.update(data)
    if not isinstance(store.get("processed"), dict):
        store["processed"] = {}
    if not isinstance(store.get("deadlines"), list):
        store["deadlines"] = []
    return store


def save_deadline_store(store: dict[str, Any], path: Path = DEADLINES_FILE) -> None:
    """Persist the deadline store."""
    store["updated_at"] = utc_now_iso()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, sort_keys=True)


def upsert_processed_result(
    store: dict[str, Any],
    *,
    uid: str,
    email: dict[str, Any],
    deadline: dict[str, Any] | None,
    model: str,
) -> dict[str, Any] | None:
    """Record one processed email and optional deadline extraction."""
    uid = str(uid)
    processed_at = utc_now_iso()
    store.setdefault("processed", {})[uid] = {
        "processed_at": processed_at,
        "has_deadline": deadline is not None,
        "model": model,
    }

    if deadline is None:
        return None

    deadlines = [item for item in store.setdefault("deadlines", []) if str(item.get("uid")) != uid]
    deadline_record = {
        "uid": uid,
        "subject": email.get("subject", "(No Subject)"),
        "sender": email.get("sender", "Unknown"),
        "email_date": email.get("date", "Unknown"),
        "processed_at": processed_at,
        "model": model,
        "discord_sent_at": None,
        "discord_error": None,
        **deadline,
    }
    deadlines.append(deadline_record)
    deadlines.sort(key=lambda item: (item.get("due_date", ""), item.get("title", "")))
    store["deadlines"] = deadlines
    return deadline_record


def mark_deadline_discord_result(
    store: dict[str, Any],
    *,
    uid: str,
    success: bool,
    message: str,
) -> None:
    """Record Discord delivery status for a deadline UID."""
    for deadline in store.setdefault("deadlines", []):
        if str(deadline.get("uid")) != str(uid):
            continue
        if success:
            deadline["discord_sent_at"] = utc_now_iso()
            deadline["discord_error"] = None
        else:
            deadline["discord_error"] = message
        return
