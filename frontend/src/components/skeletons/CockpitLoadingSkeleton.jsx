import React, { useMemo } from 'react';
import { Square, CheckCircle2, Loader2, Globe, Sparkles, Layers, Cpu, Monitor, Compass, ShieldCheck, Activity, Terminal, ArrowRight, Database, Search } from 'lucide-react';
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

export const DEFAULT_PIPELINE_STAGES = {
  LLM: ['Understanding request', 'Classifying intent', 'Preparing reasoning context', 'Generating answer', 'Completing response'],
  WEB: ['Understanding directive', 'Searching external web', 'Retrieving source pages', 'Validating evidence', 'Synthesizing verified answer'],
  HYBRID: ['Understanding directive', 'Retrieving external evidence', 'Validating factual claims', 'Synthesizing blended answer', 'Completing response'],
  DOCUMENT: ['Understanding request', 'Searching uploaded document', 'Reading document passages', 'Preparing grounded answer', 'Completing response'],
  DOC: ['Understanding request', 'Searching uploaded document', 'Reading document passages', 'Preparing grounded answer', 'Completing response'],
  DESKTOP: ['Understanding request', 'Targeting desktop application', 'Formulating automation plan', 'Evaluating safety policy', 'Executing desktop actions'],
  BROWSER: ['Understanding directive', 'Targeting web domain', 'Initializing browser tab', 'Interacting with web elements', 'Verifying navigation state'],
  COMPOSITE: ['Understanding directive', 'Coordinating cross-engine plan', 'Searching web sources', 'Preparing execution steps', 'Completing response'],
  CLARIFICATION: ['Understanding request', 'Detecting ambiguity', 'Formulating clarification question', 'Completing response']
};

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

  // 1. Resolve Effective Pipeline Stages
  const effectiveStages = useMemo(() => {
    if (stages && Array.isArray(stages) && stages.length > 0) return stages;
    return DEFAULT_PIPELINE_STAGES[normalizedMode] || DEFAULT_PIPELINE_STAGES.LLM;
  }, [stages, normalizedMode]);

  // 2. Resolve Active Stage Index with Multi-Strategy Detection
  const resolvedCurrentIndex = useMemo(() => {
    if (!effectiveStages || effectiveStages.length === 0) return 0;

    // If final streaming text is flowing, we are on the final response stage
    if (streamingChunk) {
      return effectiveStages.length - 1;
    }

    // A. Exact case-insensitive match
    if (currentStage) {
      const cLow = currentStage.toLowerCase().trim();
      const exactIdx = effectiveStages.findIndex(
        (s) => s.toLowerCase().trim() === cLow
      );
      if (exactIdx !== -1) return exactIdx;

      // B. Substring containment match
      const subIdx = effectiveStages.findIndex((s) => {
        const sLow = s.toLowerCase().trim();
        return cLow.includes(sLow) || sLow.includes(cLow);
      });
      if (subIdx !== -1) return subIdx;
    }

    // C. Fallback match based on activeAgent name
    if (activeAgent) {
      const aLow = activeAgent.toLowerCase();
      if (aLow.includes('router') || aLow.includes('understanding') || aLow.includes('intent')) return 0;
      if (aLow.includes('planner') || aLow.includes('plan')) return Math.min(1, effectiveStages.length - 1);
      if (aLow.includes('retriev') || aLow.includes('search') || aLow.includes('document')) return Math.min(1, effectiveStages.length - 1);
      if (aLow.includes('passage') || aLow.includes('crawl') || aLow.includes('evidence')) return Math.min(2, effectiveStages.length - 1);
      if (aLow.includes('reason') || aLow.includes('synthesis') || aLow.includes('executor') || aLow.includes('execut')) return Math.min(3, effectiveStages.length - 1);
      if (aLow.includes('verify') || aLow.includes('verifier') || aLow.includes('safety')) return Math.min(effectiveStages.length - 2, effectiveStages.length - 1);
      if (aLow.includes('format') || aLow.includes('persona') || aLow.includes('complete')) return effectiveStages.length - 1;
    }

    // D. Fallback match based on currentThought / safe_task_summary
    if (currentThought) {
      const tLow = currentThought.toLowerCase();
      if (tLow.includes('analyzing') || tLow.includes('understanding') || tLow.includes('received')) return 0;
      if (tLow.includes('search') || tLow.includes('query') || tLow.includes('retriev') || tLow.includes('upload') || tLow.includes('pinecone')) return Math.min(1, effectiveStages.length - 1);
      if (tLow.includes('reading') || tLow.includes('passage') || tLow.includes('evidence') || tLow.includes('validat')) return Math.min(2, effectiveStages.length - 1);
      if (tLow.includes('reasoning') || tLow.includes('preparing') || tLow.includes('synthesiz') || tLow.includes('execut') || tLow.includes('launching')) return Math.min(3, effectiveStages.length - 1);
      if (tLow.includes('complet') || tLow.includes('delivering') || tLow.includes('final') || tLow.includes('verified')) return effectiveStages.length - 1;
    }

    // Default to stage 0 (active), NEVER -1
    return 0;
  }, [effectiveStages, currentStage, activeAgent, currentThought, streamingChunk]);

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
          REAL BACKEND PROCESSING STAGES STEPPER & LIVE BACKGROUND TELEMETRY
          ========================================================================= */}
      {effectiveStages && effectiveStages.length > 0 && !streamingChunk && (
        <div className="p-2.5 rounded bg-zinc-950/90 border border-zinc-800/90 font-mono text-[10px] space-y-2 shadow-lg">
          {/* Header with Title and Stage Counter */}
          <div className="flex items-center justify-between pb-1 border-b border-zinc-800/80">
            <div className="flex items-center gap-1.5 text-zinc-300 font-bold uppercase tracking-wider text-[9px]">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>PIPELINE STAGES</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-[9px] px-2 py-0.5 rounded bg-cyan-950/90 text-cyan-300 border border-cyan-800/80 font-mono font-bold tracking-wider shadow-sm">
                STAGE {Math.min(resolvedCurrentIndex + 1, effectiveStages.length)} OF {effectiveStages.length}
              </span>
            </div>
          </div>

          {/* Animated Gradient Progress Bar */}
          <div className="w-full bg-zinc-900/90 h-1 rounded-full overflow-hidden border border-zinc-800/50">
            <div
              className="bg-gradient-to-r from-sky-500 via-cyan-400 to-emerald-400 h-full transition-all duration-500 shadow-[0_0_8px_rgba(6,182,212,0.6)]"
              style={{
                width: `${Math.min(100, Math.round(((resolvedCurrentIndex + 1) / effectiveStages.length) * 100))}%`
              }}
            />
          </div>

          {/* Interactive Stepper Items */}
          <div className="space-y-1.5 pt-0.5">
            {effectiveStages.map((stg, i) => {
              const isCompleted = i < resolvedCurrentIndex;
              const isCurrent = i === resolvedCurrentIndex;
              const isPending = i > resolvedCurrentIndex;

              return (
                <div key={i} className="transition-all duration-200">
                  <div
                    className={`flex items-center justify-between p-1.5 rounded transition-all ${
                      isCurrent
                        ? 'bg-cyan-950/50 border border-cyan-500/70 shadow-[0_0_14px_rgba(6,182,212,0.22)]'
                        : isCompleted
                        ? 'bg-zinc-950/40 border border-zinc-850/60'
                        : 'bg-zinc-950/20 border border-transparent opacity-40'
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      {isCompleted ? (
                        <div className="w-4 h-4 rounded-full bg-emerald-950 border border-emerald-500/80 flex items-center justify-center shrink-0">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                        </div>
                      ) : isCurrent ? (
                        <div className="w-4 h-4 rounded-full bg-cyan-950 border border-cyan-400 flex items-center justify-center shrink-0 shadow-[0_0_8px_rgba(6,182,212,0.7)]">
                          <Loader2 className="w-2.5 h-2.5 animate-spin text-cyan-300" />
                        </div>
                      ) : (
                        <div className="w-4 h-4 rounded-full bg-zinc-900 border border-zinc-700/60 flex items-center justify-center shrink-0">
                          <span className="w-1.5 h-1.5 rounded-full bg-zinc-600" />
                        </div>
                      )}

                      <span
                        className={`text-[10px] truncate font-mono ${
                          isCurrent
                            ? 'text-cyan-100 font-bold tracking-wide'
                            : isCompleted
                            ? 'text-zinc-400 line-through decoration-zinc-600'
                            : 'text-zinc-500'
                        }`}
                      >
                        {stg}
                      </span>
                    </div>

                    {/* Status Pill on the Right */}
                    {isCurrent && (
                      <span className="shrink-0 text-[8px] font-black px-1.5 py-0.5 rounded bg-cyan-500 text-black uppercase tracking-wider flex items-center gap-1 shadow-sm">
                        <span className="w-1.5 h-1.5 rounded-full bg-black animate-ping" />
                        <span>LIVE</span>
                      </span>
                    )}
                    {isCompleted && (
                      <span className="shrink-0 text-[8px] font-bold px-1.5 py-0.2 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">
                        DONE
                      </span>
                    )}
                  </div>

                  {/* LIVE BACKGROUND EXECUTION CARD (Embedded directly within the currently active stage) */}
                  {isCurrent && (
                    <div className="ml-5 mt-1 p-2 rounded bg-black/90 border border-cyan-800/60 font-mono text-[10px] space-y-1.5 shadow-lg animate-fadeIn">
                      <div className="flex items-center justify-between text-cyan-400 border-b border-zinc-800 pb-1">
                        <div className="flex items-center gap-1.5 font-bold text-[9px] uppercase tracking-wider">
                          <Activity className="w-3 h-3 text-cyan-400 animate-pulse" />
                          <span>LIVE BACKGROUND ACTIVITY</span>
                        </div>
                        {activeAgent && (
                          <span className="text-[8px] px-1.5 py-0.2 rounded bg-zinc-900 text-zinc-300 border border-zinc-700 font-mono">
                            Agent: {activeAgent}
                          </span>
                        )}
                      </div>

                      {/* Current Action / Live Thought */}
                      <div className="text-zinc-200 text-[10px] leading-relaxed flex items-start gap-1.5 pt-0.5">
                        <span className="text-cyan-400 shrink-0 font-bold select-none">▶</span>
                        <span className="font-semibold text-zinc-100">
                          {currentThought || `Executing ${stg.toLowerCase()} in background...`}
                        </span>
                      </div>

                      {/* Mode-Specific Real-Time Metrics */}
                      {normalizedMode === 'DOCUMENT' && (
                        <div className="grid grid-cols-2 gap-2 pt-1 border-t border-zinc-900 text-[9px] text-zinc-400">
                          <div>Index: <span className="text-amber-300 font-bold">Pinecone Ephemeral</span></div>
                          <div>Top-K: <span className="text-zinc-200 font-bold">4 Grounded Passages</span></div>
                        </div>
                      )}

                      {(normalizedMode === 'WEB' || normalizedMode === 'HYBRID') && researchTelemetry && (
                        <div className="grid grid-cols-2 gap-2 pt-1 border-t border-zinc-900 text-[9px] text-zinc-400">
                          <div>Sources Found: <span className="text-emerald-400 font-bold">{researchTelemetry.sourcesCount || 0}</span></div>
                          <div>Status: <span className="text-zinc-200 font-bold">{researchTelemetry.evidenceStatus || 'Searching'}</span></div>
                        </div>
                      )}

                      {(normalizedMode === 'DESKTOP' || normalizedMode === 'BROWSER') && automationTelemetry && (
                        <div className="grid grid-cols-2 gap-2 pt-1 border-t border-zinc-900 text-[9px] text-zinc-400">
                          <div>Target App: <span className="text-cyan-300 font-bold">{automationTelemetry.targetApp || 'System'}</span></div>
                          <div>Verifier: <span className="text-zinc-200 font-bold">{automationTelemetry.verificationStatus || 'Active'}</span></div>
                        </div>
                      )}
                    </div>
                  )}
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
