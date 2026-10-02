import React, { useState } from 'react';
import { Mic, Send, Sparkles, Terminal, Globe, Code2, Play, Loader2, Volume2, ShieldAlert } from 'lucide-react';

export default function OpsCommandCore({
  onDispatchCommand,
  isLoading,
  activeAgent,
  currentThought,
  onToggleVoice,
  isListening,
  onEmergencyHalt
}) {
  const [inputPrompt, setInputPrompt] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputPrompt.trim() || isLoading) return;
    onDispatchCommand(inputPrompt);
    setInputPrompt('');
  };

  const quickDirectives = [
    { label: "[ OPEN INSTAGRAM ]", prompt: "Open Instagram" },
    { label: "[ OPEN LEETCODE ]", prompt: "Open LeetCode" },
    { label: "[ OPEN CALC ]", prompt: "Open Calculator" },
    { label: "[ SYSTEM HEALTH ]", prompt: "Check system health and running processes" },
    { label: "[ SEARCH WEB ]", prompt: "Search web for latest open source AI agent frameworks" }
  ];

  return (
    <div className="retro-box-red p-4 shadow-2xl relative overflow-hidden font-mono">
      {/* Background cyber accent line */}
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-red-600 to-transparent"></div>

      <div className="flex flex-col md:flex-row items-center gap-4 justify-between">
        {/* Glowing O.P.S. Core Reactor Orb */}
        <div className="flex items-center gap-3">
          <div className="relative group cursor-pointer" onClick={onToggleVoice}>
            {/* Pulsing rings */}
            <div className={`absolute -inset-1 rounded-full bg-red-600 opacity-60 blur-sm ${isLoading || isListening ? 'animate-ping duration-1000' : 'animate-pulse'}`}></div>
            <div className="relative w-14 h-14 rounded-full bg-black border-2 border-red-500 flex flex-col items-center justify-center shadow-lg">
              <div className="w-4 h-4 rounded-full bg-red-600 flex items-center justify-center">
                <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></div>
              </div>
              <span className="text-[8px] font-black tracking-widest text-red-400 font-mono mt-0.5">OPS</span>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-extrabold text-white tracking-wider">=== O.P.S. COMMAND CORE ===</span>
              <span className={`px-2 py-0.5 text-[10px] font-mono font-bold tracking-wider border ${
                isLoading
                  ? 'bg-red-950 text-red-400 border-red-800 animate-pulse'
                  : isListening
                  ? 'bg-red-600 text-white border-red-500 animate-bounce'
                  : 'bg-black text-zinc-400 border-zinc-800'
              }`}>
                {isLoading ? `[BUSY: ${activeAgent || 'ORCHESTRATOR'}]` : isListening ? '[LISTENING: WISPR FLOW]' : '[STANDBY: READY]'}
              </span>
            </div>
            <p className="text-xs text-zinc-400 max-w-md truncate font-mono mt-0.5">
              &gt; {currentThought || "Autonomous workstation intelligence. Speak or type directive."}
            </p>
          </div>
        </div>

        {/* Emergency Halt Button */}
        <button
          type="button"
          onClick={onEmergencyHalt}
          className="retro-btn-red px-3 py-1.5 text-xs font-bold font-mono uppercase tracking-wider flex items-center gap-1.5 self-end md:self-center"
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>[ EMERGENCY KILL SWITCH ]</span>
        </button>
      </div>

      {/* Main Directive Command Bar */}
      <form onSubmit={handleSubmit} className="mt-3">
        <div className="relative flex items-center">
          <input
            type="text"
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            placeholder="Command O.P.S. (e.g. 'Open Instagram', 'Open Calculator', 'Search web for...')"
            disabled={isLoading}
            className="w-full bg-black border border-zinc-700 focus:border-red-500 focus:ring-1 focus:ring-red-500 rounded-none px-3.5 py-2.5 text-xs text-white placeholder-zinc-500 outline-none pr-28 transition font-mono shadow-inner"
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
              title="Voice Input (Wispr Flow)"
            >
              <Mic className="w-3.5 h-3.5" />
            </button>

            <button
              type="submit"
              disabled={isLoading || !inputPrompt.trim()}
              className="retro-btn-red px-3 py-1 text-xs disabled:opacity-40 flex items-center gap-1"
              title="Dispatch Command"
            >
              {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
              <span>DISPATCH</span>
            </button>
          </div>
        </div>

        {/* Tactical Directive Shortcuts */}
        <div className="flex flex-wrap gap-1.5 mt-2">
          <span className="text-[10px] font-mono text-zinc-500 self-center mr-1">QUICK_LAUNCH:</span>
          {quickDirectives.map((d, i) => (
            <button
              key={i}
              type="button"
              onClick={() => onDispatchCommand(d.prompt)}
              className="retro-btn px-2 py-0.5 text-[10px] font-mono hover:border-red-600 hover:text-white"
            >
              {d.label}
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
