import React, { useState } from 'react';
import {
  Mic, Send, RefreshCw, Square, Loader2, Sparkles, AlertTriangle
} from 'lucide-react';

export default function OpsCommandCore({
  onDispatchCommand,
  isLoading,
  activeAgent,
  currentThought,
  onToggleVoice,
  isListening,
  onEmergencyHalt,
  sessionId,
  onRefreshSession
}) {
  const [inputPrompt, setInputPrompt] = useState('');

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!inputPrompt.trim() || isLoading) return;
    onDispatchCommand(inputPrompt);
    setInputPrompt('');
  };

  const quickDirectives = [
    { label: "[ 1. PYTHON CREATOR ]", prompt: "Who created Python programming language and why?" },
    { label: "[ 2. WEB FRAMEWORKS ]", prompt: "What are its main web frameworks?" },
    { label: "[ 3. CONTINUED COMPARISON ]", prompt: "Compare that with Rust." },
    { label: "[ 4. ROOM TEMP SUPERCONDUCTOR ]", prompt: "What are the latest breakthroughs in room temperature superconductors?" },
    { label: "[ 5. TOKAMAK FUSION ]", prompt: "Do the same analysis for tokamak fusion progress in 2026." },
    { label: "[ 6. AI DISCOVERIES ]", prompt: "Summarize top autonomous AI agent research papers this year." }
  ];

  return (
    <div className="retro-box-red p-4 shadow-2xl relative overflow-hidden font-mono">
      {/* Background cyber accent line */}
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-red-600 to-transparent"></div>

      <div className="flex flex-col md:flex-row items-center gap-4 justify-between">
        {/* Glowing O.P.S. Core Reactor Orb & Telemetry */}
        <div className="flex items-center gap-3">
          <div className="relative group cursor-pointer" onClick={onToggleVoice}>
            <div className={`absolute -inset-1 rounded-full bg-red-600 opacity-60 blur-sm ${isLoading || isListening ? 'animate-ping duration-1000' : 'animate-pulse'}`}></div>
            <div className="relative w-14 h-14 rounded-full bg-black border-2 border-red-500 flex flex-col items-center justify-center shadow-lg">
              <div className="w-4 h-4 rounded-full bg-red-600 flex items-center justify-center">
                <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></div>
              </div>
              <span className="text-[8px] font-black tracking-widest text-red-400 font-mono mt-0.5">OPS</span>
            </div>
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-extrabold text-white tracking-wider">=== O.P.S. POP-UP COCKPIT ===</span>
              <span className={`px-2 py-0.5 text-[10px] font-mono font-bold tracking-wider border ${
                isLoading
                  ? 'bg-red-950 text-red-400 border-red-800 animate-pulse'
                  : isListening
                  ? 'bg-red-600 text-white border-red-500 animate-bounce'
                  : 'bg-black text-zinc-400 border-zinc-800'
              }`}>
                {isLoading ? `[BUSY: ${activeAgent || 'LANGGRAPH'}]` : isListening ? '[LISTENING: WISPR FLOW]' : '[STANDBY: READY]'}
              </span>
            </div>
            <p className="text-xs text-zinc-400 max-w-md truncate font-mono mt-0.5">
              &gt; {currentThought || "Continuous multi-turn session active. Type or speak follow-ups."}
            </p>
          </div>
        </div>

        {/* Action Controls: Refresh Session & Emergency Stop */}
        <div className="flex items-center gap-2 self-end md:self-center">
          {isLoading && onEmergencyHalt && (
            <button
              type="button"
              onClick={onEmergencyHalt}
              className="px-2.5 py-1.5 bg-red-950 hover:bg-red-900 border border-red-700 text-red-300 text-xs font-bold font-mono uppercase tracking-wider flex items-center gap-1.5 transition shadow"
              title="Stop ongoing generation"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>[ ⏹ STOP ]</span>
            </button>
          )}

          {/* Refresh / Reset Session Button with Confirmation Dialog */}
          <button
            type="button"
            onClick={onRefreshSession}
            disabled={isLoading}
            className="retro-btn px-2.5 py-1.5 text-xs font-bold font-mono uppercase tracking-wider flex items-center gap-1.5 hover:border-red-600 hover:text-white disabled:opacity-40"
            title="Permanently delete conversation and start fresh session"
          >
            <RefreshCw className="w-3.5 h-3.5 text-red-400" />
            <span>[ ↻ REFRESH ]</span>
          </button>
        </div>
      </div>

      {/* Main Directive Command Bar */}
      <form onSubmit={handleSubmit} className="mt-3">
        <div className="relative flex items-center">
          <input
            id="ops-command-input"
            type="text"
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            placeholder="Command O.P.S. (e.g. 'What is Python?', 'What are its web frameworks?', 'Compare that to Rust')..."
            disabled={isLoading}
            className="w-full bg-black border border-zinc-700 focus:border-red-500 focus:ring-1 focus:ring-red-500 rounded-none px-3.5 py-2.5 text-xs text-white placeholder-zinc-500 outline-none pr-32 transition font-mono shadow-inner disabled:opacity-60"
          />

          <div className="absolute right-1.5 flex items-center gap-1">
            <button
              type="button"
              onClick={onToggleVoice}
              className={`p-1.5 border transition ${
                isListening
                  ? 'bg-red-600 text-white border-red-500 animate-pulse'
                  : 'bg-zinc-900 text-zinc-400 hover:text-white border-zinc-700 hover:border-zinc-600'
              }`}
              title="Voice Input (Wispr Flow / Ctrl+Space)"
            >
              <Mic className="w-3.5 h-3.5" />
            </button>

            {isLoading && onEmergencyHalt ? (
              <button
                type="button"
                onClick={onEmergencyHalt}
                className="bg-red-700 hover:bg-red-600 text-white px-2.5 py-1 text-xs font-bold flex items-center gap-1 transition"
                title="Stop execution"
              >
                <Square className="w-3 h-3 fill-current" />
                <span>STOP</span>
              </button>
            ) : (
              <button
                type="submit"
                disabled={isLoading || !inputPrompt.trim()}
                className="retro-btn-red px-3 py-1 text-xs disabled:opacity-40 flex items-center gap-1"
                title="Dispatch Command"
              >
                <Send className="w-3.5 h-3.5" />
                <span>DISPATCH</span>
              </button>
            )}
          </div>
        </div>

        {/* Tactical Directive Shortcuts */}
        <div className="flex flex-wrap items-center gap-1.5 mt-2">
          <span className="text-[10px] font-mono text-zinc-500 mr-1">PRESETS:</span>
          {quickDirectives.map((d, i) => (
            <button
              key={i}
              type="button"
              onClick={() => onDispatchCommand(d.prompt)}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] font-mono hover:border-red-600 hover:text-white disabled:opacity-40"
            >
              {d.label}
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
