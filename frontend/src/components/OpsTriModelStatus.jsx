import React from 'react';
import { Cpu, Zap, MessageSquare, CheckCircle2 } from 'lucide-react';

export default function OpsTriModelStatus() {
  const models = [
    {
      id: 'model-1',
      name: 'Qwen3 0.6B',
      role: 'Fast Router & Intent Detection',
      desc: 'Sub-50ms intent detection, simple vs. complex routing, command classification & parameter extraction.',
      icon: Zap,
      badge: 'ROUTER',
      color: 'border-red-500/80 bg-red-950/20 text-red-400'
    },
    {
      id: 'model-2',
      name: 'Qwen3 1.7B',
      role: 'Main Reasoning & Planning Model',
      desc: 'Deep multi-step reasoning, task decomposition, agent orchestration, code generation & debugging.',
      icon: Cpu,
      badge: 'REASONER',
      color: 'border-zinc-500/80 bg-zinc-900/60 text-zinc-200'
    },
    {
      id: 'model-3',
      name: 'Llama 3.2 1B Instruct',
      role: 'Conversation, Content & Jarvis Persona',
      desc: 'Unified J.A.R.V.I.S. voice, professional emails, letters, technical summaries & user response framing.',
      icon: MessageSquare,
      badge: 'PERSONA',
      color: 'border-white/70 bg-zinc-900/60 text-white'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
      {models.map((m) => {
        const IconComponent = m.icon;
        return (
          <div
            key={m.id}
            className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-3 shadow-md hover:border-zinc-700 transition flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-red-500">
                    <IconComponent className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-white font-mono tracking-tight">{m.name}</h4>
                    <p className="text-[10px] text-red-400 font-sans font-semibold">{m.role}</p>
                  </div>
                </div>
                <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border uppercase font-bold ${m.color}`}>
                  {m.badge}
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 leading-snug font-sans mt-1">
                {m.desc}
              </p>
            </div>

            <div className="mt-2.5 pt-2 border-t border-zinc-800/80 flex items-center justify-between text-[10px] font-mono text-zinc-500">
              <span className="flex items-center gap-1 text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                ONLINE (Ollama)
              </span>
              <span>100% Local-First</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
