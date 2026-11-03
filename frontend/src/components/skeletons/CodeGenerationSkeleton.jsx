import React from 'react';
import SkeletonBase from './SkeletonBase';
import { Terminal } from 'lucide-react';

/**
 * CodeGenerationSkeleton
 * Section 3.C: Code generation skeleton
 * - Pre-code introductory line
 * - Code-block container placeholder with header badge and dark retro terminal border
 * - Multiple horizontal indented lines simulating realistic code syntax
 */
export default function CodeGenerationSkeleton({ compact = false }) {
  return (
    <div className="space-y-2.5 w-full pl-3.5 border-l-2 border-red-900/40 py-1" aria-label="Loading code response">
      {/* Short intro line */}
      <SkeletonBase height="12px" width="60%" rounded="rounded-sm" />

      {/* Code Block Container Placeholder */}
      <div className="bg-[#09090b] border border-zinc-800 rounded-md p-3 space-y-2 font-mono shadow-inner">
        {/* Code Header Bar Placeholder */}
        <div className="flex items-center justify-between border-b border-zinc-800/80 pb-2">
          <div className="flex items-center gap-1.5">
            <Terminal className="w-3 h-3 text-red-500" />
            <SkeletonBase height="10px" width="55px" rounded="rounded-sm" />
          </div>
          <SkeletonBase height="14px" width="40px" rounded="rounded-sm" />
        </div>

        {/* Code Lines with Indentation */}
        <div className="space-y-1.5 pt-1">
          {/* import statement */}
          <SkeletonBase height="11px" width="38%" rounded="rounded-sm" />
          {/* function definition */}
          <SkeletonBase height="11px" width="52%" rounded="rounded-sm" />
          {/* indent 1 */}
          <div className="pl-4">
            <SkeletonBase height="11px" width="75%" rounded="rounded-sm" />
          </div>
          {/* indent 2 */}
          <div className="pl-4">
            <SkeletonBase height="11px" width="60%" rounded="rounded-sm" />
          </div>
          {/* indent 3 return */}
          <div className="pl-4">
            <SkeletonBase height="11px" width="42%" rounded="rounded-sm" />
          </div>
          {/* call */}
          <SkeletonBase height="11px" width="30%" rounded="rounded-sm" />
        </div>
      </div>
    </div>
  );
}
