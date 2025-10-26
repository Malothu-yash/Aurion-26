import { Highlighter, Bot, Volume2, Trash2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

interface SelectionPopupProps {
  visible: boolean;
  top: number; // relative to the positioned container
  left: number; // relative to the positioned container
  onRequestClose: () => void;
  onMiniAgentClick?: () => void;
  onHighlightClick?: (color?: string) => void;
  onUnhighlightClick?: () => void;
  showUnhighlight?: boolean;
  onSpeakClick?: () => void;
}

export default function SelectionPopup({ visible, top, left, onRequestClose, onMiniAgentClick, onHighlightClick, onUnhighlightClick, showUnhighlight, onSpeakClick }: SelectionPopupProps) {
  const popupRef = useRef<HTMLDivElement>(null);
  const miniAgentBtnRef = useRef<HTMLButtonElement>(null);
  const [showColorPicker, setShowColorPicker] = useState<boolean>(false);

  // Close on escape
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onRequestClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onRequestClose]);

  useEffect(() => {
    // Optional: subtle bounce on appear for attention
    if (!visible) return;
    const btn = miniAgentBtnRef.current;
    if (!btn) return;
    btn.classList.add('animate-bounce');
    const t = setTimeout(() => btn.classList.remove('animate-bounce'), 600);
    return () => clearTimeout(t);
  }, [visible]);
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          ref={popupRef}
          style={{
            position: 'absolute',
            top: Math.max(0, top),
            left,
            transform: 'translateX(-50%)',
          }}
          initial={{ opacity: 0, scale: 0.95, y: -4 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -4 }}
          transition={{ type: 'spring', stiffness: 500, damping: 30, mass: 0.5 }}
          className="z-[9999] select-none"
          data-selection-popup="true"
        >
        <motion.div
        initial={{ scale: 0.98 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.15 }}
        className="flex items-center gap-1 rounded-2xl bg-purple-950/90 border border-orange-500/30 shadow-xl px-1.5 py-1 backdrop-blur-md"
      >
        <button
          className="p-2 rounded-xl text-orange-300 hover:text-orange-100 hover:bg-purple-900/60 transition-colors"
          title="Highlight"
          type="button"
          onMouseDown={(e) => { e.stopPropagation(); setShowColorPicker((s) => !s); }}
        >
          <Highlighter className="w-4 h-4" />
        </button>
        {/* Show color choices only after user clicks the highlighter button */}
        {showColorPicker && (
          <div className="flex items-center gap-1 ml-1">
            <button
              title="Yellow"
              type="button"
              className="w-3 h-3 rounded-sm bg-yellow-400/70 border border-yellow-600/20"
              onMouseDown={(e) => { e.stopPropagation(); onHighlightClick?.('yellow'); setShowColorPicker(false); }}
            />
            <button
              title="Pink"
              type="button"
              className="w-3 h-3 rounded-sm bg-pink-400/70 border border-pink-600/20"
              onMouseDown={(e) => { e.stopPropagation(); onHighlightClick?.('pink'); setShowColorPicker(false); }}
            />
            <button
              title="Green"
              type="button"
              className="w-3 h-3 rounded-sm bg-green-300/70 border border-green-600/20"
              onMouseDown={(e) => { e.stopPropagation(); onHighlightClick?.('green'); setShowColorPicker(false); }}
            />
            <button
              title="Blue"
              type="button"
              className="w-3 h-3 rounded-sm bg-blue-300/70 border border-blue-600/20"
              onMouseDown={(e) => { e.stopPropagation(); onHighlightClick?.('blue'); setShowColorPicker(false); }}
            />
          </div>
        )}
        <button
          ref={miniAgentBtnRef}
          className="p-2 rounded-xl text-orange-300 hover:text-orange-100 hover:bg-purple-900/60 transition-colors"
          title="Mini Agent"
          type="button"
          onMouseDown={(e) => { e.stopPropagation(); onMiniAgentClick?.(); }}
        >
          <Bot className="w-4 h-4" />
        </button>
        <button
          className="p-2 rounded-xl text-gray-300 hover:text-white hover:bg-purple-900/60 transition-colors"
          title="Speak"
          type="button"
          onMouseDown={(e) => { e.stopPropagation(); onSpeakClick?.(); }}
        >
          <Volume2 className="w-4 h-4" />
        </button>
        {/* Unhighlight button appears when selection is already highlighted */}
        {showUnhighlight && onUnhighlightClick && (
          <button
            className="p-2 rounded-xl text-red-300 hover:text-red-100 hover:bg-purple-900/60 transition-colors"
            title="Unhighlight"
            type="button"
            onMouseDown={(e) => { e.stopPropagation(); onUnhighlightClick(); }}
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
