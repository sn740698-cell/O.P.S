import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

/**
 * TypewriterResponse: A 90s retro-futuristic typewriter streaming component.
 * Renders words sequentially with a blinking block cursor (█) and auto-scroll.
 */
export default function TypewriterResponse({ text, speed = 28, isComplete = true, className = '' }) {
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const containerRef = useRef(null);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!text) {
      setDisplayedText('');
      setIsTyping(false);
      return;
    }

    // Split into tokens (words and whitespace) to preserve exact formatting
    const tokens = text.match(/\S+|\s+/g) || [text];
    let currentIndex = 0;
    let accumulated = '';
    setIsTyping(true);

    if (timerRef.current) clearInterval(timerRef.current);

    timerRef.current = setInterval(() => {
      if (currentIndex < tokens.length) {
        accumulated += tokens[currentIndex];
        setDisplayedText(accumulated);
        currentIndex++;

        if (containerRef.current) {
          containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
      } else {
        clearInterval(timerRef.current);
        timerRef.current = null;
        setIsTyping(false);
      }
    }, speed);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [text, speed]);

  const handleSkip = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setDisplayedText(text);
    setIsTyping(false);
  };

  return (
    <div
      ref={containerRef}
      onClick={handleSkip}
      className={`relative cursor-pointer select-text font-mono text-xs leading-relaxed text-zinc-100 ${className}`}
      title={isTyping ? "Click to reveal immediately" : undefined}
    >
      <span className="whitespace-pre-wrap">{displayedText}</span>
      <motion.span
        animate={{ opacity: [1, 0, 1] }}
        transition={{ duration: 0.7, repeat: Infinity, ease: 'linear' }}
        className="inline-block ml-0.5 text-red-500 font-bold select-none text-sm leading-none"
      >
        █
      </motion.span>
    </div>
  );
}
