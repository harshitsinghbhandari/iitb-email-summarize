# IITB Mail Command Center Roadmap

## Product Promise

Build a personal mail client that an IIT Bombay student can open every morning and trust within 30 seconds.

It should answer:

- What needs my attention today?
- What needs action or follow-up?
- What deadlines are real and upcoming?
- What can I ignore, archive, or delete without regret?

This is not an email summarizer. It is a local-first mail command center: fast inbox, background IMAP sync, structured AI triage, deadline review, Discord alerts, and guarded mail actions. AI helps after the mail client is reliable.

## Success Targets

- Morning triage takes under 30 seconds for already-synced mail.
- App startup performs zero live IMAP or AI calls.
- Re-running sync never duplicates emails, deadlines, or Discord posts.
- No permanent delete happens without an audit row and explicit user confirmation.
- Every AI deadline or delete suggestion has source evidence.
- Ambiguous dates enter review instead of being posted as facts.
- Discord posts fewer, higher-signal notifications rather than becoming a second inbox.

## Product Rules

- Mail client before AI assistant.
- SQLite is the source of truth for UI state.
- IMAP runs in background jobs, not page requests.
- AI output is advisory until confirmed by user action or repeated trust.
- Deletes are trash-first or dry-run first where possible.
- Every destructive or hiding action is auditable.
- Discord delivery is idempotent.
- The app must remain useful when IMAP, Ollama, cloud models, or Discord are unavailable.

## Daily User Loop

Morning:

1. Open the app.
2. See recent IITB mail instantly from SQLite.
3. Check Today, Tomorrow, and This Week deadlines.
4. Pin important mail.
5. Ignore obvious recurring noise.
6. Get Discord only for high-confidence deadlines or genuinely important mail.

Evening:

1. Review what is due tomorrow.
2. Mark completed deadlines.
3. Correct suspicious AI guesses.
4. Clean noise safely.

This loop is the product. Infrastructure exists to make this loop fast, boring, and trustworthy.

## Phase 0: Stabilize Current System

Goal: preserve what already works and put guardrails around what can cause damage.

Build:

- Document current flows: IMAP fetch, summary generation, deadline extraction, Discord posting, JSON stores, delete behavior.
- Add a central mail action layer for delete, archive, ignore, and restore-like behavior.
- Add safety mode that disables destructive IMAP actions by default.
- Add delete dry-run.
- Add read-only IMAP smoke test.
- Add configuration validation at startup.
- Add structured logs around IMAP, AI, Discord, and delete attempts.

Done when:

- App can start without touching IMAP.
- Diagnostic scripts can verify IMAP and Discord separately.
- No UI route calls IMAP delete directly.
- Delete code cannot run unless destructive actions are explicitly enabled.
- Failures are logged with enough context to debug without leaking secrets.

## Phase 1: SQLite Foundation

Goal: move durable state out of JSON before adding more UI or AI behavior.

Initial tables:

- `emails`
- `email_bodies`
- `mailboxes`
- `ignored_senders`
- `ignored_domains`
- `mail_actions`
- `ai_outputs`
- `deadlines`
- `daemon_runs`
- `discord_deliveries`
- `processing_errors`

Minimum `emails` fields:

- `id`
- `account`
- `mailbox`
- `imap_uid`
- `message_id`
- `sender`
- `sender_email`
- `subject`
- `received_at`
- `snippet`
- `flags_json`
- `local_state`
- `sync_seen_at`
- `created_at`
- `updated_at`

Minimum `mail_actions` fields:

- `id`
- `email_id`
- `action_type`
- `status`
- `requested_by`
- `confirmed_by_user`
- `created_at`
- `executed_at`
- `imap_result`
- `error`

Rules:

- `(account, mailbox, imap_uid)` is unique.
- Email body storage is separate from list metadata.
- Raw source data is preserved where practical.
- Existing JSON deadline data is migrated, not discarded.
- JSON files stop being active write paths.

Done when:

- Existing deadlines are visible from SQLite.
- UI and daemon can read from SQLite.
- Re-running import does not duplicate rows.
- A backup/export command can dump the database.

## Phase 2: Local Inbox UI

Goal: replace the daily IITB inbox glance without depending on AI or live IMAP.

Build:

- Inbox list with sender, subject, received date, snippet, and local status.
- Email detail view from stored body.
- Search by sender, subject, and body.
- Pagination or load more.
- Manual refresh that triggers sync rather than doing inline fetch.
- Pin/unpin.
- Mark seen in app.
- Ignore sender.
- Guarded delete request.

Local states:

- `seen_in_app`
- `pinned`
- `ignored_sender`
- `ignored_domain`
- `delete_requested`
- `deleted_remote`
- `needs_review`

Done when:

- App opens from SQLite only.
- Recent mail appears instantly when already synced.
- Empty state distinguishes no local mail from failed sync.
- User can open full email detail.
- Search works over locally stored mail.
- Ollama can be offline without breaking inbox use.

## Phase 3: Background IMAP Sync

Goal: make mail fetching predictable, incremental, and independent of request handlers.

Build a sync worker that:

- Fetches configured mailbox on an interval.
- Fetches by UID.
- Skips already stored UIDs.
- Updates flags for known UIDs where practical.
- Stores metadata first and body separately.
- Records each run in `daemon_runs`.
- Records per-email failures in `processing_errors`.
- Queues AI work separately from fetching.

Processing states:

- `fetched`
- `body_stored`
- `ai_pending`
- `ai_processed`
- `ai_failed`
- `needs_review`
- `ignored`

Rules:

- Ignored sender/domain rules suppress normal inbox visibility and notifications, but ignored emails remain traceable.
- One malformed email must not fail the whole sync.
- Duplicate UID insert is harmless.
- Request handlers never perform bulk IMAP fetches.

Done when:

- Background sync adds new mail without restarting the app.
- UI shows last sync status.
- Failed sync runs are visible.
- Re-running sync does not duplicate emails.

## Phase 4: Safe Mail Actions

Goal: make cleanup useful without making it dangerous.

Actions:

- Ignore sender.
- Ignore domain.
- Pin/keep email.
- Mark as noise.
- Request delete.
- Confirm delete.
- View action history.

Delete policy:

- Default behavior is `delete_requested`, not immediate permanent delete.
- Prefer move-to-trash if IITB IMAP supports Trash.
- If Trash is unavailable, require explicit confirmation before IMAP delete.
- Failed remote delete must not mark email as remotely deleted.
- Delete confirmation shows subject, sender, and UID.

Forbidden early:

- AI-triggered delete.
- Bulk permanent delete.
- Auto-delete without explicit user-created rule.

Done when:

- Deleting a test email records an audit trail.
- Failed delete is visible and retryable.
- Ignoring a sender does not delete past mail.
- There is no code path where AI directly deletes mail.

## Phase 5: Structured AI Triage

Goal: turn emails into queryable, reviewable product data while treating model output as untrusted.

Extract:

- `summary`
- `category`
- `importance`
- `action_required`
- `deadline_date`
- `deadline_title`
- `deadline_confidence`
- `suggested_action`
- `needs_review`
- `evidence_text`
- `model_name`
- `prompt_version`
- `raw_output`
- `parse_status`

Categories:

- `academic`
- `admin`
- `placement`
- `event`
- `club`
- `newsletter`
- `personal`
- `receipt`
- `security`
- `unknown`

Suggested actions:

- `read`
- `act`
- `pin`
- `archive`
- `delete_candidate`
- `ignore_sender_candidate`
- `review`

Rules:

- Parse AI output through a strict schema.
- Invalid JSON becomes `ai_failed`, not app failure.
- Keep raw output for debugging.
- Require evidence text for deadlines and delete suggestions.
- Never hide or delete an email based only on AI classification.

Done when:

- AI failures are visible and retryable.
- UI can show useful metadata without trusting it blindly.
- User can inspect evidence behind every suggested action.
- Prompt/model changes are traceable.

## Phase 6: Deadline Command Center

Goal: never miss a real deadline, and never silently trust a fake one.

Build:

- Deadlines dashboard.
- Today, Tomorrow, and This Week views.
- Sort by due date.
- Link back to source email.
- Mark done.
- Mark wrong.
- Edit title/date.
- Review queue for ambiguous dates.
- Discord post for new high-confidence deadlines.
- Daily digest for upcoming deadlines.

Deadline states:

- `new`
- `confirmed`
- `done`
- `wrong`
- `needs_review`
- `dismissed`

Validation rules:

- Preserve raw `source_text`.
- Preserve source email UID.
- Numeric dates like `28-4-29` are ambiguous unless context resolves them.
- Relative dates like "tomorrow" resolve against email received date, not current date.
- Missing year requires review unless context makes it obvious.
- Dates too far in the future require review.
- Multiple deadlines from one email are allowed.
- Low-confidence deadlines stay in UI, not Discord.

Done when:

- Deadlines live in SQLite.
- Incorrect deadlines can be corrected without deleting history.
- Ambiguous dates require review before notification.
- Discord posts each new high-confidence deadline once.

## Phase 7: Review and Correction Loop

Goal: make the assistant improve through user correction instead of silently repeating mistakes.

Build:

- `needs_review` queue for AI uncertainty.
- Correction UI for category, importance, deadline title/date, and suggested action.
- Reason capture for wrong/dismissed deadlines.
- History of user overrides.
- Feedback events stored for future personalization.

Rules:

- Corrections update display state immediately.
- Original AI output remains stored for debugging.
- Repeated correction patterns create suggestions, not hidden automation.

Done when:

- User can correct a wrong deadline.
- User can mark an AI category wrong.
- Corrections are visible in history.
- Future processing can reference correction patterns.

## Phase 8: Noise Reduction

Goal: reduce clutter without losing important mail.

Manual controls:

- Ignore sender.
- Ignore domain.
- Ignore subject keyword.
- Mark as noise.
- Keep sender.
- Keep domain.

Suggested queues:

- Delete candidates.
- Ignore sender candidates.
- Newsletters.
- Low-priority events.

Rules:

- AI may suggest cleanup.
- User confirms cleanup.
- Auto-delete applies only to explicit user-created rules.
- Auto-delete should first move to review/trash, not permanently delete.
- Every rule shows why it exists and what it matched.

Done when:

- User can review cleanup suggestions before action.
- Ignored senders stop producing notifications.
- Important categories can override noise suggestions.
- Every rule-created action has an audit trail.

## Phase 9: Discord Notifications

Goal: use Discord as a high-signal push layer, not a second inbox.

Post:

- New high-confidence deadlines.
- Daily deadline digest.
- Due-tomorrow reminders.
- New important emails above threshold.
- Cleanup summary, not individual low-value emails.

Do not post:

- Every summary.
- Every newsletter.
- Every event.
- Low-confidence extractions.
- Repeated notifications for the same deadline/email.

Reliability:

- Store delivery attempts in `discord_deliveries`.
- Deduplicate by event type and source id.
- Retry transient failures with limits.
- Rate-limit posts.
- Support dry-run mode.

Done when:

- Daemon restart does not repost old deadlines.
- Failed posts are visible.
- Discord feels like a useful nudge, not a noisy mirror.

## Phase 10: Personalization

Goal: learn from user behavior using simple, inspectable rules before model tuning.

Track:

- Deleted senders.
- Ignored senders/domains.
- Kept senders.
- Pinned categories.
- Dismissed categories.
- Corrected deadlines.
- Corrected importance/category.
- Restored delete candidates.

Examples:

- Sender deleted five times -> suggest ignore sender.
- Placement emails consistently pinned -> boost placement priority.
- Club events often dismissed -> lower default importance.
- Sender produced wrong deadline twice -> lower deadline confidence or require review.

Rules:

- Personalization creates suggestions and ranking changes first.
- Learned behavior can be reset.
- Rules beat model guesses when they conflict.

Done when:

- User can see why something was prioritized.
- User can accept, reject, or delete learned rules.
- Personalization improves triage without hiding mail unexpectedly.

## Phase 11: Hardening

Required before trusting automation:

- SQLite migrations.
- Backup/export command.
- Restore/import command.
- Trash-first delete where available.
- Audit log for delete/archive/ignore/rule actions.
- Rate limits for IMAP, AI, and Discord.
- Retry queue for failed processing.
- Structured logs.
- Secret scanning in CI.
- Health page for IMAP/Ollama/Discord/daemon status.
- Manual recovery path for corrupted local state.

Tests that matter:

- UI loads with IMAP offline.
- Duplicate IMAP sync does not duplicate emails.
- Failed IMAP delete does not mark email deleted.
- Delete action creates audit row.
- AI invalid JSON does not break processing.
- Ambiguous date becomes `needs_review`.
- Relative date uses email received date.
- Discord restart does not repost same deadline.
- Ignored sender suppresses notification but preserves auditability.

## Immediate Sprint: Reliable Local Inbox

Goal: build the smallest durable foundation for a real product.

Scope:

1. Add SQLite schema and migration setup.
2. Import existing JSON deadlines and summaries where useful.
3. Store fetched email metadata and body locally.
4. Make inbox UI read from SQLite only.
5. Add email detail view from SQLite.
6. Add background IMAP sync.
7. Add safe delete request flow with audit log.
8. Add ignore sender with audit log.
9. Move deadline daemon output from `deadlines.json` into SQLite.
10. Preserve Discord posting for new high-confidence deadlines.

Explicitly out of scope:

- Auto-delete.
- AI-based inbox hiding.
- Full personalization.
- Bulk permanent delete.
- Model fine-tuning.
- Multi-account support unless it falls out naturally from schema.

Definition of done:

- App opens without live IMAP calls.
- Recent emails appear from SQLite.
- Background sync can add new emails.
- Re-running sync does not duplicate emails.
- User can open full email detail.
- User can request deletion of a test email.
- Delete action is audited.
- User can ignore a sender.
- Ignored sender state persists.
- Deadlines are stored in SQLite.
- Discord posting still works for new high-confidence deadlines.
- IMAP/Ollama/Discord failure does not crash app startup.

## Next Sprint: Structured Processing

Goal: make AI output useful without making it trusted by default.

Scope:

1. Add `ai_outputs` table.
2. Add processing queue states.
3. Extract structured fields from email bodies.
4. Store raw and parsed AI output.
5. Add `needs_review` handling.
6. Add deadline evidence and confidence.
7. Add UI badges for category, importance, action required, and review-needed.
8. Add correction events for wrong category/date/action.

Definition of done:

- AI failure does not break inbox usage.
- Each processed email has structured metadata or a recorded failure.
- Deadlines link back to source emails.
- Ambiguous dates enter review instead of being silently accepted.
- User corrections are stored.

## Product Milestone Order

### Milestone 1: Local Mail Client

- SQLite
- background sync
- inbox list
- detail view
- search
- safe delete
- ignore sender

### Milestone 2: Deadline Reliability

- deadline SQLite storage
- validation rules
- dashboard
- review states
- Discord dedupe

### Milestone 3: AI Triage

- structured extraction
- importance/category
- suggested actions
- processing retries
- correction loop

### Milestone 4: Noise Reduction

- cleanup queues
- ignore rules
- bulk non-permanent actions
- audit views

### Milestone 5: Personal Command Center

- learned preferences
- explainable ranking
- user-created rules
- limited reversible automation
- daily operating flow

## Current Known Risks

- IITB IMAP may require insecure SSL compatibility in local testing.
- IMAP UID behavior must be understood per mailbox before relying on it.
- Direct IMAP delete already works, so destructive flows need guardrails immediately.
- AI date parsing can produce plausible wrong dates.
- Relative dates must be resolved using email received date.
- JSON stores are past their useful limit.
- Discord duplicate posting is likely unless delivery state is stored.
- Background daemon errors can silently rot without visible status.
- Ignored sender/domain rules can hide important one-off emails if applied too aggressively.

## Product Differentiation

This should become more than a local AI inbox. The differentiator is the correction loop:

- The app shows why it classified or extracted something.
- The user corrects wrong dates, categories, and actions.
- Corrections become visible preferences and safer future defaults.
- The system earns more automation only after repeated confirmed behavior.

The long-term product is a personal command center that understands IITB email patterns, not a generic mail skin with summaries.
