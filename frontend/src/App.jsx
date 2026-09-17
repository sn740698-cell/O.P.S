import React, { useState, useEffect } from 'react';
import ModelStatusCard from './components/ModelStatusCard';
import AutomationTerminal from './components/AutomationTerminal';
import FloatingAvatar from './components/FloatingAvatar';
import { Cpu, Globe, Terminal, Shield, Layers, Activity } from 'lucide-react';

export default function App() {
  const [logs, setLogs] = useState([]);
  const [systemInfo, setSystemInfo] = useState({
    status: 'connecting',
    version: '0.1.0',
    tri_models: {
      router: 'qwen2.5:0.5b',
      reasoning: 'llama3.2:1b',
      coding: 'qwen2.5-coder:1.5b'
    }
  });

  useEffect(() => {
    fetch('/api/v1/health/')
      .then((res) => res.json())
      .then((data) => {
        setSystemInfo(data);
        addLog('System connected to Django backend & Ollama tri-model provider.', 'info');
      })
      .catch((err) => {
        setSystemInfo((prev) => ({ ...prev, status: 'offline' }));
        addLog('Backend offline. Make sure Django server is running on port 8000.', 'error');
      });
  }, []);

  const addLog = (message, type = 'info') => {
    setLogs((prev) => [...prev, { message, type }]);
  };

  const handlePromptSubmit = async (promptText) => {
    addLog(`User Request: "${promptText}"`, 'info');
    try {
      const res = await fetch('/api/v1/orchestrate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: promptText })
      });
      const data = await res.json();
      
      addLog(`Router Model classified: [${data.router?.category}] (Confidence: ${data.router?.confidence})`, 'route');
      addLog(`Reasoning Engine Plan (${data.reasoning?.model}): ${data.reasoning?.plan?.join(' -> ')}`, 'info');
      
      if (data.coding?.parameters) {
        addLog(`Coding Synthesizer parameters: ${JSON.stringify(data.coding?.parameters)}`, 'info');
      }
    } catch (e) {
      addLog(`Failed to dispatch prompt: ${e.message}`, 'error');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 font-sans">
      {/* Top Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between pb-6 mb-8 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 via-purple-300 to-emerald-400 bg-clip-text text-transparent">
              O.P.S. (Over-Engineered Programmed System)
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
              v{systemInfo.version} SKELETON
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Local-First Developer AI Environment • Persistent Overlay • Multi-Agent Automation
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs font-mono bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
            <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
            <span className="text-slate-400">Backend:</span>
            <span className={systemInfo.status === 'online' ? 'text-emerald-400' : 'text-amber-400'}>
              {systemInfo.status.toUpperCase()}
            </span>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="space-y-8 max-w-7xl mx-auto">
        {/* Model Serving Dashboard */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Cpu className="w-5 h-5 text-indigo-400" />
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
              Ollama Tri-Model Architecture Status
            </h2>
          </div>
          <ModelStatusCard models={systemInfo.tri_models} />
        </section>

        {/* System Capabilities Grid */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="rounded-xl bg-slate-900/40 border border-slate-800/80 p-5">
            <div className="flex items-center gap-2 text-indigo-400 mb-2">
              <Globe className="w-5 h-5" />
              <h3 className="font-semibold text-sm text-slate-200">Web Automation & Crawling</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Crawl4AI, ScrapeGraphAI & Playwright for headless browser DOM control, markdown extraction, and web interaction.
            </p>
          </div>

          <div className="rounded-xl bg-slate-900/40 border border-slate-800/80 p-5">
            <div className="flex items-center gap-2 text-purple-400 mb-2">
              <Layers className="w-5 h-5" />
              <h3 className="font-semibold text-sm text-slate-200">OS & GUI Control</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              PyAutoGUI & native desktop automation gatekept strictly by Django validation to prevent unauthorized actions.
            </p>
          </div>

          <div className="rounded-xl bg-slate-900/40 border border-slate-800/80 p-5">
            <div className="flex items-center gap-2 text-emerald-400 mb-2">
              <Shield className="w-5 h-5" />
              <h3 className="font-semibold text-sm text-slate-200">Safety Gatekeeper</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Ollama models output JSON proposals; Django backend validates schema and security before executing system calls.
            </p>
          </div>
        </section>

        {/* Live Execution Console */}
        <section>
          <AutomationTerminal logs={logs} />
        </section>
      </main>

      {/* Floating Avatar Widget */}
      <FloatingAvatar
        activeCategory={systemInfo.status === 'online' ? 'READY' : 'OFFLINE'}
        onPromptSubmit={handlePromptSubmit}
      />
    </div>
  );
}
