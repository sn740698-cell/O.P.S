import React from 'react';
import SkeletonBase from './SkeletonBase';

/**
 * StructuredResponseSkeleton
 * Section 3.B: Structured answer skeleton
 * - Heading placeholder
 * - Intro paragraph placeholder
 * - Bullet-point placeholders (tactical bullet indicator + line)
 * - Concluding note placeholder
 */
export default function StructuredResponseSkeleton({ compact = false }) {
  return (
    <div className="space-y-3 w-full pl-3.5 border-l-2 border-red-900/40 py-1" aria-label="Loading structured response">
      {/* Section Heading Placeholder */}
      <div className="flex items-center gap-2">
        <SkeletonBase height={compact ? "14px" : "16px"} width="45%" variant="red" rounded="rounded-sm" />
      </div>

      {/* Intro text */}
      <div className="space-y-1.5">
        <SkeletonBase height="12px" width="92%" rounded="rounded-sm" />
        <SkeletonBase height="12px" width="78%" rounded="rounded-sm" />
      </div>

      {/* Bullet-Point Placeholders */}
      <div className="space-y-2 pt-1 pl-1">
        {/* Bullet 1 */}
        <div className="flex items-center gap-2">
          <SkeletonBase height="6px" width="6px" variant="red" rounded="rounded-full" />
          <SkeletonBase height="11px" width="85%" rounded="rounded-sm" />
        </div>

        {/* Bullet 2 */}
        <div className="flex items-center gap-2">
          <SkeletonBase height="6px" width="6px" variant="red" rounded="rounded-full" />
          <SkeletonBase height="11px" width="70%" rounded="rounded-sm" />
        </div>

        {/* Bullet 3 */}
        <div className="flex items-center gap-2">
          <SkeletonBase height="6px" width="6px" variant="red" rounded="rounded-full" />
          <SkeletonBase height="11px" width="80%" rounded="rounded-sm" />
        </div>
      </div>

      {/* Summary conclusion placeholder */}
      {!compact && (
        <div className="pt-1.5">
          <SkeletonBase height="12px" width="55%" rounded="rounded-sm" />
        </div>
      )}
    </div>
  );
}
