from pathlib import Path

from db import store


def test_runtime_defaults_live_under_db_runtime():
    runtime_dir = Path("db/runtime")

    assert store.RUNTIME_DIR.relative_to(store.ROOT_DIR) == runtime_dir
    assert store.SUMMARIES_FILE.relative_to(store.ROOT_DIR) == runtime_dir / "summaries.json"
    assert store.DEADLINES_FILE.relative_to(store.ROOT_DIR) == runtime_dir / "deadlines.json"
    assert store.MAIL_RECORDS_FILE.relative_to(store.ROOT_DIR) == (
        runtime_dir / "mail_harvest" / "emails.jsonl"
    )
    assert store.OFFLINE_FIXTURE_FILE.relative_to(store.ROOT_DIR) == (
        runtime_dir / "mail_harvest" / "sanitized_emails.json"
    )
    assert store.LEGACY_SUMMARIES_FILE.relative_to(store.ROOT_DIR) == Path("summaries.json")
    assert store.LEGACY_DEADLINES_FILE.relative_to(store.ROOT_DIR) == Path("deadlines.json")


def test_append_mail_record_writes_jsonl(tmp_path):
    path = tmp_path / "mail" / "emails.jsonl"

    store.append_mail_record({"uid": "101", "subject": "Stored"}, path=path)

    assert path.read_text(encoding="utf-8").strip() == '{"subject": "Stored", "uid": "101"}'
