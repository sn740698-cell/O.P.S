import React from 'react';
import SkeletonBase from './SkeletonBase';

/**
 * TextGenerationSkeleton
 * Section 3.A: Text response skeleton
 * - 3 to 5 animated placeholder lines
 * - Natural variable line widths to simulate a realistic assistant reply
 * - Subtle shimmer effect
 */
export default function TextGenerationSkeleton({ compact = false }) {
  return (
    <div className="space-y-2.5 w-full pl-3.5 border-l-2 border-red-900/40 py-1" aria-label="Loading text response">
      {/* Line 1: Main statement */}
      <SkeletonBase height={compact ? "11px" : "13px"} width="94%" rounded="rounded-sm" />

      {/* Line 2: Follow-up sentence */}
      <SkeletonBase height={compact ? "11px" : "13px"} width="82%" rounded="rounded-sm" />

      {/* Line 3: Elaborating thought */}
      <SkeletonBase height={compact ? "11px" : "13px"} width="88%" rounded="rounded-sm" />

      {/* Line 4: Short concluding sentence */}
      <SkeletonBase height={compact ? "11px" : "13px"} width="64%" rounded="rounded-sm" />

      {!compact && (
        <>
          {/* Paragraph break */}
          <div className="h-1.5" />
          {/* Second paragraph starter */}
          <SkeletonBase height="13px" width="76%" rounded="rounded-sm" />
          <SkeletonBase height="13px" width="48%" rounded="rounded-sm" />
        </>
      )}
    </div>
  );
}
