import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Markdown } from "../components/Markdown";
import { Nav } from "../components/Nav";
import { ToastStack } from "../components/Toast";
import { useToasts } from "../components/useToasts";
import { api, EmailDetailData } from "../lib/api";

export default function EmailDetail() {
  const { uid = "" } = useParams<{ uid: string }>();
  const [email, setEmail] = useState<EmailDetailData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const { toasts, push, dismiss } = useToasts();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.email(uid);
        if (cancelled) return;
        if (data.status === "success" && data.data) {
          setEmail(data.data);
        } else {
          setError(data.message ?? "Failed to load email.");
        }
      } catch {
        if (!cancelled) setError("Failed to load email.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [uid]);

  async function sendToDiscord() {
    setSending(true);
    try {
      const data = await api.sendDiscord(uid);
      if (data.status === "success") {
        push("Successfully sent to Discord!");
      } else {
        push(data.message ?? "Failed to send", "error");
      }
    } catch {
      push("Network error while sending to Discord", "error");
    } finally {
      setSending(false);
    }
  }

  if (error) {
    return (
      <div className="page">
        <Nav />
        <div className="detail-card" style={{ textAlign: "center" }}>
          <h1 style={{ color: "var(--error)" }}>Error</h1>
          <p>{error}</p>
          <Link to="/" className="back-btn" style={{ marginTop: "2rem" }}>
            ← Back to Inbox
          </Link>
        </div>
        <ToastStack toasts={toasts} dismiss={dismiss} />
      </div>
    );
  }

  if (!email) {
    return (
      <div className="page">
        <Nav />
        <div className="loader large" aria-label="Loading" />
      </div>
    );
  }

  return (
    <div className="page">
      <Nav />
      <div className="detail-card">
        <Link to="/" className="back-btn">
          ← Back to Inbox
        </Link>
        <div className="email-meta">
          <h1>{email.subject}</h1>
          <div className="meta-row">
            <span className="label">From:</span>
            <span>{email.sender}</span>
          </div>
          <div className="meta-row">
            <span className="label">Date:</span>
            <span>{email.date}</span>
          </div>
        </div>
        <div className="summary-section">
          <div className="summary-header">
            <span className="summary-label">AI Summary</span>
            <button className="discord-btn" type="button" onClick={sendToDiscord} disabled={sending}>
              {sending ? "Sending..." : "Send to Discord"}
            </button>
          </div>
          <div className="summary-text">
            <Markdown>{email.summary ?? "No summary available."}</Markdown>
          </div>
        </div>
        <div className="email-content">{email.body || "No content."}</div>
      </div>
      <ToastStack toasts={toasts} dismiss={dismiss} />
    </div>
  );
}
