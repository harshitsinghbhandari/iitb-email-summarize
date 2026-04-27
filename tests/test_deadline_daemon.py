from types import SimpleNamespace
from unittest.mock import Mock, patch

from deadline_tools.daemon import scan_once


def test_scan_once_skips_processed_uid():
    store = {
        "version": 1,
        "updated_at": None,
        "processed": {"101": {"has_deadline": False}},
        "deadlines": [],
    }

    with (
        patch("deadline_tools.daemon.validate_config", return_value=[]),
        patch("deadline_tools.daemon.load_deadline_store", return_value=store),
        patch("deadline_tools.daemon.get_last_10_emails", return_value=[{"uid": "101"}]),
        patch("deadline_tools.daemon.get_email_by_uid") as get_email_by_uid,
        patch("deadline_tools.daemon.call_deadline_tool") as call_deadline_tool,
        patch("deadline_tools.daemon.send_deadline_to_discord") as send_deadline_to_discord,
    ):
        stats = scan_once(limit=10)

    assert stats["seen"] == 1
    assert stats["skipped"] == 1
    get_email_by_uid.assert_not_called()
    call_deadline_tool.assert_not_called()
    send_deadline_to_discord.assert_not_called()


def test_scan_once_extracts_deadline_and_posts_to_discord():
    store = {"version": 1, "updated_at": None, "processed": {}, "deadlines": []}
    deadline = SimpleNamespace(
        title="Project Proposal Deadline",
        due_date="2026-05-10",
        source_text="Proposal due May 10, 2026.",
        action_required=True,
        confidence=1.0,
    )
    email = {
        "uid": "202",
        "subject": "Project Proposal Deadline",
        "sender": "prof@example.com",
        "date": "May 01, 2026 10:00 AM",
        "body": "Proposal due May 10, 2026.",
    }

    with (
        patch("deadline_tools.daemon.validate_config", return_value=[]),
        patch("deadline_tools.daemon.load_deadline_store", return_value=store),
        patch("deadline_tools.daemon.save_deadline_store") as save_deadline_store,
        patch("deadline_tools.daemon.get_last_10_emails", return_value=[{"uid": "202"}]),
        patch("deadline_tools.daemon.get_email_by_uid", return_value=email),
        patch("deadline_tools.daemon.call_deadline_tool", return_value=deadline),
        patch("deadline_tools.daemon.send_deadline_to_discord", return_value=(True, "sent")) as send_deadline,
    ):
        stats = scan_once(limit=10)

    assert stats["processed"] == 1
    assert stats["deadlines"] == 1
    assert stats["discord_sent"] == 1
    assert store["processed"]["202"]["has_deadline"] is True
    assert store["deadlines"][0]["title"] == "Project Proposal Deadline"
    assert store["deadlines"][0]["discord_sent_at"] is not None
    send_deadline.assert_called_once()
    assert save_deadline_store.call_count == 2


def test_scan_once_can_disable_discord_posts():
    store = {"version": 1, "updated_at": None, "processed": {}, "deadlines": []}
    deadline = SimpleNamespace(
        title="Fee Payment Deadline",
        due_date="2026-05-02",
        source_text="Pay fees before May 2, 2026.",
        action_required=True,
        confidence=1.0,
    )

    with (
        patch("deadline_tools.daemon.validate_config", return_value=[]),
        patch("deadline_tools.daemon.load_deadline_store", return_value=store),
        patch("deadline_tools.daemon.save_deadline_store"),
        patch("deadline_tools.daemon.get_last_10_emails", return_value=[{"uid": "303"}]),
        patch(
            "deadline_tools.daemon.get_email_by_uid",
            return_value={
                "uid": "303",
                "subject": "Fee Payment",
                "sender": "admin@example.com",
                "date": "May 01, 2026 10:00 AM",
                "body": "Pay fees before May 2, 2026.",
            },
        ),
        patch("deadline_tools.daemon.call_deadline_tool", return_value=deadline),
        patch("deadline_tools.daemon.send_deadline_to_discord") as send_deadline_to_discord,
    ):
        stats = scan_once(limit=10, post_to_discord=False)

    assert stats["deadlines"] == 1
    assert stats["discord_sent"] == 0
    assert store["deadlines"][0]["discord_sent_at"] is None
    send_deadline_to_discord.assert_not_called()


def test_scan_once_records_no_deadline_without_discord():
    store = {"version": 1, "updated_at": None, "processed": {}, "deadlines": []}

    with (
        patch("deadline_tools.daemon.validate_config", return_value=[]),
        patch("deadline_tools.daemon.load_deadline_store", return_value=store),
        patch("deadline_tools.daemon.save_deadline_store"),
        patch("deadline_tools.daemon.get_last_10_emails", return_value=[{"uid": "404"}]),
        patch(
            "deadline_tools.daemon.get_email_by_uid",
            return_value={
                "uid": "404",
                "subject": "Newsletter",
                "sender": "club@example.com",
                "date": "May 01, 2026 10:00 AM",
                "body": "Here are this week's updates.",
            },
        ),
        patch("deadline_tools.daemon.call_deadline_tool", return_value=None),
        patch("deadline_tools.daemon.send_deadline_to_discord") as send_deadline_to_discord,
    ):
        stats = scan_once(limit=10)

    assert stats["processed"] == 1
    assert stats["deadlines"] == 0
    assert store["processed"]["404"]["has_deadline"] is False
    assert store["deadlines"] == []
    send_deadline_to_discord.assert_not_called()
