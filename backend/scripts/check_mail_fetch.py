#!/usr/bin/env python3
"""Verify IMAP credentials and fetch a small email sample."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mail_fetch.config import (  # noqa: E402
    IMAP_ALLOW_INSECURE_SSL,
    IMAP_PORT,
    IMAP_SERVER,
    IMAP_USERNAME,
    MAILBOX,
    validate_config,
)
from mail_fetch.main import get_last_10_emails  # noqa: E402


def main() -> int:
    missing = validate_config()
    if missing:
        print("Missing required config:")
        for name in missing:
            print(f"- {name}")
        print("\nCheck mail_fetch/.env and run again.")
        return 1

    print("Checking IMAP credentials...")
    print(f"Server: {IMAP_SERVER}:{IMAP_PORT}")
    print(f"User: {IMAP_USERNAME}")
    print(f"Mailbox: {MAILBOX}")
    print(f"Insecure SSL fallback: {'enabled' if IMAP_ALLOW_INSECURE_SSL else 'disabled'}")
    print("\nConnecting. This can take a bit on slow networks...\n")

    emails = get_last_10_emails()
    if isinstance(emails, dict) and "error" in emails:
        print("Connection failed.")
        print(emails["error"])
        if not IMAP_ALLOW_INSECURE_SSL and "handshake failure" in emails["error"].lower():
            print("\nThis server may need legacy TLS compatibility.")
            print("Set IMAP_ALLOW_INSECURE_SSL=true in mail_fetch/.env and retry.")
        return 1

    print(f"Success. Fetched {len(emails)} email(s).")
    if not emails:
        print("Credentials worked, but the mailbox returned no visible emails.")
        return 0

    print("\nSample:")
    for index, email in enumerate(emails[:5], start=1):
        print(f"{index}. UID {email.get('uid')} | {email.get('date')}")
        print(f"   From: {email.get('sender')}")
        print(f"   Subject: {email.get('subject')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
