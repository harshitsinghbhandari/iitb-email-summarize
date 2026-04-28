export type ApiEnvelope<T> =
  | { status: "success"; data: T }
  | { status: "error"; message: string };

export interface EmailListItem {
  uid: string;
  sender: string;
  subject: string;
  date: string;
  snippet: string;
}

export interface EmailDetailData {
  uid: string;
  sender: string;
  subject: string;
  date: string;
  body: string;
  summary?: string;
  html_body?: string;
  attachments?: Array<{ filename: string; content_type: string; size: number }>;
  flags?: string[];
}

export interface OfflineEnvelope<T> {
  status: "success" | "error";
  data?: T;
  manifest?: { count?: number; generated_at?: string; uids?: string[] };
  message?: string;
  command?: string;
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
  offlineEmail: (uid: string) =>
    getJson<OfflineEnvelope<EmailDetailData>>(
      `/api/offline/email/${encodeURIComponent(uid)}`,
    ),
};
