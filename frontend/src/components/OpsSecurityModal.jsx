import React from 'react';
import { ShieldAlert, Check, X, ShieldCheck, Terminal } from 'lucide-react';

export default function OpsSecurityModal({ activeRequest, onResolvePermission, auditLogs = [] }) {
  if (!activeRequest) return null;

  return (
    <div className="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center p-4 font-mono">
      <div className="retro-box-red max-w-lg w-full p-4 shadow-2xl space-y-3.5 glow-red">
        {/* Retro Header */}
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2.5">
          <div className="flex items-center gap-2">
            <div className="px-1.5 py-0.5 bg-red-600 text-white font-black text-xs border border-red-500">
              ALERT
            </div>
            <div>
              <h3 className="text-xs font-bold text-white tracking-wider uppercase">
                === SECURITY AUTHORIZATION REQUIRED ===
              </h3>
              <p className="text-[10px] text-red-400">
                ORIGINATING_AGENT: [{activeRequest.agent || activeRequest.agent_name || 'Autonomous Agent'}]
              </p>
            </div>
          </div>
          <span className="px-2 py-0.5 text-[10px] font-bold uppercase bg-red-950 text-red-200 border border-red-700">
            [{activeRequest.risk_level || 'HIGH'}_RISK]
          </span>
        </div>

        {/* Action Details */}
        <div className="space-y-2 text-xs">
          <div className="text-zinc-400">
            ACTION_TYPE: <span className="text-white font-bold">[{activeRequest.action || activeRequest.action_type}]</span>
          </div>
          {activeRequest.reason && (
            <div className="text-zinc-400">
              SECURITY_REASON: <span className="text-zinc-200">{activeRequest.reason}</span>
            </div>
          )}

          <div className="mt-2 p-2.5 bg-black border border-red-900/80 text-xs text-red-300 break-all leading-relaxed">
            <div className="text-[10px] text-zinc-500 uppercase mb-1">&gt; TARGET COMMAND:</div>
            {activeRequest.command || activeRequest.command_text || 'No command text'}
          </div>
        </div>

        {/* 90s Retro Tactile Decision Buttons (Deny / Accept) */}
        <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-zinc-900">
          <button
            onClick={() => onResolvePermission(activeRequest.request_id, 'DENY')}
            className="retro-btn-red px-3.5 py-1.5 text-xs font-bold flex items-center gap-1.5"
          >
            <X className="w-3.5 h-3.5 text-white" />
            <span>[ ❌ DENY ACTION ]</span>
          </button>
          <button
            onClick={() => onResolvePermission(activeRequest.request_id, 'ALLOW')}
            className="retro-btn px-3.5 py-1.5 text-xs font-bold text-white border-red-600 bg-red-950/60 hover:bg-red-900/80 flex items-center gap-1.5"
          >
            <Check className="w-3.5 h-3.5 text-emerald-400" />
            <span>[ ✅ ACCEPT ACTION ]</span>
          </button>
        </div>
      </div>
    </div>
  );
}
