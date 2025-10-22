import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import { Bot, Send, X, Minimize2, Maximize2, MessageSquare, Lightbulb, Zap, BookOpen, Code, Search, Languages, FileText, Brain, Sparkles, Pin, PinOff, RotateCcw, Copy } from 'lucide-react';
import { MiniAgentChatProps } from '@/shared/types';
import MiniAgentErrorBoundary from './ErrorBoundary';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import { usePerformanceMonitoring } from '../hooks/usePerformanceMonitoring';

const MiniAgentChat = memo(function MiniAgentChat({
  session,
  isOpen,
  onClose,
  onSendMessage,
  isLoading,
}: MiniAgentChatProps) {
  const [isMinimized, setIsMinimized] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [isPinned, setIsPinned] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [position, setPosition] = useState({ x: window.innerWidth - 450, y: 100 });
  const [inputValue, setInputValue] = useState('');
  const [showQuickSuggestions, setShowQuickSuggestions] = useState(true);
  const [showAdvancedActions, setShowAdvancedActions] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [typingText, setTypingText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const chatRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Performance monitoring
  const { trackRequest } = usePerformanceMonitoring();
  
  // Keyboard shortcuts
  useKeyboardShortcuts({
    onOpenMiniAgent: () => {
      if (!isOpen) {
        // Mini Agent is closed, but we can't open it from here
        // This would be handled by the parent component
      }
    },
    onCloseMiniAgent: onClose,
    onToggleHighlight: () => {
      // This would be handled by the parent component
    }
  });

  // Generate intelligent quick suggestions based on snippet content
  const generateQuickSuggestions = useCallback(() => {
    const text = session.snippet.toLowerCase();
    const suggestions = [];
    
    // Code-related suggestions
    if (text.includes('code') || text.includes('function') || text.includes('class') || text.includes('api')) {
      suggestions.push(
        { icon: Code, text: 'Explain code', action: 'Can you explain this code step by step?' },
        { icon: Search, text: 'Find examples', action: 'Show me similar code examples' },
        { icon: FileText, text: 'Debug help', action: 'Help me debug this code' }
      );
    }
    
    // Error/problem-related suggestions
    if (text.includes('error') || text.includes('problem') || text.includes('issue') || text.includes('bug')) {
      suggestions.push(
        { icon: Zap, text: 'Fix this', action: 'How can I fix this problem?' },
        { icon: Search, text: 'Common solutions', action: 'What are common solutions for this?' },
        { icon: Brain, text: 'Troubleshoot', action: 'Help me troubleshoot this step by step' }
      );
    }
    
    // Learning/educational content
    if (text.includes('learn') || text.includes('understand') || text.includes('concept') || text.includes('theory')) {
      suggestions.push(
        { icon: BookOpen, text: 'Explain simply', action: 'Explain this in simple terms' },
        { icon: Brain, text: 'Deep dive', action: 'Give me a detailed explanation' },
        { icon: Search, text: 'Related topics', action: 'What topics are related to this?' }
      );
    }
    
    // Default suggestions
    if (suggestions.length === 0) {
      suggestions.push(
        { icon: BookOpen, text: 'Explain this', action: 'Can you explain this concept in simple terms?' },
        { icon: FileText, text: 'Summarize', action: 'Give me a quick summary of this' },
        { icon: Search, text: 'Find related', action: 'What are related topics to this?' },
        { icon: Zap, text: 'Quick help', action: 'How can this help me?' }
      );
    }
    
    return suggestions.slice(0, 4);
  }, [session.snippet]);

  const quickSuggestions = generateQuickSuggestions();

  // Advanced action suggestions
  const advancedActions = [
    { icon: Languages, text: 'Translate', action: 'Translate this to another language' },
    { icon: FileText, text: 'Summarize', action: 'Create a detailed summary' },
    { icon: Brain, text: 'Analyze', action: 'Analyze this content deeply' },
    { icon: Code, text: 'Code it', action: 'Convert this to code' },
    { icon: Search, text: 'Research', action: 'Research this topic further' },
    { icon: Sparkles, text: 'Improve', action: 'How can this be improved?' }
  ];

  // Drag functionality
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.target !== e.currentTarget) return; // Only drag from header
    setIsDragging(true);
    const rect = chatRef.current?.getBoundingClientRect();
    if (rect) {
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      });
    }
  }, []);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragOffset.x,
      y: e.clientY - dragOffset.y
    });
  }, [isDragging, dragOffset]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // Typing animation for AI responses
  useEffect(() => {
    if (isLoading && session.conversation.length > 0) {
      const lastMessage = session.conversation[session.conversation.length - 1];
      if (lastMessage.role === 'assistant') {
        setIsTyping(true);
        setTypingText('');
        let index = 0;
        const text = lastMessage.content;
        
        const typeText = () => {
          if (index < text.length) {
            setTypingText(text.slice(0, index + 1));
            index++;
            typingTimeoutRef.current = setTimeout(typeText, 20);
          } else {
            setIsTyping(false);
          }
        };
        
        typeText();
      }
    }
    
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, [isLoading, session.conversation]);

  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus();
    }
  }, [isOpen, isMinimized]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [session.conversation, typingText]);

  const handleSendMessage = useCallback(() => {
    if (inputValue.trim() && !isLoading) {
      const startTime = Date.now();
      
      // Track the request start
      const message = inputValue.trim();
      onSendMessage(message);
      setInputValue('');
      setShowQuickSuggestions(false); // Hide suggestions after first message
      
      // Track performance (success will be determined by the response)
      setTimeout(() => {
        trackRequest(startTime, true); // Assume success for now
      }, 100);
    }
  }, [inputValue, isLoading, onSendMessage, trackRequest]);

  const handleQuickSuggestion = (suggestion: string) => {
    onSendMessage(suggestion);
    setShowQuickSuggestions(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getWindowSize = () => {
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
      return {
        width: window.innerWidth - 20,
        height: window.innerHeight * 0.5,
        x: 10,
        y: window.innerHeight * 0.5,
      };
    }
    
    if (isMaximized) {
      return {
        width: window.innerWidth - 40,
        height: window.innerHeight - 100,
        x: 20,
        y: 20,
      };
    }
    
    return {
      width: 420,
      height: 600,
      x: position.x,
      y: position.y,
    };
  };

  if (!isOpen) return null;

  const isMobile = window.innerWidth <= 768;
  const windowSize = getWindowSize();

  return (
    <MiniAgentErrorBoundary>
      <div
        ref={chatRef}
        className={`fixed z-50 ${isMobile ? 'mini-agent-mobile' : ''} ${isDragging ? 'cursor-grabbing' : 'cursor-grab'} ${isPinned ? 'ring-2 ring-orange-400/50' : ''}`}
        style={{
          width: windowSize.width,
          height: windowSize.height,
          left: windowSize.x,
          top: windowSize.y,
          transform: isDragging ? 'scale(1.02)' : 'scale(1)',
          transition: isDragging ? 'none' : 'transform 0.2s ease-out',
        }}
      >
      <div className="w-full h-full bg-purple-950/95 backdrop-blur-lg border border-orange-500/30 rounded-xl shadow-2xl overflow-hidden animate-fade-in-up">
        {/* Header */}
        <div 
          className="drag-handle flex items-center justify-between p-4 border-b border-orange-500/20 bg-purple-900/50 cursor-grab active:cursor-grabbing"
          onMouseDown={handleMouseDown}
        >
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center animate-pulse">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-semibold text-white">Mini Agent</h3>
                {isPinned && <Pin className="w-3 h-3 text-orange-400" />}
                {isTyping && (
                  <div className="flex space-x-1">
                    <div className="w-1 h-1 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-1 h-1 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-1 h-1 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                )}
              </div>
              <p className="text-xs text-gray-400 truncate max-w-48">
                Context: "{session.snippet.substring(0, 30)}..."
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-1">
            {/* Pin/Unpin button */}
            <button
              onClick={() => setIsPinned(!isPinned)}
              className="p-1 rounded-lg hover:bg-orange-900/30 transition-colors duration-200 text-gray-400 hover:text-orange-400"
              title={isPinned ? 'Unpin' : 'Pin to stay on top'}
            >
              {isPinned ? <PinOff className="w-4 h-4" /> : <Pin className="w-4 h-4" />}
            </button>
            
            {/* Advanced actions toggle */}
            <button
              onClick={() => setShowAdvancedActions(!showAdvancedActions)}
              className="p-1 rounded-lg hover:bg-purple-800/50 transition-colors duration-200 text-gray-400 hover:text-purple-300"
              title="Advanced actions"
            >
              <Sparkles className="w-4 h-4" />
            </button>
            
            {/* Minimize button */}
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-1 rounded-lg hover:bg-purple-800/50 transition-colors duration-200 text-gray-400 hover:text-white"
              title={isMinimized ? 'Restore' : 'Minimize'}
            >
              {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
            </button>
            
            {/* Maximize button */}
            <button
              onClick={() => setIsMaximized(!isMaximized)}
              className="p-1 rounded-lg hover:bg-purple-800/50 transition-colors duration-200 text-gray-400 hover:text-white"
              title={isMaximized ? 'Restore' : 'Maximize'}
            >
              {isMaximized ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
            
            {/* Close button */}
            <button
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-red-900/50 transition-colors duration-200 text-gray-400 hover:text-red-300"
              title="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {!isMinimized && (
          <>
            {/* Advanced Actions Panel */}
            {showAdvancedActions && (
              <div className="border-b border-orange-500/20 p-3 bg-purple-900/30">
                <div className="flex items-center space-x-2 mb-3">
                  <Sparkles className="w-4 h-4 text-purple-400" />
                  <span className="text-sm font-medium text-white">Advanced Actions</span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {advancedActions.map((action, index) => (
                    <button
                      key={index}
                      onClick={() => handleQuickSuggestion(action.action)}
                      className="flex items-center space-x-2 p-2 rounded-lg bg-purple-800/30 hover:bg-purple-800/50 transition-colors duration-200 text-gray-200 hover:text-white text-xs"
                    >
                      <action.icon className="w-3 h-3 text-orange-400 flex-shrink-0" />
                      <span className="truncate">{action.text}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 max-h-96">
              {/* Context snippet with enhanced styling */}
              <div className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 border border-blue-500/30 rounded-lg p-3 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5"></div>
                <div className="relative">
                  <div className="flex items-center space-x-2 mb-2">
                    <MessageSquare className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-semibold text-blue-400">Context</span>
                    <div className="flex-1 h-px bg-gradient-to-r from-blue-500/30 to-transparent"></div>
                  </div>
                  <p className="text-sm text-gray-200 italic leading-relaxed">"{session.snippet}"</p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-gray-500">
                      {session.conversation.length} messages
                    </span>
                    <button
                      onClick={() => {
                        // Reset conversation logic here
                      }}
                      className="text-xs text-orange-400 hover:text-orange-300 transition-colors duration-200 flex items-center space-x-1"
                    >
                      <RotateCcw className="w-3 h-3" />
                      <span>Reset</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Conversation messages with enhanced styling */}
              {session.conversation.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} group`}
                >
                  <div
                    className={`max-w-xs p-3 rounded-lg relative ${
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-orange-500/80 to-orange-600/80 text-white rounded-tr-sm shadow-lg'
                        : 'bg-gradient-to-r from-purple-900/40 to-purple-800/40 text-gray-200 rounded-tl-sm border-l-2 border-orange-400/50 shadow-lg'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
                    <div className="flex items-center justify-between mt-2">
                      <p className="text-xs opacity-70">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </p>
                      {message.role === 'assistant' && (
                        <div className="flex items-center space-x-1">
                          <button
                            onClick={() => {
                              // Copy message content
                              navigator.clipboard.writeText(message.content);
                            }}
                            className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 p-1 rounded hover:bg-white/10"
                            title="Copy"
                          >
                            <Copy className="w-3 h-3" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* Enhanced loading indicator */}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gradient-to-r from-purple-900/40 to-purple-800/40 text-gray-200 rounded-lg p-3 border-l-2 border-orange-400/50 shadow-lg">
                    <div className="flex items-center space-x-2">
                      <div className="typing-indicator">
                        <div className="dot"></div>
                        <div className="dot"></div>
                        <div className="dot"></div>
                      </div>
                      <span className="text-sm">Mini Agent is thinking...</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Typing animation for AI responses */}
              {isTyping && typingText && (
                <div className="flex justify-start">
                  <div className="bg-gradient-to-r from-purple-900/40 to-purple-800/40 text-gray-200 rounded-lg p-3 border-l-2 border-orange-400/50 shadow-lg">
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{typingText}</p>
                    <div className="flex items-center space-x-1 mt-2">
                      <div className="w-1 h-1 bg-orange-400 rounded-full animate-pulse"></div>
                      <div className="w-1 h-1 bg-orange-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                      <div className="w-1 h-1 bg-orange-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Enhanced Quick Suggestions */}
            {showQuickSuggestions && session.conversation.length === 0 && (
              <div className="border-t border-orange-500/20 p-4 bg-gradient-to-r from-purple-900/10 to-orange-900/10">
                <div className="flex items-center space-x-2 mb-3">
                  <Lightbulb className="w-4 h-4 text-purple-400" />
                  <span className="text-sm font-medium text-white">Smart Suggestions</span>
                  <div className="flex-1 h-px bg-gradient-to-r from-purple-500/30 to-transparent"></div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {quickSuggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleQuickSuggestion(suggestion.action)}
                      className="flex items-center space-x-2 p-3 rounded-lg bg-gradient-to-r from-purple-900/30 to-purple-800/30 hover:from-purple-900/50 hover:to-purple-800/50 transition-all duration-200 text-gray-200 hover:text-white text-sm group border border-purple-500/20 hover:border-purple-400/40"
                    >
                      <suggestion.icon className="w-4 h-4 text-orange-400 flex-shrink-0 group-hover:scale-110 transition-transform duration-200" />
                      <span className="truncate font-medium">{suggestion.text}</span>
                    </button>
                  ))}
                </div>
                <div className="mt-3 text-xs text-gray-500 text-center">
                  Click any suggestion to start the conversation
                </div>
              </div>
            )}

            {/* Enhanced Input Area */}
            <div className="border-t border-orange-500/20 p-4 bg-gradient-to-r from-purple-900/20 to-orange-900/20">
              <div className="flex items-center space-x-2">
                <div className="flex-1 relative">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask about the selected text..."
                    className="w-full bg-purple-900/50 border border-orange-500/30 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-orange-400/60 focus:ring-2 focus:ring-orange-400/30 transition-all duration-200"
                    disabled={isLoading}
                  />
                  {isLoading && (
                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                      <div className="w-4 h-4 border-2 border-orange-400 border-t-transparent rounded-full animate-spin"></div>
                    </div>
                  )}
                </div>
                <button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isLoading}
                  className="p-3 bg-gradient-to-r from-orange-500/80 to-orange-600/80 hover:from-orange-500 hover:to-orange-600 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-all duration-200 shadow-lg hover:shadow-orange-500/25 group"
                  title="Send message"
                >
                  <Send className="w-4 h-4 group-hover:scale-110 transition-transform duration-200" />
                </button>
              </div>
              
              {/* Input hints */}
              <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                <span>Press Enter to send, Shift+Enter for new line</span>
                <span>{inputValue.length}/500</span>
              </div>
            </div>
          </>
        )}
      </div>
      </div>
    </MiniAgentErrorBoundary>
  );
});

export default MiniAgentChat;
