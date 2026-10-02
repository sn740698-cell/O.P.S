import React, { useState } from 'react';
import { Play, Send, Cpu, CheckCircle2, Loader2, Sparkles, Terminal } from 'lucide-react';

export default function AgentCockpit({ onDispatchPrompt, agentOutput, thoughts, isLoading, activeAgent }) {
  const [prompt, setPrompt] = useState('');
  const [mode, setMode] = useState('langgraph'); // 'langgraph' or 'trimodel'

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;
    onDispatchPrompt(prompt, mode);
  };

  const samplePrompts = [
    "Check disk storage and list large files",
    "Explain what O.P.S. architecture does",
    "Scrape latest news from python.org",
    "Run directory diagnostics"
  ];

  return (
    <div className="space-y-4">
      {/* Agent Workflow Execution Badges */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-3">
        <div className="text-xs uppercase font-bold tracking-wider text-zinc-400 mb-2 flex items-center justify-between">
          <span>Active Agent Workflow</span>
          <span className="text-red-400 font-mono">LANGGRAPH STATE GRAPH</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
          {[
            { id: 'Supervisor', label: 'Supervisor (Router)' },
            { id: 'DeveloperAgent', label: 'Developer (Coder)' },
            { id: 'BrowserAgent', label: 'Browser (Scraper)' },
            { id: 'SystemAutomationAgent', label: 'Automation (OS)' },
            { id: 'Synthesizer', label: 'Synthesizer (Output)' }
          ].map((agent) => {
            const isActive = activeAgent === agent.id;
            return (
              <div
                key={agent.id}
                className={`p-2.5 rounded border transition-all ${
                  isActive
                    ? 'bg-red-950/60 border-red-600 text-white shadow-sm'
                    : 'bg-zinc-900 border-zinc-800 text-zinc-400'
                }`}
              >
                <div className="flex items-center gap-1.5 font-semibold text-xs">
                  {isActive ? (
                    <Loader2 className="w-3.5 h-3.5 text-red-400 animate-spin" />
                  ) : (
                    <Cpu className="w-3.5 h-3.5 text-zinc-500" />
                  )}
                  <span>{agent.label}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Prompt Form */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold uppercase tracking-wider text-zinc-200 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-red-500" />
            Command Dispatcher
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="text-zinc-400">Mode:</span>
            <button
              type="button"
              onClick={() => setMode('langgraph')}
              className={`px-2 py-1 rounded text-xs font-medium transition ${
                mode === 'langgraph'
                  ? 'bg-red-600 text-white'
                  : 'bg-zinc-900 text-zinc-400 hover:text-white'
              }`}
            >
              LangGraph Multi-Agent
            </button>
            <button
              type="button"
              onClick={() => setMode('trimodel')}
              className={`px-2 py-1 rounded text-xs font-medium transition ${
                mode === 'trimodel'
                  ? 'bg-red-600 text-white'
                  : 'bg-zinc-900 text-zinc-400 hover:text-white'
              }`}
            >
              Tri-Model Pipeline
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-2">
          <div className="relative">
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter instruction for O.P.S. autonomous agent..."
              disabled={isLoading}
              className="w-full bg-zinc-900 border border-zinc-700 focus:border-red-500 focus:ring-1 focus:ring-red-500 rounded-lg px-4 py-3 text-sm text-white placeholder-zinc-500 outline-none pr-12 transition"
            />
            <button
              type="submit"
              disabled={isLoading || !prompt.trim()}
              className="absolute right-2 top-2 p-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:hover:bg-red-600 text-white rounded-md transition"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>

          {/* Quick suggestions */}
          <div className="flex flex-wrap gap-1.5 pt-1">
            <span className="text-zinc-500 text-xs self-center mr-1">Quick:</span>
            {samplePrompts.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setPrompt(p)}
                className="text-xs bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-800 hover:border-zinc-700 px-2.5 py-1 rounded transition"
              >
                {p}
              </button>
            ))}
          </div>
        </form>
      </div>

      {/* Streaming Thoughts and Result */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Thoughts stream */}
        <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-3 space-y-2 h-72 flex flex-col">
          <div className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center justify-between border-b border-zinc-800 pb-1.5">
            <span className="flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-zinc-400" />
              Agent Thoughts & Plan Stream
            </span>
            <span className="text-zinc-500 font-mono text-[10px]">{thoughts.length} events</span>
          </div>
          <div className="flex-1 overflow-y-auto space-y-2 pr-1 font-mono text-xs">
            {thoughts.length === 0 ? (
              <div className="text-zinc-600 italic text-center py-10">No agent actions in progress. Submit a prompt above.</div>
            ) : (
              thoughts.map((item, idx) => (
                <div key={idx} className="p-2 rounded bg-zinc-900/80 border border-zinc-800/80">
                  <div className="flex items-center justify-between text-[10px] text-red-400 font-semibold mb-1">
                    <span>{item.agent || 'Agent'}</span>
                    <span className="text-zinc-500">{new Date(item.timestamp * 1000).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-zinc-200 whitespace-pre-wrap">{item.thought || item.message || JSON.stringify(item)}</p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Final Synthesized Output */}
        <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-3 space-y-2 h-72 flex flex-col">
          <div className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center justify-between border-b border-zinc-800 pb-1.5">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-red-400" />
              Synthesized Agent Response
            </span>
            <span className="text-red-400 font-mono text-[10px]">O.P.S. RESPONSE</span>
          </div>
          <div className="flex-1 overflow-y-auto pr-1 text-xs text-zinc-100 bg-zinc-900/50 rounded p-3 font-sans leading-relaxed border border-zinc-800">
            {isLoading && !agentOutput ? (
              <div className="flex items-center gap-2 text-zinc-400 py-10 justify-center">
                <Loader2 className="w-4 h-4 animate-spin text-red-500" />
                <span>Synthesizing autonomous multi-agent solution...</span>
              </div>
            ) : agentOutput ? (
              <div className="whitespace-pre-wrap">{agentOutput}</div>
            ) : (
              <div className="text-zinc-600 italic text-center py-10">Awaiting user command dispatch...</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
