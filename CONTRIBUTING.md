# Contributing to Inbox Broadcast 📧

Thank you for your interest in improving Inbox Broadcast! We welcome
contributions from the IIT Bombay community and beyond.

## 🚀 Getting Started

1. Fork the repository and clone your fork.
2. Set up the environment (see the **Getting Started** section in
   [`README.md`](./README.md)) — Python virtualenv for the backend and
   `npm install` inside `frontend/`.
3. Create a descriptive branch:
   `git checkout -b feature/your-feature-name` or
   `git checkout -b fix/issue-description`.

## 📁 Where Code Lives

| Area | Path |
| :--- | :--- |
| FastAPI service & API routes | `backend/app/` |
| IMAP, summarization, notifier | `backend/mail_fetch/`, `backend/summarize_mail/`, `backend/notify/` |
| Deadline extraction | `backend/deadline_tools/` |
| CLI scripts | `backend/scripts/` |
| Pytest suite | `backend/tests/` |
| React UI | `frontend/src/` |
| JSON persistence + seeds | `db/` |

## 🛠️ Development Guidelines

### Python

- PEP 8, type hints on new functions, docstrings on classes / public APIs.
- Format with `black .` and run `mypy backend db` before pushing.
- Run `pytest` from the repo root.

### Frontend

- TypeScript strict mode is enabled — keep it that way.
- Run `npm run lint`, `npm run typecheck`, and `npm run build` before
  pushing UI changes.
- Reuse the CSS variables in `frontend/src/index.css` to preserve the
  glassmorphism aesthetic.

### AI Prompting

- When modifying `backend/summarize_mail/PROMPT.py`, keep the output
  concise and tuned to student-facing summaries. Prompt-hash changes
  invalidate the cache automatically.

## ✅ Before opening a PR

- `pytest`
- `black .`
- `cd frontend && npm run lint && npm run typecheck && npm run build`
- Verify the IMAP / summarization pipeline still loads emails end-to-end.

## 📝 Pull Request Process

1. Push your branch to your fork.
2. Open a PR using the provided template.
3. Describe **what changed and why** (include screenshots for UI changes).
4. Make sure the `backend` and `frontend` GitHub Actions workflows pass.

## ⚖️ License

By contributing to this project, you agree that your contributions will be
licensed under the project's existing license.
