import React from 'react';
import { Cpu, Zap, MessageSquare } from 'lucide-react';

export default function OpsTriModelStatus() {
  const models = [
    {
      id: 'model-1',
      name: 'Qwen3 0.6B',
      role: 'Core Normalization & Structuring',
      badge: 'CORE & SCHEMA',
      desc: 'Pattern normalization, entity extraction, DOM sanitization & result schemas.',
      agents: 'Prompt Template • BeautifulSoup • Open File • Result',
      icon: Zap,
      color: 'border-red-500/80 bg-red-950/30 text-red-400'
    },
    {
      id: 'model-2',
      name: 'Qwen3 1.7B',
      role: 'Superior Reasoning & Routing',
      badge: 'REASONER',
      desc: '2-way domain routing, task decomposition & retrieval quality loop.',
      agents: 'Router • Web Superior • Web Understanding • Quality Gate',
      icon: Cpu,
      color: 'border-amber-500/80 bg-amber-950/20 text-amber-300'
    },
    {
      id: 'model-3',
      name: 'Llama 3.2 1B Instruct',
      role: 'Autonomous Tool Execution & Voice',
      badge: 'EXECUTION',
      desc: 'Structured scraping, multi-page crawling, app control & Jarvis voice.',
      agents: 'ScrapeGraphAI • Crawlee • Open Web • Apps • Desktop • Jarvis',
      icon: MessageSquare,
      color: 'border-cyan-500/80 bg-cyan-950/20 text-cyan-300'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-2 font-mono">
      {models.map((m) => {
        const IconComponent = m.icon;
        return (
          <div
            key={m.id}
            className="rounded-lg border border-zinc-800/90 bg-zinc-950/90 px-2.5 py-2 shadow-sm hover:border-zinc-700 transition flex flex-col justify-between"
          >
            <div>
              {/* Header */}
              <div className="flex items-center justify-between gap-1.5 mb-1">
                <div className="flex items-center gap-1.5 min-w-0">
                  <div className="p-1 rounded bg-zinc-900 border border-zinc-800 text-red-500 shrink-0">
                    <IconComponent className="w-3 h-3" />
                  </div>
                  <div className="truncate">
                    <h4 className="text-[11px] font-bold text-white tracking-tight truncate">{m.name}</h4>
                    <p className="text-[9px] text-zinc-400 font-sans font-medium truncate">{m.role}</p>
                  </div>
                </div>
                <span className={`text-[8px] font-mono px-1 py-0.2 rounded border uppercase font-bold tracking-wider shrink-0 ${m.color}`}>
                  {m.badge}
                </span>
              </div>

              {/* Description */}
              <p className="text-[10px] text-zinc-300 leading-tight font-sans mt-0.5">
                {m.desc}
              </p>

              {/* Sub-agents Assigned */}
              <div className="mt-1.5 pt-1 border-t border-zinc-900 text-[9px] text-zinc-400 flex items-start gap-1 font-mono">
                <span className="text-red-400 font-bold shrink-0">Agents:</span>
                <span className="text-zinc-400 leading-tight truncate">{m.agents}</span>
              </div>
            </div>

            {/* Status Footer */}
            <div className="mt-1.5 pt-1 border-t border-zinc-900 flex items-center justify-between text-[9px] font-mono text-zinc-500">
              <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                <span className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
                ONLINE (Ollama)
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
