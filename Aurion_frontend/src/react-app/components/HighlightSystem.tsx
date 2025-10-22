import React, { useState } from 'react';
import { Highlighter, X, Edit3, Trash2, Palette, BookOpen, Tag, Filter } from 'lucide-react';
import { HIGHLIGHT_COLORS, HighlightColor } from '@/shared/types';

interface HighlightColorPaletteProps {
  onColorSelect: (color: HighlightColor) => void;
  onClose: () => void;
  selectedText?: string;
}

export function HighlightColorPalette({ onColorSelect, onClose, selectedText }: HighlightColorPaletteProps) {
  const [showSmartSuggestions, setShowSmartSuggestions] = useState(false);
  
  // Generate smart color suggestions based on text content
  const getSmartColorSuggestions = (text: string) => {
    const lowerText = text.toLowerCase();
    const suggestions: { color: HighlightColor; reason: string }[] = [];
    
    if (lowerText.includes('important') || lowerText.includes('critical') || lowerText.includes('urgent')) {
      suggestions.push({ color: 'red', reason: 'Important/Critical content' });
    }
    
    if (lowerText.includes('code') || lowerText.includes('function') || lowerText.includes('class')) {
      suggestions.push({ color: 'blue', reason: 'Code/Technical content' });
    }
    
    if (lowerText.includes('note') || lowerText.includes('remember') || lowerText.includes('tip')) {
      suggestions.push({ color: 'yellow', reason: 'Notes/Tips' });
    }
    
    if (lowerText.includes('success') || lowerText.includes('correct') || lowerText.includes('good')) {
      suggestions.push({ color: 'green', reason: 'Positive/Success content' });
    }
    
    if (lowerText.includes('warning') || lowerText.includes('caution') || lowerText.includes('careful')) {
      suggestions.push({ color: 'orange', reason: 'Warning/Caution content' });
    }
    
    if (lowerText.includes('question') || lowerText.includes('why') || lowerText.includes('how')) {
      suggestions.push({ color: 'purple', reason: 'Questions/Explanations' });
    }
    
    return suggestions.slice(0, 3); // Limit to 3 suggestions
  };

  const smartSuggestions = selectedText ? getSmartColorSuggestions(selectedText) : [];
  return (
    <div className="absolute z-50 bg-purple-950/95 backdrop-blur-lg border border-orange-500/30 rounded-xl shadow-2xl p-4 animate-fade-in-up">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Highlighter className="w-4 h-4 text-yellow-400" />
          <span className="text-sm font-medium text-white">Choose highlight color</span>
        </div>
        <div className="flex items-center space-x-2">
          {smartSuggestions.length > 0 && (
            <button
              onClick={() => setShowSmartSuggestions(!showSmartSuggestions)}
              className="p-1 rounded-lg hover:bg-purple-900/50 transition-colors duration-200 text-purple-400 hover:text-purple-300"
              title="Smart suggestions"
            >
              <Palette className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-purple-900/50 transition-colors duration-200 text-gray-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Smart Suggestions */}
      {showSmartSuggestions && smartSuggestions.length > 0 && (
        <div className="mb-3 p-2 bg-purple-900/30 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <Palette className="w-3 h-3 text-purple-400" />
            <span className="text-xs font-medium text-purple-300">Smart Suggestions</span>
          </div>
          <div className="space-y-1">
            {smartSuggestions.map((suggestion, index) => {
              const colorData = HIGHLIGHT_COLORS.find(c => c.name === suggestion.color);
              return (
                <button
                  key={index}
                  onClick={() => onColorSelect(suggestion.color)}
                  className="w-full flex items-center space-x-2 p-1 rounded hover:bg-purple-800/40 transition-colors duration-200"
                >
                  <div className={`w-4 h-4 rounded-full ${colorData?.bgClass}`} />
                  <span className="text-xs text-gray-300">{suggestion.reason}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
      
      <div className="grid grid-cols-3 gap-2">
        {HIGHLIGHT_COLORS.map((colorOption) => (
          <button
            key={colorOption.name}
            onClick={() => onColorSelect(colorOption.name)}
            className={`w-8 h-8 rounded-full ${colorOption.bgClass} hover:scale-110 transition-all duration-200 border-2 border-transparent hover:border-white/30`}
            title={`Highlight with ${colorOption.name}`}
          />
        ))}
      </div>
    </div>
  );
}

interface HighlightTooltipProps {
  highlight: {
    text: string;
    color: string;
    note?: string;
  };
  position: { x: number; y: number };
  onClose: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
}

export function HighlightTooltip({ 
  highlight, 
  position, 
  onClose, 
  onEdit, 
  onDelete 
}: HighlightTooltipProps) {
  return (
    <div
      className="fixed z-50 bg-purple-950/95 backdrop-blur-lg border border-orange-500/30 rounded-xl shadow-2xl p-3 max-w-xs animate-fade-in-up"
      style={{
        left: position.x,
        top: position.y - 80,
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <div 
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: highlight.color }}
          />
          <span className="text-xs font-semibold text-gray-400">Highlight</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg hover:bg-purple-900/50 transition-colors duration-200 text-gray-400 hover:text-white"
        >
          <X className="w-3 h-3" />
        </button>
      </div>
      
      <p className="text-sm text-gray-200 mb-2 line-clamp-3">
        "{highlight.text}"
      </p>
      
      {highlight.note && (
        <div className="bg-purple-900/30 rounded-lg p-2 mb-2">
          <p className="text-xs text-gray-300 italic">"{highlight.note}"</p>
        </div>
      )}
      
      <div className="flex items-center space-x-2">
        {onEdit && (
          <button
            onClick={onEdit}
            className="flex items-center space-x-1 px-2 py-1 rounded-lg bg-blue-900/40 text-blue-300 hover:bg-blue-900/60 transition-colors duration-200"
          >
            <Edit3 className="w-3 h-3" />
            <span className="text-xs">Edit</span>
          </button>
        )}
        {onDelete && (
          <button
            onClick={onDelete}
            className="flex items-center space-x-1 px-2 py-1 rounded-lg bg-red-900/40 text-red-300 hover:bg-red-900/60 transition-colors duration-200"
          >
            <Trash2 className="w-3 h-3" />
            <span className="text-xs">Delete</span>
          </button>
        )}
      </div>
    </div>
  );
}

interface HighlightNoteModalProps {
  isOpen: boolean;
  initialNote?: string;
  onSave: (note: string) => void;
  onClose: () => void;
}

export function HighlightNoteModal({ isOpen, initialNote, onSave, onClose }: HighlightNoteModalProps) {
  const [note, setNote] = useState(initialNote || '');

  const handleSave = () => {
    onSave(note);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-purple-950/95 backdrop-blur-lg border border-orange-500/30 rounded-xl shadow-2xl p-6 w-full max-w-md animate-fade-in-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center space-x-2 mb-4">
          <Highlighter className="w-5 h-5 text-yellow-400" />
          <h3 className="text-lg font-semibold text-white">Add Note to Highlight</h3>
        </div>
        
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Why did you highlight this text? (optional)"
          className="w-full h-24 bg-purple-900/50 border border-orange-500/30 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-orange-400/60 focus:ring-1 focus:ring-orange-400/30 resize-none"
        />
        
        <div className="flex items-center justify-end space-x-3 mt-4">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-white transition-colors duration-200"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-orange-500/80 hover:bg-orange-500 text-white rounded-lg transition-colors duration-200"
          >
            Save Note
          </button>
        </div>
      </div>
    </div>
  );
}
