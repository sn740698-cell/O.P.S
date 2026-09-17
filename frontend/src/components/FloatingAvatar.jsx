import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Bot, Sparkles, MessageSquare, Terminal, ShieldAlert } from 'lucide-react';

export default function FloatingAvatar({ activeCategory, onPromptSubmit }) {
  const [isOpen, setIsOpen] = useState(false);
  const [prompt, setPrompt] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    onPromptSubmit(prompt);
    setPrompt('');
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="mb-4 w-96 rounded-2xl bg-slate-900/95 border border-indigo-500/30 p-4 shadow-2xl backdrop-blur-xl"
        >
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-400 animate-pulse" />
              <span className="font-semibold text-sm text-slate-200">O.P.S. Ambient Overlay</span>
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              {activeCategory || 'ROUTER READY'}
            </span>
          </div>

          <form onSubmit={handleSubmit} className="mt-3">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Ask O.P.S. to automate, code, or scrape..."
              className="w-full h-24 rounded-lg bg-slate-950 border border-slate-800 p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
            />
            <div className="flex items-center justify-between mt-2">
              <span className="text-xs text-slate-500 flex items-center gap-1">
                <ShieldAlert className="w-3.5 h-3.5 text-emerald-400" /> Safe Gatekeeper
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

      {/* Floating Action Button Avatar */}
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className="w-14 h-14 rounded-full bg-gradient-to-tr from-indigo-600 via-purple-600 to-indigo-400 flex items-center justify-center text-white shadow-xl shadow-indigo-500/30 border border-indigo-300/30 relative"
      >
        <Bot className="w-7 h-7" />
        <span className="absolute top-0 right-0 w-3.5 h-3.5 bg-emerald-500 border-2 border-slate-950 rounded-full"></span>
      </motion.button>
    </div>
  );
}
