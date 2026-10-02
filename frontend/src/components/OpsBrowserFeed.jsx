import React from 'react';
import { Globe, ExternalLink, Search, FileText } from 'lucide-react';

export default function OpsBrowserFeed({ searchResults = [], visitedUrls = [], lastScrape = null }) {
  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-4 flex flex-col h-full space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-2.5">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-red-500" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-200">
            Live Web & Search Intelligence
          </h3>
        </div>
        <span className="text-[10px] font-mono text-zinc-500">BROWSER AGENT HUD</span>
      </div>

      {/* Main Results / Crawl Feed */}
      <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 max-h-96">
        {searchResults.length > 0 ? (
          <div className="space-y-2">
            <div className="text-[11px] font-mono text-zinc-400 font-semibold flex items-center gap-1.5">
              <Search className="w-3 h-3 text-red-400" />
              <span>Parsed Search Intelligence ({searchResults.length} items):</span>
            </div>
            {searchResults.map((res, idx) => (
              <div key={idx} className="p-3 bg-zinc-900/90 border border-zinc-800 hover:border-zinc-700 rounded-lg space-y-1 transition">
                <a
                  href={res.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-bold text-red-400 hover:text-red-300 flex items-center gap-1.5 line-clamp-1"
                >
                  <span>{res.title || res.url}</span>
                  <ExternalLink className="w-3 h-3 flex-shrink-0" />
                </a>
                <p className="text-xs text-zinc-300 leading-relaxed line-clamp-3">
                  {res.snippet || res.text}
                </p>
                <div className="text-[10px] font-mono text-zinc-500 truncate pt-0.5">
                  {res.url}
                </div>
              </div>
            ))}
          </div>
        ) : lastScrape ? (
          <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg space-y-1.5">
            <div className="text-xs font-bold text-red-400 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5" />
              <span>{lastScrape.title || 'Scraped Document'}</span>
            </div>
            <p className="text-xs text-zinc-300 leading-relaxed line-clamp-6 font-mono">
              {lastScrape.text || lastScrape.content}
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-48 text-center text-zinc-600 space-y-2">
            <Globe className="w-8 h-8 text-zinc-700 stroke-1" />
            <div className="text-xs font-medium">Browser Agent Standby</div>
            <div className="text-[11px] text-zinc-500 max-w-xs">
              Direct O.P.S. to "Search for..." or "Scrape URL" to view real-time DOM intelligence.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
