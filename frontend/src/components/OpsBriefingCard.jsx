import React from 'react';
import { CheckCircle2, Cpu, Volume2, Sparkles, Layers, Terminal } from 'lucide-react';
import TypewriterResponse from './TypewriterResponse';

export default function OpsBriefingCard({ briefingText, planSteps = [], activeCategory, onSpeakText }) {
  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-4 flex flex-col h-full space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-2.5">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-red-500" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-200">
            O.P.S. Executive Synthesis
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {activeCategory && (
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-zinc-900 border border-zinc-800 text-red-400">
              {activeCategory}
            </span>
          )}
          {briefingText && (
            <button
              onClick={() => onSpeakText && onSpeakText(briefingText)}
              className="p-1.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 hover:text-white transition"
              title="Speak Briefing (Piper TTS)"
            >
              <Volume2 className="w-3.5 h-3.5 text-red-400" />
            </button>
          )}
        </div>
      </div>

      {/* Formulated Plan Section */}
      {planSteps.length > 0 && (
        <div className="p-3 bg-zinc-900/60 rounded-lg border border-zinc-800/80 space-y-1.5">
          <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-red-400 flex items-center gap-1.5">
            <Layers className="w-3 h-3" />
            <span>Multi-Agent Tactical Plan:</span>
          </div>
          <div className="space-y-1">
            {planSteps.map((step, i) => (
              <div key={i} className="text-xs text-zinc-300 flex items-start gap-2">
                <span className="text-red-500 font-mono text-[10px]">{i + 1}.</span>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Formatted Response Body */}
      <div className="flex-1 overflow-y-auto pr-1 text-xs text-zinc-100 bg-zinc-900/40 rounded-lg p-3.5 font-mono leading-relaxed border border-zinc-800/70 max-h-80">
        {briefingText ? (
          <TypewriterResponse text={briefingText} speed={20} />
        ) : (
          <div className="flex flex-col items-center justify-center h-48 text-center text-zinc-600 space-y-2">
            <Cpu className="w-8 h-8 text-zinc-700 stroke-1" />
            <div className="text-xs font-medium">Awaiting Directive</div>
            <div className="text-[11px] text-zinc-500 max-w-xs">
              Direct O.P.S. using the central Command Core above to begin autonomous execution.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
