import React, { useState } from 'react';
import { Bot, Copy, Check, Volume2, Globe, ExternalLink, Sparkles } from 'lucide-react';
import MarkdownRenderer from './MarkdownRenderer';

export default function AssistantMessage({
  turn,
  idx,
  onSpeakText
}) {
  const [copied, setCopied] = useState(false);
  const messageText = turn?.text || turn?.content || '';

  const handleCopy = () => {
    if (!messageText) return;
    navigator.clipboard.writeText(messageText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const citations = turn?.citations || turn?.metadata?.citations || [];

  return (
    <div className="space-y-1.5 pb-3 border-b border-zinc-900 last:border-b-0 font-mono">
      {/* JARVIS Assistant Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-sky-400 animate-pulse"></div>
          <span className="font-bold text-[11px] uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
            <Bot className="w-3.5 h-3.5 text-sky-400" />
            <span>O.P.S. // JARVIS</span>
          </span>
          {turn?.category && (
            <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold border ${
              turn.category.toUpperCase().includes('LLM')
                ? 'bg-blue-950/80 text-blue-300 border-blue-700'
                : turn.category.toUpperCase().includes('WEB')
                ? 'bg-emerald-950/80 text-emerald-300 border-emerald-700'
                : turn.category.toUpperCase().includes('HYBRID')
                ? 'bg-purple-950/80 text-purple-300 border-purple-700'
                : 'bg-zinc-900 border-zinc-800 text-zinc-400'
            }`}>
              [{turn.category}]
            </span>
          )}
        </div>

        {/* Turn Utilities */}
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={handleCopy}
            className="p-1 rounded bg-zinc-900/60 hover:bg-zinc-800 text-zinc-400 hover:text-white border border-zinc-800 transition"
            title="Copy response"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          </button>
          {onSpeakText && (
            <button
              type="button"
              onClick={() => onSpeakText(messageText)}
              className="p-1 rounded bg-zinc-900/60 hover:bg-zinc-800 text-zinc-400 hover:text-red-400 border border-zinc-800 transition"
              title="Speak (Voice Synthesizer)"
            >
              <Volume2 className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Structured Markdown Body */}
      <div className="pl-3.5 border-l border-zinc-800/80">
        <MarkdownRenderer content={messageText} />

        {/* Verified Citation Links if available */}
        {citations && citations.length > 0 && (
          <div className="mt-3 pt-2.5 border-t border-zinc-900 space-y-1.5">
            <div className="text-[10px] uppercase font-bold text-zinc-400 tracking-wider flex items-center gap-1.5">
              <Globe className="w-3 h-3 text-red-500" />
              <span>VERIFIED EVIDENCE SOURCES:</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              {citations.map((c, cIdx) => (
                <a
                  key={cIdx}
                  href={c.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 bg-zinc-950 hover:bg-zinc-900 border border-zinc-800 hover:border-zinc-700 transition flex items-start gap-1.5 group text-[11px]"
                >
                  <span className="text-red-400 font-bold shrink-0">{c.citation_tag || `[${c.index || cIdx + 1}]`}</span>
                  <div className="min-w-0 flex-1">
                    <div className="text-zinc-200 group-hover:text-white truncate font-medium">
                      {c.title || c.url}
                    </div>
                    <div className="text-[10px] text-zinc-500 truncate flex items-center gap-1">
                      <span>{c.url}</span>
                      <ExternalLink className="w-2.5 h-2.5 shrink-0 opacity-0 group-hover:opacity-100 transition" />
                    </div>
                  </div>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
