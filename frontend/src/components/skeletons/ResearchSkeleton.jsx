import React from 'react';
import SkeletonBase from './SkeletonBase';
import { Globe, BookOpen } from 'lucide-react';

/**
 * ResearchSkeleton
 * Section 3.D: Research response skeleton
 * - Executive heading placeholder
 * - Source/Citation pills placeholders (simulating verified Web Research citations)
 * - Synthesized analysis paragraph placeholders
 * - Key findings list placeholders
 */
export default function ResearchSkeleton({ compact = false }) {
  return (
    <div className="space-y-3 w-full pl-3.5 border-l-2 border-red-900/40 py-1" aria-label="Loading research response">
      {/* Executive Heading */}
      <SkeletonBase height={compact ? "14px" : "16px"} width="50%" variant="red" rounded="rounded-sm" />

      {/* Verified Source Citations Badges */}
      <div className="flex items-center gap-2 flex-wrap pt-0.5">
        <div className="flex items-center gap-1.5 px-2 py-0.5 bg-zinc-950 border border-zinc-800 rounded">
          <Globe className="w-2.5 h-2.5 text-zinc-500" />
          <SkeletonBase height="9px" width="70px" rounded="rounded-sm" />
        </div>
        <div className="flex items-center gap-1.5 px-2 py-0.5 bg-zinc-950 border border-zinc-800 rounded">
          <BookOpen className="w-2.5 h-2.5 text-zinc-500" />
          <SkeletonBase height="9px" width="60px" rounded="rounded-sm" />
        </div>
        {!compact && (
          <div className="flex items-center gap-1.5 px-2 py-0.5 bg-zinc-950 border border-zinc-800 rounded">
            <Globe className="w-2.5 h-2.5 text-zinc-500" />
            <SkeletonBase height="9px" width="85px" rounded="rounded-sm" />
          </div>
        )}
      </div>

      {/* Synthesized Research Findings Paragraph */}
      <div className="space-y-1.5">
        <SkeletonBase height="12px" width="95%" rounded="rounded-sm" />
        <SkeletonBase height="12px" width="86%" rounded="rounded-sm" />
        <SkeletonBase height="12px" width="72%" rounded="rounded-sm" />
      </div>

      {/* Key Findings List Placeholders */}
      <div className="space-y-1.5 pt-1 pl-1">
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-red-500 font-bold">1.</span>
          <SkeletonBase height="11px" width="80%" rounded="rounded-sm" />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-red-500 font-bold">2.</span>
          <SkeletonBase height="11px" width="68%" rounded="rounded-sm" />
        </div>
      </div>
    </div>
  );
}
