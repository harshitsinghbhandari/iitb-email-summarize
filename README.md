# 📧 Inbox Broadcast

A sleek, AI-powered mail viewer designed for **IIT Bombay students**. It
fetches your latest campus emails, provides instant AI summaries, and
manages a prioritized processing queue to help you stay on top of academic
and administrative updates.

## ✨ Features

- **Live Mail View** — Vite + React SPA with a glassmorphism aesthetic.
- **Rich AI Summarization** — Markdown summaries via Ollama (overview, quick
  details, prioritized key items).
- **Smart Filtering** — ignore specific senders to keep the view clean.
- **Summary Caching** — JSON cache invalidated by prompt-hash mismatch.
- **Prioritized Processing** — batch summarize the oldest unsummarized UIDs.
- **Discord Integration** — send summaries or extracted deadlines to Discord.

## 📁 Repository Layout

This repo is a small monorepo with three top-level areas:

```
.
├── backend/                FastAPI Python service (only JSON; no HTML)
│   ├── app/                FastAPI application + routes
│   ├── mail_fetch/         IMAP fetching + config
│   ├── summarize_mail/     Ollama summarization client + cache
│   ├── notify/             Discord webhook integration
│   ├── deadline_tools/     Function-calling deadline extractor + daemon
│   ├── scripts/            CLI utilities (mail check, harvest, daemon, etc.)
│   └── tests/              pytest suite
├── frontend/               Vite + React + TypeScript SPA
│   ├── src/pages/          /, /email/:uid, /offline routes
│   ├── src/components/     Toast, Markdown, Nav, hooks
│   └── src/lib/api.ts      typed fetch client to /api/*
├── db/                     Persistence layer
│   ├── store.py            JSON store for deadlines (db.store)
│   ├── schemas/            JSON Schema for the on-disk shapes
│   └── seeds/              copy-paste example payloads
├── docs/                   Long-form notes and roadmap
├── pyproject.toml          Python tooling (pytest, black, mypy)
└── requirements.txt        Backend runtime dependencies
```

### Why this split

- **backend** is a pure JSON API. Routing and rendering live in the SPA, so
  swapping or hosting the frontend separately stays simple.
- **frontend** is a standard Vite project — it can be deployed to any static
  host or mounted behind FastAPI in production.
- **db** owns persistence. Today this is JSON files; tomorrow it can become
  a real database with no changes to call sites.

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node 20+** (for the frontend)
- **Ollama** running locally for AI summaries:
  - macOS / Linux: `curl -fsSL https://ollama.com/install.sh | sh`
  - Pull the model: `ollama pull qwen3.5:0.8b`

### Backend

```bash
python -m venv env
env/bin/pip install -r requirements.txt
```

Create `backend/mail_fetch/.env` (IMAP credentials) and
`backend/notify/.env` (Discord webhook). Examples are committed under each
package as `.env.example`. SSO token reference:
[sso.iitb.ac.in](https://sso.iitb.ac.in) → Manage account → Access tokens →
Emails.

Run the API:

```bash
env/bin/uvicorn --app-dir backend app.main:app --reload
```

The backend serves only `/api/*`. Tests:

```bash
env/bin/pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api/*` to
`http://127.0.0.1:8000` (override with `VITE_BACKEND_URL`). Production
build:

```bash
npm run build       # outputs frontend/dist/
npm run lint
npm run typecheck
```

### Database / Persistence

Runtime state lives in JSON/JSONL files under `db/runtime/` (gitignored):

- `db/runtime/summaries.json` — written by `backend/summarize_mail` (override with
  `SUMMARIES_FILE`)
- `db/runtime/deadlines.json` — written by `db.store` (override with `DEADLINES_FILE`)
- `db/runtime/mail_harvest/emails.jsonl` — full fetched/harvested email records
- `db/runtime/mail_harvest/sanitized_emails.json` — offline viewer fixture

Set `DB_RUNTIME_DIR` to move all default runtime stores together.
If older root-level JSON files exist, the app can read them as a fallback until
the corresponding `db/runtime/` file is written.

Seed examples are in `db/seeds/`.

## 🛠️ API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/health` | GET | Liveness probe |
| `/api/emails` | GET | Last 10 non-ignored emails |
| `/api/email/{uid}` | GET | Single email + summary |
| `/api/email/{uid}/summary` | GET | Cached or freshly generated summary |
| `/api/email/{uid}/discord` | POST | Send the summary to Discord |
| `/api/summarize-pending` | GET | Batch summarize unsummarized UIDs |
| `/api/offline/emails` | GET | List from harvested fixture |
| `/api/offline/email/{uid}` | GET | Single email from fixture |

## 🧪 Useful Scripts

```bash
env/bin/python backend/scripts/check_mail_fetch.py
env/bin/python backend/scripts/harvest_recent_mail.py --target 100
env/bin/python backend/scripts/prepare_mail_fixture.py
env/bin/python backend/scripts/check_deadline_function_calling.py
env/bin/python backend/scripts/evaluate_deadline_function_calling.py
DEADLINE_FUNCTION_MODEL=minimax-m2.5:cloud \
  env/bin/python backend/scripts/run_deadline_daemon.py --once
```

## ⚙️ Configuration Notes

- `backend/mail_fetch/.env` and `backend/notify/.env` are loaded explicitly
  so the app behaves the same whether you run it from the repo root or from
  `backend/`.
- IMAP TLS verification is enabled by default. Set
  `IMAP_ALLOW_INSECURE_SSL=true` only if your server requires legacy TLS.
- CORS for the dev server is enabled for `http://localhost:5173`. Override
  with `CORS_ALLOW_ORIGINS=https://prod.example.com,...`.

## 🛡️ Security Note

This application uses IMAP. Always use an **SSO Access Token** rather than
your main LDAP password, and keep `IMAP_ALLOW_INSECURE_SSL=false` unless
you specifically need legacy TLS compatibility.
