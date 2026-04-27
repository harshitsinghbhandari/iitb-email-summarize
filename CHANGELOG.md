# Changelog

## [Unreleased]

### Added
- Add a standalone mail credential check script.
- Add an experimental deadline extraction module for testing Ollama function calling with `functiongemma:270m`.
- Add a live deadline function-calling evaluation script with multiple sample emails.
- Add a background deadline extraction daemon that scans recent email, stores deadlines, and posts new deadlines to Discord.

### Fixed
- Load package-specific `.env` files reliably for mail fetching and Discord notifications.
- Fix pending summary detection so batch summarization checks cached email summaries correctly.
- Store summary cache data at a stable repo-root path by default.

### Security
- Enable verified IMAP TLS by default, with an explicit opt-in for legacy insecure SSL connections.
- Render email fields, email bodies, and AI-generated Markdown more safely in the web UI.
