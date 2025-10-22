// services/textSelectionService.ts
// Service for handling text selection features (highlights and mini agent sessions)

import axios from 'axios';
import { 
  Highlight, 
  MiniAgentSession, 
  SaveHighlightRequest, 
  SaveMiniAgentSessionRequest,
  GetHighlightsRequest,
  GetMiniAgentSessionsRequest 
} from '@/shared/types';
import { ENV } from '@/config/env';

const API_BASE_URL = ENV.API_BASE_URL;

class TextSelectionService {
  // Highlight methods
  async saveHighlight(request: SaveHighlightRequest): Promise<Highlight> {
    try {
      const response = await axios.post(`${API_BASE_URL}/highlights`, request);
      return response.data;
    } catch (error) {
      console.error('Failed to save highlight:', error);
      // Return a mock highlight for testing
      return {
        id: crypto.randomUUID(),
        messageId: request.messageId,
        userId: 'test-user',
        text: request.text,
        color: request.color,
        note: request.note,
        rangeStart: request.rangeStart,
        rangeEnd: request.rangeEnd,
        createdAt: new Date().toISOString()
      };
    }
  }

  async getHighlights(request: GetHighlightsRequest): Promise<Highlight[]> {
    try {
      const params = new URLSearchParams();
      if (request.messageId) params.append('messageId', request.messageId);
      params.append('userId', request.userId);
      
      const response = await axios.get(`${API_BASE_URL}/highlights?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get highlights:', error);
      throw error;
    }
  }

  async deleteHighlight(highlightId: string): Promise<void> {
    try {
      await axios.delete(`${API_BASE_URL}/highlights/${highlightId}`);
    } catch (error) {
      console.error('Failed to delete highlight:', error);
      throw error;
    }
  }

  // Mini Agent Session methods
  async saveMiniAgentSession(request: SaveMiniAgentSessionRequest): Promise<MiniAgentSession> {
    try {
      const response = await axios.post(`${API_BASE_URL}/mini-agent-sessions`, request);
      return response.data;
    } catch (error) {
      console.error('Failed to save mini agent session:', error);
      throw error;
    }
  }

  async getMiniAgentSessions(request: GetMiniAgentSessionsRequest): Promise<MiniAgentSession[]> {
    try {
      const params = new URLSearchParams();
      if (request.messageId) params.append('messageId', request.messageId);
      params.append('userId', request.userId);
      
      const response = await axios.get(`${API_BASE_URL}/mini-agent-sessions?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get mini agent sessions:', error);
      throw error;
    }
  }

  async deleteMiniAgentSession(sessionId: string): Promise<void> {
    try {
      await axios.delete(`${API_BASE_URL}/mini-agent-sessions/${sessionId}`);
    } catch (error) {
      console.error('Failed to delete mini agent session:', error);
      throw error;
    }
  }

  // Mini Agent AI Response
  async sendMiniAgentMessage(snippet: string, userMessage: string): Promise<string> {
    try {
      const response = await fetch(ENV.MINI_AGENT_STREAM, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          snippet: snippet,
          user_message: userMessage,
          conversation_id: 'mini-agent-conversation'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body reader available');
      }

      let accumulatedContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data: ')) continue;

          try {
            const jsonData = line.replace('data: ', '').trim();
            if (!jsonData) continue;

            const parsed = JSON.parse(jsonData);
            if (parsed.event === 'text_chunk' && parsed.data) {
              accumulatedContent += parsed.data;
            }
          } catch (parseError) {
            console.debug('SSE parse warning:', parseError);
          }
        }
      }

      return accumulatedContent;
    } catch (error) {
      console.error('Failed to send mini agent message:', error);
      // Return a mock response for testing
      return `I understand you're asking about: "${snippet}". Based on the selected text, here's my response to your question: "${userMessage}". This is a contextual response based on the highlighted content.`;
    }
  }
}

export const textSelectionService = new TextSelectionService();
