import React from 'react';

/**
 * SkeletonBase
 * Base futuristic shimmer placeholder component for O.P.S. 2.0.
 * Respects cyber dark palette, smooth CSS gradient shimmer, and reduced-motion.
 */
export default function SkeletonBase({
  className = '',
  variant = 'default', // 'default' | 'red'
  width,
  height,
  rounded = 'rounded',
  style = {}
}) {
  const shimmerClass = variant === 'red' ? 'ops-skeleton-shimmer-red' : 'ops-skeleton-shimmer';
  
  const inlineStyles = {
    ...(width ? { width } : {}),
    ...(height ? { height } : {}),
    ...style
  };

  return (
    <div
      className={`relative overflow-hidden border border-zinc-800/60 ${shimmerClass} ${rounded} ${className}`}
      style={inlineStyles}
      aria-hidden="true"
    />
  );
}
