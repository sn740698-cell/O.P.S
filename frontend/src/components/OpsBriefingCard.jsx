import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles, Layers, Volume2, Cpu, ShieldAlert, CheckCircle2, XCircle, Copy, Check, Loader2, MessageSquare, RefreshCw
} from 'lucide-react';
import TypewriterResponse from './TypewriterResponse';

export default function OpsBriefingCard({
  briefingText,
  activeTaskPrompt = '',
  isLoading = false,
  currentThought = '',
  activeAgent = '',
  planSteps = [],
  activeCategory,
  onSpeakText,
  activePermissionReq,
  onResolvePermission,
  conversationHistory = []
}) {
  const [copiedIdx, setCopiedIdx] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversationHistory, briefingText, isLoading, currentThought]);

  const handleCopy = (text, idx) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-4 flex flex-col h-full space-y-3 font-mono">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-2.5">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-red-500" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-200">
            O.P.S. Executive Query Output
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {activeCategory && (
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-zinc-900 border border-zinc-800 text-red-400">
              {activeCategory}
            </span>
          )}
          {conversationHistory.length > 0 && (
            <span className="text-[10px] text-zinc-500 font-semibold">
              [{conversationHistory.length} TURNS]
            </span>
          )}
        </div>
      </div>

      {/* HITL Inline Approval Notice if pending */}
      {activePermissionReq && (
        <div className="p-3.5 bg-red-950/80 border-2 border-red-600 rounded-lg shadow-lg space-y-2.5 animate-pulse">
          <div className="flex items-center gap-2 text-red-300 font-bold text-xs uppercase tracking-wider">
            <ShieldAlert className="w-4 h-4 text-red-400" />
            <span>HITL APPROVAL REQUIRED BEFORE EXECUTION</span>
          </div>
          <div className="text-xs text-white bg-black/70 p-2 border border-zinc-700 rounded font-mono whitespace-pre-wrap">
            {activePermissionReq.reason || activePermissionReq.command || "Automation action plan requires confirmation."}
          </div>
          <div className="flex items-center gap-2 pt-1">
            <button
              onClick={() => onResolvePermission && onResolvePermission(activePermissionReq.request_id || activePermissionReq.id, 'ALLOW_ONCE')}
              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded flex items-center gap-1.5 transition"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>[ ACCEPT ]</span>
            </button>
            <button
              onClick={() => onResolvePermission && onResolvePermission(activePermissionReq.request_id || activePermissionReq.id, 'DENY')}
              className="px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-red-400 font-bold text-xs rounded flex items-center gap-1.5 transition"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>[ DECLINE ]</span>
            </button>
          </div>
        </div>
      )}

      {/* Formulated Plan Section */}
      {planSteps && planSteps.length > 0 && (
        <div className="p-2.5 bg-zinc-900/60 rounded-lg border border-zinc-800/80 space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-wider text-red-400 flex items-center gap-1.5">
            <Layers className="w-3 h-3" />
            <span>Multi-Agent Execution Steps:</span>
          </div>
          <div className="space-y-0.5">
            {planSteps.map((step, i) => (
              <div key={i} className="text-xs text-zinc-300 flex items-start gap-2">
                <span className="text-red-500 text-[10px] font-bold">{i + 1}.</span>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Multi-Turn Continuous Scrollable Conversation Screen */}
      <div className="flex-1 min-h-64 overflow-y-auto pr-1 text-xs text-zinc-100 bg-black p-3.5 rounded-lg leading-relaxed border border-zinc-900 max-h-96 space-y-3.5">
        {conversationHistory.length === 0 && !isLoading ? (
          <div className="flex flex-col items-center justify-center h-48 text-center text-zinc-600 space-y-2">
            <Cpu className="w-8 h-8 text-zinc-700 stroke-1" />
            <div className="text-xs font-medium text-zinc-400">Awaiting Directive</div>
            <div className="text-[11px] text-zinc-500 max-w-xs leading-normal">
              Continuous multi-turn session active.<br />
              user / bot conversation loop persists until Refresh.
            </div>
          </div>
        ) : (
          <>
            {conversationHistory.map((turn, idx) => (
              <div key={idx} className="space-y-1 pb-2 border-b border-zinc-900/70 last:border-b-0">
                <div className="flex items-center justify-between">
                  <span className={`font-bold text-[11px] uppercase tracking-wider ${
                    turn.role === 'user' ? 'text-red-400' : 'text-sky-400'
                  }`}>
                    {turn.role === 'user' ? 'user :' : 'bot :'}
                  </span>
                  {turn.role === 'bot' && (
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => handleCopy(turn.text, idx)}
                        className="text-zinc-500 hover:text-zinc-300 p-0.5"
                        title="Copy turn"
                      >
                        {copiedIdx === idx ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      </button>
                      <button
                        type="button"
                        onClick={() => onSpeakText && onSpeakText(turn.text)}
                        className="text-zinc-500 hover:text-red-400 p-0.5"
                        title="Speak (Piper TTS)"
                      >
                        <Volume2 className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>

                <div className={`text-xs whitespace-pre-wrap leading-relaxed ${
                  turn.role === 'user' ? 'text-white font-medium pl-1' : 'text-zinc-200 pl-1'
                }`}>
                  {turn.text}
                </div>
              </div>
            ))}

            {/* Live Thinking / Synthesis Ticker */}
            {isLoading && (
              <div className="space-y-1 pt-1">
                <div className="font-bold text-[11px] uppercase tracking-wider text-sky-400">
                  bot :
                </div>
                <div className="text-xs text-red-400 animate-pulse flex items-center gap-2 pl-1 font-mono">
                  <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" />
                  <span>{currentThought || 'Formulating tactical response...'}</span>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={scrollRef} />
      </div>
    </div>
  );
}
