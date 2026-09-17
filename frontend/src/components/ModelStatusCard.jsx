import React from 'react';
import { Cpu, Zap, Brain, Code } from 'lucide-react';

export default function ModelStatusCard({ models }) {
  const modelList = [
    {
      name: 'Router Model',
      id: models?.router || 'qwen2.5:0.5b',
      role: 'Intent Classification & Dispatch',
      latency: '< 50ms',
      icon: Zap,
      color: 'text-amber-400 bg-amber-400/10 border-amber-400/20'
    },
    {
      name: 'Reasoning Engine',
      id: models?.reasoning || 'llama3.2:1b',
      role: 'Multi-Step Planning & Validation',
      latency: '150ms',
      icon: Brain,
      color: 'text-indigo-400 bg-indigo-400/10 border-indigo-400/20'
    },
    {
      name: 'Coding & Automation',
      id: models?.coding || 'qwen2.5-coder:1.5b',
      role: 'Code Gen & DOM/GUI Synthesizer',
      latency: '200ms',
      icon: Code,
      color: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {modelList.map((m, idx) => {
        const Icon = m.icon;
        return (
          <div
            key={idx}
            className="rounded-xl bg-slate-900/60 border border-slate-800 p-4 hover:border-slate-700 transition-all"
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`p-2 rounded-lg border ${m.color}`}>
                <Icon className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                {m.latency}
              </span>
            </div>
            <h3 className="text-sm font-semibold text-slate-200">{m.name}</h3>
            <p className="text-xs text-indigo-400 font-mono mt-0.5">{m.id}</p>
            <p className="text-xs text-slate-400 mt-2">{m.role}</p>
          </div>
        );
      })}
    </div>
  );
}
