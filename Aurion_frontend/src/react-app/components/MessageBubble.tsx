import { useState, useRef, useEffect, useCallback } from 'react';
import { User, Sparkles, Copy, Check, MoreHorizontal, Trash2, RotateCcw, Archive, Share, Edit3, Youtube, CheckCircle, Search, ExternalLink } from 'lucide-react';
import SelectionPopup from '@/react-app/components/SelectionPopup';
import MiniAgentPanelHost from '@/react-app/components/MiniAgentPanelHost';
import type { HighlightRange } from '@/react-app/services/highlightsService';
import { addHighlight as apiAddHighlight, getHighlights as apiGetHighlights, highlightsExists as apiHighlightsExists, removeHighlightRange as apiRemoveHighlightRange } from '@/react-app/services/highlightsService';
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
  const [selectionOffsets, setSelectionOffsets] = useState<{ start: number; end: number } | null>(null);
  const [showUnhighlightBtn, setShowUnhighlightBtn] = useState<boolean>(false);
  const [showMiniAgent, setShowMiniAgent] = useState<boolean>(false);
  const [hasMiniAgentHistory, setHasMiniAgentHistory] = useState<boolean>(false);
  const [highlights, setHighlights] = useState<HighlightRange[]>([]);
  const [lastHighlightDebug, setLastHighlightDebug] = useState<string | null>(null);
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
    try {
      const root = getContentRoot();
      const offsets = getOffsetsForRange(range, root!);
      if (offsets) {
        setSelectionOffsets({ start: offsets.start, end: offsets.end });
        const overlaps = highlights.some((h) => h.start < offsets.end && h.end > offsets.start);
        setShowUnhighlightBtn(overlaps);
      } else {
        setSelectionOffsets(null);
        setShowUnhighlightBtn(false);
      }
    } catch (e) {
      setSelectionOffsets(null);
      setShowUnhighlightBtn(false);
    }
    console.debug('[MessageBubble] selection detected', { text, top, left });
    setShowSelectionPopup(true);
  }, [isUser, highlights]);

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
          setHighlights(normalizeRanges(doc.ranges));
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

  // Build HTML string with <mark> wrappers for ranges so React can render highlights
  const buildHighlightedHtml = (html: string, ranges: HighlightRange[]) => {
    if (!html) return html;
    // If no ranges, return original
    if (!ranges || ranges.length === 0) return html;

    // Parse HTML into a temporary container
    const container = document.createElement('div');
    container.innerHTML = html;

    // Helper to escape HTML in text nodes
    const escapeHtml = (s: string) => s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] as string));

    // Sort ranges
    const sortedRanges = ranges.slice().sort((a, b) => a.start - b.start);

    // Walk text nodes and inject <mark> wrappers where ranges apply
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
    let pos = 0; // cumulative text position
    let rIdx = 0;
    while (walker.nextNode()) {
      const node = walker.currentNode as Text;
      const text = node.nodeValue || '';
      const nodeStart = pos;
      const nodeEnd = pos + text.length;
      if (rIdx >= sortedRanges.length) {
        pos = nodeEnd;
        continue;
      }

      // If current range ends before this node, advance rIdx
      while (rIdx < sortedRanges.length && sortedRanges[rIdx].end <= nodeStart) rIdx++;
      if (rIdx >= sortedRanges.length) { pos = nodeEnd; continue; }

      // Build fragments for this text node
      const parts: string[] = [];
      let cur = 0;
      let j = rIdx;
      while (j < sortedRanges.length && sortedRanges[j].start < nodeEnd) {
        const range = sortedRanges[j];
        const overlapStart = Math.max(range.start, nodeStart) - nodeStart;
        const overlapEnd = Math.min(range.end, nodeEnd) - nodeStart;
        if (overlapEnd <= overlapStart) { j++; continue; }
        // plain text before
        if (overlapStart > cur) parts.push(escapeHtml(text.slice(cur, overlapStart)));
        // highlighted part
        const snippet = escapeHtml(text.slice(overlapStart, overlapEnd));
        const colorMap: Record<string, string> = {
          yellow: 'rgba(250, 204, 21, 0.28)',
          pink: 'rgba(236, 72, 153, 0.24)',
          green: 'rgba(110, 231, 183, 0.22)',
          blue: 'rgba(96, 165, 250, 0.22)'
        };
        const color = (range as any).color ? ((colorMap as any)[(range as any).color] || (range as any).color) : colorMap.yellow;
        parts.push(`<mark data-aurion-highlight="true" style="background-color: ${color};">${snippet}</mark>`);
        cur = overlapEnd;
        if (range.end <= nodeEnd) j++; else break;
      }
      // remainder
      if (cur < text.length) parts.push(escapeHtml(text.slice(cur)));

      if (parts.length > 0) {
        const wrapper = document.createElement('span');
        wrapper.innerHTML = parts.join('');
        const frag = document.createDocumentFragment();
        while (wrapper.firstChild) frag.appendChild(wrapper.firstChild);
        node.parentNode?.replaceChild(frag, node);
      }

      pos = nodeEnd;
    }

    return container.innerHTML;
  };

  // Memoize computed HTML so we don't recompute on every render
  const computedHtml = (() => {
    try {
      return buildHighlightedHtml(message.content || '', highlights || []);
    } catch (e) {
      return message.content || '';
    }
  })();

  // Normalize highlight ranges: sort, deduplicate identical ranges and merge overlaps
  const normalizeRanges = (ranges: HighlightRange[] | undefined): HighlightRange[] => {
    if (!ranges || ranges.length === 0) return [];
    const arr = ranges.slice().map(r => ({ start: r.start, end: r.end, text: r.text, color: (r as any).color } as HighlightRange));
    arr.sort((a, b) => a.start - b.start || a.end - b.end);
    const out: HighlightRange[] = [];
    for (const r of arr) {
      if (out.length === 0) { out.push({ ...r }); continue; }
      const last = out[out.length - 1];
      // If duplicate or overlapping/adjacent, merge
      if (r.start <= last.end) {
        // extend end to the farthest
        last.end = Math.max(last.end, r.end);
        // prefer the newer color (r) if provided
        if ((r as any).color) last.color = (r as any).color;
        // merge text if missing
        if (!last.text && r.text) last.text = r.text;
      } else {
        out.push({ ...r });
      }
    }
    return out;
  };

  const getOffsetsForRange = (range: Range, root: HTMLElement) => {
    // Robust implementation that resolves element containers to their
    // nearest text node descendants. This avoids failing when selection
    // start/end containers are ELEMENT_NODEs (e.g., when selection crosses
    // inline elements or contains markup).
    const resolveTextNode = (container: Node, offset: number): { node: Text | null; offset: number } => {
      if (!container) return { node: null, offset: 0 };
      if (container.nodeType === Node.TEXT_NODE) return { node: container as Text, offset };
      // If container is an element, try to find the text node at or after the child index
      const el = container as Element;
      const children = Array.from(el.childNodes || []);

      // Helper: find first text node in subtree (depth-first)
      const findFirstText = (n: Node | null): Text | null => {
        if (!n) return null;
        if (n.nodeType === Node.TEXT_NODE) return n as Text;
        for (let i = 0; i < (n.childNodes?.length || 0); i++) {
          const found = findFirstText(n.childNodes[i]);
          if (found) return found;
        }
        return null;
      };

      // Helper: find last text node in subtree
      const findLastText = (n: Node | null): Text | null => {
        if (!n) return null;
        if (n.nodeType === Node.TEXT_NODE) return n as Text;
        for (let i = (n.childNodes?.length || 0) - 1; i >= 0; i--) {
          const found = findLastText(n.childNodes[i]);
          if (found) return found;
        }
        return null;
      };

      // Prefer the node at child index 'offset' (start of that child)
      let child = children[offset] || null;
      if (child) {
        const first = findFirstText(child);
        if (first) return { node: first, offset: 0 };
      }

      // Otherwise, search forward from the offset for the next text node
      for (let i = offset; i < children.length; i++) {
        const first = findFirstText(children[i]);
        if (first) return { node: first, offset: 0 };
      }

      // If none found forward, search backward from offset-1
      for (let i = Math.min(offset - 1, children.length - 1); i >= 0; i--) {
        const last = findLastText(children[i]);
        if (last) return { node: last, offset: (last.nodeValue || '').length };
      }

      // As a last resort, search entire root for a text node
      const fallback = findFirstText(root);
      if (fallback) return { node: fallback, offset: 0 };
      return { node: null, offset: 0 };
    };

    // Walk all text nodes and compute cumulative positions
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let pos = 0;
    let startPos: number | null = null;
    let endPos: number | null = null;

    // Determine resolved start and end text nodes + offsets
    const startResolved = resolveTextNode(range.startContainer, range.startOffset);
    const endResolved = resolveTextNode(range.endContainer, range.endOffset);
    if (!startResolved.node || !endResolved.node) return null;

    while (walker.nextNode()) {
      const node = walker.currentNode as Text;
      const len = node.nodeValue?.length || 0;
      if (node === startResolved.node && startPos == null) {
        startPos = pos + Math.max(0, Math.min(startResolved.offset, len));
      }
      if (node === endResolved.node && endPos == null) {
        endPos = pos + Math.max(0, Math.min(endResolved.offset, len));
        // We can break after finding end
        break;
      }
      pos += len;
    }

    if (startPos == null || endPos == null) {
      // Fallback: try to locate the selected string inside the root text
      try {
        const selText = range.toString();
        const full = root.innerText || root.textContent || '';
        const idx = full.indexOf(selText);
        if (selText && idx >= 0) {
          return { start: idx, end: idx + selText.length };
        }
      } catch {}
      return null;
    }
    if (endPos < startPos) {
      const t = startPos; startPos = endPos; endPos = t;
    }
    return { start: startPos, end: endPos };
  };

  // Apply highlights into DOM by wrapping ranges; first remove existing wrappers
  const applyHighlightsToDom = useCallback(() => {
    const root = getContentRoot();
    if (!root) return;
    console.debug('[MessageBubble] applyHighlightsToDom start', { highlights });
    // unwrap existing non-optimistic highlights
    const existingMarks = Array.from(root.querySelectorAll('[data-aurion-highlight="true"]')) as HTMLElement[];
    let removedCount = 0;
    for (const el of existingMarks) {
      if (el.getAttribute('data-aurion-optimistic') === 'true') continue;
      const span = el as HTMLElement;
      const parent = span.parentNode;
      if (!parent) continue;
      while (span.firstChild) parent.insertBefore(span.firstChild, span);
      parent.removeChild(span);
      removedCount++;
    }
    console.debug('[MessageBubble] unwrapped non-optimistic highlights', { removedCount });

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
    console.debug('[MessageBubble] applying sorted highlights', { sorted });
    for (const h of sorted) {
      if (h.end <= h.start) continue;
      const startLoc = findNodeAt(h.start);
      const endLoc = findNodeAt(h.end);
      if (!startLoc || !endLoc) {
        console.debug('[MessageBubble] failed to find nodes for highlight', { highlight: h, startLoc, endLoc });
        continue;
      }
      const r = document.createRange();
      r.setStart(startLoc.node, Math.max(0, Math.min(startLoc.offset, startLoc.node.length)));
      r.setEnd(endLoc.node, Math.max(0, Math.min(endLoc.offset, endLoc.node.length)));
      try {
        const mark = document.createElement('mark');
        mark.setAttribute('data-aurion-highlight', 'true');
        mark.className = 'text-inherit rounded-sm px-0.5';
        // Map color names to CSS background colors; allow direct hex as well
        const colorMap: Record<string, string> = {
          yellow: 'rgba(250, 204, 21, 0.28)',
          pink: 'rgba(236, 72, 153, 0.24)',
          green: 'rgba(110, 231, 183, 0.22)',
          blue: 'rgba(96, 165, 250, 0.22)'
        };
        const bg = (h as any).color ? (colorMap[(h as any).color] || (h as any).color) : colorMap.yellow;
        (mark.style as any).backgroundColor = bg;
        // Add a transient class so the new highlight flashes briefly
        mark.classList.add('new-highlight');
        const frag = r.extractContents();
        mark.appendChild(frag);
        r.insertNode(mark);
        // Remove the transient class after animation completes
        try {
          setTimeout(() => mark.classList.remove('new-highlight'), 800);
        } catch {}
        console.debug('[MessageBubble] inserted mark for highlight', { highlight: h });
      } catch (err) {
        console.debug('[MessageBubble] error inserting mark', { err, highlight: h });
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
              dangerouslySetInnerHTML={{ __html: computedHtml }}
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
            onHighlightClick={async (color) => {
              try {
                console.debug('[MessageBubble] highlight requested', { selectedText, color });
                const sel = window.getSelection();
                const root = getContentRoot();
                if (!sel) {
                  console.debug('[MessageBubble] no selection object');
                  setLastHighlightDebug('No selection available');
                  return;
                }
                if (sel.rangeCount === 0) {
                  console.debug('[MessageBubble] rangeCount is 0');
                  setLastHighlightDebug('No selection range');
                  return;
                }
                if (!root) {
                  console.debug('[MessageBubble] content root not found');
                  setLastHighlightDebug('Content root not found');
                  return;
                }
                const range = sel.getRangeAt(0);
                console.debug('[MessageBubble] range', { startContainer: range.startContainer.nodeName, endContainer: range.endContainer.nodeName, startOffset: range.startOffset, endOffset: range.endOffset });
                const offsets = getOffsetsForRange(range, root);
                console.debug('[MessageBubble] computed offsets', { offsets });
                if (!offsets) {
                  setLastHighlightDebug('Failed to compute offsets for selection');
                  return;
                }

                // If offsets are equal (zero-length), try a safer fallback by searching
                // the selected text in the root's plain text. This often fixes cases
                // where DOM ranges map to the same absolute index due to markup.
                if (offsets.start === offsets.end) {
                  try {
                    const selText = (selectedText || '').trim();
                    const full = (root.textContent || '').replace(/\s+/g, ' ').trim();
                    const normalizedSel = selText.replace(/\s+/g, ' ').trim();
                    const idx = normalizedSel ? full.indexOf(normalizedSel) : -1;
                    console.debug('[MessageBubble] fallback search', { fullSample: full.slice(0, 200), normalizedSel, idx });
                    if (idx >= 0) {
                      offsets.start = idx;
                      offsets.end = idx + normalizedSel.length;
                    } else {
                      setLastHighlightDebug('Could not resolve selection to offsets');
                      return;
                    }
                  } catch (e) {
                    setLastHighlightDebug('Could not resolve selection to offsets');
                    return;
                  }
                }
                const payload = {
                  sessionId: _sessionId || 'unknown',
                  start: offsets.start,
                  end: offsets.end,
                  text: selectedText || undefined,
                  color: color || undefined,
                };

                // Optimistic UI: apply highlight directly to the current DOM Range so user
                // sees immediate feedback while we persist to the backend.
                try {
                  const markEl = document.createElement('mark');
                  markEl.setAttribute('data-aurion-highlight', 'true');
                  markEl.setAttribute('data-aurion-optimistic', 'true');
                  markEl.className = 'text-inherit rounded-sm px-0.5';
                  const colorMap: Record<string, string> = {
                    yellow: 'rgba(250, 204, 21, 0.28)',
                    pink: 'rgba(236, 72, 153, 0.24)',
                    green: 'rgba(110, 231, 183, 0.22)',
                    blue: 'rgba(96, 165, 250, 0.22)'
                  };
                  const bg = (color && (colorMap as any)[color]) ? (colorMap as any)[color] : (color || colorMap.yellow);
                  (markEl.style as any).backgroundColor = bg;
                  markEl.classList.add('new-highlight');
                  const cloneRange = range.cloneRange();
                  const frag = cloneRange.extractContents();
                  markEl.appendChild(frag);
                  cloneRange.insertNode(markEl);
                  setTimeout(() => markEl.classList.remove('new-highlight'), 800);
                } catch (e) {
                  console.debug('[MessageBubble] optimistic highlight failed', e);
                }
                // Also update highlights state optimistically so applyHighlightsToDom
                // will include this range and persist visual state across re-renders.
                try {
                  setHighlights((prev) => {
                    const newRange = { start: offsets.start, end: offsets.end, text: selectedText || undefined, color: color || undefined };
                    // avoid duplicates roughly by checking identical start/end
                    if (prev.some((r) => r.start === newRange.start && r.end === newRange.end)) return prev;
                    return [...prev, newRange];
                  });
                } catch {}

                console.debug('[MessageBubble] highlight payload', { messageId: message.id, payload });
                const doc = await apiAddHighlight(message.id, payload);
                console.debug('[MessageBubble] highlight API response', { doc });
                // Remove optimistic marks for this message so re-apply from server ranges
                try {
                  const elRoot = messageRef.current;
                  if (elRoot) {
                    elRoot.querySelectorAll('mark[data-aurion-highlight="true"][data-aurion-optimistic="true"]').forEach((m) => m.remove());
                  }
                } catch {}
                if (doc && Array.isArray(doc.ranges)) {
                  setHighlights(normalizeRanges(doc.ranges));
                  setLastHighlightDebug('Highlight saved');
                } else {
                  const newRange = { start: offsets.start, end: offsets.end, text: selectedText || undefined, color: color || undefined };
                  setHighlights((prev) => normalizeRanges([...prev, newRange]));
                  setLastHighlightDebug('Highlight applied locally');
                }
              } catch (err: any) {
                console.error('Highlight error', err);
                setLastHighlightDebug('Highlight error: ' + (err?.message || String(err)));
              }
              finally {
                // keep popup open briefly so user can see debug, then close
                setTimeout(() => setShowSelectionPopup(false), 300);
                setTimeout(() => setLastHighlightDebug(null), 2500);
              }
            }}
              onSpeakClick={() => { handleSpeakSelected(); setShowSelectionPopup(false); }}
              onUnhighlightClick={async () => {
                try {
                  const offsets = selectionOffsets;
                  if (!offsets) {
                    setLastHighlightDebug('No selection offsets for unhighlight');
                    return;
                  }
                  // Optimistic UI: remove overlapping ranges locally
                  setHighlights((prev) => normalizeRanges(prev.filter((h) => !(h.start < offsets.end && h.end > offsets.start))));
                  // Also remove any optimistic mark nodes in the DOM for neatness
                  try {
                    const elRoot = messageRef.current;
                    if (elRoot) {
                      elRoot.querySelectorAll('mark[data-aurion-highlight="true"][data-aurion-optimistic="true"]').forEach((m) => m.remove());
                    }
                  } catch {}
                  // Call server to remove the exact range (backend will fallback to start/end match)
                  const doc = await apiRemoveHighlightRange(message.id, offsets.start, offsets.end, selectedText || undefined);
                  if (doc && Array.isArray(doc.ranges)) {
                    setHighlights(normalizeRanges(doc.ranges));
                    setLastHighlightDebug('Unhighlight saved');
                  } else {
                    setLastHighlightDebug('Unhighlight applied locally');
                  }
                } catch (err: any) {
                  console.error('Unhighlight error', err);
                  setLastHighlightDebug('Unhighlight error: ' + (err?.message || String(err)));
                } finally {
                  setTimeout(() => setShowSelectionPopup(false), 200);
                  setTimeout(() => setLastHighlightDebug(null), 2500);
                }
              }}
              showUnhighlight={showUnhighlightBtn}
          />
        )}
        {/* Small debug message shown near popup to help debugging selection/highlight issues */}
        {!isUser && showSelectionPopup && lastHighlightDebug && (
          <div
            className="absolute z-[10000] left-1/2 transform -translate-x-1/2 mt-2 w-max max-w-[26rem] px-3 py-1 rounded bg-black/80 text-xs text-white"
            style={{ top: (popupPos?.top ?? 0) + 44, left: popupPos?.left ?? '50%' }}
          >
            {lastHighlightDebug}
          </div>
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