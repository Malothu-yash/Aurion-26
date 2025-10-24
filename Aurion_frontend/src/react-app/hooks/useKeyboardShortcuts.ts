import { useEffect } from 'react';

interface KeyboardShortcuts {
  // Add other keyboard shortcuts here as needed
}

export const useKeyboardShortcuts = ({}: KeyboardShortcuts) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Add keyboard shortcuts here as needed
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);
};
