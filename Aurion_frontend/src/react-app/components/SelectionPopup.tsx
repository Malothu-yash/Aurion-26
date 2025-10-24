import { Highlighter, Bot, Volume2 } from 'lucide-react';
import { useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

interface SelectionPopupProps {
  visible: boolean;
  top: number; // relative to the positioned container
  left: number; // relative to the positioned container
  onRequestClose: () => void;
  onMiniAgentClick?: () => void;
  onHighlightClick?: () => void;
  onSpeakClick?: () => void;
}

export default function SelectionPopup({ visible, top, left, onRequestClose, onMiniAgentClick, onHighlightClick, onSpeakClick }: SelectionPopupProps) {
  const popupRef = useRef<HTMLDivElement>(null);
  const miniAgentBtnRef = useRef<HTMLButtonElement>(null);

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
          onMouseDown={(e) => { e.stopPropagation(); onHighlightClick?.(); }}
        >
          <Highlighter className="w-4 h-4" />
        </button>
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
      </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
