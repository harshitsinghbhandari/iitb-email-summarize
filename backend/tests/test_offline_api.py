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
                "attachments": [
                    {"filename": "file.pdf", "content_type": "application/pdf", "size": 123}
                ],
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
    assert data["command"] == "python backend/scripts/prepare_mail_fixture.py"


def test_unknown_offline_uid_returns_not_found(tmp_path, monkeypatch):
    fixture_path = tmp_path / "sanitized_emails.json"
    write_fixture(fixture_path)
    monkeypatch.setattr(app_main, "OFFLINE_FIXTURE_PATH", fixture_path)

    response = asyncio.run(app_main.api_get_offline_email("999"))
    data = json.loads(response.body)

    assert response.status_code == 404
    assert data["status"] == "error"
    assert "not found" in data["message"]


def test_offline_summary_uses_fixture_body_without_imap(tmp_path, monkeypatch):
    fixture_path = tmp_path / "sanitized_emails.json"
    write_fixture(fixture_path)
    monkeypatch.setattr(app_main, "OFFLINE_FIXTURE_PATH", fixture_path)

    calls = []

    def fake_get_summary(uid, body):
        calls.append((uid, body))
        return "Offline summary"

    monkeypatch.setattr(app_main, "get_summary", fake_get_summary)

    data = asyncio.run(app_main.api_get_offline_summary("2"))

    assert data["status"] == "success"
    assert data["summary"] == "Offline summary"
    assert calls == [("2", "Full body two")]


def test_offline_discord_posts_fixture_summary(tmp_path, monkeypatch):
    fixture_path = tmp_path / "sanitized_emails.json"
    write_fixture(fixture_path)
    monkeypatch.setattr(app_main, "OFFLINE_FIXTURE_PATH", fixture_path)
    monkeypatch.setattr(app_main, "get_summary", lambda uid, body: "Offline summary")

    sent = []

    def fake_send_to_discord(email, summary):
        sent.append((email["uid"], summary))
        return True, "sent"

    monkeypatch.setattr(app_main, "send_to_discord", fake_send_to_discord)

    data = asyncio.run(app_main.api_send_offline_to_discord("2"))

    assert data["status"] == "success"
    assert data["message"] == "sent"
    assert data["summary"] == "Offline summary"
    assert sent == [("2", "Offline summary")]


def test_offline_fetch_more_harvests_and_returns_refreshed_fixture(tmp_path, monkeypatch):
    fixture_path = tmp_path / "sanitized_emails.json"
    records_path = tmp_path / "emails.jsonl"
    write_fixture(fixture_path)
    monkeypatch.setattr(app_main, "OFFLINE_FIXTURE_PATH", fixture_path)
    monkeypatch.setattr(app_main, "MAIL_RECORDS_FILE", records_path)
    monkeypatch.setattr(app_main, "MAIL_HARVEST_DIR", tmp_path)

    harvest_calls = []

    def fake_harvest_recent_mail(**kwargs):
        harvest_calls.append(kwargs)
        return {"fetched": 1}

    def fake_write_fixture(source_file, output_file):
        assert source_file == records_path
        assert output_file == fixture_path
        return {
            "manifest": {
                "generated_at": "2026-04-28T01:00:00+00:00",
                "count": 3,
                "uids": ["3", "2", "1"],
            },
            "emails": [
                {
                    "uid": "3",
                    "subject": "Fresh",
                    "sender": "fresh@example.com",
                    "date": "2026-04-29T09:00:00+00:00",
                    "snippet": "Fresh snippet",
                    "body": "Fresh body",
                    "body_source": "text",
                    "attachments": [],
                    "flags": [],
                }
            ],
        }

    monkeypatch.setattr(app_main, "harvest_recent_mail", fake_harvest_recent_mail)
    monkeypatch.setattr(app_main, "write_fixture", fake_write_fixture)

    data = asyncio.run(app_main.api_offline_fetch_more(app_main.OfflineFetchMoreRequest(count=25)))

    assert data["status"] == "success"
    assert data["fetched"] == 1
    assert data["target"] == 27
    assert data["manifest"]["count"] == 3
    assert data["data"][0]["uid"] == "3"
    assert "body" not in data["data"][0]
    assert harvest_calls[0]["target"] == 27
    assert harvest_calls[0]["no_sleep"] is True
