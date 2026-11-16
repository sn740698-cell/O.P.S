import React from 'react';
import { RefreshCw, Square, Activity, Zap } from 'lucide-react';

export default function OpsCommandCore({
  activeTaskPrompt = '',
  isLoading = false,
  activeAgent = '',
  currentThought = '',
  onEmergencyHalt,
  sessionId = '',
  onRefreshSession,
  activeEngine = null,
  activeMode = null
}) {
  return (
    <div className="retro-box-red p-4 shadow-2xl relative overflow-hidden font-mono">
      {/* Background cyber accent line */}
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-red-600 to-transparent"></div>

      <div className="flex flex-col md:flex-row items-center gap-4 justify-between">
        {/* Glowing O.P.S. Core Reactor Orb & Telemetry */}
        <div className="flex items-center gap-3">
          <div className="relative group">
            <div className={`absolute -inset-1 rounded-full bg-red-600 opacity-60 blur-sm ${isLoading ? 'animate-ping duration-1000' : 'animate-pulse'}`}></div>
            <div className="relative w-14 h-14 rounded-full bg-black border-2 border-red-500 flex flex-col items-center justify-center shadow-lg">
              <div className="w-4 h-4 rounded-full bg-red-600 flex items-center justify-center">
                <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></div>
              </div>
              <span className="text-[8px] font-black tracking-widest text-red-400 font-mono mt-0.5">OPS</span>
            </div>
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-extrabold text-white tracking-wider">=== O.P.S. COMMAND COCKPIT // DIRECTIVE MONITOR ===</span>
              <span className={`px-2 py-0.5 text-[10px] font-mono font-bold tracking-wider border ${
                isLoading
                  ? 'bg-red-950 text-red-400 border-red-800 animate-pulse'
                  : 'bg-black text-zinc-400 border-zinc-800'
              }`}>
                {isLoading ? `[BUSY: ${activeAgent || 'LANGGRAPH'}]` : '[STANDBY: READY]'}
              </span>
            </div>
            <p className="text-xs text-zinc-400 max-w-md truncate font-mono mt-0.5">
              &gt; {currentThought || "Continuous multi-turn session active. Directives from Popup Cockpit stream live here."}
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
          {onRefreshSession && (
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
          )}
        </div>
      </div>

      {/* Active Directive Display Synchronized from Popup Cockpit */}
      <div className="mt-3 p-3 bg-black/90 border border-zinc-800 rounded flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-inner">
        <div className="flex items-start sm:items-center gap-2.5 flex-1 min-w-0">
          <span className="px-2 py-0.5 bg-red-600 text-white font-black text-[10px] tracking-wider uppercase shrink-0 flex items-center gap-1">
            <Zap className="w-3 h-3 text-white fill-current" />
            <span>ACTIVE DIRECTIVE</span>
          </span>
          <span className="text-xs font-bold text-white font-mono truncate select-text">
            {activeTaskPrompt ? `"${activeTaskPrompt}"` : "(Awaiting directive from Desktop Popup Cockpit...)"}
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0 text-[10px]">
          <span className="text-zinc-500 uppercase font-mono">STAGE:</span>
          <span className={`px-2 py-0.5 rounded font-bold font-mono ${
            isLoading
              ? 'bg-amber-950 text-amber-300 border border-amber-800 animate-pulse'
              : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
          }`}>
            {isLoading ? (currentThought || 'PROCESSING') : 'STANDBY READY'}
          </span>
        </div>
      </div>

      {/* Real-Time Engine, Mode & Specialist Agent Telemetry Ribbon */}
      <div className="flex flex-wrap items-center justify-between gap-2 mt-2 pt-2 border-t border-zinc-800/80 text-[10px] text-zinc-400">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span className="text-zinc-500 font-bold uppercase">ACTIVE ENGINE:</span>
            <span className={`font-bold ${
              activeEngine === 'COMPOSITE' ? 'text-rose-400 animate-pulse' :
              activeEngine === 'AUTOMATION' ? 'text-cyan-400' :
              activeEngine === 'ANSWERING' ? 'text-sky-400' : 'text-zinc-300'
            }`}>
              {activeEngine || (isLoading ? 'ROUTING' : 'STANDBY')}
            </span>
          </span>
          <span className="text-zinc-700">|</span>
          <span className="flex items-center gap-1">
            <span className="text-zinc-500 font-bold uppercase">RESPONSE MODE:</span>
            <span className={`font-bold ${
              activeMode === 'LLM' ? 'text-blue-400' :
              activeMode === 'WEB' ? 'text-emerald-400' :
              activeMode === 'HYBRID' ? 'text-purple-400' :
              activeMode === 'DOCUMENT' ? 'text-amber-400' :
              activeMode === 'DESKTOP' ? 'text-cyan-400' :
              activeMode === 'BROWSER' ? 'text-indigo-400' :
              activeMode === 'COMPOSITE' ? 'text-rose-400' :
              activeMode ? 'text-rose-400' : 'text-zinc-400'
            }`}>
              {activeMode || (isLoading ? 'DETECTING' : 'IDLE')}
            </span>
          </span>
          <span className="text-zinc-700">|</span>
          <span className="flex items-center gap-1">
            <span className="text-zinc-500 font-bold uppercase">CURRENT AGENT:</span>
            <span className="font-bold text-zinc-200">
              {activeAgent || (isLoading ? 'Global Intent Router' : 'Supervisor Ready')}
            </span>
          </span>
        </div>

        <span className="text-[9px] text-zinc-500 font-mono hidden md:inline">
          SESSION: {sessionId ? sessionId.slice(0, 16) : 'active'}
        </span>
      </div>
    </div>
  );
}
