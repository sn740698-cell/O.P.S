import React, { useState } from 'react';
import { Copy, Check, Terminal } from 'lucide-react';

export default function CodeBlock({ language = '', value = '' }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!value) return;
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const cleanLang = (language || 'code').toUpperCase();

  return (
    <div className="my-3 rounded-none border border-zinc-800 bg-black/90 font-mono text-xs overflow-hidden shadow-lg">
      {/* Code Block Header */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-zinc-950 border-b border-zinc-800 text-[10px] text-zinc-400 select-none">
        <div className="flex items-center gap-1.5 font-bold tracking-wider text-red-400">
          <Terminal className="w-3.5 h-3.5 text-red-500" />
          <span>{cleanLang}</span>
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1 px-2 py-0.5 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white border border-zinc-700 transition"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-[9px] text-emerald-400 font-bold uppercase tracking-wider">COPIED</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3 text-zinc-400" />
              <span className="text-[9px] uppercase tracking-wider">COPY</span>
            </>
          )}
        </button>
      </div>

      {/* Code Content */}
      <div className="p-3 overflow-x-auto text-zinc-100 leading-relaxed font-mono selection:bg-red-900 selection:text-white">
        <pre className="m-0 whitespace-pre">
          <code>{value}</code>
        </pre>
      </div>
    </div>
  );
}
