export type ApiEnvelope<T> =
  | { status: "success"; data: T }
  | { status: "error"; message: string };

export interface EmailListItem {
  uid: string;
  sender: string;
  subject: string;
  date: string;
  date_display?: string;
  snippet: string;
  mailbox?: string;
  body_source?: string;
  attachment_count?: number;
  attachments?: Array<{ filename?: string; content_type?: string; size?: number }>;
  flags?: string[];
  is_read?: boolean;
  is_unread?: boolean;
  is_flagged?: boolean;
  has_html?: boolean;
  contains_secret?: boolean;
  secret_count?: number;
  secret_types?: string[];
  secret_findings?: SecretFinding[];
  search_text?: string;
}

export interface EmailDetailData {
  uid: string;
  sender: string;
  subject: string;
  date: string;
  date_display?: string;
  body: string;
  body_source?: string;
  summary?: string;
  html_body?: string;
  has_html?: boolean;
  mailbox?: string;
  attachments?: Array<{ filename?: string; content_type?: string; size?: number }>;
  attachment_count?: number;
  flags?: string[];
  is_read?: boolean;
  is_unread?: boolean;
  is_flagged?: boolean;
  contains_secret?: boolean;
  secret_count?: number;
  secret_types?: string[];
  secret_findings?: SecretFinding[];
  search_text?: string;
}

export interface SecretFinding {
  type?: string;
  label?: string;
  evidence?: string;
}

export interface OfflineEnvelope<T> {
  status: "success" | "error";
  data?: T;
  manifest?: { count?: number; generated_at?: string; uids?: string[] };
  message?: string;
  command?: string;
  fetched?: number;
  target?: number;
}

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  return (await res.json()) as T;
}

export const api = {
  emails: () =>
    getJson<{ status: string; data?: EmailListItem[]; message?: string }>("/api/emails"),
  email: (uid: string) =>
    getJson<{ status: string; data?: EmailDetailData; message?: string }>(
      `/api/email/${encodeURIComponent(uid)}`,
    ),
  summary: (uid: string) =>
    getJson<{ status: string; summary?: string; message?: string }>(
      `/api/email/${encodeURIComponent(uid)}/summary`,
    ),
  sendDiscord: (uid: string) =>
    getJson<{ status: string; message?: string }>(
      `/api/email/${encodeURIComponent(uid)}/discord`,
      { method: "POST" },
    ),
  offlineEmails: () => getJson<OfflineEnvelope<EmailListItem[]>>("/api/offline/emails"),
  offlineFetchMore: (count = 25) =>
    getJson<OfflineEnvelope<EmailListItem[]>>("/api/offline/fetch-more", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ count }),
    }),
  offlineEmail: (uid: string) =>
    getJson<OfflineEnvelope<EmailDetailData>>(
      `/api/offline/email/${encodeURIComponent(uid)}`,
    ),
  offlineSummary: (uid: string) =>
    getJson<{ status: string; summary?: string; message?: string }>(
      `/api/offline/email/${encodeURIComponent(uid)}/summary`,
    ),
  sendOfflineDiscord: (uid: string) =>
    getJson<{ status: string; message?: string; summary?: string }>(
      `/api/offline/email/${encodeURIComponent(uid)}/discord`,
      { method: "POST" },
    ),
};
