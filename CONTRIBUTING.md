# Contributing to Inbox Broadcast 📧

Thank you for your interest in improving Inbox Broadcast! We welcome contributions from the IIT Bombay community and beyond.

## 🚀 Getting Started

1. **Fork the Repository**: Create your own copy of the project.
2. **Set Up Environment**: Follow the [Installation](#installation) guide in the `README.md`.
3. **Create a Branch**: Give your branch a descriptive name:
   `git checkout -b feature/your-feature-name` or `git checkout -b fix/issue-description`.

## 🛠️ Development Guidelines

### Coding Style
- **Python**: Follow PEP 8 guidelines. Use clear variable names and include docstrings for complex functions.
- **Frontend**: Maintain the glassmorphism aesthetic. Use the established CSS variables in `app/templates` for consistency.
- **AI Prompting**: When modifying `summarize_mail/PROMPT.py`, ensure the output remains concise and focused on a student's needs.

### Testing Your Changes
- Run the server using `uvicorn app.main:app --reload`.
- Verify that your changes don't break the IMAP fetching or the AI summarization pipeline.
- Check that Markdown rendering still works across both index and detail views.

## 📝 Pull Request Process

1. **Push your changes** to your fork.
2. **Open a Pull Request** using the provided PR template.
3. **Provide a clear description** of what you changed and why.
4. **Include screenshots** if you've made UI changes.

## ⚖️ License
By contributing to this project, you agree that your contributions will be licensed under the project's existing license.
