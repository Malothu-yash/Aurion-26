// context/TextSelectionContext.tsx
// Context for managing text selection features across the app

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import { 
  Highlight, 
  MiniAgentSession, 
  TextSelection,
  SaveHighlightRequest
} from '@/shared/types';
import { textSelectionService } from '@/react-app/services/textSelectionService';

interface TextSelectionContextType {
  // State
  highlights: Highlight[];
  miniAgentSessions: MiniAgentSession[];
  activeMiniAgentSession: MiniAgentSession | null;
  isMiniAgentOpen: boolean;
  
  // Text selection
  currentSelection: TextSelection | null;
  showSelectionPopup: boolean;
  selectionPosition: { x: number; y: number };
  
  // Actions
  setCurrentSelection: (selection: TextSelection | null) => void;
  setSelectionPopup: (show: boolean, position?: { x: number; y: number }) => void;
  
  // Highlight actions
  saveHighlight: (request: SaveHighlightRequest) => Promise<void>;
  deleteHighlight: (highlightId: string) => Promise<void>;
  loadHighlights: (messageId?: string) => Promise<void>;
  
  // Mini Agent actions
  openMiniAgent: (session: MiniAgentSession) => void;
  closeMiniAgent: () => void;
  sendMiniAgentMessage: (message: string) => Promise<void>;
  loadMiniAgentSessions: (messageId?: string) => Promise<void>;
  
  // Speaker actions
  speakText: (text: string) => void;
}

const TextSelectionContext = createContext<TextSelectionContextType | undefined>(undefined);

export function TextSelectionProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  
  // State
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [miniAgentSessions, setMiniAgentSessions] = useState<MiniAgentSession[]>([]);
  const [activeMiniAgentSession, setActiveMiniAgentSession] = useState<MiniAgentSession | null>(null);
  const [isMiniAgentOpen, setIsMiniAgentOpen] = useState(false);
  
  const [currentSelection, setCurrentSelection] = useState<TextSelection | null>(null);
  const [showSelectionPopup, setShowSelectionPopup] = useState(false);
  const [selectionPosition, setSelectionPosition] = useState({ x: 0, y: 0 });

  // Text selection handlers
  const handleSetCurrentSelection = useCallback((selection: TextSelection | null) => {
    setCurrentSelection(selection);
  }, []);

  const handleSetSelectionPopup = useCallback((show: boolean, position?: { x: number; y: number }) => {
    setShowSelectionPopup(show);
    if (position) {
      setSelectionPosition(position);
    }
  }, []);

  // Highlight actions
  const saveHighlight = useCallback(async (request: SaveHighlightRequest) => {
    if (!user?.email) return;
    
    try {
      const highlight = await textSelectionService.saveHighlight(request);
      setHighlights(prev => [...prev, highlight]);
    } catch (error) {
      console.error('Failed to save highlight:', error);
    }
  }, [user?.email]);

  const deleteHighlight = useCallback(async (highlightId: string) => {
    try {
      await textSelectionService.deleteHighlight(highlightId);
      setHighlights(prev => prev.filter(h => h.id !== highlightId));
    } catch (error) {
      console.error('Failed to delete highlight:', error);
    }
  }, []);

  const loadHighlights = useCallback(async (messageId?: string) => {
    if (!user?.email) return;
    
    try {
      const highlights = await textSelectionService.getHighlights({
        userId: user.email,
        messageId
      });
      setHighlights(highlights);
    } catch (error) {
      console.error('Failed to load highlights:', error);
    }
  }, [user?.email]);

  // Mini Agent actions
  const openMiniAgent = useCallback((session: MiniAgentSession) => {
    console.log('TextSelectionContext: Opening mini agent session:', session);
    setActiveMiniAgentSession(session);
    setIsMiniAgentOpen(true);
  }, []);

  const closeMiniAgent = useCallback(() => {
    console.log('TextSelectionContext: Closing mini agent');
    setIsMiniAgentOpen(false);
    setActiveMiniAgentSession(null);
  }, []);

  const sendMiniAgentMessage = useCallback(async (message: string) => {
    if (!activeMiniAgentSession || !user?.email) return;
    
    try {
      // Add user message to conversation
      const userMessageObj = {
        role: 'user' as const,
        content: message,
        timestamp: new Date().toISOString()
      };
      
      const updatedSession = {
        ...activeMiniAgentSession,
        conversation: [...activeMiniAgentSession.conversation, userMessageObj]
      };
      
      setActiveMiniAgentSession(updatedSession);
      
      // Send to AI
      const aiResponse = await textSelectionService.sendMiniAgentMessage(
        activeMiniAgentSession.snippet,
        message
      );
      
      // Add AI response to conversation
      const aiMessageObj = {
        role: 'assistant' as const,
        content: aiResponse,
        timestamp: new Date().toISOString()
      };
      
      const finalSession = {
        ...updatedSession,
        conversation: [...updatedSession.conversation, aiMessageObj]
      };
      
      setActiveMiniAgentSession(finalSession);
      
      // Save to backend
      await textSelectionService.saveMiniAgentSession({
        messageId: finalSession.messageId,
        snippet: finalSession.snippet,
        conversation: finalSession.conversation
      });
      
    } catch (error) {
      console.error('Failed to send mini agent message:', error);
    }
  }, [activeMiniAgentSession, user?.email]);

  const loadMiniAgentSessions = useCallback(async (messageId?: string) => {
    if (!user?.email) return;
    
    try {
      const sessions = await textSelectionService.getMiniAgentSessions({
        userId: user.email,
        messageId
      });
      setMiniAgentSessions(sessions);
    } catch (error) {
      console.error('Failed to load mini agent sessions:', error);
    }
  }, [user?.email]);

  // Speaker actions
  const speakText = useCallback((text: string) => {
    console.log('TextSelectionContext: Speaking text:', text);
    if ('speechSynthesis' in window) {
      console.log('Speech synthesis available, creating utterance');
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 0.8;
      
      utterance.onstart = () => console.log('Speech started');
      utterance.onend = () => console.log('Speech ended');
      utterance.onerror = (e) => console.log('Speech error:', e);
      
      window.speechSynthesis.speak(utterance);
    } else {
      console.log('Speech synthesis not available');
    }
  }, []);

  const value: TextSelectionContextType = {
    // State
    highlights,
    miniAgentSessions,
    activeMiniAgentSession,
    isMiniAgentOpen,
    currentSelection,
    showSelectionPopup,
    selectionPosition,
    
    // Actions
    setCurrentSelection: handleSetCurrentSelection,
    setSelectionPopup: handleSetSelectionPopup,
    saveHighlight,
    deleteHighlight,
    loadHighlights,
    openMiniAgent,
    closeMiniAgent,
    sendMiniAgentMessage,
    loadMiniAgentSessions,
    speakText,
  };

  return (
    <TextSelectionContext.Provider value={value}>
      {children}
    </TextSelectionContext.Provider>
  );
}

export function useTextSelection() {
  const context = useContext(TextSelectionContext);
  if (context === undefined) {
    throw new Error('useTextSelection must be used within a TextSelectionProvider');
  }
  return context;
}
