import { X, GripHorizontal, Send, Copy, Volume2, Paperclip, Trash2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

interface MiniAgentPanelHostProps {
  visible: boolean;
  selectedText: string;
  onClose: () => void;
  messageId?: string;
  sessionId?: string;
  onHistoryAvailable?: () => void;
}

export default function MiniAgentPanelHost({ visible, selectedText, onClose, messageId, sessionId, onHistoryAvailable }: MiniAgentPanelHostProps) {
  const dragRef = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState(false);
  const [resizing, setResizing] = useState(false);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [size, setSize] = useState<{ width: number; height: number }>(() => {
    // Default around 350px with sane bounds for small screens
    const vw = typeof window !== 'undefined' ? window.innerWidth : 1024;
    const initialWidth = Math.min(Math.max(320, 350), Math.max(350, Math.min(420, vw - 40)));
    return { width: initialWidth, height: 420 };
  });
  const startPos = useRef({ x: 0, y: 0 });
  const startOffset = useRef({ x: 0, y: 0 });
  const startSize = useRef<{ width: number; height: number }>({ width: 380, height: 420 });
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const [messages, setMessages] = useState<Array<{ id: string; role: 'user' | 'assistant'; content: string }>>([
    { id: 'welcome', role: 'assistant', content: "I'm your Mini Agent. Ask me anything about the selected snippet." },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  useEffect(() => {
    const onPointerMove = (e: PointerEvent) => {
      if (dragging) {
        const dx = e.clientX - startPos.current.x;
        const dy = e.clientY - startPos.current.y;
        setOffset({ x: startOffset.current.x + dx, y: startOffset.current.y + dy });
      } else if (resizing) {
        const dx = e.clientX - startPos.current.x;
        const dy = e.clientY - startPos.current.y;
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const minW = 280;
        const maxW = Math.min(560, vw - 32);
        const minH = 260;
        const maxH = Math.min(720, vh - 32);
        setSize({
          width: Math.max(minW, Math.min(maxW, startSize.current.width + dx)),
          height: Math.max(minH, Math.min(maxH, startSize.current.height + dy)),
        });
      }
    };
    const onPointerUp = () => { setDragging(false); setResizing(false); };
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
    return () => {
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
    };
  }, [dragging]);

  // Auto-scroll to bottom on new messages and while thinking
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, isThinking]);

  // Ensure pinned to bottom on open
  useEffect(() => {
    if (!visible) return;
    const el = scrollContainerRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [visible]);

  // While typing, keep view scrolled to bottom
  useEffect(() => {
    if (!visible) return;
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [visible, inputValue]);

  // Load saved conversation if available
  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!visible || !messageId) return;
      setIsLoadingHistory(true);
      try {
        const { getMiniAgentConversation } = await import('@/react-app/services/miniAgentService');
        const conv = await getMiniAgentConversation(messageId);
        if (!cancelled) {
          if (conv && Array.isArray(conv.conversations) && conv.conversations.length > 0) {
            setMessages(
              conv.conversations.map((m, idx) => ({ id: `${idx}-${m.role}`, role: m.role, content: m.content }))
            );
          } else {
            // keep default welcome message
          }
        }
      } catch {
        // ignore fetch errors; panel will just show welcome
      } finally {
        if (!cancelled) setIsLoadingHistory(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [visible, messageId]);

  const onPointerDown = (e: React.PointerEvent) => {
    setDragging(true);
    startPos.current = { x: e.clientX, y: e.clientY };
    startOffset.current = { ...offset };
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
  };
  const onResizeDown = (e: React.PointerEvent) => {
    e.preventDefault();
    setResizing(true);
    startPos.current = { x: e.clientX, y: e.clientY };
    startSize.current = { ...size };
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
  };

  const handleCopy = async (text: string) => {
    try { await navigator.clipboard.writeText(text); } catch {}
  };

  const handleSpeak = (text: string) => {
    try {
      if ('speechSynthesis' in window) {
        const utter = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utter);
      }
    } catch {}
  };

  const handleClearHistory = async () => {
    if (!messageId) return;
    const ok = window.confirm('Clear mini agent history for this message?');
    if (!ok) return;
    try {
      const { deleteMiniAgentConversation } = await import('@/react-app/services/miniAgentService');
      await deleteMiniAgentConversation(messageId);
      setMessages([{ id: 'welcome', role: 'assistant', content: "I'm your Mini Agent. Ask me anything about the selected snippet." }]);
    } catch (e) {
      // Optionally surface error in UI
    }
  };

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const content = inputValue.trim();
    if (!content && attachedFiles.length === 0) return;
    const userMsg = { id: crypto.randomUUID(), role: 'user' as const, content: content || '(sent attachments)' };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setAttachedFiles([]);
    setIsThinking(true);
    // Optimistically mark history as available for this message
    onHistoryAvailable?.();
    try {
      const { miniAgentChat } = await import('@/react-app/services/miniAgentService');
      const payload = {
        messageId: messageId || 'unknown',
        selectedText: selectedText || undefined,
        userMessage: content,
        sessionId: sessionId || 'unknown'
      };
      const res = await miniAgentChat(payload);
      setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', content: res.reply }]);
    } catch (err: any) {
      const errText = err?.message || 'Mini Agent failed to reply.';
      setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', content: `Error: ${errText}` }]);
    } finally {
      setIsThinking(false);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const onFilesPicked = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files ? Array.from(e.target.files) : [];
    if (files.length) setAttachedFiles(prev => [...prev, ...files]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div
      style={{ transform: `translate(${offset.x}px, ${offset.y}px)` }}
      className="absolute top-0 right-0 z-[9998] pointer-events-auto"
      aria-hidden={!visible}
    >
      <AnimatePresence>
        {visible && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 8 }}
            transition={{ type: 'spring', stiffness: 420, damping: 28, mass: 0.6 }}
            className="rounded-2xl bg-gradient-to-br from-violet-950/95 via-purple-950/90 to-black/80 border border-orange-500/25 shadow-2xl backdrop-blur-md overflow-hidden will-change-transform"
            style={{ width: size.width, height: size.height, maxWidth: '92vw', maxHeight: '80vh' }}
          >
        <div className="flex h-full flex-col">
          <div
            ref={dragRef}
            onPointerDown={onPointerDown}
            className="cursor-grab active:cursor-grabbing flex items-center justify-between px-4 py-3 bg-purple-900/40 border-b border-orange-500/20"
          >
            <div className="flex items-center gap-2">
              <GripHorizontal className="w-4 h-4 text-orange-300" />
              <h3 className="text-sm font-semibold text-white tracking-wide">Mini Agent</h3>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleClearHistory}
                className="p-1.5 rounded-lg text-gray-300 hover:text-white hover:bg-purple-800/60"
                title="Clear history"
                aria-label="Clear history"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={onClose}
                className="p-1.5 rounded-lg text-gray-300 hover:text-white hover:bg-purple-800/60"
                aria-label="Close mini agent"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {selectedText && (
            <div className="px-4 py-3 bg-purple-900/30 border-b border-orange-500/20">
              <p className="text-xs text-gray-300 italic line-clamp-3">“{selectedText}”</p>
            </div>
          )}

          {/* Conversation Area */}
          <div ref={scrollContainerRef} className="flex-1 p-4 overflow-y-auto space-y-3 custom-scrollbar">
            {isLoadingHistory && (
              <div className="text-xs text-gray-300/80">Loading previous messages…</div>
            )}
            {messages.map((m) => (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ type: 'spring', stiffness: 500, damping: 35, mass: 0.6 }}
                className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm leading-relaxed shadow-sm ${
                    m.role === 'user'
                      ? 'bg-gradient-to-r from-orange-500 to-purple-600 text-white rounded-br-sm'
                      : 'bg-purple-900/50 text-gray-100 border border-orange-500/20 rounded-bl-sm'
                  }`}
                >
                  <div className="whitespace-pre-wrap break-words">{m.content}</div>
                  <div className={`mt-1 flex items-center gap-2 ${m.role === 'user' ? 'justify-end' : 'justify-start'} opacity-80`}>
                    <button onClick={() => handleCopy(m.content)} className="p-1.5 rounded-md text-gray-200/90 hover:text-white hover:bg-white/10" title="Copy">
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={() => handleSpeak(m.content)} className="p-1.5 rounded-md text-gray-200/90 hover:text-white hover:bg-white/10" title="Speak">
                      <Volume2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
            <div ref={endOfMessagesRef} />
            {isThinking && (
              <div className="flex items-center gap-2 text-gray-300/80 text-xs">
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-orange-400 rounded-full animate-bounce [animation-delay:-0.2s]"></span>
                  <span className="w-1.5 h-1.5 bg-orange-400 rounded-full animate-bounce [animation-delay:-0.1s]"></span>
                  <span className="w-1.5 h-1.5 bg-orange-400 rounded-full animate-bounce"></span>
                </div>
                <span>Mini Agent is thinking…</span>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-3 border-t border-orange-500/20 bg-purple-950/60 relative">
            {attachedFiles.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-2">
                {attachedFiles.map((f, idx) => (
                  <span key={idx} className="text-xs px-2 py-1 rounded-md bg-purple-900/50 border border-orange-500/20 text-gray-300">{f.name}</span>
                ))}
              </div>
            )}
            <form onSubmit={handleSend} className="flex items-end gap-2">
              <button type="button" onClick={() => fileInputRef.current?.click()} className="p-2 rounded-lg bg-purple-900/40 text-gray-300 hover:text-white hover:bg-purple-900/60" title="Attach files">
                <Paperclip className="w-4 h-4" />
              </button>
              <input ref={fileInputRef} type="file" multiple hidden onChange={onFilesPicked} />
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={onKeyDown}
                rows={1}
                placeholder="Ask something..."
                className="flex-1 resize-none bg-purple-900/40 border border-orange-500/30 rounded-lg px-3 py-2 text-sm text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-400/40 max-h-32"
                onInput={(e) => { const el = e.currentTarget; el.style.height = 'auto'; el.style.height = Math.min(128, el.scrollHeight) + 'px'; }}
              />
              <button type="submit" disabled={!inputValue.trim() && attachedFiles.length === 0} className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-gradient-to-r from-orange-500 to-purple-600 text-white text-sm font-medium hover:from-orange-400 hover:to-purple-500 shadow disabled:opacity-50 disabled:cursor-not-allowed">
                <Send className="w-4 h-4" />
                Send
              </button>
            </form>
            <div onPointerDown={onResizeDown} className="absolute -bottom-2 -right-2 w-4 h-4 cursor-se-resize" title="Resize">
              <div className="w-full h-full bg-orange-500/60 rounded-sm shadow" />
            </div>
          </div>
        </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
