import React from 'react';
import { Terminal as TerminalIcon, ShieldCheck, Play } from 'lucide-react';

export default function AutomationTerminal({ logs }) {
  return (
    <div className="rounded-xl bg-slate-950 border border-slate-800 p-4 font-mono text-xs shadow-inner">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-900">
        <div className="flex items-center gap-2 text-slate-400">
          <TerminalIcon className="w-4 h-4 text-indigo-400" />
          <span className="font-semibold text-slate-300">O.P.S. Gatekept Execution Terminal</span>
        </div>
        <div className="flex items-center gap-1.5 text-emerald-400 text-[11px]">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Django Safety Active</span>
        </div>
      </div>

      <div className="h-48 overflow-y-auto space-y-1.5 pr-2">
        {(!logs || logs.length === 0) ? (
          <div className="text-slate-600 italic">No execution logs yet. Dispatch a task from the overlay...</div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="flex items-start gap-2">
              <span className="text-slate-600">[{new Date().toLocaleTimeString()}]</span>
              <span className={log.type === 'error' ? 'text-rose-400' : log.type === 'route' ? 'text-amber-300' : 'text-slate-300'}>
                {log.message}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
