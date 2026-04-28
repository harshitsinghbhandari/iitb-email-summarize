import { useEffect, useMemo, useState } from "react";

import { Nav } from "../components/Nav";
import { api, EmailDetailData, EmailListItem } from "../lib/api";

interface FixtureState {
  emails: EmailListItem[];
  manifest: { count?: number; generated_at?: string };
}

export default function Offline() {
  const [fixture, setFixture] = useState<FixtureState | null>(null);
  const [error, setError] = useState<{ message: string; command?: string } | null>(null);
  const [selectedUid, setSelectedUid] = useState<string | null>(null);
  const [detail, setDetail] = useState<EmailDetailData | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.offlineEmails();
        if (cancelled) return;
        if (data.status === "success" && data.data) {
          setFixture({ emails: data.data, manifest: data.manifest ?? {} });
          if (data.data.length) setSelectedUid(data.data[0].uid);
        } else {
          setError({ message: data.message ?? "Failed to load fixture.", command: data.command });
        }
      } catch {
        if (!cancelled) setError({ message: "Failed to connect to offline fixture API." });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedUid) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await api.offlineEmail(selectedUid);
        if (cancelled) return;
        if (data.status === "success" && data.data) {
          setDetail(data.data);
        } else {
          setDetail(null);
        }
      } catch {
        if (!cancelled) setDetail(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedUid]);

  const filtered = useMemo(() => {
    if (!fixture) return [];
    const q = search.trim().toLowerCase();
    if (!q) return fixture.emails;
    return fixture.emails.filter((email) =>
      [email.subject, email.sender, email.snippet].some((value) =>
        (value ?? "").toLowerCase().includes(q),
      ),
    );
  }, [fixture, search]);

  return (
    <div className="page">
      <header className="page-header">
        <h1>Offline Fixture Viewer</h1>
        {fixture && (
          <p style={{ color: "var(--text-muted)" }}>
            {fixture.manifest.count ?? fixture.emails.length} emails generated at{" "}
            {fixture.manifest.generated_at ?? "unknown time"}
          </p>
        )}
      </header>
      <Nav />

      {error && (
        <div className="container">
          <div className="error-state">
            <h2>Fixture not available</h2>
            <p>{error.message}</p>
            {error.command && (
              <p style={{ marginTop: "1rem", color: "var(--text-muted)" }}>
                Run: <code>{error.command}</code>
              </p>
            )}
          </div>
        </div>
      )}

      {!error && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "320px 1fr",
            gap: "1rem",
            width: "100%",
            maxWidth: "1100px",
          }}
        >
          <aside style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <input
              type="search"
              placeholder="Filter by subject, sender, snippet…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                padding: "0.6rem 0.9rem",
                borderRadius: "10px",
                border: "1px solid var(--border)",
                background: "var(--surface-color)",
                color: "var(--text-main)",
              }}
            />
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {filtered.map((email) => {
                const active = email.uid === selectedUid;
                return (
                  <button
                    key={email.uid}
                    type="button"
                    onClick={() => {
                      setDetail(null);
                      setSelectedUid(email.uid);
                    }}
                    className="email-card"
                    style={{
                      animation: "none",
                      opacity: 1,
                      transform: "none",
                      textAlign: "left",
                      padding: "1rem",
                      border: active ? "1px solid var(--accent)" : "1px solid var(--border)",
                    }}
                  >
                    <div className="email-header">
                      <div className="email-sender" style={{ fontSize: "0.9rem" }}>
                        {email.sender}
                      </div>
                      <div className="email-date">{email.date}</div>
                    </div>
                    <div className="email-subject" style={{ fontSize: "0.95rem" }}>
                      {email.subject}
                    </div>
                    <div className="email-snippet">{email.snippet}</div>
                  </button>
                );
              })}
              {filtered.length === 0 && fixture && (
                <div className="error-state" style={{ padding: "1.5rem" }}>
                  <p>No emails match your filter.</p>
                </div>
              )}
            </div>
          </aside>

          <main className="detail-card" style={{ padding: "2rem" }}>
            {!detail && <div className="loader large" aria-label="Loading" />}
            {detail && (
              <>
                <div className="email-meta">
                  <h1 style={{ fontSize: "1.6rem" }}>{detail.subject}</h1>
                  <div className="meta-row">
                    <span className="label">From:</span>
                    <span>{detail.sender}</span>
                  </div>
                  <div className="meta-row">
                    <span className="label">Date:</span>
                    <span>{detail.date}</span>
                  </div>
                </div>
                <div className="email-content">{detail.body || "No content."}</div>
              </>
            )}
          </main>
        </div>
      )}
    </div>
  );
}
