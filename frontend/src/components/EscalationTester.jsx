import React, { useState } from 'react';
import { Layers, Send, Loader2, CheckCircle2, ChevronRight } from 'lucide-react';

export default function EscalationTester() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const tiers = [
    { tier: 1, name: 'Short Memory', desc: 'Active conversation buffer' },
    { tier: 2, name: 'Vector RAG', desc: 'ChromaDB indexed codebase' },
    { tier: 3, name: 'Local Fast LLM', desc: '0.5B-1.5B instant response' },
    { tier: 4, name: 'Multi-Agent', desc: 'LangGraph full autonomous graph' },
    { tier: 5, name: 'Live Web Search', desc: 'Real-time internet crawling' },
    { tier: 6, name: 'Cloud Fallback', desc: 'High-parameter cloud models' },
    { tier: 7, name: 'Human Operator', desc: 'Interactive developer escalation' }
  ];

  const handleEscalate = async (e) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    setResult(null);

    try {
      const resp = await fetch('/api/v1/intelligence/escalate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await resp.json();
      setResult(data);
    } catch (err) {
      setResult({ error: err.message, resolved: false });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* 7-Tier Pipeline Indicator */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-3">
        <div className="text-xs uppercase font-bold tracking-wider text-zinc-400 mb-2 flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-red-500" />
            7-Tier Intelligence Architecture
          </span>
          <span className="text-zinc-500 font-mono text-[10px]">TIERS 1 - 7</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
          {tiers.map((t) => {
            const isUsed = result && result.tier_used === t.tier;
            return (
              <div
                key={t.tier}
                className={`p-2 rounded border text-center transition ${
                  isUsed
                    ? 'bg-red-950/80 border-red-500 text-white glow-red'
                    : 'bg-zinc-900 border-zinc-800 text-zinc-400'
                }`}
              >
                <div className="text-[10px] font-mono text-red-400 font-bold">TIER {t.tier}</div>
                <div className="text-xs font-semibold text-zinc-200 truncate">{t.name}</div>
                <div className="text-[10px] text-zinc-500 truncate">{t.desc}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Query Input */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 space-y-3">
        <div className="text-xs font-bold uppercase tracking-wider text-zinc-200">
          Escalation Query Tester
        </div>
        <form onSubmit={handleEscalate} className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask anything to test intelligent tier routing..."
              disabled={loading}
              className="flex-1 bg-zinc-900 border border-zinc-700 focus:border-red-500 rounded-lg px-4 py-2.5 text-sm text-white placeholder-zinc-500 outline-none transition"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-5 py-2.5 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded-lg font-semibold text-xs flex items-center gap-1.5 transition"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              <span>ESCALATE</span>
            </button>
          </div>
        </form>

        {/* Result Card */}
        {result && (
          <div className="mt-3 p-3.5 bg-zinc-900 border border-zinc-800 rounded-lg space-y-2">
            <div className="flex items-center justify-between text-xs border-b border-zinc-800 pb-2">
              <span className="text-zinc-400">
                Resolved By:{' '}
                <span className="text-red-400 font-bold font-mono">
                  Tier {result.tier_used}: {result.tier_name}
                </span>
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-zinc-800 text-zinc-200">
                {result.resolved ? 'RESOLVED' : 'PARTIAL'}
              </span>
            </div>
            <div className="text-xs text-zinc-200 whitespace-pre-wrap leading-relaxed font-mono">
              {result.response || result.error || JSON.stringify(result, null, 2)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
