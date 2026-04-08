# 📧 Inbox Broadcast

A sleek, AI-powered mail viewer designed for **IIT Bombay students**. It fetches your latest campus emails, provides instant AI summaries, and manages a prioritized processing queue to help you stay on top of academic and administrative updates.

## ✨ Features

- **Live Mail View**: A modern, glassmorphism-inspired web interface to browse your inbox.
- **Rich AI Summarization**: Integrated with Ollama to provide concise, Markdown-formatted summaries including an overview, quick details, and prioritized key items.
- **Smart Filtering**: Ability to ignore specific email addresses (e.g., redundant newsletters) to keep your view clean.
- **Summary Caching**: JSON-based caching system with prompt-hash validation to ensure instant loads and automatic updates when the AI prompt changes.
- **Prioritized Processing**: A batch summarization endpoint that processes emails starting from the oldest (smallest UID) first.
- **Discord Integration**: Send AI-generated summaries directly to your Discord channel with a single click.

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Ollama**: The AI engine must be running in the background for summarization to work.
  - **Installation**: 
    - Visit [ollama.com](https://ollama.com/) for official installation instructions.
    - **Linux/Mac**: Run `curl -fsSL https://ollama.com/install.sh | sh` in your terminal.
    - **Windows**: Download and run the installer from the official website.
  - **Running Ollama**: 
    - You must either open the Ollama application from your apps menu **OR** run `ollama serve` in a separate terminal window.
  - **Pull the Model**:
    ```bash
    ollama pull qwen3.5:0.8b
    ```

### Installation

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   Create a `.env` file in the `mail_fetch/` directory based on `.env.example`. Use the following IITB-specific settings:
   ```env
   IMAP_SERVER=imap.iitb.ac.in
   IMAP_PORT=993
   IMAP_USERNAME=ldapid@iitb.ac.in
   IMAP_PASSWORD=your_sso_token
   MAILBOX=INBOX
   IGNORE_EMAILS=newsletter@spam.com,alerts@system.com
   ```

   And create a `.env` file in the `notify/` directory for Discord notifications:
   ```env
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url
   ```

   > **How to get your SSO token:**
   > Go to [sso.iitb.ac.in](https://sso.iitb.ac.in) $\rightarrow$ **Manage account** $\rightarrow$ **Access tokens** $\rightarrow$ **Emails**.

### Running the App

Start the server using `uvicorn`:
```bash
uvicorn app.main:app --reload
```
Open your browser and visit: `http://127.0.0.1:8000`

## 🛠️ API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | GET | Serves the main Inbox UI |
| `/api/emails` | GET | Fetches the last 10 non-ignored emails |
| `/api/email/{uid}` | GET | Fetches a specific email and its cached/new summary |
| `/api/email/{uid}/summary` | GET | Retrieves only the AI summary for a specific email |
| `/api/email/{uid}/discord` | POST | Sends an email summary to a Discord webhook |
| `/api/summarize-pending` | GET | Triggers batch summarization for all unsummarized emails in ascending order |

## 📁 Project Structure

- `app/`: FastAPI application and Jinja2 templates.
- `mail_fetch/`: IMAP integration and configuration.
- `summarize_mail/`: LLM prompt and caching logic.
- `notify/`: Discord notification system.
- `summaries.json`: Local cache storing `{uid: summary}`.

## 🛡️ Security Note

This application uses the IMAP protocol to access your mail. Always use an **SSO Access Token** as described in the configuration section rather than your main LDAP password to ensure the security of your account.
