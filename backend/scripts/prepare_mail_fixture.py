#!/usr/bin/env python3
"""Prepare harvested IMAP JSONL mail for offline UI testing."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_FILE = REPO_ROOT / "mail_harvest" / "emails.jsonl"
DEFAULT_OUTPUT_FILE = REPO_ROOT / "mail_harvest" / "sanitized_emails.json"

HEADER_SUBSET_KEYS = (
    "from",
    "to",
    "cc",
    "reply-to",
    "date",
    "subject",
    "message-id",
    "list-id",
)

SECRET_PATTERNS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    (
        "password",
        "Password-like value",
        re.compile(
            r"\b(password|passwd|pwd|passcode)\b\s*(?:is|:|=|-)\s*([^\s<>'\"]{4,})",
            re.IGNORECASE,
        ),
    ),
    (
        "otp",
        "OTP or verification code",
        re.compile(
            r"\b(otp|one[-\s]?time password|verification code|security code)\b.{0,50}?\b(\d{4,8})\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "api_key",
        "API key or token",
        re.compile(
            r"\b(api[_\s-]?key|access[_\s-]?token|auth[_\s-]?token|bearer[_\s-]?token|secret[_\s-]?key)\b"
            r"\s*(?:is|:|=|-)?\s*([A-Za-z0-9_./+=-]{12,})",
            re.IGNORECASE,
        ),
    ),
    (
        "private_key",
        "Private key block",
        re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----", re.IGNORECASE),
    ),
)


class ReadableHTMLParser(HTMLParser):
    """Small HTML-to-text converter tuned for email fixture readability."""

    BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "li",
        "p",
        "section",
        "table",
        "tr",
    }
    SKIP_TAGS = {"script", "style", "head", "title", "meta"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "li":
            self._parts.append("\n- ")
        elif tag in self.BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if not self._skip_depth and tag in self.BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self._parts.append(data)

    def text(self) -> str:
        return normalize_text("".join(self._parts))


def normalize_text(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def html_to_text(html: Any) -> str:
    parser = ReadableHTMLParser()
    parser.feed(str(html or ""))
    parser.close()
    return parser.text()


def collapse_for_snippet(value: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."


def redacted_secret_evidence(match: re.Match[str], secret_group: int | None = 2) -> str:
    evidence = re.sub(r"\s+", " ", match.group(0)).strip()
    if secret_group is not None and len(match.groups()) >= secret_group:
        secret_value = match.group(secret_group)
        if secret_value:
            evidence = evidence.replace(secret_value, "[redacted]")
    return collapse_for_snippet(evidence, limit=140)


def scan_for_secrets(*contents: Any) -> dict[str, Any]:
    text = "\n".join(str(content or "") for content in contents)
    findings: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for secret_type, label, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            evidence = redacted_secret_evidence(match, None if secret_type == "private_key" else 2)
            key = (secret_type, evidence.lower())
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                {
                    "type": secret_type,
                    "label": label,
                    "evidence": evidence,
                }
            )

    secret_types = sorted({finding["type"] for finding in findings})
    return {
        "contains_secret": bool(findings),
        "secret_count": len(findings),
        "secret_types": secret_types,
        "secret_findings": findings,
    }


def parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None

    try:
        normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        try:
            parsed = parsedate_to_datetime(text)
        except (TypeError, ValueError):
            return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def timestamp_for_sort(record: dict[str, Any], keys: tuple[str, ...]) -> float:
    for key in keys:
        parsed = parse_datetime(record.get(key))
        if parsed is not None:
            return parsed.timestamp()
    return float("-inf")


def format_date_display(date_value: Any) -> str:
    parsed = parse_datetime(date_value)
    if parsed is None:
        return ""
    return parsed.strftime("%b %d, %Y %I:%M %p UTC")


def normalize_headers(headers: Any) -> dict[str, list[str]]:
    if not isinstance(headers, dict):
        return {}

    normalized: dict[str, list[str]] = {}
    for key, value in headers.items():
        lower_key = str(key).lower()
        if isinstance(value, list):
            normalized[lower_key] = [str(item) for item in value if item is not None]
        elif isinstance(value, tuple):
            normalized[lower_key] = [str(item) for item in value if item is not None]
        elif value is None:
            normalized[lower_key] = []
        else:
            normalized[lower_key] = [str(value)]
    return normalized


def headers_subset(headers: Any) -> dict[str, list[str]]:
    normalized = normalize_headers(headers)
    return {key: normalized.get(key, []) for key in HEADER_SUBSET_KEYS if key in normalized}


def attachment_metadata(attachments: Any) -> list[dict[str, Any]]:
    if not isinstance(attachments, list):
        return []

    metadata: list[dict[str, Any]] = []
    for attachment in attachments:
        if not isinstance(attachment, dict):
            continue
        clean = {
            key: value
            for key, value in attachment.items()
            if key not in {"content", "payload", "data", "body"}
        }
        metadata.append(clean)
    return metadata


def normalize_flags(flags: Any) -> list[str]:
    if not isinstance(flags, list):
        return []
    return [str(flag) for flag in flags]


def flag_set(flags: list[str]) -> set[str]:
    return {flag.lower().lstrip("\\") for flag in flags}


def choose_body(record: dict[str, Any]) -> tuple[str, str]:
    text_body = normalize_text(record.get("text"))
    if text_body:
        return text_body, "text"

    html_body = html_to_text(record.get("html"))
    if html_body:
        return html_body, "html"

    body = normalize_text(record.get("body"))
    if body:
        return body, "body"

    return "", "empty"


def uid_sort_value(uid: Any) -> tuple[int, Any]:
    uid_text = str(uid or "")
    if uid_text.isdigit():
        return (1, int(uid_text))
    return (0, uid_text)


def normalize_record(record: dict[str, Any]) -> dict[str, Any] | None:
    uid = record.get("uid")
    if uid is None or str(uid).strip() == "":
        return None

    body, body_source = choose_body(record)
    subject = str(record.get("subject") or "(No Subject)")
    sender = str(record.get("sender") or record.get("from") or "")
    date = str(record.get("date") or "")
    html_body = str(record.get("html") or "")
    attachments = attachment_metadata(record.get("attachments"))
    flags = normalize_flags(record.get("flags"))
    normalized_flags = flag_set(flags)
    is_read = "seen" in normalized_flags
    secret_scan = scan_for_secrets(subject, body, html_body)

    return {
        "uid": str(uid),
        "subject": subject,
        "sender": sender,
        "date": date,
        "date_display": format_date_display(date),
        "mailbox": str(record.get("mailbox") or ""),
        "snippet": collapse_for_snippet(body),
        "body": body,
        "body_source": body_source,
        "html_body": html_body,
        "has_html": bool(html_body.strip()),
        "attachments": attachments,
        "attachment_count": len(attachments),
        "flags": flags,
        "is_read": is_read,
        "is_unread": not is_read,
        "is_flagged": "flagged" in normalized_flags,
        **secret_scan,
        "search_text": collapse_for_snippet(" ".join([sender, subject, body]), limit=20000),
        "headers_subset": headers_subset(record.get("headers")),
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if isinstance(value, dict):
                records.append(value)
    return records


def deduplicate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_uid: dict[str, tuple[float, int, dict[str, Any]]] = {}
    for index, record in enumerate(records):
        uid = record.get("uid")
        if uid is None:
            continue
        uid_key = str(uid)
        harvested_at = timestamp_for_sort(record, ("fetched_at", "harvested_at", "created_at", "date"))
        current = by_uid.get(uid_key)
        if current is None or (harvested_at, index) >= (current[0], current[1]):
            by_uid[uid_key] = (harvested_at, index, record)
    return [item[2] for item in by_uid.values()]


def build_fixture(source_file: Path) -> dict[str, Any]:
    records = deduplicate_records(read_jsonl(source_file))
    emails = [email for record in records if (email := normalize_record(record)) is not None]
    emails.sort(
        key=lambda email: (
            timestamp_for_sort(email, ("date",)),
            uid_sort_value(email["uid"]),
        ),
        reverse=True,
    )

    return {
        "manifest": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_file": str(source_file),
            "count": len(emails),
            "uids": [email["uid"] for email in emails],
        },
        "emails": emails,
    }


def write_fixture(source_file: Path, output_file: Path) -> dict[str, Any]:
    fixture = build_fixture(source_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(fixture, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    return fixture


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize harvested mail JSONL into an offline UI fixture.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_FILE, help="Input harvested JSONL path.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE, help="Output sanitized JSON fixture path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.source.exists():
        print(f"Source file not found: {args.source}", file=sys.stderr)
        return 1

    fixture = write_fixture(args.source, args.output)
    print(f"Wrote {fixture['manifest']['count']} email(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
