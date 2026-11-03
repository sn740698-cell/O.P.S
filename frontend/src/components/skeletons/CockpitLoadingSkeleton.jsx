import React, { useMemo } from 'react';
import { Square, CheckCircle2, Loader2, Globe, Sparkles, Layers, Cpu } from 'lucide-react';
import LoadingStatusIndicator, { resolveLoadingStateKey } from './LoadingStatusIndicator';
import TextGenerationSkeleton from './TextGenerationSkeleton';
import StructuredResponseSkeleton from './StructuredResponseSkeleton';
import CodeGenerationSkeleton from './CodeGenerationSkeleton';
import ResearchSkeleton from './ResearchSkeleton';
import MarkdownRenderer from '../MarkdownRenderer';

/**
 * Detects the most appropriate skeleton variation from user query.
 */
export function detectSkeletonVariation(query = '') {
  if (!query || typeof query !== 'string') return 'text';
  const q = query.toLowerCase();

  // Code generation intent
  if (
    q.includes('code') ||
    q.includes('python') ||
    q.includes('script') ||
    q.includes('function') ||
    q.includes('class') ||
    q.includes('implement') ||
    q.includes('regex') ||
    q.includes('bug') ||
    q.includes('debug') ||
    q.includes('syntax') ||
    q.includes('javascript') ||
    q.includes('typescript') ||
    q.includes('rust') ||
    q.includes('sql')
  ) {
    return 'code';
  }

  // Structured answer intent
  if (
    q.includes('compare') ||
    q.includes('difference') ||
    q.includes('pros and cons') ||
    q.includes('table') ||
    q.includes('list the') ||
    q.includes('steps to') ||
    q.includes('versus') ||
    q.includes(' vs ')
  ) {
    return 'structured';
  }

  // Deep research intent
  if (
    q.includes('research') ||
    q.includes('search') ||
    q.includes('find') ||
    q.includes('breakthrough') ||
    q.includes('superconductor') ||
    q.includes('fusion') ||
    q.includes('papers') ||
    q.includes('discover') ||
    q.includes('who created') ||
    q.includes('what are') ||
    q.includes('investigate') ||
    q.includes('analyze')
  ) {
    return 'research';
  }

  return 'text';
}

/**
 * CockpitLoadingSkeleton — Master Live Mode Preview & Response Loader
 * Fully implements Part 5 of O.P.S. 2.0 Specification:
 * 1. Three Mode Preview Indicators: [ LLM ] [ WEB ] [ HYBRID ] with distinct color highlights
 * 2. Active Mode Status & Short Reason Banner
 * 3. Real Processing Stages Stepper (LLM, WEB, HYBRID real stages)
 * 4. Real Research Activity Preview (sources discovered, pages retrieved, domains, evidence status)
 * 5. Seamless live typewriter streaming transition
 */
export default function CockpitLoadingSkeleton({
  query = '',
  activeAgent = '',
  currentThought = '',
  streamingChunk = '',
  onStopExecution,
  variationOverride,
  compact = false,
  activeMode = 'LLM',
  modeReason = '',
  stages = [],
  currentStage = '',
  researchTelemetry = null
}) {
  const variation = useMemo(() => {
    return variationOverride || detectSkeletonVariation(query);
  }, [variationOverride, query]);

  const stateKey = useMemo(() => {
    return resolveLoadingStateKey(activeAgent, currentThought);
  }, [activeAgent, currentThought]);

  const normalizedMode = (activeMode || 'LLM').toUpperCase();

  return (
    <div
      className="space-y-2.5 pt-1 font-mono transition-all duration-200"
      aria-live="polite"
      aria-busy="true"
    >
      {/* =========================================================================
          PART 5.A: THREE MODE PREVIEW INDICATORS ([ LLM ] [ WEB ] [ HYBRID ])
          ========================================================================= */}
      <div className="flex items-center justify-between p-2 rounded bg-zinc-950/90 border border-zinc-800/80 font-mono text-[11px] select-none shadow-sm">
        <div className="flex items-center gap-1.5 font-bold">
          <span className="text-[10px] text-zinc-500 uppercase tracking-wider mr-0.5">MODE:</span>

          {/* 1. LLM Mode Indicator (Blue) */}
          <div
            className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-all flex items-center gap-1 ${
              normalizedMode === 'LLM'
                ? 'bg-blue-950/90 text-blue-300 border-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.35)]'
                : 'bg-zinc-900/40 text-zinc-600 border-zinc-800'
            }`}
            title="LLM Mode: Local reasoning & knowledge"
          >
            {normalizedMode === 'LLM' && <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />}
            <span>LLM</span>
          </div>

          {/* 2. WEB Mode Indicator (Green) */}
          <div
            className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-all flex items-center gap-1 ${
              normalizedMode === 'WEB'
                ? 'bg-emerald-950/90 text-emerald-300 border-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.35)]'
                : 'bg-zinc-900/40 text-zinc-600 border-zinc-800'
            }`}
            title="WEB Mode: Live search, retrieval & evidence grounding"
          >
            {normalizedMode === 'WEB' && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />}
            <span>WEB</span>
          </div>

          {/* 3. HYBRID Mode Indicator (Purple) */}
          <div
            className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-all flex items-center gap-1 ${
              normalizedMode === 'HYBRID'
                ? 'bg-purple-950/90 text-purple-300 border-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.35)]'
                : 'bg-zinc-900/40 text-zinc-600 border-zinc-800'
            }`}
            title="HYBRID Mode: Local LLM reasoning combined with live web research"
          >
            {normalizedMode === 'HYBRID' && <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />}
            <span>HYBRID</span>
          </div>

          {/* 4. DOCUMENT Mode Indicator (Amber) */}
          <div
            className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-all flex items-center gap-1 ${
              normalizedMode === 'DOCUMENT'
                ? 'bg-amber-950/90 text-amber-300 border-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.35)]'
                : 'bg-zinc-900/40 text-zinc-600 border-zinc-800'
            }`}
            title="DOCUMENT Mode: Temporary document intelligence via Pinecone"
          >
            {normalizedMode === 'DOCUMENT' && <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />}
            <span>DOCUMENT</span>
          </div>
        </div>

        {/* Emergency Stop Button */}
        {onStopExecution && (
          <button
            type="button"
            onClick={onStopExecution}
            className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-950 border border-red-700 text-red-300 hover:bg-red-900 transition flex items-center gap-1 font-mono shrink-0 shadow-sm"
            title="Halt active response generation"
          >
            <Square className="w-2.5 h-2.5 fill-current" />
            <span>STOP</span>
          </button>
        )}
      </div>

      {/* =========================================================================
          PART 5.A: ACTIVE MODE STATUS & USER-FRIENDLY REASON BANNER
          ========================================================================= */}
      <div className="flex items-center gap-2 px-2.5 py-1.5 rounded bg-zinc-950/70 border border-zinc-800/60 text-[10px] font-mono">
        <span className="font-bold shrink-0 flex items-center gap-1">
          <span className="text-zinc-400">ACTIVE:</span>
          <span
            className={
              normalizedMode === 'LLM'
                ? 'text-blue-400 font-extrabold'
                : normalizedMode === 'WEB'
                ? 'text-emerald-400 font-extrabold'
                : normalizedMode === 'HYBRID'
                ? 'text-purple-400 font-extrabold'
                : normalizedMode === 'DOCUMENT'
                ? 'text-amber-400 font-extrabold'
                : 'text-zinc-300'
            }
          >
            {normalizedMode} MODE
          </span>
        </span>
        {modeReason && (
          <span className="text-zinc-400 truncate border-l border-zinc-800 pl-2">
            {modeReason}
          </span>
        )}
      </div>

      {/* =========================================================================
          PART 5.B: REAL BACKEND PROCESSING STAGES STEPPER
          Only displayed when real stages are dispatched by backend
          ========================================================================= */}
      {stages && stages.length > 0 && !streamingChunk && (
        <div className="px-2.5 py-2 rounded bg-black/60 border border-zinc-800/70 space-y-1 font-mono text-[10px]">
          <div className="text-[9px] uppercase font-bold text-zinc-500 tracking-wider pb-0.5 flex items-center justify-between">
            <span>PROCESSING STAGES</span>
            <span className="text-zinc-400 font-normal">
              Stage {Math.max(1, stages.indexOf(currentStage) + 1)} of {stages.length}
            </span>
          </div>
          <div className="space-y-1">
            {stages.map((stg, i) => {
              const currentIndex = stages.indexOf(currentStage);
              const isCurrent = stg === currentStage;
              const isCompleted = currentIndex > -1 && i < currentIndex;

              return (
                <div key={i} className="flex items-center gap-2 transition-all">
                  {isCompleted ? (
                    <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                  ) : isCurrent ? (
                    <Loader2 className="w-3 h-3 animate-spin text-sky-400 shrink-0" />
                  ) : (
                    <span className="w-2 h-2 rounded-full border border-zinc-800 bg-zinc-900 shrink-0 mx-0.5" />
                  )}
                  <span
                    className={
                      isCurrent
                        ? 'text-zinc-100 font-bold'
                        : isCompleted
                        ? 'text-zinc-400 line-through decoration-zinc-700'
                        : 'text-zinc-600'
                    }
                  >
                    {stg}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* =========================================================================
          PART 5.D: RESEARCH ACTIVITY PREVIEW (When WEB or HYBRID Mode Active)
          Displays only actual values received from backend execution events
          ========================================================================= */}
      {(normalizedMode === 'WEB' || normalizedMode === 'HYBRID') &&
        researchTelemetry &&
        (researchTelemetry.sourcesCount > 0 || researchTelemetry.pagesCount > 0 || researchTelemetry.evidenceStatus) && (
          <div className="p-2 rounded bg-zinc-950/90 border border-emerald-900/50 font-mono text-[10px] space-y-1">
            <div className="flex items-center justify-between text-emerald-400 font-bold">
              <span className="flex items-center gap-1.5">
                <Globe className="w-3 h-3 text-emerald-400" />
                <span>LIVE RESEARCH ACTIVITY</span>
              </span>
              <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-950/80 border border-emerald-700 text-emerald-300 font-mono">
                {researchTelemetry.evidenceStatus || 'Searching'}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-zinc-400 text-[10px] pt-0.5">
              <div>
                Sources discovered:{' '}
                <span className="text-zinc-100 font-bold">{researchTelemetry.sourcesCount || 0}</span>
              </div>
              <div>
                Pages retrieved:{' '}
                <span className="text-zinc-100 font-bold">{researchTelemetry.pagesCount || 0}</span>
              </div>
            </div>
            {researchTelemetry.domains && researchTelemetry.domains.length > 0 && (
              <div className="text-[9px] text-zinc-500 truncate pt-0.5">
                Domains: {researchTelemetry.domains.slice(0, 3).join(', ')}
              </div>
            )}
          </div>
        )}

      {/* =========================================================================
          PART 5.E & STREAMING: LIVE TYPEWRITER OUTPUT OR SKELETON PLACEHOLDER
          ========================================================================= */}
      {streamingChunk ? (
        <div className="pl-3.5 border-l-2 border-sky-800/80 font-mono">
          <div className="text-xs text-zinc-100 font-mono leading-relaxed">
            <MarkdownRenderer content={streamingChunk} isStreaming={true} />
            <span className="inline-block w-2 h-3.5 bg-sky-400 ml-1 animate-pulse" />
          </div>
        </div>
      ) : (
        <div className="transition-opacity duration-300">
          {variation === 'code' && <CodeGenerationSkeleton compact={compact} />}
          {variation === 'structured' && <StructuredResponseSkeleton compact={compact} />}
          {variation === 'research' && <ResearchSkeleton compact={compact} />}
          {variation === 'text' && <TextGenerationSkeleton compact={compact} />}
        </div>
      )}
    </div>
  );
}
