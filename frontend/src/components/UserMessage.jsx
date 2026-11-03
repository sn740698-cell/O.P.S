import React from 'react';
import { User, CornerDownRight } from 'lucide-react';

export default function UserMessage({ turn }) {
  return (
    <div className="space-y-1 pb-2.5 font-mono">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 bg-red-600"></div>
        <span className="font-bold text-[11px] uppercase tracking-wider text-red-400 flex items-center gap-1.5">
          <User className="w-3.5 h-3.5 text-red-500" />
          <span>USER // DIRECTIVE</span>
        </span>
      </div>

      <div className="pl-3.5 border-l border-red-950/80">
        <div className="text-xs text-white font-medium whitespace-pre-wrap leading-relaxed bg-zinc-950/60 p-2.5 border border-zinc-800/80 shadow-sm">
          {turn.text}
        </div>
      </div>
    </div>
  );
}
