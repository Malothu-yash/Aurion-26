
/**
 * Types shared between the client and server go here.
 */

// Basic message types
export interface Message {
  id: string;
  content: string;
  message_type: 'user' | 'assistant';
  attachments?: any[];
  metadata?: any;
  created_at: string;
}
