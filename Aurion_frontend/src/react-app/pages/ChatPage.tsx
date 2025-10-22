import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/react-app/context/AuthContext';
import { ENV } from '@/config/env';
import { useNavigate, useParams } from 'react-router';
import Sidebar from '@/react-app/components/Sidebar';
import ChatInput from '@/react-app/components/ChatInput';
import MessageBubble from '@/react-app/components/MessageBubble';
import WelcomeScreen from '@/react-app/components/WelcomeScreen';
import { Sparkles } from 'lucide-react';

interface Message {
  id: string;
  content: string;
  message_type: 'user' | 'assistant';
  attachments?: any[];
  metadata?: any;
  created_at: string;
}

export default function ChatPage() {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(sessionId || null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Protected route check is now handled by ProtectedRoute component
    // This is just for extra safety
    if (!isAuthenticated) {
      navigate('/');
      return;
    }

    if (sessionId) {
      setCurrentSessionId(sessionId);
      // Note: fetchMessages removed - backend doesn't have session history API yet
      // Messages will be loaded from local storage or fresh chat
    } else {
      // Show welcome screen for new chat
      setMessages([]);
      setCurrentSessionId(null);
    }
  }, [isAuthenticated, sessionId, navigate]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async (content: string, attachments: any[] = []) => {
    if (!content.trim()) return;

    // Use user email as conversation_id for persistent chat history
    const conversationId = user?.email || 'anonymous';

    // Add user message to UI
    const userMessage: Message = {
      id: crypto.randomUUID(),
      content,
      message_type: 'user',
      attachments,
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Create a temporary assistant message for streaming
    const assistantMessageId = crypto.randomUUID();
    const assistantMessage: Message = {
      id: assistantMessageId,
      content: '',
      message_type: 'assistant',
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, assistantMessage]);

    try {
      // Connect to AURION backend streaming endpoint
      const response = await fetch(ENV.CHAT_STREAM, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: content,
          conversation_id: conversationId,
          hint: null
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
            
            // Skip empty lines
            if (!jsonData) continue;
            
            // Try to parse as JSON
            let parsed;
            try {
              parsed = JSON.parse(jsonData);
            } catch {
              // If it's not JSON, treat it as plain text chunk
              accumulatedContent += jsonData;
              setMessages(prev => 
                prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: accumulatedContent }
                    : msg
                )
              );
              continue;
            }

            // Handle different event types
            if (parsed.event === 'text_chunk' && parsed.data) {
              accumulatedContent += parsed.data;
              
              // Update the assistant message in real-time
              setMessages(prev => 
                prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: accumulatedContent }
                    : msg
                )
              );
            }
            // Handle rich content (YouTube, weather, search results, etc.)
            else if (parsed.event === 'rich_content' && parsed.data) {
              try {
                const richContent = typeof parsed.data === 'string' 
                  ? JSON.parse(parsed.data) 
                  : parsed.data;
                
                // Store as metadata for special rendering
                setMessages(prev => 
                  prev.map(msg => 
                    msg.id === assistantMessageId 
                      ? { 
                          ...msg, 
                          content: accumulatedContent || 'Processing your request...',
                          metadata: { richContent }
                        }
                      : msg
                  )
                );
              } catch (e) {
                console.error('Error parsing rich content:', e);
              }
            }
            // Handle errors from backend
            else if (parsed.event === 'error' && parsed.data) {
              console.error('Backend error:', parsed.data);
              accumulatedContent += `\n\n⚠️ ${parsed.data}`;
              setMessages(prev => 
                prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: accumulatedContent }
                    : msg
                )
              );
            }
          } catch (parseError) {
            // Silently ignore parse errors for non-critical data
            console.debug('SSE parse warning:', parseError);
          }
        }
      }

      setIsLoading(false);

    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Show error message to user
      setMessages(prev => 
        prev.map(msg => 
          msg.id === assistantMessageId 
            ? { 
                ...msg, 
                content: `⚠️ Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`
              }
            : msg
        )
      );
      
      setIsLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="h-screen flex items-center justify-center bg-gradient-to-br from-violet-900 via-purple-900/10 to-black">
        <div className="text-center">
          <Sparkles className="w-16 h-16 gradient-text-aurora animate-spin mx-auto mb-4" />
          <p className="text-gray-300">Please sign in to continue</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gradient-to-br from-violet-950/20 via-purple-950/10 to-black flex">
      <Sidebar />
      
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="h-16 border-b border-orange-500/20 flex items-center px-6">
          <div className="flex items-center space-x-3">
            <Sparkles className="w-6 h-6 gradient-text-aurora" />
            <h1 className="text-xl font-semibold text-white">
              {currentSessionId ? 'Chat Session' : 'New Chat'}
            </h1>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <WelcomeScreen onSendMessage={sendMessage} />
          ) : (
            <>
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {isLoading && (
                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-purple-600 flex items-center justify-center">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-gradient-to-r from-purple-900/40 to-violet-900/40 rounded-2xl rounded-tl-sm p-4 max-w-4xl">
                    <div className="flex items-center space-x-2">
                      <div className="typing-indicator">
                        <div className="dot"></div>
                        <div className="dot"></div>
                        <div className="dot"></div>
                      </div>
                      <span className="text-gray-300 text-sm">Aurion is thinking...</span>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Chat Input */}
        <div className="border-t border-orange-500/20 p-6">
          <ChatInput onSendMessage={sendMessage} disabled={isLoading} />
        </div>
      </div>
    </div>
  );
}
