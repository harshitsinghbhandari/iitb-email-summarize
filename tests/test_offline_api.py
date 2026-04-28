import asyncio
import json

import app.main as app_main


def write_fixture(path):
    fixture = {
        "manifest": {
            "generated_at": "2026-04-28T00:00:00+00:00",
            "source_file": "mail_harvest/emails.jsonl",
            "count": 2,
            "uids": ["2", "1"],
        },
        "emails": [
            {
                "uid": "2",
                "subject": "With attachment",
                "sender": "sender@example.com",
                "date": "2026-04-28T09:00:00+00:00",
                "date_display": "Apr 28, 2026 09:00 AM UTC",
                "mailbox": "INBOX",
                "snippet": "Snippet two",
                "body": "Full body two",
                "body_source": "text",
                "attachments": [{"filename": "file.pdf", "content_type": "application/pdf", "size": 123}],
                "flags": [],
                "headers_subset": {"message-id": ["abc"]},
            },
            {
                "uid": "1",
                "subject": "Without attachment",
                "sender": "other@example.com",
                "date": "2026-04-27T09:00:00+00:00",
                "date_display": "Apr 27, 2026 09:00 AM UTC",
                "mailbox": "INBOX",
                "snippet": "Snippet one",
                "body": "Full body one",
                "body_source": "html",
                "attachments": [],
                "flags": ["\\Seen"],
                "headers_subset": {},
            },
        ],
    }
    path.write_text(json.dumps(fixture), encoding="utf-8")


def test_offline_email_list_returns_metadata_without_bodies(tmp_path, monkeypatch):
    fixture_path = tmp_path / "sanitized_emails.json"
    write_fixture(fixture_path)
    monkeypatch.setattr(app_main, "OFFLINE_FIXTURE_PATH", fixture_path)

    data = asyncio.run(app_main.api_get_offline_emails())

    assert data["status"] == "success"
    assert data["manifest"]["count"] == 2
    assert data["data"][0]["uid"] == "2"
    assert data["data"][0]["snippet"] == "Snippet two"
    assert "body" not in data["data"][0]


def test_offline_single_email_returns_full_body(tmp_path, monkeypatch):
    fixture_path = tmp_path / "sanitized_emails.json"
    write_fixture(fixture_path)
    monkeypatch.setattr(app_main, "OFFLINE_FIXTURE_PATH", fixture_path)

    data = asyncio.run(app_main.api_get_offline_email("2"))

    assert data["status"] == "success"
    assert data["data"]["uid"] == "2"
    assert data["data"]["body"] == "Full body two"


def test_missing_offline_fixture_returns_clear_error(tmp_path, monkeypatch):
    monkeypatch.setattr(app_main, "OFFLINE_FIXTURE_PATH", tmp_path / "missing.json")

    response = asyncio.run(app_main.api_get_offline_emails())
    data = json.loads(response.body)

    assert response.status_code == 404
    assert data["status"] == "error"
    assert "Offline fixture not found" in data["message"]
    assert data["command"] == "env/bin/python scripts/prepare_mail_fixture.py"


def test_unknown_offline_uid_returns_not_found(tmp_path, monkeypatch):
    fixture_path = tmp_path / "sanitized_emails.json"
    write_fixture(fixture_path)
    monkeypatch.setattr(app_main, "OFFLINE_FIXTURE_PATH", fixture_path)

    response = asyncio.run(app_main.api_get_offline_email("999"))
    data = json.loads(response.body)

    assert response.status_code == 404
    assert data["status"] == "error"
    assert "not found" in data["message"]
