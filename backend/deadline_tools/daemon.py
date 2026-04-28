"""Background scanner that extracts deadlines from recent email."""

from __future__ import annotations

import argparse
import logging
import time
from typing import Any

from mail_fetch.config import EMAILS_TO_FETCH, validate_config
from mail_fetch.main import get_email_by_uid, get_last_10_emails
from notify.main import send_deadline_to_discord

from .function_calling import DEADLINE_FUNCTION_MODEL, call_deadline_tool
from .store import (
    DEADLINES_FILE,
    load_deadline_store,
    mark_deadline_discord_result,
    save_deadline_store,
    upsert_processed_result,
)

logger = logging.getLogger("deadline_daemon")


def deadline_to_dict(deadline: Any) -> dict[str, Any]:
    """Convert a DeadlineFunctionCall-like object into JSON-serializable data."""
    return {
        "title": deadline.title,
        "due_date": deadline.due_date,
        "source_text": deadline.source_text,
        "action_required": deadline.action_required,
        "confidence": deadline.confidence,
    }


def scan_once(limit: int = EMAILS_TO_FETCH, force: bool = False, post_to_discord: bool = True) -> dict[str, int]:
    """Scan recent email once and extract deadlines for unprocessed messages."""
    missing = validate_config()
    if missing:
        raise RuntimeError(f"Missing mail configuration: {', '.join(missing)}")

    store = load_deadline_store()
    processed = store.setdefault("processed", {})
    latest = get_last_10_emails()

    if isinstance(latest, dict) and "error" in latest:
        raise RuntimeError(latest["error"])

    stats = {
        "seen": 0,
        "skipped": 0,
        "processed": 0,
        "deadlines": 0,
        "discord_sent": 0,
        "discord_failed": 0,
        "errors": 0,
    }

    for preview in latest[:limit]:
        uid = str(preview.get("uid"))
        stats["seen"] += 1

        if not force and uid in processed:
            stats["skipped"] += 1
            continue

        email = get_email_by_uid(uid)
        if isinstance(email, dict) and "error" in email:
            logger.warning("Skipping UID %s: %s", uid, email["error"])
            stats["errors"] += 1
            continue
        if not email:
            logger.warning("Skipping UID %s: email not found", uid)
            stats["errors"] += 1
            continue

        try:
            deadline = call_deadline_tool(email.get("body", ""))
        except Exception as exc:
            logger.warning("Deadline extraction failed for UID %s: %s", uid, exc)
            stats["errors"] += 1
            continue

        deadline_data = deadline_to_dict(deadline) if deadline else None
        deadline_record = upsert_processed_result(
            store,
            uid=uid,
            email=email,
            deadline=deadline_data,
            model=DEADLINE_FUNCTION_MODEL,
        )
        save_deadline_store(store)

        stats["processed"] += 1
        if deadline_data:
            stats["deadlines"] += 1
            logger.info("Extracted deadline for UID %s: %s due %s", uid, deadline.title, deadline.due_date)
            if post_to_discord and deadline_record:
                success, message = send_deadline_to_discord(deadline_record)
                mark_deadline_discord_result(store, uid=uid, success=success, message=message)
                save_deadline_store(store)
                if success:
                    stats["discord_sent"] += 1
                    logger.info("Posted deadline for UID %s to Discord", uid)
                else:
                    stats["discord_failed"] += 1
                    logger.warning("Failed to post deadline for UID %s to Discord: %s", uid, message)
        else:
            logger.info("No deadline found for UID %s", uid)

    return stats


def run_daemon(interval_seconds: int, limit: int, force: bool = False, post_to_discord: bool = True) -> None:
    """Run deadline extraction forever."""
    logger.info("Deadline daemon started. Store: %s", DEADLINES_FILE)
    logger.info("Model: %s", DEADLINE_FUNCTION_MODEL)
    logger.info(
        "Interval: %ss, limit: %s, force: %s, post_to_discord: %s",
        interval_seconds,
        limit,
        force,
        post_to_discord,
    )

    while True:
        try:
            stats = scan_once(limit=limit, force=force, post_to_discord=post_to_discord)
            logger.info("Scan complete: %s", stats)
        except Exception:
            logger.exception("Deadline scan failed")
        time.sleep(interval_seconds)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract email deadlines in the background.")
    parser.add_argument("--once", action="store_true", help="Run one scan and exit.")
    parser.add_argument("--force", action="store_true", help="Reprocess emails even if their UID was seen.")
    parser.add_argument("--no-discord", action="store_true", help="Do not post extracted deadlines to Discord.")
    parser.add_argument("--limit", type=int, default=EMAILS_TO_FETCH, help="Number of recent emails to scan.")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between scans in daemon mode.")
    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    args = build_parser().parse_args()

    if args.once:
        stats = scan_once(limit=args.limit, force=args.force, post_to_discord=not args.no_discord)
        print(stats)
        print(f"Deadline store: {DEADLINES_FILE}")
        return 0

    run_daemon(
        interval_seconds=args.interval,
        limit=args.limit,
        force=args.force,
        post_to_discord=not args.no_discord,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
