import z from "zod";

/**
 * Types shared between the client and server go here.
 */

// Text Selection and Highlighting Types
export const HighlightSchema = z.object({
  id: z.string(),
  messageId: z.string(),
  userId: z.string(),
  text: z.string(),
  color: z.string(),
  note: z.string().optional(),
  rangeStart: z.number(),
  rangeEnd: z.number(),
  createdAt: z.string(),
});

export const MiniAgentSessionSchema = z.object({
  id: z.string(),
  messageId: z.string(),
  userId: z.string(),
  snippet: z.string(),
  conversation: z.array(z.object({
    role: z.enum(['user', 'assistant']),
    content: z.string(),
    timestamp: z.string(),
  })),
  createdAt: z.string(),
  updatedAt: z.string(),
});

export const TextSelectionSchema = z.object({
  text: z.string(),
  rangeStart: z.number(),
  rangeEnd: z.number(),
  messageId: z.string(),
});

// API Request/Response Types
export const SaveHighlightRequestSchema = z.object({
  messageId: z.string(),
  text: z.string(),
  color: z.string(),
  note: z.string().optional(),
  rangeStart: z.number(),
  rangeEnd: z.number(),
});

export const SaveMiniAgentSessionRequestSchema = z.object({
  messageId: z.string(),
  snippet: z.string(),
  conversation: z.array(z.object({
    role: z.enum(['user', 'assistant']),
    content: z.string(),
    timestamp: z.string(),
  })),
});

export const GetHighlightsRequestSchema = z.object({
  messageId: z.string().optional(),
  userId: z.string(),
});

export const GetMiniAgentSessionsRequestSchema = z.object({
  messageId: z.string().optional(),
  userId: z.string(),
});

// Derived Types
export type Highlight = z.infer<typeof HighlightSchema>;
export type MiniAgentSession = z.infer<typeof MiniAgentSessionSchema>;
export type TextSelection = z.infer<typeof TextSelectionSchema>;
export type SaveHighlightRequest = z.infer<typeof SaveHighlightRequestSchema>;
export type SaveMiniAgentSessionRequest = z.infer<typeof SaveMiniAgentSessionRequestSchema>;
export type GetHighlightsRequest = z.infer<typeof GetHighlightsRequestSchema>;
export type GetMiniAgentSessionsRequest = z.infer<typeof GetMiniAgentSessionsRequestSchema>;

// UI Component Props Types
export interface TextSelectionPopupProps {
  selection: TextSelection;
  position: { x: number; y: number };
  onHighlight: (color: string) => void;
  onMiniAgent: () => void;
  onSpeaker: () => void;
  onClose: () => void;
}

export interface MiniAgentChatProps {
  session: MiniAgentSession;
  isOpen: boolean;
  onClose: () => void;
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export interface HighlightTooltipProps {
  highlight: Highlight;
  position: { x: number; y: number };
  onClose: () => void;
}

// Color palette for highlights
export const HIGHLIGHT_COLORS = [
  { name: 'yellow', value: '#FFD700', bgClass: 'bg-yellow-400' },
  { name: 'green', value: '#90EE90', bgClass: 'bg-green-400' },
  { name: 'blue', value: '#87CEEB', bgClass: 'bg-blue-400' },
  { name: 'red', value: '#FFB6C1', bgClass: 'bg-red-400' },
  { name: 'purple', value: '#DDA0DD', bgClass: 'bg-purple-400' },
  { name: 'orange', value: '#FFA500', bgClass: 'bg-orange-400' },
] as const;

export type HighlightColor = typeof HIGHLIGHT_COLORS[number]['name'];
