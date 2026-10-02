import React, { useState, useRef, useEffect } from 'react';
import { Terminal, Play, Loader2, Trash2 } from 'lucide-react';

export default function OpsTerminalConsole({ terminalLogs = [], onExecuteCommand }) {
  const [cmdInput, setCmdInput] = useState('');
  const [executing, setExecuting] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalLogs]);

  const handleRun = async (e) => {
    e.preventDefault();
    if (!cmdInput.trim() || executing) return;
    setExecuting(true);
    if (onExecuteCommand) {
      await onExecuteCommand(cmdInput);
    }
    setCmdInput('');
    setExecuting(false);
  };

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-4 flex flex-col h-full space-y-3 font-mono">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-2.5">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-red-500" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-200">
            Workstation Sandbox Terminal
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-zinc-500">BASH / POWERSHELL</span>
        </div>
      </div>

      {/* Output Console Screen */}
      <div className="flex-1 min-h-64 max-h-96 overflow-y-auto bg-black p-3.5 rounded-lg border border-zinc-900 text-xs leading-relaxed space-y-1">
        {terminalLogs.length === 0 ? (
          <div className="text-zinc-600 italic py-12 text-center">
            Terminal stdout/stderr streaming channel ready.
          </div>
        ) : (
          terminalLogs.map((log, idx) => (
            <div
              key={idx}
              className={`break-all ${
                log.stream === 'stderr' || log.data?.startsWith('[ERROR]')
                  ? 'text-red-400'
                  : log.data?.startsWith('$')
                  ? 'text-red-500 font-bold'
                  : log.data?.startsWith('[OPS')
                  ? 'text-white font-semibold'
                  : 'text-zinc-300'
              }`}
            >
              {log.data}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Interactive Command Prompt Line */}
      <form onSubmit={handleRun} className="flex gap-2">
        <div className="relative flex-1">
          <span className="absolute left-3 top-2.5 text-red-500 font-bold text-xs">$</span>
          <input
            type="text"
            value={cmdInput}
            onChange={(e) => setCmdInput(e.target.value)}
            placeholder="Execute system command directly..."
            disabled={executing}
            className="w-full bg-black border border-zinc-800 focus:border-red-500 rounded-lg pl-7 pr-3 py-2 text-xs text-white placeholder-zinc-600 outline-none transition"
          />
        </div>
        <button
          type="submit"
          disabled={executing || !cmdInput.trim()}
          className="px-3.5 py-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 hover:border-zinc-600 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 transition"
        >
          {executing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 text-red-400" />}
          <span>EXEC</span>
        </button>
      </form>
    </div>
  );
}
