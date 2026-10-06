import React, { useRef, useEffect } from 'react';
import { Terminal, Loader2, Trash2, Activity, CheckCircle2, ArrowRight } from 'lucide-react';

export default function OpsTerminalConsole({
  terminalLogs = [],
  onClearLogs,
  activeTaskPrompt = '',
  activeAgent = '',
  currentThought = '',
  isLoading = false,
  planSteps = [],
  sessionId = ''
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalLogs, currentThought]);

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-4 flex flex-col h-full space-y-3 font-mono">
      {/* Terminal Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-2.5">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-red-500" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-200">
            Workstation Sandbox Terminal
          </h3>
        </div>
        <div className="flex items-center gap-2.5">
          {isLoading && (
            <span className="flex items-center gap-1 text-[10px] text-red-400 font-bold animate-pulse">
              <span className="w-2 h-2 rounded-full bg-red-500"></span>
              EXECUTING
            </span>
          )}
          <span className="text-[10px] text-zinc-500">BASH / POWERSHELL</span>
          {onClearLogs && terminalLogs.length > 0 && (
            <button
              type="button"
              onClick={onClearLogs}
              className="text-zinc-500 hover:text-zinc-300 transition p-0.5"
              title="Clear terminal log"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Real-time Task Status Banner */}
      <div className={`p-2.5 rounded-lg border text-xs transition-all ${
        isLoading
          ? 'bg-red-950/40 border-red-800/80 text-zinc-100 shadow-[0_0_15px_rgba(220,38,38,0.15)]'
          : activeTaskPrompt
          ? 'bg-zinc-900/60 border-zinc-800 text-zinc-300'
          : 'bg-black/60 border-zinc-900 text-zinc-500'
      }`}>
        <div className="flex items-center justify-between gap-2 mb-1">
          <div className="flex items-center gap-1.5 font-bold">
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 text-red-400 animate-spin" />
                <span className="text-red-400 tracking-wider uppercase text-[11px]">
                  [ CURRENT TASK PERFORMING ]
                </span>
              </>
            ) : activeTaskPrompt ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400 tracking-wider uppercase text-[11px]">
                  [ LAST PERFORMED TASK ]
                </span>
              </>
            ) : (
              <>
                <Activity className="w-3.5 h-3.5 text-zinc-500" />
                <span className="text-zinc-500 tracking-wider uppercase text-[11px]">
                  [ SYSTEM STATUS: STANDBY ]
                </span>
              </>
            )}
          </div>
          {activeAgent && (
            <span className="px-1.5 py-0.5 bg-zinc-900 text-red-300 border border-zinc-700 text-[10px] font-bold rounded">
              {activeAgent}
            </span>
          )}
        </div>

        {/* Task Objective Description */}
        <div className="font-semibold text-white break-words mt-0.5">
          {activeTaskPrompt ? (
            <span className="text-zinc-100">
              &gt; {activeTaskPrompt}
            </span>
          ) : (
            <span className="text-zinc-500 italic">
              No active task running. Dispatch a directive from the Cockpit.
            </span>
          )}
        </div>

        {/* Real-time Sub-Action / Thought */}
        {isLoading && currentThought && (
          <div className="mt-1.5 pt-1.5 border-t border-red-900/50 flex items-start gap-1.5 text-[11px] text-red-200">
            <ArrowRight className="w-3 h-3 text-red-400 mt-0.5 shrink-0" />
            <span className="leading-snug">{currentThought}</span>
          </div>
        )}
      </div>

      {/* Output Console Screen */}
      <div className="flex-1 min-h-72 overflow-y-auto bg-black p-3.5 rounded-lg border border-zinc-900 text-xs leading-relaxed space-y-1">
        {terminalLogs.length === 0 ? (
          <div className="text-zinc-600 italic py-12 text-center space-y-1 font-mono">
            <div className="text-zinc-500 font-bold">O.P.S. Real-Time Workstation Sandbox Ready</div>
            <div className="text-[11px]">All agent directives, shell executions & subprocess logs stream here live.</div>
          </div>
        ) : (
          terminalLogs.map((log, idx) => {
            const isErr = log.stream === 'stderr' || log.data?.startsWith('[ERROR]');
            const isThought = log.stream === 'ops_thought' || log.data?.startsWith('[AGENT');
            const isSuccess = log.stream === 'ops_success' || log.data?.startsWith('[TASK COMPLETED') || log.data?.startsWith('[PASS');
            const isDirective = log.stream === 'ops_event' || log.data?.startsWith('>>') || log.data?.startsWith('[TASK INITIATED');
            const isCmd = log.data?.startsWith('$');

            return (
              <div
                key={idx}
                className={`break-all font-mono ${
                  isErr
                    ? 'text-red-400 font-medium'
                    : isSuccess
                    ? 'text-emerald-400 font-medium'
                    : isDirective
                    ? 'text-cyan-300 font-semibold'
                    : isThought
                    ? 'text-amber-300'
                    : isCmd
                    ? 'text-red-500 font-bold'
                    : 'text-zinc-300'
                }`}
              >
                {log.timestamp && (
                  <span className="text-zinc-600 text-[10px] mr-2">[{log.timestamp}]</span>
                )}
                {log.data || log.message}
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
