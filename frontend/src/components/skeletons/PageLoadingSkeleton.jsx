import React from 'react';
import SkeletonBase from './SkeletonBase';
import { Loader2 } from 'lucide-react';

/**
 * PageLoadingSkeleton
 * Section 6: Universal loading skeletons for dashboard content,
 * conversation history loading, memories, or settings panels.
 */
export default function PageLoadingSkeleton({
  title = 'Loading data...',
  rows = 4,
  variant = 'card' // 'card' | 'table' | 'history'
}) {
  if (variant === 'history') {
    return (
      <div className="space-y-3 p-3 bg-zinc-950/60 rounded-lg border border-zinc-900 animate-pulse">
        <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
          <SkeletonBase height="14px" width="120px" variant="red" />
          <SkeletonBase height="12px" width="60px" />
        </div>
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="p-2.5 bg-black/60 border border-zinc-900 rounded space-y-1.5">
            <div className="flex justify-between items-center">
              <SkeletonBase height="12px" width="40%" />
              <SkeletonBase height="10px" width="50px" />
            </div>
            <SkeletonBase height="10px" width="85%" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3 p-4 bg-zinc-950 border border-zinc-800 rounded-xl font-mono">
      {/* Title & Spinner */}
      <div className="flex items-center justify-between border-b border-zinc-800/80 pb-2.5">
        <div className="flex items-center gap-2">
          <Loader2 className="w-3.5 h-3.5 text-red-500 animate-spin" />
          <span className="text-xs font-bold uppercase tracking-wider text-zinc-300">
            {title}
          </span>
        </div>
        <SkeletonBase height="12px" width="70px" />
      </div>

      {/* Rows */}
      <div className="space-y-2.5 pt-1">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="space-y-1">
            <SkeletonBase height="12px" width={`${90 - (i % 3) * 15}%`} />
          </div>
        ))}
      </div>
    </div>
  );
}
