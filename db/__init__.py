"""Persistence layer for Inbox Broadcast.

This package owns the on-disk JSON stores (deadlines, summaries) and
their schemas. Application code should import storage helpers from here
rather than reaching directly into the JSON files.
"""

from .store import (  # noqa: F401
    DEADLINES_FILE,
    LEGACY_DEADLINES_FILE,
    LEGACY_MAIL_RECORDS_FILE,
    LEGACY_SUMMARIES_FILE,
    MAIL_HARVEST_DIR,
    MAIL_HARVEST_STATE_FILE,
    MAIL_RECORDS_FILE,
    OFFLINE_FIXTURE_FILE,
    RUNTIME_DIR,
    SUMMARIES_FILE,
    append_mail_record,
    empty_store,
    load_deadline_store,
    mark_deadline_discord_result,
    save_deadline_store,
    upsert_processed_result,
    write_mail_harvest_state,
)
