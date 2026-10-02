import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, Sparkles, Keyboard, ShieldAlert, Radio, Send, X, Loader2, MessageSquare, RotateCcw, Mic, ShieldCheck } from 'lucide-react';
import TypewriterResponse from './TypewriterResponse';
import { retroSoundEngine } from '../utils/retroSounds';

export default function FloatingAvatar({ activeCategory, onPromptSubmit, agentOutput, isLoading, onClearMemory }) {
  const [isOpen, setIsOpen] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [heyOpsTriggered, setHeyOpsTriggered] = useState(false);
  const [isWisprActive, setIsWisprActive] = useState(false);
  const [memoryClearedAlert, setMemoryClearedAlert] = useState(false);
  const textareaRef = useRef(null);

  // Global Hotkey Listener:
  // - Ctrl + Alt: Open with Starting Sound
  // - Ctrl + Alt + Space: Disappear with Disappearing Sound
  // - Ctrl + Win (Meta): Wispr Flow Active Indicator
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Wispr Flow Trigger (Ctrl + Win)
      if (e.ctrlKey && (e.metaKey || e.key === 'Meta' || e.code === 'MetaLeft' || e.code === 'MetaRight')) {
        setIsWisprActive(true);
        setTimeout(() => setIsWisprActive(false), 3000);
      }

      if (e.ctrlKey && e.altKey) {
        // Check for Space: Ctrl + Alt + Space -> Disappear
        if (e.code === 'Space' || e.key === ' ') {
          e.preventDefault();
          if (isOpen) {
            setIsOpen(false);
            retroSoundEngine.playDisappear();
          }
          return;
        }

        // Ctrl + Alt: Open
        e.preventDefault();
        if (!isOpen) {
          retroSoundEngine.playAppear();
          setHeyOpsTriggered(true);
          setTimeout(() => setHeyOpsTriggered(false), 3000);
          setIsOpen(true);
          setTimeout(() => {
            if (textareaRef.current) textareaRef.current.focus();
          }, 100);
        }
      }

      // Escape to close
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
        retroSoundEngine.playDisappear();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  const handleClearMemoryClick = () => {
    retroSoundEngine.playMemoryErase();
    if (onClearMemory) {
      onClearMemory();
    }
    setMemoryClearedAlert(true);
    setTimeout(() => setMemoryClearedAlert(false), 3000);
  };

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!prompt.trim() || isLoading) return;

    onPromptSubmit(prompt);
    setPrompt('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleToggle = () => {
    if (isOpen) {
      setIsOpen(false);
      retroSoundEngine.playDisappear();
    } else {
      setIsOpen(true);
      retroSoundEngine.playAppear();
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end font-mono">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ duration: 0.15 }}
            className="mb-3 w-[450px] retro-box-red p-3.5 shadow-2xl relative overflow-hidden glow-red flex flex-col max-h-[540px]"
          >
            {/* Header */}
            <div className="flex items-center justify-between pb-2 border-b border-zinc-800 flex-shrink-0">
              <div className="flex items-center gap-2">
                <motion.div
                  animate={{
                    scale: heyOpsTriggered ? [1, 1.2, 1] : 1
                  }}
                  className="px-1.5 py-0.5 bg-red-600 border border-red-400 text-white font-black text-xs"
                >
                  OPS
                </motion.div>

                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-extrabold text-xs text-white uppercase tracking-wider">
                      === O.P.S. AMBIENT POP-UP ===
                    </span>
                  </div>
                  <p className="text-[10px] text-zinc-500">
                    [CTRL+ALT: OPEN] [CTRL+ALT+SPACE: CLOSE]
                  </p>
                </div>
              </div>

              {/* Action Buttons: Refresh/Erase Memory + Close */}
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={handleClearMemoryClick}
                  className="retro-btn px-2 py-0.5 text-[10px] text-red-400 hover:text-white hover:border-red-500 flex items-center gap-1 font-bold"
                  title="Purge active session memory & reset vector store"
                >
                  <RotateCcw className="w-2.5 h-2.5" />
                  <span>[⟳ ERASE MEMORY]</span>
                </button>
                <button
                  onClick={handleToggle}
                  className="retro-btn px-1.5 py-0.5 text-zinc-400 hover:text-white text-xs"
                  title="Close (Ctrl+Alt+Space)"
                >
                  [X]
                </button>
              </div>
            </div>

            {/* Live Hotkey Status & Wispr Flow Indicator Banner */}
            <div className="mt-2 flex items-center justify-between gap-1 text-[10px] bg-zinc-950 p-1.5 border border-zinc-800">
              <div className="flex items-center gap-1.5">
                <Mic className={`w-3 h-3 ${isWisprActive ? 'text-red-500 animate-bounce' : 'text-zinc-500'}`} />
                <span className="text-zinc-400">WISPR FLOW (CTRL+WIN):</span>
                <span className={`px-1.5 py-0.2 font-bold border ${
                  isWisprActive 
                    ? 'bg-red-600 text-white border-white animate-pulse' 
                    : 'bg-black text-zinc-400 border-zinc-700'
                }`}>
                  {isWisprActive ? '🎙 LISTENING LIVE' : 'STANDBY READY'}
                </span>
              </div>
              <div className="text-[9px] text-zinc-500 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-red-500" />
                <span>HITL PERMISSION ACTIVE</span>
              </div>
            </div>

            {/* Memory Cleared Transient Notification */}
            {memoryClearedAlert && (
              <div className="mt-1.5 bg-red-950/90 border border-red-500 text-white text-[10px] px-2 py-1 flex items-center justify-between font-bold animate-pulse">
                <span>[•] TEMPORARY CHAT MEMORY PURGED & RESET</span>
                <span className="text-[9px] text-red-300">RAM ZEROED</span>
              </div>
            )}

            {/* Input Form */}
            <form onSubmit={handleSubmit} className="mt-2.5 space-y-2 flex-shrink-0">
              <textarea
                ref={textareaRef}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={2}
                disabled={isLoading}
                placeholder="Command O.P.S. (e.g. 'Open Instagram', 'Search web for...')"
                className="w-full bg-black border border-zinc-700 focus:border-red-500 p-2 text-xs text-white placeholder-zinc-500 outline-none resize-none font-mono"
              />

              <div className="flex items-center justify-between">
                <span className="text-[10px] text-zinc-500">&gt; Enter to dispatch</span>

                <button
                  type="submit"
                  disabled={!prompt.trim() || isLoading}
                  className="retro-btn-red px-3 py-1 text-xs font-bold flex items-center gap-1.5 disabled:opacity-40"
                >
                  {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                  <span>[ DISPATCH ]</span>
                </button>
              </div>
            </form>

            {/* Response Section */}
            {(isLoading || agentOutput) && (
              <div className="mt-2.5 pt-2 border-t border-zinc-800 flex-1 overflow-y-auto space-y-1">
                <div className="text-[10px] uppercase font-bold text-red-400 flex items-center gap-1">
                  <MessageSquare className="w-3 h-3" />
                  <span>&gt; O.P.S. RESPONSE STREAM:</span>
                </div>
                <div className="p-2 bg-black border border-zinc-800 text-xs text-zinc-200 leading-relaxed font-mono">
                  {isLoading && !agentOutput ? (
                    <div className="flex items-center gap-2 text-zinc-400 py-1">
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-red-500" />
                      <span>Formulating response, sir...</span>
                    </div>
                  ) : (
                    <TypewriterResponse text={agentOutput} speed={25} />
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Retro HUD Orb Trigger Button */}
      <button
        onClick={handleToggle}
        className="w-12 h-12 bg-black border-2 border-red-600 flex flex-col items-center justify-center text-white shadow-2xl relative glow-red hover:border-red-400 transition"
        title="O.P.S. Ambient Pop-Up (Ctrl+Alt to open | Ctrl+Alt+Space to close)"
      >
        <div className="w-3.5 h-3.5 bg-red-600 flex items-center justify-center">
          <div className="w-1 h-1 bg-white animate-pulse"></div>
        </div>
        <span className="text-[8px] font-black text-red-400 mt-0.5">OPS</span>
      </button>
    </div>
  );
}
