import { ENV } from '@/config/env';

export interface HighlightRange {
  start: number;
  end: number;
  text?: string;
}

export interface HighlightsDoc {
  messageId: string;
  sessionId: string;
  ranges: HighlightRange[];
  createdAt: string;
  updatedAt?: string;
}

export interface HighlightAddRequest {
  sessionId: string;
  start: number;
  end: number;
  text?: string;
}

export async function highlightsExists(messageId: string): Promise<boolean> {
  const url = `${ENV.BACKEND_URL}/api/highlights/exists/${encodeURIComponent(messageId)}`;
  try {
    const res = await fetch(url);
    if (!res.ok) return false;
    const data = await res.json();
    return !!data?.exists;
  } catch {
    return false;
  }
}

export async function addHighlight(messageId: string, payload: HighlightAddRequest): Promise<HighlightsDoc> {
  const url = `${ENV.BACKEND_URL}/api/highlights/${encodeURIComponent(messageId)}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    throw new Error(`Add highlight failed: ${res.status} ${txt}`);
  }
  return res.json();
}

export async function getHighlights(messageId: string): Promise<HighlightsDoc | null> {
  const url = `${ENV.BACKEND_URL}/api/highlights/${encodeURIComponent(messageId)}`;
  const res = await fetch(url);
  if (res.status === 404) return null;
  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    throw new Error(`Get highlights failed: ${res.status} ${txt}`);
  }
  return res.json();
}

export async function deleteHighlights(messageId: string): Promise<void> {
  const url = `${ENV.BACKEND_URL}/api/highlights/${encodeURIComponent(messageId)}`;
  const res = await fetch(url, { method: 'DELETE' });
  if (res.status === 404) return;
  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    throw new Error(`Delete highlights failed: ${res.status} ${txt}`);
  }
}
