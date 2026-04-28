# db/

Persistence layer for Inbox Broadcast.

The project does not currently use a relational database. Runtime state is
persisted as JSON/JSONL files under `db/runtime/` by default (gitignored):

- `db/runtime/deadlines.json` — deadline scan results, written by `db.store`
- `db/runtime/summaries.json` — AI summary cache, written by `summarize_mail`
- `db/runtime/mail_harvest/emails.jsonl` — full fetched/harvested email records
- `db/runtime/mail_harvest/state.json` — harvest progress metadata
- `db/runtime/mail_harvest/sanitized_emails.json` — normalized offline viewer fixture

These files can be relocated by setting `DB_RUNTIME_DIR`, or by setting the
specific path variables: `DEADLINES_FILE`, `SUMMARIES_FILE`,
`MAIL_HARVEST_DIR`, `MAIL_RECORDS_FILE`, `MAIL_HARVEST_STATE_FILE`, and
`OFFLINE_FIXTURE_FILE`.

For local continuity, readers tolerate legacy root-level files
(`summaries.json`, `deadlines.json`, and `mail_harvest/emails.jsonl`) when the
new `db/runtime/` file does not exist yet. New writes go to `db/runtime/`.

## Layout

- `store.py` — read/write helpers and canonical runtime paths. Imported as `db.store`.
- `__init__.py` — re-exports the public API of `store.py`.
- `schemas/` — JSON Schema documents describing the on-disk shape of each
  store. Useful for IDE validation and as living documentation.
- `seeds/` — example payloads matching each schema. Copy one into the repo
  root if you need a populated store for local development:
  ```bash
  mkdir -p db/runtime
  cp db/seeds/deadlines.example.json db/runtime/deadlines.json
  cp db/seeds/summaries.example.json db/runtime/summaries.json
  ```

## Migrating to a real database

If we move off JSON in the future, the migration path is:

1. Add a `db/migrations/` directory with versioned SQL.
2. Replace the bodies of `store.py` helpers with SQLAlchemy queries while
   keeping the same function signatures so callers do not change.
3. Replace the JSON/JSONL runtime files under `db/runtime/` once the cutover is done.
