import axios from 'axios';
import { ENV } from '@/config/env';

// Some routes live in the Cloudflare worker under BACKEND_URL + /api (e.g. /api/chat/sessions)
// while the FastAPI backend exposes /api/v1/.. routes. Try worker first, then fall back to API_BASE_URL.
const workerBase = `${ENV.BACKEND_URL.replace(/\/$/, '')}/api`;
const fastApiBase = ENV.API_BASE_URL.replace(/\/$/, '');

const axiosDefault = axios.create({
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

export interface ChatSessionPayload {
  id: string;
  title: string;
  is_pinned?: boolean;
  is_saved?: boolean;
  updated_at?: string;
}

export const chatService = {
  // All methods accept an optional userEmail (x-user-email header) used by FastAPI dev auth
  getSessions: async (userEmail?: string): Promise<ChatSessionPayload[]> => {
    const headers = userEmail ? { 'x-user-email': userEmail } : undefined;
    // Try worker first, then FastAPI
    try {
      console.debug('[chatService] getSessions: trying worker path', `${workerBase}/chat/sessions`);
      const res = await axiosDefault.get(`${workerBase}/chat/sessions`, { headers });
      console.debug('[chatService] getSessions: worker response', res?.data);
      return res.data || [];
    } catch (err) {
  console.debug('[chatService] getSessions: worker failed, falling back to FastAPI', (err as any)?.message || err);
      try {
        const res = await axiosDefault.get(`${fastApiBase}/chat/sessions`, { headers });
        console.debug('[chatService] getSessions: fastapi response', res?.data);
        return res.data || [];
      } catch (err2) {
  console.warn('[chatService] getSessions: both worker and FastAPI failed', (err2 as any)?.message || err2);
        throw err2;
      }
    }
  },

  createSession: async (title?: string, userEmail?: string): Promise<ChatSessionPayload> => {
    const headers = userEmail ? { 'x-user-email': userEmail } : undefined;
    try {
      console.debug('[chatService] createSession: trying worker path', `${workerBase}/chat/sessions`, { title });
      const res = await axiosDefault.post(`${workerBase}/chat/sessions`, { title }, { headers });
      console.debug('[chatService] createSession: worker response', res?.data);
      return res.data;
    } catch (err) {
  console.debug('[chatService] createSession: worker failed, falling back to FastAPI', (err as any)?.message || err);
      try {
        const res = await axiosDefault.post(`${fastApiBase}/chat/sessions`, { title }, { headers });
        console.debug('[chatService] createSession: fastapi response', res?.data);
        return res.data;
      } catch (err2) {
  console.warn('[chatService] createSession: both worker and FastAPI failed', (err2 as any)?.message || err2);
        throw err2;
      }
    }
  },

  deleteSession: async (id: string, userEmail?: string): Promise<void> => {
    const headers = userEmail ? { 'x-user-email': userEmail } : undefined;
    try {
      console.debug('[chatService] deleteSession: trying worker path', `${workerBase}/chat/sessions/${id}`);
      await axiosDefault.delete(`${workerBase}/chat/sessions/${id}`, { headers });
      console.debug('[chatService] deleteSession: worker delete succeeded', id);
    } catch (err) {
  console.debug('[chatService] deleteSession: worker delete failed, falling back to FastAPI', (err as any)?.message || err);
      try {
        await axiosDefault.delete(`${fastApiBase}/chat/sessions/${id}`, { headers });
        console.debug('[chatService] deleteSession: fastapi delete succeeded', id);
      } catch (err2) {
  console.warn('[chatService] deleteSession: both worker and FastAPI delete failed', (err2 as any)?.message || err2);
        throw err2;
      }
    }
  },

  getSessionMessages: async (sessionId: string, userEmail?: string) => {
    const headers = userEmail ? { 'x-user-email': userEmail } : undefined;
    try {
      console.debug('[chatService] getSessionMessages: trying worker path', `${workerBase}/chat/sessions/${sessionId}/messages`);
      const res = await axiosDefault.get(`${workerBase}/chat/sessions/${sessionId}/messages`, { headers });
      console.debug('[chatService] getSessionMessages: worker response', res?.data);
      return res.data || [];
    } catch (err) {
      console.debug('[chatService] getSessionMessages: worker failed, falling back to FastAPI', (err as any)?.message || err);
      try {
        const res = await axiosDefault.get(`${fastApiBase}/chat/sessions/${sessionId}/messages`, { headers });
        console.debug('[chatService] getSessionMessages: fastapi response', res?.data);
        return res.data || [];
      } catch (err2) {
        console.warn('[chatService] getSessionMessages: both worker and FastAPI failed', (err2 as any)?.message || err2);
        throw err2;
      }
    }
  },

  postSessionMessage: async (sessionId: string, body: any, userEmail?: string) => {
    const headers = userEmail ? { 'x-user-email': userEmail } : undefined;
    try {
      console.debug('[chatService] postSessionMessage: trying worker path', `${workerBase}/chat/sessions/${sessionId}/messages`, body);
      const res = await axiosDefault.post(`${workerBase}/chat/sessions/${sessionId}/messages`, body, { headers });
      console.debug('[chatService] postSessionMessage: worker response', res?.data);
      return res.data;
    } catch (err) {
      console.debug('[chatService] postSessionMessage: worker failed, falling back to FastAPI', (err as any)?.message || err);
      try {
        const res = await axiosDefault.post(`${fastApiBase}/chat/sessions/${sessionId}/messages`, body, { headers });
        console.debug('[chatService] postSessionMessage: fastapi response', res?.data);
        return res.data;
      } catch (err2) {
        console.warn('[chatService] postSessionMessage: both worker and FastAPI failed', (err2 as any)?.message || err2);
        throw err2;
      }
    }
  },

  updateSession: async (id: string, body: Partial<ChatSessionPayload>) => {
    // accept optional userEmail inside body or undefined
    const userEmail = (body as any)?.userEmail;
    const headers = userEmail ? { 'x-user-email': userEmail } : undefined;
    try {
      console.debug('[chatService] updateSession: trying worker path', `${workerBase}/chat/sessions/${id}`, body);
      await axiosDefault.put(`${workerBase}/chat/sessions/${id}`, body, { headers });
      console.debug('[chatService] updateSession: worker update succeeded', id);
    } catch (err) {
  console.debug('[chatService] updateSession: worker update failed, falling back to FastAPI', (err as any)?.message || err);
      try {
        await axiosDefault.put(`${fastApiBase}/chat/sessions/${id}`, body, { headers });
        console.debug('[chatService] updateSession: fastapi update succeeded', id);
      } catch (err2) {
  console.warn('[chatService] updateSession: both worker and FastAPI update failed', (err2 as any)?.message || err2);
        throw err2;
      }
    }
  },
};

export default chatService;
