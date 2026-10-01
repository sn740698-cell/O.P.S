import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, Sparkles, Mic, MicOff, ShieldAlert, Radio, Volume2 } from 'lucide-react';

export default function FloatingAvatar({ activeCategory, onPromptSubmit }) {
  const [isOpen, setIsOpen] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState('Wispr Flow Standby');
  const recognitionRef = useRef(null);

  // Initialize Speech Recognition for Wispr Flow Voice-to-Text
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
        setVoiceStatus('Wispr Flow Listening... (Ctrl+Win)');
      };

      recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        const combined = (finalTranscript || interimTranscript).trim();
        if (combined) {
          setPrompt(combined);
        }
      };

      recognition.onerror = (event) => {
        console.error('Wispr Flow Speech Error:', event.error);
        setVoiceStatus(`Wispr Voice Error: ${event.error}`);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
        setVoiceStatus('Wispr Flow Standby');
      };

      recognitionRef.current = recognition;
    } else {
      setVoiceStatus('Wispr Flow API Ready');
    }
  }, []);

  // Global Ctrl + Win (Ctrl + Meta/Super) Hotkey Listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Check for Ctrl + Meta / Win key combination
      if (e.ctrlKey && (e.key === 'Meta' || e.key === 'OS' || e.code === 'MetaLeft' || e.code === 'MetaRight')) {
        e.preventDefault();
        toggleWisprVoice();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isListening]);

  const toggleWisprVoice = async () => {
    setIsOpen(true); // Auto-open overlay on voice hotkey trigger
    
    // Notify Django backend of Wispr voice toggle
    try {
      await fetch('/api/v1/voice/toggle/', { method: 'POST' });
    } catch (err) {
      console.warn('Backend voice toggle ping failed, continuing frontend voice STT:', err);
    }

    if (recognitionRef.current) {
      if (isListening) {
        recognitionRef.current.stop();
      } else {
        recognitionRef.current.start();
      }
    } else {
      // Fallback state toggle if browser speech recognition is simulated/external Wispr engine
      setIsListening(!isListening);
      if (!isListening) {
        setVoiceStatus('Wispr Flow Voice Active (Ctrl+Win)');
      } else {
        setVoiceStatus('Wispr Flow Standby');
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
    }

    onPromptSubmit(prompt);

    // Send transcript payload to backend voice logging
    fetch('/api/v1/voice/transcript/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transcript: prompt, auto_dispatch: false })
    }).catch(err => console.log('Voice logging error:', err));

    setPrompt('');
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="mb-4 w-96 rounded-2xl bg-slate-900/95 border border-indigo-500/30 p-4 shadow-2xl backdrop-blur-xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-400 animate-pulse" />
                <span className="font-semibold text-sm text-slate-200">O.P.S. Ambient Overlay</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center gap-1">
                  <Radio className={`w-3 h-3 ${isListening ? 'text-red-400 animate-ping' : 'text-purple-400'}`} />
                  Wispr Flow [Ctrl+Win]
                </span>
              </div>
            </div>

            {/* Voice Recording Waveform Indicator */}
            {isListening && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-2 p-2.5 rounded-lg bg-indigo-950/60 border border-indigo-500/40 flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
                  <span className="text-xs font-mono text-indigo-200">Listening via Wispr Flow...</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-1 h-4 bg-indigo-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-1 h-6 bg-purple-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-1 h-3 bg-emerald-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                  <div className="w-1 h-5 bg-indigo-400 animate-bounce" style={{ animationDelay: '450ms' }} />
                </div>
              </motion.div>
            )}

            {/* Prompt Form */}
            <form onSubmit={handleSubmit} className="mt-3">
              <div className="relative">
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Speak via Wispr Flow (Ctrl+Win) or type command..."
                  className="w-full h-24 rounded-lg bg-slate-950 border border-slate-800 p-3 pr-10 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
                />
                <button
                  type="button"
                  onClick={toggleWisprVoice}
                  title="Toggle Wispr Flow Voice (Ctrl+Win)"
                  className={`absolute top-2.5 right-2.5 p-1.5 rounded-md transition-all ${
                    isListening
                      ? 'bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse'
                      : 'bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>
              </div>

              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-slate-500 flex items-center gap-1 font-mono">
                  <ShieldAlert className="w-3.5 h-3.5 text-emerald-400" /> Hotkey: Ctrl+Win
                </span>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white transition-all shadow-md shadow-indigo-600/20"
                >
                  Dispatch Pipeline
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Action Button Avatar */}
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className={`w-14 h-14 rounded-full flex items-center justify-center text-white shadow-xl border relative transition-all ${
          isListening
            ? 'bg-gradient-to-tr from-red-600 via-purple-600 to-indigo-600 border-red-400/50 shadow-red-500/30 ring-4 ring-red-500/20'
            : 'bg-gradient-to-tr from-indigo-600 via-purple-600 to-indigo-400 border-indigo-300/30 shadow-indigo-500/30'
        }`}
      >
        {isListening ? <Mic className="w-7 h-7 text-white animate-bounce" /> : <Bot className="w-7 h-7" />}
        <span className={`absolute top-0 right-0 w-3.5 h-3.5 border-2 border-slate-950 rounded-full ${
          isListening ? 'bg-red-500 animate-ping' : 'bg-emerald-500'
        }`} />
      </motion.button>
    </div>
  );
}
