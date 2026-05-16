# Changelog

## [Unreleased]

### Added
- Add offline email summary and Discord actions directly in the mail reader.
- Add a standalone mail credential check script.
- Add an experimental deadline extraction module for testing Ollama function calling with `functiongemma:270m`.
- Add a live deadline function-calling evaluation script with multiple sample emails.
- Add a background deadline extraction daemon that scans recent email, stores deadlines, and posts new deadlines to Discord.
- Add offline fixture scanning for likely passwords, OTPs, API keys, tokens, and private keys, with review flags in the offline mail viewer.
- Store fetched mail, harvested fixtures, summaries, and deadline results under the `db/runtime/` persistence area by default.

### Changed
- Make the offline mail viewer the main frontend experience.

### Fixed
- Trim Discord embed titles and summary fields so long AI summaries can post successfully.
- Load package-specific `.env` files reliably for mail fetching and Discord notifications.
- Fix pending summary detection so batch summarization checks cached email summaries correctly.
- Store summary cache data at a stable repo-root path by default.

### Security
- Enable verified IMAP TLS by default, with an explicit opt-in for legacy insecure SSL connections.
- Render email fields, email bodies, and AI-generated Markdown more safely in the web UI.
