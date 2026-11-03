import React from 'react';
import {
  Bot,
  Brain,
  Search,
  Download,
  Cpu,
  Layers,
  CheckCircle2,
  Radio,
  Sparkles,
  Loader2
} from 'lucide-react';

/**
 * Intelligent Loading State Labels Map
 * Section 2 Specification
 */
export const LOADING_STATES_CONFIG = {
  thinking: {
    label: 'Thinking...',
    icon: Brain,
    color: 'text-sky-400',
    badge: 'bg-sky-950/60 border-sky-800 text-sky-400'
  },
  planning: {
    label: 'Planning your request...',
    icon: Layers,
    color: 'text-amber-400',
    badge: 'bg-amber-950/60 border-amber-800 text-amber-400'
  },
  generating: {
    label: 'Generating response...',
    icon: Sparkles,
    color: 'text-emerald-400',
    badge: 'bg-emerald-950/60 border-emerald-800 text-emerald-400'
  },
  searching: {
    label: 'Searching for information...',
    icon: Search,
    color: 'text-blue-400',
    badge: 'bg-blue-950/60 border-blue-800 text-blue-400'
  },
  retrieving: {
    label: 'Retrieving relevant information...',
    icon: Download,
    color: 'text-indigo-400',
    badge: 'bg-indigo-950/60 border-indigo-800 text-indigo-400'
  },
  processing: {
    label: 'Processing your request...',
    icon: Cpu,
    color: 'text-red-400',
    badge: 'bg-red-950/60 border-red-800 text-red-400'
  },
  executing: {
    label: 'Executing your task...',
    icon: Loader2,
    color: 'text-purple-400',
    badge: 'bg-purple-950/60 border-purple-800 text-purple-400'
  },
  verifying: {
    label: 'Verifying the result...',
    icon: CheckCircle2,
    color: 'text-teal-400',
    badge: 'bg-teal-950/60 border-teal-800 text-teal-400'
  },
  connecting: {
    label: 'Connecting to the service...',
    icon: Radio,
    color: 'text-yellow-400',
    badge: 'bg-yellow-950/60 border-yellow-800 text-yellow-400'
  },
  neutral: {
    label: 'Working on your request...',
    icon: Bot,
    color: 'text-zinc-300',
    badge: 'bg-zinc-900 border-zinc-700 text-zinc-300'
  }
};

/**
 * Resolves the state key from real backend events / activeAgent / currentThought
 */
export function resolveLoadingStateKey(activeAgent = '', currentThought = '') {
  const combined = `${activeAgent} ${currentThought}`.toLowerCase();

  if (combined.includes('plan') || combined.includes('routing') || combined.includes('intent')) {
    return 'planning';
  }
  if (combined.includes('search') || combined.includes('brave') || combined.includes('query')) {
    return 'searching';
  }
  if (
    combined.includes('crawl') ||
    combined.includes('scrape') ||
    combined.includes('retriev') ||
    combined.includes('extract') ||
    combined.includes('download')
  ) {
    return 'retrieving';
  }
  if (combined.includes('verif') || combined.includes('fact-check') || combined.includes('evaluat')) {
    return 'verifying';
  }
  if (combined.includes('connect') || combined.includes('ollama') || combined.includes('model server')) {
    return 'connecting';
  }
  if (combined.includes('generat') || combined.includes('answer') || combined.includes('synthesiz')) {
    return 'generating';
  }
  if (combined.includes('execut') || combined.includes('tool') || combined.includes('running')) {
    return 'executing';
  }
  if (combined.includes('think') || combined.includes('analyz') || combined.includes('understand')) {
    return 'thinking';
  }
  if (combined.includes('process') || combined.includes('langgraph')) {
    return 'processing';
  }

  return 'neutral';
}

export default function LoadingStatusIndicator({
  stateKey,
  activeAgent = '',
  currentThought = '',
  showThought = true,
  compact = false
}) {
  const resolvedKey = stateKey || resolveLoadingStateKey(activeAgent, currentThought);
  const config = LOADING_STATES_CONFIG[resolvedKey] || LOADING_STATES_CONFIG.neutral;
  const IconComponent = config.icon;

  return (
    <div className="flex flex-col gap-1 font-mono">
      <div className="flex items-center gap-2">
        {/* Pulsing Tactical Core Indicator */}
        <div className="relative flex items-center justify-center">
          <span className="w-2.5 h-2.5 rounded-full bg-red-600 animate-ping absolute opacity-70"></span>
          <span className="w-2 h-2 rounded-full bg-red-500 relative"></span>
        </div>

        {/* Identity & Status Label */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="font-bold text-[11px] uppercase tracking-wider text-zinc-300 flex items-center gap-1.5">
            <Bot className="w-3.5 h-3.5 text-red-500" />
            <span>O.P.S. // JARVIS</span>
          </span>

          <span
            className={`text-[9px] px-1.5 py-0.5 rounded border font-bold uppercase tracking-wider flex items-center gap-1 ${config.badge}`}
          >
            <IconComponent className="w-2.5 h-2.5 animate-spin" />
            <span>{config.label}</span>
          </span>
        </div>
      </div>

      {/* Real Backend Telemetry Ticker (transparent, never fake) */}
      {showThought && currentThought && (
        <div className="text-[11px] text-zinc-400 pl-4 border-l border-zinc-800 flex items-center gap-1.5 truncate">
          <span className="text-red-500">&gt;</span>
          <span className="truncate">{currentThought}</span>
        </div>
      )}
    </div>
  );
}
