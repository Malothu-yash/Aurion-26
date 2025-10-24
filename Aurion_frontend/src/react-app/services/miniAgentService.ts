import { ENV } from '@/config/env';

export interface MiniAgentChatPayload {
  messageId: string;
  selectedText?: string;
  userMessage: string;
  sessionId: string;
}

export interface MiniAgentChatResponse {
  reply: string;
}

export async function miniAgentChat(payload: MiniAgentChatPayload): Promise<MiniAgentChatResponse> {
  const url = `${ENV.BACKEND_URL}/api/mini-agent/chat`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Mini agent chat failed: ${res.status} ${text}`);
  }
  return res.json();
}

export interface MiniAgentMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface MiniAgentConversationDto {
  messageId: string;
  sessionId: string;
  selectedText?: string;
  conversations: MiniAgentMessage[];
  createdAt: string;
  updatedAt?: string;
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function getMiniAgentConversation(messageId: string): Promise<MiniAgentConversationDto | null> {
  if (!messageId) {
    console.warn('miniAgentService.getMiniAgentConversation: empty messageId');
    return null;
  }
  const url = `${ENV.BACKEND_URL}/api/mini-agent/${encodeURIComponent(messageId)}`;
  const maxAttempts = 3;
  const baseDelay = 200; // ms
  let lastErr: any = null;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const res = await fetch(url);
      if (res.status === 404) return null;
      if (res.ok) return res.json();
      // Retry on transient server errors
      if (res.status === 503 || res.status === 502 || res.status === 500) {
        const text = await res.text().catch(() => '');
        lastErr = new Error(`Fetch mini agent conversation failed: ${res.status} ${text}`);
      } else {
        const text = await res.text().catch(() => '');
        throw new Error(`Fetch mini agent conversation failed: ${res.status} ${text}`);
      }
    } catch (e) {
      // Network or parsing error — mark to retry
      lastErr = e;
    }
    if (attempt < maxAttempts) {
      await sleep(baseDelay * Math.pow(2, attempt - 1));
      continue;
    }
  }
  throw lastErr || new Error('Fetch mini agent conversation failed');
}

export async function deleteMiniAgentConversation(messageId: string): Promise<void> {
  const url = `${ENV.BACKEND_URL}/api/mini-agent/${encodeURIComponent(messageId)}`;
  const res = await fetch(url, { method: 'DELETE' });
  if (res.status === 404) return; // already gone
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Delete mini agent conversation failed: ${res.status} ${text}`);
  }
}

// In-memory cache of session → messageIds with mini agent history
const sessionMessageIdsCache = new Map<string, Set<string>>();

// In-memory cache for per-message existence checks to avoid repeated 404 fetches
const conversationExistsCache = new Map<string, boolean>();
const conversationExistsCacheTimestamps = new Map<string, number>();
const EXISTS_TTL_MS = 15000; // 15s throttle for negative checks

export async function getMiniAgentMessageIdsForSession(sessionId: string): Promise<Set<string>> {
  if (sessionMessageIdsCache.has(sessionId)) {
    return sessionMessageIdsCache.get(sessionId)!;
  }
  const url = `${ENV.BACKEND_URL}/api/mini-agent/session/${encodeURIComponent(sessionId)}`;
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Fetch session mini agent overview failed: ${res.status} ${text}`);
  }
  const data = await res.json();
  const set = new Set<string>(Array.isArray(data?.messageIds) ? data.messageIds : []);
  sessionMessageIdsCache.set(sessionId, set);
  return set;
}

export function addMessageIdToSessionCache(sessionId: string, messageId: string) {
  const set = sessionMessageIdsCache.get(sessionId) || new Set<string>();
  set.add(messageId);
  sessionMessageIdsCache.set(sessionId, set);
}

// Mark conversation existence in cache (useful on optimistic create)
export function markMiniAgentConversationExists(messageId: string, exists: boolean = true) {
  conversationExistsCache.set(messageId, exists);
  conversationExistsCacheTimestamps.set(messageId, Date.now());
}

// Lightweight checker to see if a conversation exists for a message without spamming network
export async function miniAgentConversationExists(messageId: string): Promise<boolean> {
  if (!messageId) return false;
  const ts = conversationExistsCacheTimestamps.get(messageId) || 0;
  if (conversationExistsCache.has(messageId) && (Date.now() - ts) < EXISTS_TTL_MS) {
    return conversationExistsCache.get(messageId)!;
  }
  try {
    const url = `${ENV.BACKEND_URL}/api/mini-agent/exists/${encodeURIComponent(messageId)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`exists check failed: ${res.status}`);
    const data = await res.json();
    const exists = !!data?.exists;
    conversationExistsCache.set(messageId, exists);
    conversationExistsCacheTimestamps.set(messageId, Date.now());
    return exists;
  } catch {
    return false;
  }
}
