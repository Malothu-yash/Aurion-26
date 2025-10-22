import { useState, useRef, useEffect } from 'react';
import { 
  User, 
  Sparkles, 
  Copy, 
  Edit3, 
  Check, 
  Bot, 
  MoreHorizontal,
  Trash2,
  RotateCcw,
  Share,
  Archive,
  ExternalLink,
  Youtube,
  CheckCircle,
  Search
} from 'lucide-react';
import { useTextSelection } from '@/react-app/context/TextSelectionContext';
import TextSelectionPopup from './TextSelectionPopup';
import MiniAgentChat from './MiniAgentChat';
import { HighlightColorPalette, HighlightTooltip, HighlightNoteModal } from './HighlightSystem';
import { SpeakerButton } from './SpeakerFeature';
import { HIGHLIGHT_COLORS, HighlightColor } from '@/shared/types';

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
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [showMoreMenu, setShowMoreMenu] = useState(false);
  const [showHighlightTooltip, setShowHighlightTooltip] = useState(false);
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [selectedHighlight, setSelectedHighlight] = useState<any>(null);
  const [highlightTooltipPosition, setHighlightTooltipPosition] = useState({ x: 0, y: 0 });
  
  const messageRef = useRef<HTMLDivElement>(null);
  const textSelectionRef = useRef<HTMLDivElement>(null);

  const {
    currentSelection,
    showSelectionPopup,
    selectionPosition,
    setCurrentSelection,
    setSelectionPopup,
    saveHighlight,
    openMiniAgent,
    speakText,
    highlights,
    miniAgentSessions,
    isMiniAgentOpen,
    activeMiniAgentSession,
    closeMiniAgent,
    sendMiniAgentMessage
  } = useTextSelection();

  const isUser = message.message_type === 'user';

  // Load highlights and mini agent sessions for this message
  useEffect(() => {
    // This would be called when the component mounts
    // The context will handle loading the data
  }, [message.id]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const handleTextSelection = (event: React.MouseEvent) => {
    if (isUser) return; // Only allow selection on AI messages
    
    const selection = window.getSelection();
    if (selection && selection.toString().trim()) {
      const selectedText = selection.toString().trim();
      const range = selection.getRangeAt(0);
      
      console.log('Text selected:', selectedText);
      
      // Get position for popup
      const rect = range.getBoundingClientRect();
      const position = {
        x: rect.left + rect.width / 2,
        y: rect.top
      };
      
      const textSelection = {
        text: selectedText,
        rangeStart: range.startOffset,
        rangeEnd: range.endOffset,
        messageId: message.id
      };
      
      console.log('Setting current selection:', textSelection);
      setCurrentSelection(textSelection);
      setSelectionPopup(true, position);
    } else {
      setSelectionPopup(false);
    }
  };

  const handleHighlight = async (color: HighlightColor) => {
    if (!currentSelection) {
      console.log('No current selection for highlighting');
      return;
    }
    
    console.log('Highlighting with color:', color);
    
    try {
      const colorData = HIGHLIGHT_COLORS.find(c => c.name === color);
      if (!colorData) {
        console.log('Color data not found for:', color);
        return;
      }
      
      console.log('Color data:', colorData);
      
      // Apply highlight to DOM
      const selection = window.getSelection();
      if (selection && selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        const span = document.createElement('span');
        span.style.backgroundColor = colorData.value;
        span.style.padding = '2px 4px';
        span.style.borderRadius = '3px';
        span.className = 'highlighted-text';
        span.setAttribute('data-highlight-color', colorData.name);
        span.setAttribute('data-highlight-text', currentSelection.text);
        
        try {
          range.surroundContents(span);
          console.log('Successfully highlighted text');
        } catch (e) {
          console.log('surroundContents failed, trying alternative method');
          // If surroundContents fails, extract content and replace
          const contents = range.extractContents();
          span.appendChild(contents);
          range.insertNode(span);
        }
        
        selection.removeAllRanges();
      }
      
      // Save to backend
      console.log('Saving highlight to backend...');
      await saveHighlight({
        messageId: message.id,
        text: currentSelection.text,
        color: colorData.value,
        rangeStart: currentSelection.rangeStart,
        rangeEnd: currentSelection.rangeEnd
      });
      
      console.log('Highlight saved successfully');
      setSelectionPopup(false);
      setCurrentSelection(null);
    } catch (error) {
      console.error('Failed to highlight text:', error);
    }
  };

  const handleMiniAgent = () => {
    if (!currentSelection) {
      console.log('No current selection for mini agent');
      return;
    }
    
    console.log('Opening mini agent with text:', currentSelection.text);
    
    // Check if mini agent session already exists for this message
    const existingSession = miniAgentSessions.find(session => session.messageId === message.id);
    
    if (existingSession) {
      console.log('Found existing session:', existingSession);
      openMiniAgent(existingSession);
    } else {
      console.log('Creating new mini agent session');
      // Create new session
      const newSession = {
        id: crypto.randomUUID(),
        messageId: message.id,
        userId: 'current-user', // This would come from auth context
        snippet: currentSelection.text,
        conversation: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      console.log('New session created:', newSession);
      openMiniAgent(newSession);
    }
    
    setSelectionPopup(false);
    setCurrentSelection(null);
  };

  const handleSpeaker = () => {
    if (!currentSelection) {
      console.log('No current selection for speaker');
      return;
    }
    console.log('Speaking text:', currentSelection.text);
    
    // Check if speech synthesis is supported
    if ('speechSynthesis' in window) {
      console.log('Speech synthesis is supported');
      speakText(currentSelection.text);
    } else {
      console.log('Speech synthesis is not supported');
    }
    
    setSelectionPopup(false);
    setCurrentSelection(null);
  };

  const handleHighlightClick = (highlight: any, event: React.MouseEvent) => {
    event.stopPropagation();
    setSelectedHighlight(highlight);
    setHighlightTooltipPosition({
      x: event.clientX,
      y: event.clientY
    });
    setShowHighlightTooltip(true);
  };

  const handleEdit = () => {
    console.log('Edit message:', message.id);
  };

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this message?')) {
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

  const handleShare = () => {
    console.log('Share message:', message.id);
  };

  // Check for special content types
  const specialContent = message.metadata?.specialContent;
  const isYouTubeVideo = specialContent?.type === 'youtube';
  const isConfirmation = specialContent?.type === 'confirmation';
  const isSearchResults = specialContent?.type === 'searchResults';

  // Check if this message has mini agent session
  const hasMiniAgentSession = miniAgentSessions.some(session => session.messageId === message.id);

  return (
    <>
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
        <div className={`flex-1 max-w-4xl ${isUser ? 'text-right' : ''}`}>
          <div
            ref={messageRef}
            className={`inline-block p-4 rounded-2xl relative ${
              isUser
                ? 'bg-gradient-to-r from-orange-500/80 to-purple-600/80 text-white rounded-tr-sm'
                : 'bg-transparent text-gray-100 rounded-tl-sm border-l-4 border-orange-400/50 pl-6'
            }`}
            onMouseUp={!isUser ? handleTextSelection : undefined}
          >
            {/* Regular text content */}
            {message.content && (
              <div 
                ref={textSelectionRef}
                className="whitespace-pre-wrap leading-relaxed font-medium"
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
                  <SpeakerButton text={message.content} />
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
                  <SpeakerButton text={message.content} />
                  {hasMiniAgentSession && (
                    <button
                      onClick={() => {
                        const session = miniAgentSessions.find(s => s.messageId === message.id);
                        if (session) openMiniAgent(session);
                      }}
                      className="p-2 rounded-lg bg-purple-900/40 text-gray-400 hover:text-blue-400 hover:bg-purple-900/60 transition-all duration-200 opacity-0 group-hover:opacity-100"
                      title="Open Mini Agent"
                    >
                      <Bot className="w-4 h-4" />
                    </button>
                  )}
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

      {/* Text Selection Popup */}
      {showSelectionPopup && currentSelection && (
        <TextSelectionPopup
          selection={currentSelection}
          position={selectionPosition}
          onHighlight={handleHighlight}
          onMiniAgent={handleMiniAgent}
          onSpeaker={handleSpeaker}
          onClose={() => {
            setSelectionPopup(false);
            setCurrentSelection(null);
          }}
        />
      )}

      {/* Highlight Tooltip */}
      {showHighlightTooltip && selectedHighlight && (
        <HighlightTooltip
          highlight={selectedHighlight}
          position={highlightTooltipPosition}
          onClose={() => setShowHighlightTooltip(false)}
          onEdit={() => {
            setShowHighlightTooltip(false);
            setShowNoteModal(true);
          }}
          onDelete={() => {
            setShowHighlightTooltip(false);
            // Delete highlight logic
          }}
        />
      )}

      {/* Highlight Note Modal */}
      {showNoteModal && (
        <HighlightNoteModal
          isOpen={showNoteModal}
          initialNote={selectedHighlight?.note}
          onSave={(note) => {
            // Save note logic
            setShowNoteModal(false);
          }}
          onClose={() => setShowNoteModal(false)}
        />
      )}

      {/* Mini Agent Chat */}
      {isMiniAgentOpen && activeMiniAgentSession && (
        <MiniAgentChat
          session={activeMiniAgentSession}
          isOpen={isMiniAgentOpen}
          onClose={closeMiniAgent}
          onSendMessage={sendMiniAgentMessage}
          isLoading={false}
        />
      )}
    </>
  );
}
