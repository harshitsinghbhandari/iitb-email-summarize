#!/usr/bin/env python3
"""Harvest recent IMAP emails in throttled batches for offline testing."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import random
import sys
import time
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from imap_tools import MailBox  # noqa: E402

from mail_fetch.config import (  # noqa: E402
    IMAP_PASSWORD,
    IMAP_PORT,
    IMAP_SERVER,
    IMAP_USERNAME,
    MAILBOX,
    validate_config,
)
from mail_fetch.main import _get_imap_context  # noqa: E402

DEFAULT_OUTPUT_DIR = REPO_ROOT / "mail_harvest"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_existing_uids(jsonl_path: Path) -> set[str]:
    if not jsonl_path.exists():
        return set()

    uids: set[str] = set()
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                uid = json.loads(line).get("uid")
            except json.JSONDecodeError:
                continue
            if uid is not None:
                uids.add(str(uid))
    return uids


def normalize_headers(headers: Any) -> dict[str, list[str]]:
    normalized: dict[str, list[str]] = {}
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


def attachment_metadata(message: Any) -> list[dict[str, Any]]:
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


def message_to_record(message: Any) -> dict[str, Any]:
    return {
        "uid": str(message.uid),
        "mailbox": MAILBOX,
        "fetched_at": utc_now(),
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
        "headers": normalize_headers(message.headers),
        "text": message.text or "",
        "html": message.html or "",
        "attachments": attachment_metadata(message),
    }


def append_record(jsonl_path: Path, record: dict[str, Any]) -> None:
    with jsonl_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        f.write("\n")


def write_state(state_path: Path, state: dict[str, Any]) -> None:
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def chunks(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def fetch_batch(mailbox: MailBox, batch_uids: list[str]) -> list[Any]:
    criteria = f"UID {','.join(batch_uids)}"
    return list(mailbox.fetch(criteria, mark_seen=False, bulk=True))


def fetch_individual(mailbox: MailBox, uid: str) -> Any | None:
    for message in mailbox.fetch(f"UID {uid}", mark_seen=False, limit=1):
        return message
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch recent IMAP emails in small randomized batches for offline testing."
    )
    parser.add_argument("--target", type=int, default=100, help="Number of newest UIDs to harvest.")
    parser.add_argument("--batch-size", type=int, default=10, help="Full emails to fetch per batch.")
    parser.add_argument("--base-delay", type=float, default=30, help="Base delay between batches in seconds.")
    parser.add_argument("--jitter", type=float, default=20, help="Plus/minus randomized delay in seconds.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for harvested data.")
    parser.add_argument("--no-sleep", action="store_true", help="Disable sleeping between batches for tests.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    missing = validate_config()
    if missing:
        print(f"Missing mail configuration: {', '.join(missing)}")
        return 1

    if args.target <= 0 or args.batch_size <= 0:
        print("--target and --batch-size must be positive")
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = args.output_dir / "emails.jsonl"
    state_path = args.output_dir / "state.json"

    existing_uids = read_existing_uids(jsonl_path)
    print(f"Output: {jsonl_path}")
    print(f"Already harvested: {len(existing_uids)} UID(s)")
    print(f"Connecting to {IMAP_SERVER}:{IMAP_PORT} mailbox={MAILBOX}")

    context = _get_imap_context()
    state: dict[str, Any] = {
        "started_at": utc_now(),
        "target": args.target,
        "batch_size": args.batch_size,
        "base_delay": args.base_delay,
        "jitter": args.jitter,
        "output": str(jsonl_path),
        "batches": [],
    }

    with MailBox(IMAP_SERVER, port=IMAP_PORT, ssl_context=context).login(
        IMAP_USERNAME,
        IMAP_PASSWORD,
        initial_folder=MAILBOX,
    ) as mailbox:
        all_uids = mailbox.uids("ALL")
        target_uids = list(reversed(all_uids[-args.target :]))
        pending_uids = [str(uid) for uid in target_uids if str(uid) not in existing_uids]

        state["candidate_uids"] = len(target_uids)
        state["pending_uids"] = len(pending_uids)
        write_state(state_path, state)

        print(f"Newest UID candidates: {len(target_uids)}")
        print(f"Pending full fetches: {len(pending_uids)}")

        if not pending_uids:
            print("Nothing to do. All target UIDs are already harvested.")
            return 0

        batches = chunks(pending_uids, args.batch_size)
        for batch_index, batch_uids in enumerate(batches, start=1):
            print(f"\nBatch {batch_index}/{len(batches)}: {', '.join(batch_uids)}")
            fetched = 0
            failed: list[str] = []

            try:
                messages = fetch_batch(mailbox, batch_uids)
            except Exception as exc:
                print(f"Batch fetch failed: {exc}. Retrying individually.")
                messages = []
                for uid in batch_uids:
                    try:
                        message = fetch_individual(mailbox, uid)
                    except Exception as uid_exc:
                        print(f"  UID {uid} failed: {uid_exc}")
                        failed.append(uid)
                        continue
                    if message is None:
                        failed.append(uid)
                    else:
                        messages.append(message)

            for message in messages:
                record = message_to_record(message)
                append_record(jsonl_path, record)
                existing_uids.add(record["uid"])
                fetched += 1
                print(f"  saved UID {record['uid']}: {record['subject'][:90]}")

            fetched_uids = {str(message.uid) for message in messages}
            failed.extend(uid for uid in batch_uids if uid not in fetched_uids and uid not in failed)
            state["batches"].append(
                {
                    "batch_index": batch_index,
                    "uids": batch_uids,
                    "fetched": fetched,
                    "failed": failed,
                    "finished_at": utc_now(),
                }
            )
            state["harvested_total"] = len(existing_uids)
            write_state(state_path, state)

            if batch_index == len(batches):
                break

            delay = max(0, args.base_delay + random.uniform(-args.jitter, args.jitter))
            print(f"Sleeping {delay:.1f}s before next batch...")
            if not args.no_sleep:
                time.sleep(delay)

    state["finished_at"] = utc_now()
    write_state(state_path, state)
    print(f"\nDone. Harvested total stored UIDs: {len(existing_uids)}")
    print(f"Data: {jsonl_path}")
    print(f"State: {state_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
