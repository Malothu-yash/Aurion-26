import React, { useEffect, useRef, useState } from 'react';
import { Highlighter, Bot, Volume2, X, Lightbulb, BookOpen, MessageSquare, Zap, Languages, FileText, Brain, Sparkles, Copy, Share, Pin } from 'lucide-react';
import { TextSelectionPopupProps } from '@/shared/types';
import { HIGHLIGHT_COLORS } from '@/shared/types';
import { HighlightColorPalette } from './HighlightSystem';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

export default function TextSelectionPopup({
  selection,
  position,
  onHighlight,
  onMiniAgent,
  onSpeaker,
  onClose,
}: TextSelectionPopupProps) {
  const popupRef = useRef<HTMLDivElement>(null);
  const [showColorPalette, setShowColorPalette] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showAdvancedActions, setShowAdvancedActions] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isHovered, setIsHovered] = useState(false);

  // Keyboard shortcuts for the popup
  useKeyboardShortcuts({
    onOpenMiniAgent: () => onMiniAgent(selection.text),
    onCloseMiniAgent: onClose,
    onToggleHighlight: () => setShowColorPalette(!showColorPalette)
  });

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  // Generate intelligent suggestions based on selected text
  useEffect(() => {
    const generateSuggestions = (text: string) => {
      const suggestions: { text: string; icon: any; action: string }[] = [];
      const lowerText = text.toLowerCase();
      
      // Code-related suggestions
      if (lowerText.includes('code') || lowerText.includes('function') || lowerText.includes('class') || lowerText.includes('api')) {
        suggestions.push(
          { text: 'Explain code', icon: Code, action: 'Can you explain this code step by step?' },
          { text: 'Find examples', icon: Search, action: 'Show me similar code examples' },
          { text: 'Debug help', icon: FileText, action: 'Help me debug this code' },
          { text: 'Optimize', icon: Zap, action: 'How can I optimize this code?' }
        );
      }
      
      // Error/problem-related suggestions
      if (lowerText.includes('error') || lowerText.includes('problem') || lowerText.includes('issue') || lowerText.includes('bug')) {
        suggestions.push(
          { text: 'Fix this', icon: Zap, action: 'How can I fix this problem?' },
          { text: 'Common solutions', icon: Search, action: 'What are common solutions for this?' },
          { text: 'Troubleshoot', icon: Brain, action: 'Help me troubleshoot this step by step' },
          { text: 'Prevention', icon: Lightbulb, action: 'How can I prevent this issue?' }
        );
      }
      
      // Learning/educational content
      if (lowerText.includes('learn') || lowerText.includes('understand') || lowerText.includes('concept') || lowerText.includes('theory')) {
        suggestions.push(
          { text: 'Explain simply', icon: BookOpen, action: 'Explain this in simple terms' },
          { text: 'Deep dive', icon: Brain, action: 'Give me a detailed explanation' },
          { text: 'Related topics', icon: Search, action: 'What topics are related to this?' },
          { text: 'Examples', icon: FileText, action: 'Show me practical examples' }
        );
      }
      
      // API/Technical documentation
      if (lowerText.includes('api') || lowerText.includes('endpoint') || lowerText.includes('request') || lowerText.includes('response')) {
        suggestions.push(
          { text: 'API docs', icon: FileText, action: 'Show me API documentation for this' },
          { text: 'Usage examples', icon: Code, action: 'Give me usage examples' },
          { text: 'Test endpoint', icon: Zap, action: 'Help me test this endpoint' },
          { text: 'Integration', icon: Share, action: 'How do I integrate this?' }
        );
      }
      
      // Database/SQL content
      if (lowerText.includes('database') || lowerText.includes('sql') || lowerText.includes('query') || lowerText.includes('table')) {
        suggestions.push(
          { text: 'Query optimization', icon: Zap, action: 'How can I optimize this query?' },
          { text: 'Database design', icon: Brain, action: 'Explain the database design' },
          { text: 'Performance tips', icon: Lightbulb, action: 'Give me performance tips' },
          { text: 'Best practices', icon: BookOpen, action: 'What are the best practices?' }
        );
      }
      
      // Default suggestions if no specific patterns found
      if (suggestions.length === 0) {
        suggestions.push(
          { text: 'Explain this', icon: BookOpen, action: 'Can you explain this concept in simple terms?' },
          { text: 'Give examples', icon: FileText, action: 'Can you provide examples of this?' },
          { text: 'Find related', icon: Search, action: 'What are related topics to this?' },
          { text: 'Summarize', icon: Zap, action: 'Give me a quick summary of this' }
        );
      }
      
      return suggestions.slice(0, 4); // Limit to 4 suggestions
    };

    setSuggestions(generateSuggestions(selection.text));
  }, [selection.text]);

  // Advanced actions for the popup
  const advancedActions = [
    { icon: Languages, text: 'Translate', action: 'Translate this to another language' },
    { icon: FileText, text: 'Summarize', action: 'Create a detailed summary' },
    { icon: Brain, text: 'Analyze', action: 'Analyze this content deeply' },
    { icon: Code, text: 'Code it', action: 'Convert this to code' },
    { icon: Search, text: 'Research', action: 'Research this topic further' },
    { icon: Sparkles, text: 'Improve', action: 'How can this be improved?' }
  ];

  const handleColorSelect = (color: string) => {
    onHighlight(color);
    setShowColorPalette(false);
  };

  const handleSuggestionClick = (action: string) => {
    // This would trigger the mini agent with the suggestion
    console.log('Suggestion clicked:', action);
    // You could call onMiniAgent with the suggestion as initial message
    onMiniAgent();
  };

  const handleAdvancedActionClick = (action: string) => {
    console.log('Advanced action clicked:', action);
    onMiniAgent();
  };

  const handleCopyText = () => {
    navigator.clipboard.writeText(selection.text);
    // You could show a toast notification here
  };

  return (
    <div
      ref={popupRef}
      className="fixed z-50 bg-gradient-to-br from-purple-950/95 to-purple-900/95 backdrop-blur-lg border border-orange-500/30 rounded-xl shadow-2xl p-4 animate-fade-in-up"
      style={{
        left: position.x,
        top: position.y - 80,
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-orange-400 to-purple-600 flex items-center justify-center">
            <MessageSquare className="w-3 h-3 text-white" />
          </div>
          <span className="text-sm font-semibold text-white">Text Selection</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg hover:bg-red-900/30 transition-colors duration-200 text-gray-400 hover:text-red-300"
          title="Close"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Selected text preview */}
      <div className="mb-4 p-3 bg-purple-900/30 rounded-lg border border-purple-500/20">
        <p className="text-xs text-gray-400 mb-2 flex items-center space-x-1">
          <Pin className="w-3 h-3" />
          <span>Selected Text</span>
        </p>
        <p className="text-sm text-gray-200 line-clamp-3 leading-relaxed">
          "{selection.text}"
        </p>
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-gray-500">{selection.text.length} characters</span>
          <button
            onClick={handleCopyText}
            className="text-xs text-orange-400 hover:text-orange-300 transition-colors duration-200 flex items-center space-x-1"
          >
            <Copy className="w-3 h-3" />
            <span>Copy</span>
          </button>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex items-center space-x-2 mb-4">
        {/* Highlight button with color palette */}
        <div className="relative">
          <button
            onMouseEnter={() => setShowColorPalette(true)}
            onMouseLeave={() => setShowColorPalette(false)}
            className="p-2 rounded-lg hover:bg-yellow-900/30 transition-all duration-200 text-yellow-400 hover:text-yellow-300 group"
            title="Highlight text"
          >
            <Highlighter className="w-5 h-5 group-hover:scale-110 transition-transform duration-200" />
          </button>

          {/* Color Palette */}
          {showColorPalette && (
            <HighlightColorPalette
              onColorSelect={handleColorSelect}
              onClose={() => setShowColorPalette(false)}
              selectedText={selection.text}
            />
          )}
        </div>

        {/* Mini Agent button */}
        <button
          onClick={onMiniAgent}
          className="p-2 rounded-lg hover:bg-blue-900/30 transition-all duration-200 text-blue-400 hover:text-blue-300 group"
          title="Ask Mini Agent about this text"
        >
          <Bot className="w-5 h-5 group-hover:scale-110 transition-transform duration-200" />
        </button>

        {/* Speaker button */}
        <button
          onClick={onSpeaker}
          className="p-2 rounded-lg hover:bg-green-900/30 transition-all duration-200 text-green-400 hover:text-green-300 group"
          title="Read aloud"
        >
          <Volume2 className="w-5 h-5 group-hover:scale-110 transition-transform duration-200" />
        </button>

        {/* Advanced actions toggle */}
        <button
          onClick={() => setShowAdvancedActions(!showAdvancedActions)}
          className="p-2 rounded-lg hover:bg-purple-900/30 transition-all duration-200 text-purple-400 hover:text-purple-300 group"
          title="Advanced actions"
        >
          <Sparkles className="w-5 h-5 group-hover:scale-110 transition-transform duration-200" />
        </button>

        {/* Smart suggestions toggle */}
        <div className="relative">
          <button
            onMouseEnter={() => setShowSuggestions(true)}
            onMouseLeave={() => setShowSuggestions(false)}
            className="p-2 rounded-lg hover:bg-purple-900/30 transition-all duration-200 text-purple-400 hover:text-purple-300 group"
            title="Smart suggestions"
          >
            <Lightbulb className="w-5 h-5 group-hover:scale-110 transition-transform duration-200" />
          </button>

          {/* Suggestions Panel */}
          {showSuggestions && (
            <div className="absolute bottom-full right-0 mb-2 bg-purple-950/95 backdrop-blur-lg border border-orange-500/30 rounded-xl shadow-2xl p-3 animate-fade-in-up min-w-72">
              <div className="flex items-center space-x-2 mb-3">
                <Lightbulb className="w-4 h-4 text-purple-400" />
                <span className="text-sm font-medium text-white">Smart Suggestions</span>
                <div className="flex-1 h-px bg-gradient-to-r from-purple-500/30 to-transparent"></div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion.action)}
                    className="flex items-center space-x-2 p-2 rounded-lg hover:bg-purple-900/40 transition-colors duration-200 text-gray-200 hover:text-white text-sm group"
                  >
                    <suggestion.icon className="w-3 h-3 text-orange-400 flex-shrink-0 group-hover:scale-110 transition-transform duration-200" />
                    <span className="truncate">{suggestion.text}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Advanced Actions Panel */}
      {showAdvancedActions && (
        <div className="border-t border-orange-500/20 pt-3">
          <div className="flex items-center space-x-2 mb-3">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span className="text-sm font-medium text-white">Advanced Actions</span>
            <div className="flex-1 h-px bg-gradient-to-r from-purple-500/30 to-transparent"></div>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {advancedActions.map((action, index) => (
              <button
                key={index}
                onClick={() => handleAdvancedActionClick(action.action)}
                className="flex items-center space-x-2 p-2 rounded-lg bg-purple-800/30 hover:bg-purple-800/50 transition-colors duration-200 text-gray-200 hover:text-white text-xs group"
              >
                <action.icon className="w-3 h-3 text-orange-400 flex-shrink-0 group-hover:scale-110 transition-transform duration-200" />
                <span className="truncate">{action.text}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
