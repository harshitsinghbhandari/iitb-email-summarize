# LLM Forge Transcript: IITB Mail Command Center Roadmap

Timestamp: 2026-04-27 21:50:00 IST

## Original Artifact

Source: `docs/product-roadmap.md`

The original roadmap defined a personal AI mail client for IIT Bombay email with phases for basic mail UI, SQLite storage, background sync, structured AI extraction, deadlines, noise handling, Discord notifications, personalization, hardening, and an immediate sprint.

## Framed Context

- Existing repo has FastAPI mail UI, IMAP fetching, Ollama summaries, deadline extraction daemon, Discord posting, and JSON stores.
- The product direction is a full personal mail UI for IIT Bombay, not only an email summarizer.
- Critical constraints: reliable foundation before AI expansion, safe IMAP delete behavior, and moving product state to SQLite.

## Craftsperson Outputs

### The Surgeon

Produced a lean build plan with non-negotiables, a clear Do Not Build Yet list, SQLite-first sequencing, inbox-from-SQLite, safe actions, deadline review, high-signal Discord, and concise done conditions.

### The Architect

Produced the best structural expansion: product thesis, explicit build order, local mail foundation, SQLite backbone, sync pipeline, safe actions, structured AI, deadline system, Discord, noise, personalization, hardening, immediate sprint, next sprint, later milestones, risks, and non-goals.

### The Sharpener

Added precise safety and schema details: Phase 0 stabilization, config validation, IMAP wrapper, read-only smoke test, safety mode, minimum SQLite fields, action fields, processing states, model/prompt metadata, and a build order summary.

### The Humanizer

Anchored the roadmap around a student-facing promise: open every morning and trust the app within 30 seconds. Added morning/evening daily loops and strong language about Discord interrupting only for worthwhile items.

### The Stress-Tester

Strengthened failure handling: no synchronous IMAP, failed delete cannot mark mail deleted, relative dates resolve against email received date, multiple deadlines are allowed, Discord idempotency, health page, and tests that matter.

## Peer Review Highlights

- Most reviewers favored the Humanizer because the 30-second morning trust promise keeps the roadmap product-led.
- One reviewer favored the Architect for strongest execution structure.
- One reviewer favored the Stress-Tester for reliability and failure-mode coverage.
- The best shared improvements were SQLite as source of truth, explicit safety/idempotency, audited mail actions, raw/parsed AI outputs, and review/correction loops.
- Regressions to avoid: turning the plan into only a reliability backlog, or compressing it into a narrow engineering checklist.
- Common remaining gap: the assistant intelligence loop needed sharper definition around user correction, confidence, evidence, learning, and measurable success criteria.

## Master Synthesis

The final roadmap combines:

- Humanizer's 30-second trust promise and daily flow.
- Architect's staged structure and sprint sequencing.
- Sharpener's schema/config/action precision.
- Stress-Tester's safety, idempotency, and failure-mode requirements.
- Surgeon's scope control and Do Not Build Yet boundaries.

The forged version was written to `docs/product-roadmap.md`.

## What Changed and Why

- Reframed from feature roadmap to product promise plus measurable success targets.
- Moved SQLite, sync, and safety into hard gates before richer AI behavior.
- Added a dedicated review and correction loop so AI mistakes become product feedback.
- Added explicit Discord idempotency and mail-action auditability.
- Added immediate and next sprint scopes with definitions of done.

## What the Forge Could Not Fix

- Exact SQLite schema still needs implementation discovery.
- IITB IMAP trash-folder behavior needs verification before choosing trash-first delete.
- UI route structure and deep-link behavior from Discord need product/design decisions.
- Real AI quality targets need measurement on actual IITB emails.
