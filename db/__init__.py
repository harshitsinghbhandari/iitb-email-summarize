"""Persistence layer for Inbox Broadcast.

This package owns the on-disk JSON stores (deadlines, summaries) and
their schemas. Application code should import storage helpers from here
rather than reaching directly into the JSON files.
"""

from .store import (  # noqa: F401
    DEADLINES_FILE,
    empty_store,
    load_deadline_store,
    mark_deadline_discord_result,
    save_deadline_store,
    upsert_processed_result,
)
