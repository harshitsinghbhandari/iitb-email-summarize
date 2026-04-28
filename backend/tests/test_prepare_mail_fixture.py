import json

from scripts.prepare_mail_fixture import build_fixture, write_fixture


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record))
            f.write("\n")


def test_text_email_uses_text_body(tmp_path):
    source = tmp_path / "emails.jsonl"
    write_jsonl(
        source,
        [
            {
                "uid": "1",
                "subject": "Plain",
                "sender": "sender@example.com",
                "date": "2026-04-28T10:00:00+00:00",
                "text": "Hello from text",
                "html": "<p>HTML body</p>",
            }
        ],
    )

    fixture = build_fixture(source)

    assert fixture["manifest"]["count"] == 1
    assert fixture["emails"][0]["body"] == "Hello from text"
    assert fixture["emails"][0]["body_source"] == "text"
    assert fixture["emails"][0]["html_body"] == "<p>HTML body</p>"
    assert fixture["emails"][0]["has_html"] is True
    assert fixture["emails"][0]["snippet"] == "Hello from text"
    assert "Hello from text" in fixture["emails"][0]["search_text"]


def test_flags_and_attachment_counts_become_filter_fields(tmp_path):
    source = tmp_path / "emails.jsonl"
    write_jsonl(
        source,
        [
            {
                "uid": "9",
                "date": "2026-04-28T10:00:00+00:00",
                "text": "Filter me",
                "flags": ["\\Seen", "\\Flagged"],
                "attachments": [{"filename": "paper.pdf", "content": "discarded"}],
            }
        ],
    )

    email = build_fixture(source)["emails"][0]

    assert email["is_read"] is True
    assert email["is_unread"] is False
    assert email["is_flagged"] is True
    assert email["attachment_count"] == 1
    assert email["attachments"] == [{"filename": "paper.pdf"}]


def test_secret_scan_flags_passwords_and_redacts_values(tmp_path):
    source = tmp_path / "emails.jsonl"
    write_jsonl(
        source,
        [
            {
                "uid": "8",
                "date": "2026-04-28T10:00:00+00:00",
                "text": "Temporary password: SuperSecret123. Use it once.",
            }
        ],
    )

    email = build_fixture(source)["emails"][0]

    assert email["contains_secret"] is True
    assert email["secret_count"] == 1
    assert email["secret_types"] == ["password"]
    assert email["secret_findings"][0]["label"] == "Password-like value"
    assert "SuperSecret123" not in email["secret_findings"][0]["evidence"]
    assert "[redacted]" in email["secret_findings"][0]["evidence"]


def test_secret_scan_flags_html_tokens_and_otp_codes(tmp_path):
    source = tmp_path / "emails.jsonl"
    write_jsonl(
        source,
        [
            {
                "uid": "7",
                "date": "2026-04-28T10:00:00+00:00",
                "text": "Your verification code is 123456.",
                "html": "<p>api key = sk_test_1234567890abcdef</p>",
            }
        ],
    )

    email = build_fixture(source)["emails"][0]

    assert email["contains_secret"] is True
    assert email["secret_count"] == 2
    assert email["secret_types"] == ["api_key", "otp"]
    evidence = " ".join(finding["evidence"] for finding in email["secret_findings"])
    assert "123456" not in evidence
    assert "sk_test_1234567890abcdef" not in evidence


def test_secret_scan_does_not_flag_generic_password_advice(tmp_path):
    source = tmp_path / "emails.jsonl"
    write_jsonl(
        source,
        [
            {
                "uid": "6",
                "date": "2026-04-28T10:00:00+00:00",
                "text": "If this was not you, change your password immediately.",
            }
        ],
    )

    email = build_fixture(source)["emails"][0]

    assert email["contains_secret"] is False
    assert email["secret_count"] == 0
    assert email["secret_types"] == []
    assert email["secret_findings"] == []


def test_html_only_email_becomes_readable_plain_text(tmp_path):
    source = tmp_path / "emails.jsonl"
    write_jsonl(
        source,
        [
            {
                "uid": "2",
                "subject": "HTML",
                "sender": "sender@example.com",
                "date": "2026-04-28T10:00:00+00:00",
                "text": "",
                "html": "<h1>Title</h1><p>Hello <strong>world</strong>.</p><ul><li>One</li><li>Two</li></ul>",
            }
        ],
    )

    email = build_fixture(source)["emails"][0]

    assert email["body_source"] == "html"
    assert email["has_html"] is True
    assert email["html_body"].startswith("<h1>Title</h1>")
    assert "Title" in email["body"]
    assert "Hello world." in email["body"]
    assert "- One" in email["body"]
    assert "- Two" in email["body"]


def test_duplicate_uid_keeps_latest_harvested_record(tmp_path):
    source = tmp_path / "emails.jsonl"
    write_jsonl(
        source,
        [
            {
                "uid": "3",
                "subject": "Old",
                "date": "2026-04-27T10:00:00+00:00",
                "fetched_at": "2026-04-28T10:00:00+00:00",
                "text": "old body",
            },
            {
                "uid": "3",
                "subject": "New",
                "date": "2026-04-27T10:00:00+00:00",
                "fetched_at": "2026-04-28T11:00:00+00:00",
                "text": "new body",
            },
        ],
    )

    fixture = build_fixture(source)

    assert fixture["manifest"]["uids"] == ["3"]
    assert fixture["emails"][0]["subject"] == "New"
    assert fixture["emails"][0]["body"] == "new body"


def test_missing_subject_body_and_date_do_not_crash(tmp_path):
    source = tmp_path / "emails.jsonl"
    output = tmp_path / "sanitized.json"
    write_jsonl(source, [{"uid": "4"}])

    fixture = write_fixture(source, output)

    assert output.exists()
    assert fixture["emails"][0]["subject"] == "(No Subject)"
    assert fixture["emails"][0]["body"] == ""
    assert fixture["emails"][0]["has_html"] is False
    assert fixture["emails"][0]["date_display"] == ""


def test_output_sorted_newest_first_by_date_then_uid(tmp_path):
    source = tmp_path / "emails.jsonl"
    write_jsonl(
        source,
        [
            {"uid": "10", "date": "2026-04-27T10:00:00+00:00", "text": "older"},
            {"uid": "11", "date": "2026-04-28T09:00:00+00:00", "text": "newer"},
            {"uid": "12", "date": "2026-04-28T09:00:00+00:00", "text": "same date higher uid"},
        ],
    )

    fixture = build_fixture(source)

    assert fixture["manifest"]["uids"] == ["12", "11", "10"]
