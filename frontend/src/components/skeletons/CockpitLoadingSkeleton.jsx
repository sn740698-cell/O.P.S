import React, { useMemo } from 'react';
import { Square, CheckCircle2, Loader2, Globe, Sparkles, Layers, Cpu, Monitor, Compass, ShieldCheck } from 'lucide-react';
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
 * Dual Engine Architecture:
 * 1. Answering Engine: [ LLM ] [ WEB ] [ HYBRID ] [ DOCUMENT ]
 * 2. Automation Engine: [ DESKTOP ] [ BROWSER ] [ HYBRID AUTO ]
 * Dynamic Engine & Mode highlighting, stage stepper, live research & automation telemetry.
 */
export default function CockpitLoadingSkeleton({
  query = '',
  activeEngine = '',
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
  researchTelemetry = null,
  automationTelemetry = null
}) {
  const variation = useMemo(() => {
    return variationOverride || detectSkeletonVariation(query);
  }, [variationOverride, query]);

  const normalizedMode = (activeMode || 'LLM').toUpperCase();
  const normalizedEngine = (activeEngine || (
    ['DESKTOP', 'BROWSER', 'HYBRID AUTO', 'HYBRID_AUTO'].includes(normalizedMode)
      ? 'AUTOMATION'
      : normalizedMode === 'COMPOSITE'
      ? 'COMPOSITE'
      : 'ANSWERING'
  )).toUpperCase();

  const isAnsweringActive = normalizedEngine === 'ANSWERING' || normalizedEngine === 'COMPOSITE';
  const isAutomationActive = normalizedEngine === 'AUTOMATION' || normalizedEngine === 'COMPOSITE';

  return (
    <div
      className="space-y-2.5 pt-1 font-mono transition-all duration-200"
      aria-live="polite"
      aria-busy="true"
    >
      {/* =========================================================================
          DUAL ENGINE INDICATOR PANEL: ANSWERING & AUTOMATION ENGINES
          ========================================================================= */}
      <div className="p-2.5 rounded bg-zinc-950/95 border border-zinc-800/90 font-mono text-[11px] select-none shadow-md space-y-2">
        {/* Top Bar: Active Engine & Emergency Halt */}
        <div className="flex items-center justify-between border-b border-zinc-850 pb-1.5">
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-bold">ENGINE:</span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-black tracking-wider border flex items-center gap-1.5 ${
              normalizedEngine === 'COMPOSITE'
                ? 'bg-rose-950/90 text-rose-300 border-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.4)] animate-pulse'
                : normalizedEngine === 'AUTOMATION'
                ? 'bg-cyan-950/90 text-cyan-300 border-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.4)]'
                : 'bg-blue-950/90 text-blue-300 border-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.3)]'
            }`}>
              <span className="w-1.5 h-1.5 rounded-full bg-current animate-ping" />
              <span>{normalizedEngine} ENGINE</span>
            </span>
          </div>

          {/* Emergency Stop Button */}
          {onStopExecution && (
            <button
              type="button"
              onClick={onStopExecution}
              className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-950 border border-red-700 text-red-300 hover:bg-red-900 transition flex items-center gap-1 font-mono shrink-0 shadow-sm"
              title="Halt active operation"
            >
              <Square className="w-2.5 h-2.5 fill-current" />
              <span>HALT</span>
            </button>
          )}
        </div>

        {/* Engine 1: ANSWERING ENGINE MODES */}
        <div className={`p-1.5 rounded border transition-all ${
          isAnsweringActive
            ? 'bg-zinc-900/60 border-zinc-700'
            : 'bg-zinc-950/40 border-zinc-900 opacity-50'
        }`}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-[9px] uppercase tracking-wider font-bold text-zinc-400 flex items-center gap-1">
              <Cpu className="w-3 h-3 text-sky-400" />
              <span>Answering Engine</span>
            </span>
            {isAnsweringActive && (
              <span className="text-[8px] px-1 py-0.2 rounded bg-sky-950/80 text-sky-400 border border-sky-800">
                ACTIVE
              </span>
            )}
          </div>
          <div className="grid grid-cols-4 gap-1">
            {/* LLM */}
            <div
              className={`px-1.5 py-0.5 rounded text-[9px] font-bold border text-center transition-all flex items-center justify-center gap-1 ${
                normalizedMode === 'LLM'
                  ? 'bg-blue-950/90 text-blue-300 border-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.4)]'
                  : 'bg-zinc-900/40 text-zinc-500 border-zinc-800'
              }`}
              title="LLM Mode: Local knowledge & high-speed reasoning"
            >
              {normalizedMode === 'LLM' && <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />}
              <span>LLM</span>
            </div>

            {/* WEB */}
            <div
              className={`px-1.5 py-0.5 rounded text-[9px] font-bold border text-center transition-all flex items-center justify-center gap-1 ${
                normalizedMode === 'WEB'
                  ? 'bg-emerald-950/90 text-emerald-300 border-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]'
                  : 'bg-zinc-900/40 text-zinc-500 border-zinc-800'
              }`}
              title="WEB Mode: Live search & grounded evidence"
            >
              {normalizedMode === 'WEB' && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />}
              <span>WEB</span>
            </div>

            {/* HYBRID */}
            <div
              className={`px-1.5 py-0.5 rounded text-[9px] font-bold border text-center transition-all flex items-center justify-center gap-1 ${
                normalizedMode === 'HYBRID'
                  ? 'bg-purple-950/90 text-purple-300 border-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.4)]'
                  : 'bg-zinc-900/40 text-zinc-500 border-zinc-800'
              }`}
              title="HYBRID Mode: Local reasoning combined with live web search"
            >
              {normalizedMode === 'HYBRID' && <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />}
              <span>HYBRID</span>
            </div>

            {/* DOCUMENT */}
            <div
              className={`px-1.5 py-0.5 rounded text-[9px] font-bold border text-center transition-all flex items-center justify-center gap-1 ${
                normalizedMode === 'DOCUMENT'
                  ? 'bg-amber-950/90 text-amber-300 border-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.4)]'
                  : 'bg-zinc-900/40 text-zinc-500 border-zinc-800'
              }`}
              title="DOCUMENT Mode: Ephemeral Pinecone RAG session"
            >
              {normalizedMode === 'DOCUMENT' && <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />}
              <span>DOC</span>
            </div>
          </div>
        </div>

        {/* Engine 2: AUTOMATION ENGINE MODES */}
        <div className={`p-1.5 rounded border transition-all ${
          isAutomationActive
            ? 'bg-zinc-900/60 border-zinc-700'
            : 'bg-zinc-950/40 border-zinc-900 opacity-50'
        }`}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-[9px] uppercase tracking-wider font-bold text-zinc-400 flex items-center gap-1">
              <Monitor className="w-3 h-3 text-cyan-400" />
              <span>Automation Engine</span>
            </span>
            {isAutomationActive && (
              <span className="text-[8px] px-1 py-0.2 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-800">
                ACTIVE
              </span>
            )}
          </div>
          <div className="grid grid-cols-3 gap-1">
            {/* DESKTOP */}
            <div
              className={`px-1.5 py-0.5 rounded text-[9px] font-bold border text-center transition-all flex items-center justify-center gap-1 ${
                normalizedMode === 'DESKTOP'
                  ? 'bg-cyan-950/90 text-cyan-300 border-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.4)]'
                  : 'bg-zinc-900/40 text-zinc-500 border-zinc-800'
              }`}
              title="Desktop Mode: Pywinauto Windows desktop automation"
            >
              {normalizedMode === 'DESKTOP' && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />}
              <span>DESKTOP</span>
            </div>

            {/* BROWSER */}
            <div
              className={`px-1.5 py-0.5 rounded text-[9px] font-bold border text-center transition-all flex items-center justify-center gap-1 ${
                normalizedMode === 'BROWSER'
                  ? 'bg-indigo-950/90 text-indigo-300 border-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.4)]'
                  : 'bg-zinc-900/40 text-zinc-500 border-zinc-800'
              }`}
              title="Browser Mode: Playwright browser navigation & scraping"
            >
              {normalizedMode === 'BROWSER' && <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />}
              <span>BROWSER</span>
            </div>

            {/* HYBRID AUTO */}
            <div
              className={`px-1.5 py-0.5 rounded text-[9px] font-bold border text-center transition-all flex items-center justify-center gap-1 ${
                normalizedMode === 'HYBRID AUTO' || normalizedMode === 'HYBRID_AUTO' || (normalizedEngine === 'COMPOSITE')
                  ? 'bg-rose-950/90 text-rose-300 border-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.4)]'
                  : 'bg-zinc-900/40 text-zinc-500 border-zinc-800'
              }`}
              title="Hybrid Automation: Desktop + Browser cross-application orchestration"
            >
              {(normalizedMode === 'HYBRID AUTO' || normalizedMode === 'HYBRID_AUTO') && (
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
              )}
              <span>HYBRID AUTO</span>
            </div>
          </div>
        </div>
      </div>

      {/* =========================================================================
          ACTIVE MODE STATUS & REASON BANNER
          ========================================================================= */}
      <div className="flex items-center gap-2 px-2.5 py-1.5 rounded bg-zinc-950/70 border border-zinc-800/60 text-[10px] font-mono">
        <span className="font-bold shrink-0 flex items-center gap-1">
          <span className="text-zinc-400">MODE:</span>
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
                : normalizedMode === 'DESKTOP'
                ? 'text-cyan-400 font-extrabold'
                : normalizedMode === 'BROWSER'
                ? 'text-indigo-400 font-extrabold'
                : 'text-rose-400 font-extrabold'
            }
          >
            {normalizedMode}
          </span>
        </span>
        {modeReason && (
          <span className="text-zinc-400 truncate border-l border-zinc-800 pl-2">
            {modeReason}
          </span>
        )}
      </div>

      {/* =========================================================================
          REAL BACKEND PROCESSING STAGES STEPPER
          ========================================================================= */}
      {stages && stages.length > 0 && !streamingChunk && (
        <div className="px-2.5 py-2 rounded bg-black/60 border border-zinc-800/70 space-y-1 font-mono text-[10px]">
          <div className="text-[9px] uppercase font-bold text-zinc-500 tracking-wider pb-0.5 flex items-center justify-between">
            <span>PIPELINE STAGES</span>
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
          AUTOMATION ACTIVITY & STATE VERIFICATION PREVIEW
          ========================================================================= */}
      {isAutomationActive && automationTelemetry && (
        <div className="p-2 rounded bg-zinc-950/90 border border-cyan-900/50 font-mono text-[10px] space-y-1">
          <div className="flex items-center justify-between text-cyan-400 font-bold">
            <span className="flex items-center gap-1.5">
              <Monitor className="w-3 h-3 text-cyan-400" />
              <span>LIVE AUTOMATION PIPELINE</span>
            </span>
            <span className="text-[9px] px-1.5 py-0.2 rounded bg-cyan-950/80 border border-cyan-700 text-cyan-300 font-mono flex items-center gap-1">
              <ShieldCheck className="w-2.5 h-2.5" />
              <span>{automationTelemetry.verificationStatus || 'Verifying'}</span>
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-zinc-400 text-[10px] pt-0.5">
            <div>
              Target App: <span className="text-zinc-100 font-bold">{automationTelemetry.targetApp || 'System'}</span>
            </div>
            <div>
              Action: <span className="text-zinc-100 font-bold">{automationTelemetry.action || 'Executing'}</span>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          RESEARCH ACTIVITY PREVIEW (When WEB or HYBRID Active)
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
          LIVE TYPEWRITER OUTPUT OR SKELETON PLACEHOLDER
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
