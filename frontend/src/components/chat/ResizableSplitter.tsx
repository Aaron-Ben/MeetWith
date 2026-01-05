import { useState, useRef, useCallback, useEffect } from 'react';
import { useTheme } from '@/contexts/ThemeContext';

interface ResizableSplitterProps {
  direction: 'horizontal' | 'vertical';
  onDrag?: (delta: number) => void;
}

export default function ResizableSplitter({ direction, onDrag }: ResizableSplitterProps) {
  const { theme } = useTheme();
  const [isDragging, setIsDragging] = useState(false);
  const startPos = useRef(0);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    startPos.current = direction === 'horizontal' ? e.clientX : e.clientY;
  }, [direction]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return;

    const currentPos = direction === 'horizontal' ? e.clientX : e.clientY;
    const delta = currentPos - startPos.current;

    if (onDrag) {
      onDrag(delta);
    }

    startPos.current = currentPos;
  }, [isDragging, direction, onDrag]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  return (
    <div
      className={`bg-gray-700 w-1.25 cursor-col-resize flex-shrink-0 z-[100] opacity-50 transition-opacity hover:bg-blue-600/75 hover:opacity-100 ${
        theme === 'dark' ? '' : 'bg-slate-200 hover:bg-blue-500/70'
      }`}
      onMouseDown={handleMouseDown}
    />
  );
}
