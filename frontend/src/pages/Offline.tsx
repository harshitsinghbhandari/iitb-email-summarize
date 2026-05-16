import { useEffect, useMemo, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { api, EmailDetailData, EmailListItem } from "../lib/api";

type StatusFilter = "all" | "unread" | "read" | "attachments" | "flagged" | "secrets";
type BodyView = "html" | "text";

interface FixtureState {
  emails: EmailListItem[];
  manifest: { count?: number; generated_at?: string };
}

const statusLabels: Array<{ value: StatusFilter; label: string }> = [
  { value: "all", label: "All mail" },
  { value: "unread", label: "Unread" },
  { value: "read", label: "Read" },
  { value: "attachments", label: "Attachments" },
  { value: "flagged", label: "Flagged" },
  { value: "secrets", label: "Possible secrets" },
];

function isRead(email: EmailListItem | EmailDetailData) {
  if (typeof email.is_read === "boolean") return email.is_read;
  return (email.flags ?? []).some((flag) => flag.toLowerCase().replace("\\", "") === "seen");
}

function isFlagged(email: EmailListItem | EmailDetailData) {
  if (typeof email.is_flagged === "boolean") return email.is_flagged;
  return (email.flags ?? []).some((flag) => flag.toLowerCase().replace("\\", "") === "flagged");
}

function hasAttachments(email: EmailListItem | EmailDetailData) {
  return Number(email.attachment_count ?? 0) > 0 || Number(email.attachments?.length ?? 0) > 0;
}

function containsSecret(email: EmailListItem | EmailDetailData) {
  return Boolean(email.contains_secret || Number(email.secret_count ?? 0) > 0);
}

function displayDate(email: EmailListItem | EmailDetailData) {
  return email.date_display || email.date || "";
}

function senderName(sender: string) {
  return sender.split("<")[0].trim() || sender || "Unknown sender";
}

function initials(sender: string) {
  const clean = senderName(sender);
  const parts = clean.split(/\s+/).filter(Boolean);
  const letters = parts.length > 1 ? `${parts[0][0]}${parts[1][0]}` : clean.slice(0, 2);
  return letters.toUpperCase();
}

export default function Offline() {
  const [fixture, setFixture] = useState<FixtureState | null>(null);
  const [error, setError] = useState<{ message: string; command?: string } | null>(null);
  const [selectedUid, setSelectedUid] = useState<string | null>(null);
  const [detail, setDetail] = useState<EmailDetailData | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [mailboxFilter, setMailboxFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [bodyView, setBodyView] = useState<BodyView>("html");
  const [summary, setSummary] = useState("");
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [discordSending, setDiscordSending] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ kind: "info" | "error"; text: string } | null>(
    null,
  );

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
          setBodyView(data.data.has_html && data.data.html_body ? "html" : "text");
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

  const emails = useMemo(() => fixture?.emails ?? [], [fixture]);

  const counts = useMemo(
    () => ({
      all: emails.length,
      unread: emails.filter((email) => !isRead(email)).length,
      read: emails.filter(isRead).length,
      attachments: emails.filter(hasAttachments).length,
      flagged: emails.filter(isFlagged).length,
      secrets: emails.filter(containsSecret).length,
    }),
    [emails],
  );

  const mailboxes = useMemo(
    () => [...new Set(emails.map((email) => email.mailbox).filter(Boolean))].sort(),
    [emails],
  );

  const bodySources = useMemo(
    () => [...new Set(emails.map((email) => email.body_source).filter(Boolean))].sort(),
    [emails],
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return emails.filter((email) => {
      if (statusFilter === "unread" && isRead(email)) return false;
      if (statusFilter === "read" && !isRead(email)) return false;
      if (statusFilter === "attachments" && !hasAttachments(email)) return false;
      if (statusFilter === "flagged" && !isFlagged(email)) return false;
      if (statusFilter === "secrets" && !containsSecret(email)) return false;
      if (mailboxFilter !== "all" && email.mailbox !== mailboxFilter) return false;
      if (sourceFilter !== "all" && email.body_source !== sourceFilter) return false;
      if (!q) return true;
      const haystack = email.search_text || [email.subject, email.sender, email.snippet].join(" ");
      return haystack.toLowerCase().includes(q);
    });
  }, [emails, mailboxFilter, search, sourceFilter, statusFilter]);

  function clearFilters() {
    setSearch("");
    setStatusFilter("all");
    setMailboxFilter("all");
    setSourceFilter("all");
  }

  function selectEmail(uid: string) {
    setDetail(null);
    setSummary("");
    setActionMessage(null);
    setSummaryLoading(false);
    setDiscordSending(false);
    setSelectedUid(uid);
  }

  async function summarizeSelected() {
    if (!detail) return;
    setSummaryLoading(true);
    setActionMessage(null);
    try {
      const data = await api.offlineSummary(detail.uid);
      if (data.status === "success" && data.summary) {
        setSummary(data.summary);
        setActionMessage({ kind: "info", text: "Summary ready." });
      } else {
        setActionMessage({ kind: "error", text: data.message ?? "Summary failed." });
      }
    } catch {
      setActionMessage({ kind: "error", text: "Could not connect to the summary API." });
    } finally {
      setSummaryLoading(false);
    }
  }

  async function postSelectedToDiscord() {
    if (!detail) return;
    setDiscordSending(true);
    setActionMessage(null);
    try {
      const data = await api.sendOfflineDiscord(detail.uid);
      if (data.summary) setSummary(data.summary);
      setActionMessage({
        kind: data.status === "success" ? "info" : "error",
        text: data.message ?? (data.status === "success" ? "Posted to Discord." : "Discord post failed."),
      });
    } catch {
      setActionMessage({ kind: "error", text: "Could not connect to the Discord API." });
    } finally {
      setDiscordSending(false);
    }
  }

  if (error) {
    return (
      <div className="mail-app-shell">
        <div className="mail-empty-state">
          <h1>Offline fixture unavailable</h1>
          <p>{error.message}</p>
          {error.command && <code>{error.command}</code>}
        </div>
      </div>
    );
  }

  return (
    <div className="mail-app-shell">
      <aside className="mail-sidebar" aria-label="Mailbox filters">
        <div className="mail-brand">
          <div>
            <span className="mail-brand-kicker">Inbox Broadcast</span>
            <h1>Offline Mail</h1>
          </div>
        </div>

        <nav className="mail-nav-list">
          {statusLabels.map((item) => (
            <button
              key={item.value}
              type="button"
              className={`mail-nav-item ${statusFilter === item.value ? "active" : ""}`}
              onClick={() => setStatusFilter(item.value)}
            >
              <span>{item.label}</span>
              <strong>{counts[item.value]}</strong>
            </button>
          ))}
        </nav>

        <div className="mail-sidebar-section">
          <label htmlFor="mailbox-filter">Mailbox</label>
          <select
            id="mailbox-filter"
            value={mailboxFilter}
            onChange={(event) => setMailboxFilter(event.target.value)}
          >
            <option value="all">All mailboxes</option>
            {mailboxes.map((mailbox) => (
              <option key={mailbox} value={mailbox}>
                {mailbox}
              </option>
            ))}
          </select>
        </div>

        <div className="mail-sidebar-section">
          <label htmlFor="source-filter">Body source</label>
          <select
            id="source-filter"
            value={sourceFilter}
            onChange={(event) => setSourceFilter(event.target.value)}
          >
            <option value="all">All sources</option>
            {bodySources.map((source) => (
              <option key={source} value={source}>
                {source}
              </option>
            ))}
          </select>
        </div>

        <div className="mail-sidebar-footer">
          <span>{fixture?.manifest.count ?? emails.length} fixture emails</span>
          <span>{fixture?.manifest.generated_at ?? "No generated timestamp"}</span>
        </div>
      </aside>

      <section className="mail-list-pane">
        <header className="mail-list-toolbar">
          <div>
            <h2>{statusLabels.find((item) => item.value === statusFilter)?.label}</h2>
            <p>
              {filtered.length} shown of {emails.length}
            </p>
          </div>
          <button type="button" className="mail-ghost-button" onClick={clearFilters}>
            Clear
          </button>
        </header>

        <div className="mail-search-row">
          <input
            type="search"
            placeholder="Search sender, subject, snippet, body"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        <div className="mail-message-list">
          {filtered.map((email) => {
            const active = email.uid === selectedUid;
            const unread = !isRead(email);
            return (
              <button
                key={email.uid}
                type="button"
                onClick={() => selectEmail(email.uid)}
                className={`mail-row ${active ? "active" : ""} ${unread ? "unread" : ""}`}
              >
                <span className="mail-avatar">{initials(email.sender)}</span>
                <span className="mail-row-main">
                  <span className="mail-row-topline">
                    <strong>{senderName(email.sender)}</strong>
                    <time>{displayDate(email)}</time>
                  </span>
                  <span className="mail-row-subject">{email.subject || "(No Subject)"}</span>
                  <span className="mail-row-snippet">{email.snippet}</span>
                  <span className="mail-row-tags">
                    {unread && <span className="mail-tag unread">Unread</span>}
                    {hasAttachments(email) && <span className="mail-tag">Attachment</span>}
                    {isFlagged(email) && <span className="mail-tag flagged">Flagged</span>}
                    {containsSecret(email) && <span className="mail-tag secret">Possible secret</span>}
                    {email.has_html && <span className="mail-tag">HTML</span>}
                  </span>
                </span>
              </button>
            );
          })}

          {fixture && filtered.length === 0 && (
            <div className="mail-empty-list">
              <h3>No messages match</h3>
              <p>Adjust the current filters or clear them.</p>
            </div>
          )}

          {!fixture && <div className="loader large" aria-label="Loading" />}
        </div>
      </section>

      <main className="mail-reader-pane">
        {!detail && selectedUid && <div className="loader large" aria-label="Loading" />}
        {!selectedUid && (
          <div className="mail-empty-state">
            <h2>Select a message</h2>
            <p>The message body and metadata will appear here.</p>
          </div>
        )}

        {detail && (
          <article className="mail-reader">
            <header className="mail-reader-header">
              <div className="mail-reader-subject">
                <p>{detail.mailbox || "INBOX"}</p>
                <h2>{detail.subject || "(No Subject)"}</h2>
              </div>
              <div className="mail-reader-actions">
                {detail.has_html && detail.html_body && (
                  <div className="mail-view-toggle" aria-label="Body view">
                    <button
                      type="button"
                      className={bodyView === "html" ? "active" : ""}
                      onClick={() => setBodyView("html")}
                    >
                      HTML
                    </button>
                    <button
                      type="button"
                      className={bodyView === "text" ? "active" : ""}
                      onClick={() => setBodyView("text")}
                    >
                      Text
                    </button>
                  </div>
                )}
              </div>
            </header>

            <section className="mail-reader-meta">
              <span className="mail-avatar large">{initials(detail.sender)}</span>
              <div>
                <strong>{senderName(detail.sender)}</strong>
                <span>{detail.sender}</span>
              </div>
              <time>{displayDate(detail)}</time>
            </section>

            <section className="mail-reader-badges">
              <span className={`mail-tag ${isRead(detail) ? "" : "unread"}`}>
                {isRead(detail) ? "Read" : "Unread"}
              </span>
              {detail.body_source && <span className="mail-tag">Source: {detail.body_source}</span>}
              {hasAttachments(detail) && (
                <span className="mail-tag">Attachments: {detail.attachment_count ?? detail.attachments?.length}</span>
              )}
              {isFlagged(detail) && <span className="mail-tag flagged">Flagged</span>}
              {containsSecret(detail) && (
                <span className="mail-tag secret">Possible secrets: {detail.secret_count ?? 1}</span>
              )}
            </section>

            <section className="mail-inline-actions" aria-label="Message actions">
              <div className="mail-inline-action-copy">
                <span className="mail-action-kicker">AI actions</span>
                <strong>Process this message</strong>
              </div>
              <div className="mail-inline-action-buttons">
                <button
                  type="button"
                  className="mail-primary-action"
                  onClick={summarizeSelected}
                  disabled={summaryLoading || discordSending}
                >
                  {summaryLoading ? "Summarizing..." : "Summarize"}
                </button>
                <button
                  type="button"
                  className="mail-secondary-action"
                  onClick={postSelectedToDiscord}
                  disabled={summaryLoading || discordSending}
                >
                  {discordSending ? "Posting..." : "Post to Discord"}
                </button>
              </div>
              {actionMessage && (
                <p className={`mail-action-status ${actionMessage.kind}`}>{actionMessage.text}</p>
              )}
            </section>

            {(summary || summaryLoading) && (
              <section className="mail-inline-summary">
                <span className="mail-action-kicker">Summary</span>
                {summary ? (
                  <div className="mail-summary-rendered">
                    <Markdown remarkPlugins={[remarkGfm]}>{summary}</Markdown>
                  </div>
                ) : (
                  <p className="mail-summary-placeholder">Generating summary...</p>
                )}
              </section>
            )}

            {containsSecret(detail) && (
              <section className="mail-warning-panel">
                <h3>Possible secrets found</h3>
                <ul>
                  {(detail.secret_findings ?? []).map((finding, index) => (
                    <li key={`${finding.type ?? "secret"}-${index}`}>
                      <strong>{finding.label || finding.type || "Possible secret"}</strong>
                      {finding.evidence && <code>{finding.evidence}</code>}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <section className="mail-body-card">
              {bodyView === "html" && detail.html_body ? (
                <iframe
                  title={`HTML email ${detail.uid}`}
                  className="mail-html-frame"
                  sandbox=""
                  referrerPolicy="no-referrer"
                  srcDoc={detail.html_body}
                />
              ) : (
                <div className="mail-plain-body">{detail.body || "No content."}</div>
              )}
            </section>

            {hasAttachments(detail) && (
              <section className="mail-attachment-panel">
                <h3>Attachments</h3>
                <ul>
                  {(detail.attachments ?? []).map((attachment, index) => (
                    <li key={`${attachment.filename ?? "attachment"}-${index}`}>
                      <span>{attachment.filename || "(unnamed)"}</span>
                      <small>
                        {[attachment.content_type, attachment.size ? `${attachment.size} bytes` : ""]
                          .filter(Boolean)
                          .join(" · ")}
                      </small>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </article>
        )}
      </main>
    </div>
  );
}
