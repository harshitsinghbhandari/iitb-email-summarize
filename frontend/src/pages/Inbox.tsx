import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Markdown } from "../components/Markdown";
import { Nav } from "../components/Nav";
import { ToastStack } from "../components/Toast";
import { useToasts } from "../components/useToasts";
import { api, EmailListItem } from "../lib/api";

interface SummaryState {
  open: boolean;
  loading: boolean;
  text: string | null;
}

export default function Inbox() {
  const [emails, setEmails] = useState<EmailListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [summaries, setSummaries] = useState<Record<string, SummaryState>>({});
  const { toasts, push, dismiss } = useToasts();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.emails();
        if (cancelled) return;
        if (data.status === "success" && data.data) {
          setEmails(data.data);
        } else {
          setError(data.message ?? "Failed to fetch emails.");
        }
      } catch {
        if (!cancelled) push("Failed to connect to server", "error");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [push]);

  async function toggleSummary(uid: string) {
    const current = summaries[uid];
    if (current?.open) {
      setSummaries((prev) => ({ ...prev, [uid]: { ...current, open: false } }));
      return;
    }
    if (current?.text) {
      setSummaries((prev) => ({ ...prev, [uid]: { ...current, open: true } }));
      return;
    }

    setSummaries((prev) => ({ ...prev, [uid]: { open: true, loading: true, text: null } }));
    try {
      const data = await api.summary(uid);
      if (data.status === "success" && data.summary) {
        setSummaries((prev) => ({
          ...prev,
          [uid]: { open: true, loading: false, text: data.summary! },
        }));
      } else {
        const message = data.message ?? "Summary failed";
        setSummaries((prev) => ({
          ...prev,
          [uid]: { open: true, loading: false, text: message },
        }));
        push(message, "error");
      }
    } catch {
      setSummaries((prev) => ({
        ...prev,
        [uid]: { open: true, loading: false, text: "Failed to load summary." },
      }));
      push("Server error while summarizing", "error");
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <h1>Inbox Broadcast</h1>
      </header>
      <Nav />
      <div className="container">
        {error && (
          <div className="error-state">
            <h2>Connection Error</h2>
            <p>{error}</p>
          </div>
        )}
        {!error && emails === null && <div className="loader large" aria-label="Loading" />}
        {emails?.length === 0 && (
          <div className="error-state">
            <p>No emails found in inbox.</p>
          </div>
        )}
        {emails?.map((email, i) => {
          const state = summaries[email.uid];
          return (
            <div
              key={email.uid}
              className="email-card"
              style={{ animationDelay: `${i * 0.05}s` }}
              onClick={(e) => {
                if ((e.target as HTMLElement).closest(".detail-btn")) return;
                toggleSummary(email.uid);
              }}
            >
              <div className="email-header">
                <div className="email-sender">{email.sender}</div>
                <div className="email-date">{email.date}</div>
              </div>
              <div className="email-subject">{email.subject}</div>
              <div className="email-snippet">{email.snippet}</div>
              {state?.open && (
                <div className="summary-overlay">
                  <div className="summary-text">
                    {state.loading ? (
                      <>
                        <span className="loader" />
                        Summarizing with AI...
                      </>
                    ) : (
                      <Markdown>{state.text ?? ""}</Markdown>
                    )}
                  </div>
                  <Link to={`/email/${encodeURIComponent(email.uid)}`} className="detail-btn">
                    View Full Email
                  </Link>
                </div>
              )}
            </div>
          );
        })}
      </div>
      <ToastStack toasts={toasts} dismiss={dismiss} />
    </div>
  );
}
