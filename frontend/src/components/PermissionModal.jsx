import React from 'react';
import { ShieldAlert, Check, X, ShieldCheck, AlertTriangle, Clock } from 'lucide-react';

export default function PermissionModal({ activeRequest, onResolvePermission, auditLogs = [] }) {
  return (
    <div className="space-y-4">
      {/* Live Interactive Security Prompt Alert */}
      {activeRequest && (
        <div className="bg-red-950/40 border-2 border-red-600 rounded-lg p-4 shadow-lg animate-pulse">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-red-500 flex-shrink-0" />
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  SECURITY AUTHORIZATION REQUIRED
                </h3>
                <p className="text-xs text-red-300 font-mono">
                  Agent: <span className="text-white font-bold">{activeRequest.agent || activeRequest.agent_name || 'Agent'}</span> | Action: <span className="text-white">{activeRequest.action || activeRequest.action_type}</span>
                </p>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-red-600 text-white">
              {activeRequest.risk_level || 'HIGH'} RISK
            </span>
          </div>

          <div className="my-3 p-2.5 bg-black/80 rounded border border-red-800/80 font-mono text-xs text-zinc-100 break-all">
            {activeRequest.command || activeRequest.command_text || 'No command text provided'}
          </div>

          <div className="flex flex-wrap items-center justify-end gap-2 pt-1">
            <button
              onClick={() => onResolvePermission(activeRequest.request_id, 'DENY')}
              className="px-3 py-1.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-300 hover:text-white text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <X className="w-3.5 h-3.5 text-red-500" />
              DENY
            </button>
            <button
              onClick={() => onResolvePermission(activeRequest.request_id, 'ALLOW_ONCE')}
              className="px-3 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 border border-zinc-600 text-white text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <Check className="w-3.5 h-3.5 text-zinc-200" />
              ALLOW ONCE
            </button>
            <button
              onClick={() => onResolvePermission(activeRequest.request_id, 'ALLOW_TASK')}
              className="px-4 py-1.5 rounded bg-red-600 hover:bg-red-700 text-white text-xs font-bold flex items-center gap-1.5 transition shadow"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              ALLOW FOR ENTIRE TASK
            </button>
          </div>
        </div>
      )}

      {/* Execution Audit Log Table */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
          <div className="text-xs font-bold uppercase tracking-wider text-zinc-200 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-red-500" />
            Execution Audit Logs & Security History
          </div>
          <span className="text-zinc-500 font-mono text-xs">{auditLogs.length} logged actions</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-400">
                <th className="py-2 px-2">Time</th>
                <th className="py-2 px-2">Agent</th>
                <th className="py-2 px-2">Action</th>
                <th className="py-2 px-2">Target / Command</th>
                <th className="py-2 px-2">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-900">
              {auditLogs.length === 0 ? (
                <tr>
                  <td colSpan="5" className="py-6 text-center text-zinc-600 italic">
                    No execution audit records found.
                  </td>
                </tr>
              ) : (
                auditLogs.map((log, idx) => (
                  <tr key={idx} className="hover:bg-zinc-900/50 transition">
                    <td className="py-2 px-2 text-zinc-500 text-[11px]">
                      {log.executed_at ? new Date(log.executed_at).toLocaleTimeString() : 'Just now'}
                    </td>
                    <td className="py-2 px-2 text-zinc-300 font-semibold">{log.agent_name}</td>
                    <td className="py-2 px-2 text-red-400">{log.action_type}</td>
                    <td className="py-2 px-2 text-zinc-300 max-w-xs truncate">{log.target || JSON.stringify(log.parameters)}</td>
                    <td className="py-2 px-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        log.status === 'SUCCESS' ? 'bg-zinc-800 text-zinc-200' : 'bg-red-950 text-red-400 border border-red-800'
                      }`}>
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
