from notify import main as notify_main


class ResponseOk:
    def raise_for_status(self):
        return None


def test_send_to_discord_truncates_long_embed_values(monkeypatch):
    payloads = []

    def fake_post(url, json, timeout):
        payloads.append(json)
        return ResponseOk()

    monkeypatch.setattr(notify_main, "DISCORD_WEBHOOK_URL", "https://discord.test/webhook")
    monkeypatch.setattr(notify_main.requests, "post", fake_post)

    success, message = notify_main.send_to_discord(
        {
            "subject": "S" * 400,
            "sender": "sender@example.com",
            "date": "2026-05-16",
        },
        "A" * 1600,
    )

    assert success is True
    assert message == "Successfully sent to Discord."

    embed = payloads[0]["embeds"][0]
    assert len(embed["title"]) <= notify_main.DISCORD_EMBED_TITLE_LIMIT
    summary_field = next(field for field in embed["fields"] if field["name"] == "Summary")
    assert len(summary_field["value"]) <= notify_main.DISCORD_EMBED_FIELD_VALUE_LIMIT
    assert summary_field["value"].endswith("...")
