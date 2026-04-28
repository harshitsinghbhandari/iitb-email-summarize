# Inbox Broadcast — Frontend

Vite + React + TypeScript SPA that talks to the FastAPI backend over JSON.

## Pages

- `/` — Inbox: list of recent emails with click-to-summarize (`/api/emails`,
  `/api/email/:uid/summary`).
- `/email/:uid` — full email view with AI summary and "Send to Discord"
  (`/api/email/:uid`, `/api/email/:uid/discord`).
- `/offline` — browse the harvested fixture
  (`/api/offline/emails`, `/api/offline/email/:uid`).

## Local development

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on http://localhost:5173 and proxies `/api/*` to the
backend (`http://127.0.0.1:8000` by default; override with
`VITE_BACKEND_URL`). Start the backend in a second terminal:

```bash
cd backend
uvicorn app.main:app --reload
```

## Build

```bash
npm run build
```

Outputs a static SPA under `frontend/dist/`. Serve it with any static host,
or behind the FastAPI app via `StaticFiles` in production.

## Type check

```bash
npm run typecheck
```
