import { useState, useRef, useEffect, useCallback } from 'react';
import { User, Sparkles, Copy, Check, MoreHorizontal, Trash2, RotateCcw, Archive, Share, Edit3, Youtube, CheckCircle, Search, ExternalLink } from 'lucide-react';
import SelectionPopup from '@/react-app/components/SelectionPopup';
import MiniAgentPanelHost from '@/react-app/components/MiniAgentPanelHost';
import type { HighlightRange } from '@/react-app/services/highlightsService';
import { addHighlight as apiAddHighlight, getHighlights as apiGetHighlights, highlightsExists as apiHighlightsExists } from '@/react-app/services/highlightsService';
// ...existing code...
// ...existing code...

interface Message {
  id: string;
  content: string;
  message_type: 'user' | 'assistant';
  attachments?: any[];
  metadata?: any;
  created_at: string;
}

interface MessageBubbleProps {
  message: Message;
  sessionId?: string;
}

export default function MessageBubble({ message, sessionId: _sessionId }: MessageBubbleProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [showMoreMenu, setShowMoreMenu] = useState(false);
  const [showSelectionPopup, setShowSelectionPopup] = useState(false);
  const [popupPos, setPopupPos] = useState<{ top: number; left: number } | null>(null);
  const [selectedText, setSelectedText] = useState<string>('');
  const [showMiniAgent, setShowMiniAgent] = useState<boolean>(false);
  const [hasMiniAgentHistory, setHasMiniAgentHistory] = useState<boolean>(false);
  const [highlights, setHighlights] = useState<HighlightRange[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const messageRef = useRef<HTMLDivElement>(null);
  const isUser = message.message_type === 'user';

  // Hide popup on scroll or global click
  useEffect(() => {
    const onScroll = () => {
      if (showSelectionPopup) setShowSelectionPopup(false);
    };
    const onMouseDown = (e: MouseEvent) => {
      // If click happens outside the message block, close
      const target = e.target as HTMLElement;
      const insideSelectionPopup = target.closest('[data-selection-popup="true"]');
      if (insideSelectionPopup) return; // allow clicking inside the popup
      if (messageRef.current && !messageRef.current.contains(target)) {
        setShowSelectionPopup(false);
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('mousedown', onMouseDown);
    return () => {
      window.removeEventListener('scroll', onScroll as EventListener);
      window.removeEventListener('mousedown', onMouseDown);
    };
  }, [showSelectionPopup]);

  const handleMouseUp = useCallback(() => {
    if (isUser) return; // Only for assistant messages
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0) {
      setShowSelectionPopup(false);
      return;
    }

    const text = sel.toString().trim();
    if (!text) {
      setShowSelectionPopup(false);
      return;
    }

    // Ensure selection is within this message bubble
    const range = sel.getRangeAt(0);
    const container = range.commonAncestorContainer as Node;
    const nodeForContains = container.nodeType === 3 ? container.parentNode : container;
    if (!messageRef.current || !nodeForContains || !messageRef.current.contains(nodeForContains)) {
      setShowSelectionPopup(false);
      return;
    }

    const rect = range.getBoundingClientRect();
    if (!rect || (rect.width === 0 && rect.height === 0)) {
      setShowSelectionPopup(false);
      return;
    }

    const containerRect = containerRef.current?.getBoundingClientRect();
    const top = rect.top - (containerRect?.top ?? 0) - 40;
    const left = rect.left - (containerRect?.left ?? 0) + rect.width / 2;
    setPopupPos({ top, left });
    setSelectedText(text);
    setShowSelectionPopup(true);
  }, [isUser]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy text:', error);
    }
  };

  const handleSpeakSelected = () => {
    const text = selectedText?.trim();
    if (!text) return;
    try {
      if ('speechSynthesis' in window) {
        const utter = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utter);
      }
    } catch {}
  };

  const handleEdit = () => {
    console.log('Edit message:', message.id);
  };

  const handleDelete = () => {
    if (window.confirm('Delete this message?')) {
      console.log('Delete message:', message.id);
    }
  };

  const handleRegenerate = () => {
    console.log('Regenerate response for:', message.id);
  };

  const handleSave = () => {
    if (window.confirm('Save this message?')) {
      console.log('Save message:', message.id);
    }
  };

  // Load mini-agent history indicator when message mounts/changes
  useEffect(() => {
    let cancelled = false;
    async function checkHistory() {
      if (message.message_type !== 'assistant') return;
      try {
        if (_sessionId) {
          const { getMiniAgentMessageIdsForSession } = await import('@/react-app/services/miniAgentService');
          const set = await getMiniAgentMessageIdsForSession(_sessionId);
          if (!cancelled) setHasMiniAgentHistory(set.has(message.id));
        } else {
          const { miniAgentConversationExists } = await import('@/react-app/services/miniAgentService');
          const exists = await miniAgentConversationExists(message.id);
          if (!cancelled) setHasMiniAgentHistory(exists);
        }
      } catch {
        if (!cancelled) setHasMiniAgentHistory(false);
      }
    }
    checkHistory();
    return () => { cancelled = true; };
  }, [message.id, message.message_type, _sessionId]);

  // Load existing highlights for this message, only if they exist to avoid 404 logs
  useEffect(() => {
    let cancelled = false;
    async function loadHighlights() {
      if (message.message_type !== 'assistant') return;
      try {
        const exists = await apiHighlightsExists(message.id);
        if (!exists) return;
        const doc = await apiGetHighlights(message.id);
        if (!cancelled && doc && Array.isArray(doc.ranges)) {
          setHighlights(doc.ranges.slice().sort((a, b) => a.start - b.start));
        }
      } catch {
        // ignore
      }
    }
    loadHighlights();
    return () => { cancelled = true; };
  }, [message.id, message.message_type]);

  // Utilities to map selection <-> offsets relative to the message content container
  const getContentRoot = () => {
    return messageRef.current?.querySelector('.message-content') as HTMLElement | null;
  };

  const getOffsetsForRange = (range: Range, root: HTMLElement) => {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let pos = 0;
    let startPos: number | null = null;
    let endPos: number | null = null;
    while (walker.nextNode()) {
      const node = walker.currentNode as Text;
      const len = node.nodeValue?.length || 0;
      if (node === range.startContainer) {
        startPos = pos + range.startOffset;
      }
      if (node === range.endContainer) {
        endPos = pos + range.endOffset;
        // We can break after finding end
        break;
      }
      pos += len;
    }
    if (startPos == null || endPos == null) return null;
    if (endPos < startPos) {
      const t = startPos; startPos = endPos; endPos = t;
    }
    return { start: startPos, end: endPos };
  };

  // Apply highlights into DOM by wrapping ranges; first remove existing wrappers
  const applyHighlightsToDom = useCallback(() => {
    const root = getContentRoot();
    if (!root) return;
    // unwrap existing
    root.querySelectorAll('[data-aurion-highlight="true"]').forEach((el) => {
      const span = el as HTMLElement;
      const parent = span.parentNode;
      if (!parent) return;
      while (span.firstChild) parent.insertBefore(span.firstChild, span);
      parent.removeChild(span);
    });
    // helper to find node/offset for absolute position
    const findNodeAt = (absPos: number): { node: Text; offset: number } | null => {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      let pos = 0;
      while (walker.nextNode()) {
        const node = walker.currentNode as Text;
        const len = node.nodeValue?.length || 0;
        if (absPos <= pos + len) {
          return { node, offset: absPos - pos };
        }
        pos += len;
      }
      // If at end, place at last node
      return null;
    };
    const sorted = highlights.slice().sort((a, b) => a.start - b.start);
    for (const h of sorted) {
      if (h.end <= h.start) continue;
      const startLoc = findNodeAt(h.start);
      const endLoc = findNodeAt(h.end);
      if (!startLoc || !endLoc) continue;
      const r = document.createRange();
      r.setStart(startLoc.node, Math.max(0, Math.min(startLoc.offset, startLoc.node.length)));
      r.setEnd(endLoc.node, Math.max(0, Math.min(endLoc.offset, endLoc.node.length)));
      try {
        const mark = document.createElement('mark');
        mark.setAttribute('data-aurion-highlight', 'true');
        mark.className = 'bg-yellow-400/30 text-inherit rounded-sm px-0.5';
        const frag = r.extractContents();
        mark.appendChild(frag);
        r.insertNode(mark);
      } catch {
        // Fallback: ignore this highlight if DOM structure prevents extraction
      }
    }
  }, [highlights]);

  useEffect(() => {
    applyHighlightsToDom();
  }, [applyHighlightsToDom]);

  // After closing panel, re-check if history exists and update icon
  const handleCloseMiniAgent = async () => {
    setShowMiniAgent(false);
    if (message.message_type !== 'assistant') return;
    try {
      if (_sessionId) {
        const { getMiniAgentMessageIdsForSession } = await import('@/react-app/services/miniAgentService');
        const set = await getMiniAgentMessageIdsForSession(_sessionId);
        setHasMiniAgentHistory(set.has(message.id));
      } else {
        const { getMiniAgentConversation } = await import('@/react-app/services/miniAgentService');
        const conv = await getMiniAgentConversation(message.id);
        setHasMiniAgentHistory(!!(conv && Array.isArray(conv.conversations) && conv.conversations.length > 0));
      }
    } catch {
      setHasMiniAgentHistory(false);
    }
  };

  const handleShare = () => {
    console.log('Share message:', message.id);
  };


  // ...existing code...



  // Check for special content types
  const specialContent = message.metadata?.specialContent;
  const isYouTubeVideo = specialContent?.type === 'youtube';
  const isConfirmation = specialContent?.type === 'confirmation';
  const isSearchResults = specialContent?.type === 'searchResults';

  return (
    <div
      className={`flex items-start space-x-4 group ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser 
          ? 'bg-gradient-to-br from-orange-400 to-purple-600' 
          : 'bg-gradient-to-br from-purple-500 to-violet-600'
      }`}>
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Sparkles className="w-4 h-4 text-white" />
        )}
      </div>

  {/* Message Content */}
  <div ref={containerRef} className={`relative flex-1 max-w-4xl ${isUser ? 'text-right' : ''}`}>
        <div
          ref={messageRef}
          className={`inline-block p-4 rounded-2xl relative ${
            isUser
              ? 'bg-gradient-to-r from-orange-500/80 to-purple-600/80 text-white rounded-tr-sm'
              : 'bg-transparent text-gray-100 rounded-tl-sm border-l-4 border-orange-400/50 pl-6'
          }`}
          onMouseUp={handleMouseUp}
        >
          {/* Persistent Mini Agent icon when history exists (anchored to bubble) */}
          {!isUser && hasMiniAgentHistory && (
            <button
              type="button"
              onClick={() => setShowMiniAgent(true)}
              className="absolute -top-2 -right-2 z-20 text-xs px-2 py-1 rounded-full bg-purple-900/60 border border-orange-500/20 text-gray-300 hover:text-white hover:bg-purple-900/80 shadow"
              title="Open Mini Agent"
              aria-label="Open Mini Agent"
            >
              🤖
            </button>
          )}
          {/* Regular text content */}
          {message.content && (
            <div 
              className="whitespace-pre-wrap break-words max-w-full overflow-x-hidden leading-relaxed font-medium selectable-text message-content"
              dangerouslySetInnerHTML={{ __html: message.content }}
            />
          )}

          {/* YouTube Video Embed */}
          {isYouTubeVideo && (
            <div className="mt-4 rounded-xl overflow-hidden border-2 border-orange-500/30">
              <div className="aspect-video bg-black">
                <iframe
                  width="100%"
                  height="100%"
                  src={`https://www.youtube.com/embed/${specialContent.videoId}`}
                  title={specialContent.title}
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  className="w-full h-full"
                ></iframe>
              </div>
              <div className="bg-purple-900/40 p-3 flex items-center space-x-2">
                <Youtube className="w-5 h-5 text-red-500" />
                <span className="text-sm font-medium text-white">{specialContent.title}</span>
              </div>
            </div>
          )}

          {/* Confirmation Message */}
          {isConfirmation && (
            <div className="mt-4 bg-green-900/30 border border-green-500/50 rounded-lg p-4 flex items-start space-x-3">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
              <p className="text-green-100 font-medium">{specialContent.message}</p>
            </div>
          )}

          {/* Search Results */}
          {isSearchResults && (
            <div className="mt-4 space-y-3">
              {/* Search summary */}
              <div className="bg-purple-900/30 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Search className="w-4 h-4 text-orange-400" />
                  <span className="text-xs text-gray-400">Search Results</span>
                </div>
                <p className="text-gray-100 leading-relaxed">{specialContent.summary}</p>
              </div>

              {/* Source links */}
              {specialContent.links && specialContent.links.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Sources</p>
                  {specialContent.links.map((link: any, index: number) => (
                    <a
                      key={index}
                      href={link.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block bg-purple-900/20 hover:bg-purple-900/40 border border-orange-500/20 hover:border-orange-500/50 rounded-lg p-3 transition-all duration-200 group"
                    >
                      <div className="flex items-start justify-between space-x-3">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-orange-400 group-hover:text-orange-300 line-clamp-1">
                            {link.title}
                          </p>
                          {link.snippet && (
                            <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                              {link.snippet}
                            </p>
                          )}
                        </div>
                        <ExternalLink className="w-4 h-4 text-gray-500 group-hover:text-orange-400 flex-shrink-0" />
                      </div>
                    </a>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Timestamp */}
          <div className={`text-xs mt-2 opacity-70 ${
            isUser ? 'text-white/80' : 'text-gray-400'
          }`}>
            {new Date(message.created_at).toLocaleTimeString()}
          </div>
        </div>

        {/* Floating selection popup (Step 1) */}
        {!isUser && showSelectionPopup && popupPos && (
          <SelectionPopup
            visible={true}
            top={popupPos.top}
            left={popupPos.left}
            onRequestClose={() => setShowSelectionPopup(false)}
            onMiniAgentClick={() => { setShowSelectionPopup(false); setShowMiniAgent(true); }}
            onHighlightClick={async () => {
              try {
                const sel = window.getSelection();
                const root = getContentRoot();
                if (!sel || sel.rangeCount === 0 || !root) return;
                const range = sel.getRangeAt(0);
                const offsets = getOffsetsForRange(range, root);
                if (!offsets) return;
                const payload = {
                  sessionId: _sessionId || 'unknown',
                  start: offsets.start,
                  end: offsets.end,
                  text: selectedText || undefined,
                };
                const doc = await apiAddHighlight(message.id, payload);
                if (doc && Array.isArray(doc.ranges)) {
                  setHighlights(doc.ranges.slice().sort((a, b) => a.start - b.start));
                } else {
                  setHighlights((prev) => [...prev, { start: offsets.start, end: offsets.end, text: selectedText || undefined }]);
                }
              } catch {}
              finally {
                setShowSelectionPopup(false);
              }
            }}
            onSpeakClick={() => { handleSpeakSelected(); setShowSelectionPopup(false); }}
          />
        )}
        {/* Mini Agent Panel */}
        {!isUser && (
          <MiniAgentPanelHost
            visible={showMiniAgent}
            onClose={handleCloseMiniAgent}
            selectedText={selectedText}
            messageId={message.id}
            sessionId={_sessionId || ''}
            onHistoryAvailable={async () => {
              setHasMiniAgentHistory(true);
              if (_sessionId) {
                const { addMessageIdToSessionCache } = await import('@/react-app/services/miniAgentService');
                addMessageIdToSessionCache(_sessionId, message.id);
              }
              // Also mark existence cache to prevent future unnecessary GETs
              try {
                const { markMiniAgentConversationExists } = await import('@/react-app/services/miniAgentService');
                markMiniAgentConversationExists(message.id, true);
              } catch {}
            }}
          />
        )}

        {/* Action Buttons */}
        {isHovered && (
          <div className={`flex items-center space-x-2 mt-2 ${
            isUser ? 'justify-end' : 'justify-start'
          }`}>
            {isUser ? (
              // User message actions
              <>
                <button
                  onClick={handleEdit}
                  className="p-2 rounded-lg bg-purple-900/40 text-gray-400 hover:text-orange-400 hover:bg-purple-900/60 transition-all duration-200 opacity-0 group-hover:opacity-100"
                  title="Edit message"
                >
                  <Edit3 className="w-4 h-4" />
                </button>
                <button
                  onClick={handleCopy}
                  className="p-2 rounded-lg bg-purple-900/40 text-gray-400 hover:text-green-400 hover:bg-purple-900/60 transition-all duration-200 opacity-0 group-hover:opacity-100"
                  title="Copy message"
                >
                  {isCopied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                </button>
              </>
            ) : (
              // AI message actions
              <>
                <button
                  onClick={handleCopy}
                  className="p-2 rounded-lg bg-purple-900/40 text-gray-400 hover:text-green-400 hover:bg-purple-900/60 transition-all duration-200 opacity-0 group-hover:opacity-100"
                  title="Copy message"
                >
                  {isCopied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                </button>
                
                
                <div className="relative">
                  <button
                    onClick={() => setShowMoreMenu(!showMoreMenu)}
                    className="p-2 rounded-lg bg-purple-900/40 text-gray-400 hover:text-white hover:bg-purple-900/60 transition-all duration-200 opacity-0 group-hover:opacity-100"
                    title="More options"
                  >
                    <MoreHorizontal className="w-4 h-4" />
                  </button>
                  
                  {showMoreMenu && (
                    <div className="absolute bottom-full right-0 mb-2 bg-purple-950/90 backdrop-blur-lg border border-orange-500/20 rounded-lg shadow-xl p-2 min-w-40 animate-fade-in-up z-50">
                      <button
                        onClick={handleDelete}
                        className="w-full flex items-center space-x-3 p-2 rounded-lg hover:bg-red-900/40 transition-colors duration-200 text-gray-300 hover:text-red-300"
                      >
                        <Trash2 className="w-4 h-4" />
                        <span>Delete</span>
                      </button>
                      <button
                        onClick={handleRegenerate}
                        className="w-full flex items-center space-x-3 p-2 rounded-lg hover:bg-purple-900/40 transition-colors duration-200 text-gray-300 hover:text-white"
                      >
                        <RotateCcw className="w-4 h-4" />
                        <span>Regenerate</span>
                      </button>
                      <button
                        onClick={handleSave}
                        className="w-full flex items-center space-x-3 p-2 rounded-lg hover:bg-green-900/40 transition-colors duration-200 text-gray-300 hover:text-green-300"
                      >
                        <Archive className="w-4 h-4" />
                        <span>Save</span>
                      </button>
                      <button
                        onClick={handleShare}
                        className="w-full flex items-center space-x-3 p-2 rounded-lg hover:bg-blue-900/40 transition-colors duration-200 text-gray-300 hover:text-blue-300"
                      >
                        <Share className="w-4 h-4" />
                        <span>Share</span>
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>

    </div>
  );
}