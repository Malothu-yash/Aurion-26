/*
// (commented out legacy file)
import { X, GripHorizontal, Send } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

interface MiniAgentPanelProps {
  visible: boolean;
  selectedText: string;
  onClose: () => void;
}

export default function MiniAgentPanelHost({ visible, selectedText, onClose }: MiniAgentPanelProps) {
  const dragRef = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState(false);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const startPos = useRef({ x: 0, y: 0 });
  const startOffset = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const onPointerMove = (e: PointerEvent) => {
      if (!dragging) return;
      const dx = e.clientX - startPos.current.x;
      const dy = e.clientY - startPos.current.y;
      setOffset({ x: startOffset.current.x + dx, y: startOffset.current.y + dy });
    };
    const onPointerUp = () => {
      setDragging(false);
    };
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
    return () => {
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
    };
  }, [dragging]);

  const onPointerDown = (e: React.PointerEvent) => {
    setDragging(true);
    startPos.current = { x: e.clientX, y: e.clientY };
    startOffset.current = { ...offset };
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
  };

  return (
    <div
      // Outer container handles dragging offset; anchored to right side of message container
      style={{ transform: `translate(${offset.x}px, ${offset.y}px)` }}
      className="absolute top-0 right-0 z-[9998] max-w-[92vw] sm:max-w-[80vw] md:max-w-[420px] w-[88vw] sm:w-[70vw] md:w-[380px]"
      aria-hidden={!visible}
    >
      <div
        className={`rounded-2xl bg-purple-950/90 border border-orange-500/25 shadow-2xl backdrop-blur-md overflow-hidden
        transition-transform transition-opacity duration-300 ease-out
        ${visible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-full'}`}
      >
        // {/* Header with drag handle */}
        <div
          ref={dragRef}
          onPointerDown={onPointerDown}
          className="cursor-grab active:cursor-grabbing flex items-center justify-between px-4 py-3 bg-purple-900/50 border-b border-orange-500/20"
        >
          <div className="flex items-center gap-2">
            <GripHorizontal className="w-4 h-4 text-orange-300" />
            <h3 className="text-sm font-semibold text-white tracking-wide">Mini Agent</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-300 hover:text-white hover:bg-purple-800/60"
            aria-label="Close mini agent"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Selected snippet */}
        {selectedText && (
          <div className="px-4 py-3 bg-purple-900/30 border-b border-orange-500/20">
            <p className="text-xs text-gray-300 italic line-clamp-3">“{selectedText}”</p>
          </div>
        )}

        {/* Conversation area */}
        <div className="p-4 max-h-[45vh] sm:max-h-[50vh] overflow-y-auto space-y-3">
          <div className="text-xs text-gray-400">
            Ask questions about the selected text. This mini thread is scoped to this message.
          </div>
          {/* Placeholder conversation bubble */}
          <div className="bg-purple-900/40 border border-orange-500/20 rounded-xl p-3 text-sm text-gray-100">
            I’m your Mini Agent. How can I help with this snippet?
          </div>
        </div>

        {/* Input area */}
        <div className="p-3 border-t border-orange-500/20 bg-purple-950/60">
          <form className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Ask something..."
              className="flex-1 bg-purple-900/40 border border-orange-500/30 rounded-lg px-3 py-2 text-sm text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-400/40"
            />
            <button
              type="submit"
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-gradient-to-r from-orange-500 to-purple-600 text-white text-sm font-medium hover:from-orange-400 hover:to-purple-500 shadow"
            >
              <Send className="w-4 h-4" />
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
 

  setIsLoading(true);
    try {
      // Simulate quick action response
      setTimeout(() => {
        const assistantMessage: MiniAgentMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Quick action "${action}" applied to: "${selectedText}". This is a simulated response for the ${action} action.`,
          created_at: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        setIsLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Error with quick action:', error);
      setIsLoading(false);
    }
  };

  const quickActions = [
    { id: 'summarize', label: 'Summarize', icon: MessageSquare },
    { id: 'explain', label: 'Explain', icon: Lightbulb },
    { id: 'translate', label: 'Translate', icon: Languages },
    { id: 'create_task', label: 'Create Task', icon: CheckSquare },
    { id: 'clarify', label: 'Clarify', icon: HelpCircle }
  ];

  return (
    <div
      ref={panelRef}
      className={`fixed z-[9999] bg-gradient-to-br from-purple-950/95 to-violet-950/95 backdrop-blur-xl border border-orange-500/30 rounded-2xl shadow-2xl transition-all duration-500 ${
        isMinimized ? 'h-12' : ''
      } ${
        isVisible ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-95 translate-y-4'
      }`}
      style={{
        left: panelPosition.x,
        top: panelPosition.y,
        width: isMinimized ? 'auto' : panelSize.width,
        height: isMinimized ? 'auto' : panelSize.height,
        zIndex: 9999
      }}
    >
      {/* Header with fade-in */}
      <div 
        className="drag-handle flex items-center justify-between p-4 border-b border-orange-500/20 bg-gradient-to-r from-purple-900/30 to-orange-900/30 rounded-t-2xl cursor-move"
        onMouseDown={handleMouseDown}
      >
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-orange-500 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Mini Agent</h3>
            <p className="text-xs text-gray-400">Context-aware assistant</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-2 rounded-lg hover:bg-purple-800/50 text-gray-400 hover:text-white transition-all duration-200"
          >
            {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
          </button>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-300 transition-all duration-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Message Content for Selection */}
          <div className="p-3 border-b border-orange-500/20 bg-gradient-to-r from-blue-900/20 to-purple-900/20">
            <div className="text-xs text-gray-400 mb-1 flex items-center space-x-1">
              <span>📝</span>
              <span>Select text from below:</span>
            </div>
            <div
              className="text-sm text-gray-200 bg-black/20 rounded-lg p-2 max-h-24 overflow-y-auto selectable-text"
              style={{ userSelect: 'text', cursor: 'text' }}
              dangerouslySetInnerHTML={{ __html: messageContent }}
            />
            {selectedText && (
              <div className="mt-2 text-xs text-orange-300 font-semibold">Selected: <span className="bg-orange-900/40 px-1 rounded">{selectedText}</span></div>
            )}
          </div>

          {/* Chat Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 max-h-80 custom-scrollbar">
            {messages.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-purple-500/20 to-orange-500/20 flex items-center justify-center mx-auto mb-3">
                  <Sparkles className="w-6 h-6 text-orange-400" />
                </div>
                <p className="text-sm text-gray-400">Ask me anything about the selected text!</p>
                <div className="flex flex-wrap gap-2 mt-4 justify-center">
                  {quickActions.map((action) => (
                    <button
                      key={action.id}
                      onClick={() => handleQuickAction(action.id)}
                      className="px-3 py-1 rounded-full bg-purple-800/30 hover:bg-purple-800/50 text-gray-300 hover:text-white text-xs transition-all duration-200"
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
                >
                  <div
                    className={`max-w-[80%] p-3 rounded-2xl message-bubble ${
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-orange-500/20 to-purple-600/20 text-orange-100 rounded-br-sm'
                        : 'bg-gradient-to-r from-purple-800/30 to-violet-800/30 text-gray-100 rounded-bl-sm border-l-4 border-orange-400/50'
                    }`}
                  >
                    <div className="text-sm leading-relaxed">{message.content}</div>
                    <div className="text-xs opacity-70 mt-1">
                      {new Date(message.created_at).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {isLoading && (
              <div className="flex justify-start animate-fade-in-up">
                <div className="bg-gradient-to-r from-purple-800/30 to-violet-800/30 text-gray-100 p-3 rounded-2xl rounded-bl-sm border-l-4 border-orange-400/50">
                  <div className="flex items-center space-x-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-orange-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions */}
          <div className="p-3 border-t border-orange-500/20">
            <div className="text-xs text-gray-400 mb-2">Quick Actions:</div>
            <div className="flex flex-wrap gap-2">
              {quickActions.map((action) => (
                <button
                  key={action.id}
                  onClick={() => handleQuickAction(action.id)}
                  disabled={isLoading}
                  className="flex items-center space-x-1 px-2 py-1 rounded bg-purple-800/30 hover:bg-purple-800/50 text-gray-300 hover:text-white text-xs transition-colors disabled:opacity-50"
                >
                  <action.icon className="w-3 h-3" />
                  <span>{action.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-orange-500/20 bg-gradient-to-r from-purple-900/20 to-orange-900/20 rounded-b-2xl">
            <div className="flex space-x-2">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask about the selected text..."
                className="flex-1 bg-black/30 border border-orange-500/20 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-400/20 transition-all duration-200"
                disabled={isLoading}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="px-4 py-3 bg-gradient-to-r from-orange-500/20 to-purple-500/20 hover:from-orange-500/30 hover:to-purple-500/30 text-orange-300 hover:text-orange-200 rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
        </>
      )}

      {/* Resize Handle */}
      {!isMinimized && (
        <div
          className="absolute bottom-0 right-0 w-4 h-4 cursor-se-resize"
          onMouseDown={(e) => {
            e.preventDefault();
            setIsResizing(true);
          }}
        >
          <div className="w-full h-full bg-orange-500/30 rounded-tl-lg"></div>
        </div>
      )}
    </div>
  );
}