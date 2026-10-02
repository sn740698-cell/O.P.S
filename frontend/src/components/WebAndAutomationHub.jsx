import React, { useState } from 'react';
import { Globe, Terminal, Play, Loader2, MousePointer, Keyboard, Monitor } from 'lucide-react';

export default function WebAndAutomationHub({ terminalLogs = [] }) {
  const [scrapeUrl, setScrapeUrl] = useState('https://python.org');
  const [scrapeResult, setScrapeResult] = useState(null);
  const [scraping, setScraping] = useState(false);

  const [termCmd, setTermCmd] = useState('dir');
  const [termRunning, setTermRunning] = useState(false);
  const [termResult, setTermResult] = useState(null);

  const [autoStatus, setAutoStatus] = useState('');

  const handleScrape = async (e) => {
    e.preventDefault();
    if (!scrapeUrl.trim() || scraping) return;
    setScraping(true);
    setScrapeResult(null);

    try {
      const resp = await fetch('/api/v1/scrape/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: scrapeUrl })
      });
      const data = await resp.json();
      setScrapeResult(data);
    } catch (err) {
      setScrapeResult({ error: err.message });
    } finally {
      setScraping(false);
    }
  };

  const handleRunTerminal = async (e) => {
    e.preventDefault();
    if (!termCmd.trim() || termRunning) return;
    setTermRunning(true);

    try {
      const resp = await fetch('/api/v1/automation/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'terminal', command: termCmd })
      });
      const data = await resp.json();
      setTermResult(data);
    } catch (err) {
      setTermResult({ error: err.message });
    } finally {
      setTermRunning(false);
    }
  };

  const handleTriggerAutomation = async (actionType, params = {}) => {
    setAutoStatus(`Executing ${actionType}...`);
    try {
      const resp = await fetch('/api/v1/automation/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: actionType, ...params })
      });
      const data = await resp.json();
      setAutoStatus(`Success: ${data.message || 'Action executed'}`);
      setTimeout(() => setAutoStatus(''), 4000);
    } catch (err) {
      setAutoStatus(`Error: ${err.message}`);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Web Crawling / Scraper Panel */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 space-y-3 flex flex-col">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
          <div className="text-xs font-bold uppercase tracking-wider text-zinc-200 flex items-center gap-1.5">
            <Globe className="w-4 h-4 text-red-500" />
            Live Web Scraper & Crawler
          </div>
          <span className="text-zinc-500 font-mono text-[10px]">DOM PARSER</span>
        </div>

        <form onSubmit={handleScrape} className="flex gap-2">
          <input
            type="text"
            value={scrapeUrl}
            onChange={(e) => setScrapeUrl(e.target.value)}
            placeholder="https://example.com"
            disabled={scraping}
            className="flex-1 bg-zinc-900 border border-zinc-700 focus:border-red-500 rounded px-3 py-2 text-xs text-white placeholder-zinc-500 outline-none"
          />
          <button
            type="submit"
            disabled={scraping || !scrapeUrl.trim()}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded text-xs font-semibold flex items-center gap-1 transition"
          >
            {scraping ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            <span>SCRAPE</span>
          </button>
        </form>

        <div className="flex-1 min-h-48 max-h-64 overflow-y-auto bg-zinc-900/60 rounded p-3 text-xs font-mono text-zinc-300 border border-zinc-800">
          {scraping ? (
            <div className="flex items-center justify-center h-full gap-2 text-zinc-500 py-10">
              <Loader2 className="w-4 h-4 animate-spin text-red-500" />
              <span>Fetching and stripping DOM content...</span>
            </div>
          ) : scrapeResult ? (
            <div className="space-y-2">
              <div className="text-red-400 font-bold">{scrapeResult.title || scrapeResult.url}</div>
              <div className="text-zinc-400 whitespace-pre-wrap">{scrapeResult.text || scrapeResult.content || JSON.stringify(scrapeResult, null, 2)}</div>
            </div>
          ) : (
            <div className="text-zinc-600 italic text-center py-10">Enter URL above and click SCRAPE to test crawler.</div>
          )}
        </div>
      </div>

      {/* Terminal Sandbox & OS Automation */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 space-y-3 flex flex-col">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
          <div className="text-xs font-bold uppercase tracking-wider text-zinc-200 flex items-center gap-1.5">
            <Terminal className="w-4 h-4 text-red-500" />
            Sandbox Terminal & OS Automation
          </div>
          {autoStatus && <span className="text-red-400 text-xs font-mono">{autoStatus}</span>}
        </div>

        {/* Quick OS actions */}
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => handleTriggerAutomation('click', { x: 500, y: 500 })}
            className="px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-300 text-xs font-medium flex items-center gap-1 transition"
          >
            <MousePointer className="w-3 h-3 text-red-400" />
            Test Click
          </button>
          <button
            type="button"
            onClick={() => handleTriggerAutomation('type', { text: 'OPS' })}
            className="px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-300 text-xs font-medium flex items-center gap-1 transition"
          >
            <Keyboard className="w-3 h-3 text-red-400" />
            Test Keystroke
          </button>
        </div>

        {/* Terminal Run Form */}
        <form onSubmit={handleRunTerminal} className="flex gap-2">
          <input
            type="text"
            value={termCmd}
            onChange={(e) => setTermCmd(e.target.value)}
            placeholder="Command (e.g. dir, whoami, python --version)"
            disabled={termRunning}
            className="flex-1 bg-zinc-900 border border-zinc-700 focus:border-red-500 rounded px-3 py-2 text-xs font-mono text-white placeholder-zinc-500 outline-none"
          />
          <button
            type="submit"
            disabled={termRunning || !termCmd.trim()}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded text-xs font-semibold flex items-center gap-1 border border-zinc-600 transition"
          >
            {termRunning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 text-red-400" />}
            <span>RUN</span>
          </button>
        </form>

        {/* Live Terminal Output Window */}
        <div className="flex-1 min-h-48 max-h-64 overflow-y-auto bg-black rounded p-3 font-mono text-xs text-zinc-300 border border-zinc-800">
          {terminalLogs.length > 0 ? (
            terminalLogs.map((log, idx) => (
              <div key={idx} className={log.stream === 'stderr' ? 'text-red-400' : 'text-zinc-300'}>
                {log.data}
              </div>
            ))
          ) : termResult ? (
            <div className="whitespace-pre-wrap">{termResult.stdout || termResult.output || termResult.error || JSON.stringify(termResult, null, 2)}</div>
          ) : (
            <div className="text-zinc-600 italic text-center py-10">Terminal stream ready. Run command or listen on WebSocket.</div>
          )}
        </div>
      </div>
    </div>
  );
}
