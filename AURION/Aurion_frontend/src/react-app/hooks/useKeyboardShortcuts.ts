import { useEffect } from 'react';

interface KeyboardShortcuts {
  onOpenMiniAgent?: () => void;
  onCloseMiniAgent?: () => void;
  onToggleHighlight?: () => void;
}

export const useKeyboardShortcuts = ({
  onOpenMiniAgent,
  onCloseMiniAgent,
  onToggleHighlight
}: KeyboardShortcuts) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + M to open Mini Agent
      if ((e.ctrlKey || e.metaKey) && e.key === 'm') {
        e.preventDefault();
        onOpenMiniAgent?.();
      }
      
      // Escape to close Mini Agent
      if (e.key === 'Escape') {
        onCloseMiniAgent?.();
      }
      
      // Ctrl/Cmd + H to toggle highlight
      if ((e.ctrlKey || e.metaKey) && e.key === 'h') {
        e.preventDefault();
        onToggleHighlight?.();
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onOpenMiniAgent, onCloseMiniAgent, onToggleHighlight]);
};