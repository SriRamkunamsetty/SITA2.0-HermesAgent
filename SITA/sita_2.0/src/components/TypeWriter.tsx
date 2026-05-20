import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';

interface TypeWriterProps {
  text: string;
  delay?: number;
  className?: string;
  onComplete?: () => void;
  cursor?: boolean;
}

const TypeWriter = ({ 
  text, 
  delay = 50, 
  className, 
  onComplete,
  cursor = true 
}: TypeWriterProps) => {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    let currentIndex = 0;
    const timer = setInterval(() => {
      if (currentIndex <= text.length) {
        setDisplayedText(text.slice(0, currentIndex));
        currentIndex++;
      } else {
        clearInterval(timer);
        setIsComplete(true);
        onComplete?.();
      }
    }, delay);

    return () => clearInterval(timer);
  }, [text, delay, onComplete]);

  return (
    <span className={cn('font-mono', className)}>
      {displayedText}
      {cursor && !isComplete && (
        <span className="animate-blink border-r-2 border-primary ml-1">&nbsp;</span>
      )}
    </span>
  );
};

export default TypeWriter;
