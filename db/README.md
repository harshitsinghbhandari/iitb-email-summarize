# db/

Persistence layer for Inbox Broadcast.

The project does not currently use a relational database. Runtime state is
persisted as JSON files at the repository root (gitignored):

- `deadlines.json` — written by `db.store` (see `store.py`)
- `summaries.json` — written by `backend/summarize_mail/main.py`

Both files can be relocated by setting `DEADLINES_FILE` / `SUMMARIES_FILE`.

## Layout

- `store.py` — read/write helpers for `deadlines.json`. Imported as `db.store`.
- `__init__.py` — re-exports the public API of `store.py`.
- `schemas/` — JSON Schema documents describing the on-disk shape of each
  store. Useful for IDE validation and as living documentation.
- `seeds/` — example payloads matching each schema. Copy one into the repo
  root if you need a populated store for local development:
  ```bash
  cp db/seeds/deadlines.example.json deadlines.json
  cp db/seeds/summaries.example.json summaries.json
  ```

## Migrating to a real database

If we move off JSON in the future, the migration path is:

1. Add a `db/migrations/` directory with versioned SQL.
2. Replace the bodies of `store.py` helpers with SQLAlchemy queries while
   keeping the same function signatures so callers do not change.
3. Drop the `deadlines.json` / `summaries.json` paths once the cutover is done.
