import React, { useState, useEffect } from 'react';
import { Activity, Shield, Terminal, Smartphone, Server } from 'lucide-react';

export default function LiveConnectionStatus({ wsStatuses, backendHealth }) {
  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-3 flex flex-wrap items-center justify-between gap-3 text-xs">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-red-600 animate-ping"></div>
        <span className="font-bold tracking-wider text-zinc-100 uppercase">System Status:</span>
        <span className={`px-2 py-0.5 rounded font-mono font-medium ${backendHealth === 'online' ? 'bg-zinc-800 text-zinc-100 border border-zinc-700' : 'bg-red-950 text-red-400 border border-red-800'}`}>
          BACKEND {backendHealth ? backendHealth.toUpperCase() : 'CHECKING...'}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {/* Agent WS */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800">
          <Activity className="w-3.5 h-3.5 text-zinc-400" />
          <span className="text-zinc-400">Agent WS:</span>
          <span className={`font-mono font-semibold ${wsStatuses.agent ? 'text-red-400' : 'text-zinc-500'}`}>
            {wsStatuses.agent ? 'CONNECTED' : 'DISCONNECTED'}
          </span>
        </div>

        {/* Permission WS */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800">
          <Shield className="w-3.5 h-3.5 text-zinc-400" />
          <span className="text-zinc-400">Gatekeeper WS:</span>
          <span className={`font-mono font-semibold ${wsStatuses.permissions ? 'text-red-400' : 'text-zinc-500'}`}>
            {wsStatuses.permissions ? 'ACTIVE' : 'OFFLINE'}
          </span>
        </div>

        {/* Terminal WS */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800">
          <Terminal className="w-3.5 h-3.5 text-zinc-400" />
          <span className="text-zinc-400">Terminal WS:</span>
          <span className={`font-mono font-semibold ${wsStatuses.terminal ? 'text-red-400' : 'text-zinc-500'}`}>
            {wsStatuses.terminal ? 'STREAMING' : 'OFFLINE'}
          </span>
        </div>

        {/* Mobile WS */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800">
          <Smartphone className="w-3.5 h-3.5 text-zinc-400" />
          <span className="text-zinc-400">Mobile WS:</span>
          <span className={`font-mono font-semibold ${wsStatuses.mobile ? 'text-red-400' : 'text-zinc-500'}`}>
            {wsStatuses.mobile ? 'SYNCED' : 'STANDBY'}
          </span>
        </div>
      </div>
    </div>
  );
}
