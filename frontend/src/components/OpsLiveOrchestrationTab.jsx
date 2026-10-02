import React, { useState, useEffect } from 'react';
import {
  Play, Loader2, Sparkles, Globe, Terminal, Cpu, Bot, CheckCircle2,
  Volume2, ShieldCheck, Search, Radio, Database, Layers, ArrowRight,
  RotateCcw, RefreshCw, Trash2, Key, HardDrive, Zap, ShieldAlert,
  MessageSquare, UserCheck, Activity, GitBranch, CpuIcon
} from 'lucide-react';
import { retroSoundEngine } from '../utils/retroSounds';

// ==================== PIXEL ART SVG COMPONENTS ====================

const SirenBeacon = ({ className = "w-4 h-4", isPulsing = false }) => (
  <div className={`relative inline-block ${className} ${isPulsing ? 'animate-bounce' : ''}`}>
    <svg viewBox="0 0 24 24" className="w-full h-full drop-shadow-[0_0_6px_rgba(239,68,68,0.8)]">
      {/* Siren Base */}
      <rect x="5" y="16" width="14" height="4" fill="#27272a" stroke="#000000" strokeWidth="1" />
      {/* Red Glass Dome */}
      <path d="M7 16 C7 9, 17 9, 17 16 Z" fill="#ef4444" stroke="#000000" strokeWidth="1" />
      {/* Light Reflection */}
      <path d="M9 13 C9 11, 12 10, 14 10" stroke="#ffffff" strokeWidth="1.2" strokeLinecap="round" fill="none" />
      {/* Radiating Rays */}
      <line x1="12" y1="5" x2="12" y2="8" stroke="#ef4444" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="4" y1="8" x2="7" y2="10" stroke="#ef4444" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="20" y1="8" x2="17" y2="10" stroke="#ef4444" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  </div>
);

const UserAtWorkstation = () => (
  <svg viewBox="0 0 100 80" className="w-24 h-20">
    {/* Dual Monitors on Desk */}
    <rect x="38" y="16" width="26" height="20" fill="#09090b" stroke="#ffffff" strokeWidth="1.5" rx="1" />
    <rect x="66" y="16" width="24" height="20" fill="#09090b" stroke="#ffffff" strokeWidth="1.5" rx="1" />
    {/* Monitor Code Lines */}
    <line x1="42" y1="21" x2="60" y2="21" stroke="#ef4444" strokeWidth="1.2" />
    <line x1="42" y1="25" x2="56" y2="25" stroke="#ef4444" strokeWidth="1.2" />
    <line x1="42" y1="29" x2="52" y2="29" stroke="#ffffff" strokeWidth="1.2" />
    <line x1="70" y1="21" x2="86" y2="21" stroke="#ffffff" strokeWidth="1.2" />
    <line x1="70" y1="26" x2="80" y2="26" stroke="#ef4444" strokeWidth="1.2" />
    {/* Monitor Stands */}
    <rect x="49" y="36" width="4" height="6" fill="#71717a" />
    <rect x="76" y="36" width="4" height="6" fill="#71717a" />
    {/* Desk Surface */}
    <rect x="30" y="42" width="66" height="4" fill="#a1a1aa" stroke="#000000" strokeWidth="1" />
    {/* Desk Legs */}
    <rect x="34" y="46" width="4" height="28" fill="#52525b" />
    <rect x="90" y="46" width="4" height="28" fill="#52525b" />
    {/* Keyboard on Desk */}
    <rect x="48" y="40" width="18" height="2" fill="#e4e4e7" />
    {/* Person in Chair */}
    <rect x="10" y="32" width="6" height="30" fill="#18181b" stroke="#000000" strokeWidth="1" />
    <circle cx="22" cy="22" r="7" fill="#e4e4e7" stroke="#000000" strokeWidth="1.2" />
    <path d="M15 20 C15 15, 29 15, 29 20 Z" fill="#71717a" />
    <rect x="16" y="29" width="12" height="22" fill="#27272a" stroke="#000000" strokeWidth="1.2" rx="2" />
    <path d="M24 35 L38 41 L46 41" stroke="#e4e4e7" strokeWidth="3" strokeLinecap="round" fill="none" />
    <rect x="12" y="60" width="4" height="12" fill="#3f3f46" />
    <line x1="8" y1="72" x2="20" y2="72" stroke="#18181b" strokeWidth="2.5" />
  </svg>
);

const RobotAgentAvatar = ({ isActive = false }) => (
  <svg viewBox="0 0 64 64" className={`w-14 h-14 ${isActive ? 'animate-pulse' : ''}`}>
    <line x1="32" y1="6" x2="32" y2="14" stroke="#e4e4e7" strokeWidth="2" />
    <circle cx="32" cy="6" r="2.5" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    <rect x="16" y="14" width="32" height="24" rx="10" fill="#e4e4e7" stroke="#000000" strokeWidth="1.8" />
    <rect x="20" y="19" width="24" height="14" rx="4" fill="#09090b" stroke="#3f3f46" strokeWidth="1" />
    <circle cx="26" cy="26" r="2" fill="#ef4444" />
    <circle cx="38" cy="26" r="2" fill="#ef4444" />
    <rect x="12" y="22" width="4" height="8" rx="1" fill="#71717a" />
    <rect x="48" y="22" width="4" height="8" rx="1" fill="#71717a" />
    <rect x="18" y="38" width="28" height="20" rx="4" fill="#d4d4d8" stroke="#000000" strokeWidth="1.8" />
    <line x1="24" y1="44" x2="32" y2="44" stroke="#ef4444" strokeWidth="2" />
    <circle cx="38" cy="44" r="1.5" fill="#ef4444" />
    <rect x="10" y="42" width="6" height="12" rx="2" fill="#a1a1aa" stroke="#000000" strokeWidth="1" />
    <rect x="48" y="42" width="6" height="12" rx="2" fill="#a1a1aa" stroke="#000000" strokeWidth="1" />
  </svg>
);

const BrainIcon = () => (
  <svg viewBox="0 0 54 44" className="w-12 h-10">
    <path
      d="M20 8 C14 8, 10 14, 10 20 C10 26, 14 30, 18 34 C22 38, 24 38, 26 38 L26 8 Z"
      fill="#ffffff"
      stroke="#ef4444"
      strokeWidth="2"
    />
    <path
      d="M34 8 C40 8, 44 14, 44 20 C44 26, 40 30, 36 34 C32 38, 30 38, 28 38 L28 8 Z"
      fill="#ffffff"
      stroke="#ef4444"
      strokeWidth="2"
    />
    <circle cx="16" cy="18" r="1.5" fill="#ef4444" />
    <circle cx="20" cy="26" r="1.5" fill="#ef4444" />
    <circle cx="38" cy="18" r="1.5" fill="#ef4444" />
    <circle cx="34" cy="26" r="1.5" fill="#ef4444" />
    <circle cx="6" cy="14" r="2" fill="#ef4444" />
    <circle cx="6" cy="24" r="2" fill="#ef4444" />
    <circle cx="48" cy="14" r="2" fill="#ef4444" />
    <circle cx="48" cy="24" r="2" fill="#ef4444" />
    <circle cx="27" cy="4" r="2" fill="#ef4444" />
    <line x1="10" y1="14" x2="6" y2="14" stroke="#ef4444" strokeWidth="1.5" />
    <line x1="10" y1="24" x2="6" y2="24" stroke="#ef4444" strokeWidth="1.5" />
    <line x1="44" y1="14" x2="48" y2="14" stroke="#ef4444" strokeWidth="1.5" />
    <line x1="44" y1="24" x2="48" y2="24" stroke="#ef4444" strokeWidth="1.5" />
  </svg>
);

const NeuralNetIcon = () => (
  <svg viewBox="0 0 54 44" className="w-12 h-10">
    <line x1="12" y1="12" x2="27" y2="8" stroke="#ffffff" strokeWidth="1.2" />
    <line x1="12" y1="12" x2="27" y2="22" stroke="#ffffff" strokeWidth="1.2" />
    <line x1="12" y1="32" x2="27" y2="22" stroke="#ffffff" strokeWidth="1.2" />
    <line x1="12" y1="32" x2="27" y2="36" stroke="#ffffff" strokeWidth="1.2" />
    <line x1="27" y1="8" x2="42" y2="16" stroke="#ef4444" strokeWidth="1.2" />
    <line x1="27" y1="22" x2="42" y2="16" stroke="#ef4444" strokeWidth="1.2" />
    <line x1="27" y1="22" x2="42" y2="28" stroke="#ef4444" strokeWidth="1.2" />
    <line x1="27" y1="36" x2="42" y2="28" stroke="#ef4444" strokeWidth="1.2" />
    <circle cx="12" cy="12" r="3.5" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    <circle cx="12" cy="32" r="3.5" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    <circle cx="27" cy="8" r="3.5" fill="#ffffff" stroke="#000000" strokeWidth="1" />
    <circle cx="27" cy="22" r="3.5" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    <circle cx="27" cy="36" r="3.5" fill="#ffffff" stroke="#000000" strokeWidth="1" />
    <circle cx="42" cy="16" r="3.5" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    <circle cx="42" cy="28" r="3.5" fill="#ffffff" stroke="#000000" strokeWidth="1" />
  </svg>
);

const DatabaseIcon = () => (
  <svg viewBox="0 0 36 36" className="w-8 h-8">
    <ellipse cx="18" cy="8" rx="14" ry="4" fill="#09090b" stroke="#ffffff" strokeWidth="1.8" />
    <path d="M4 8 V16 C4 18.5, 32 18.5, 32 16 V8" fill="#09090b" stroke="#ffffff" strokeWidth="1.8" />
    <path d="M4 16 V24 C4 26.5, 32 26.5, 32 24 V16" fill="#09090b" stroke="#ffffff" strokeWidth="1.8" />
    <ellipse cx="18" cy="24" rx="14" ry="4" fill="#ef4444" stroke="#000000" strokeWidth="1.5" />
    <line x1="9" y1="12" x2="13" y2="12" stroke="#ef4444" strokeWidth="1.5" />
    <line x1="9" y1="20" x2="13" y2="20" stroke="#ef4444" strokeWidth="1.5" />
  </svg>
);

const KnowledgeStackIcon = () => (
  <svg viewBox="0 0 36 36" className="w-8 h-8">
    <rect x="10" y="4" width="20" height="26" fill="#27272a" stroke="#ffffff" strokeWidth="1.5" rx="1" />
    <rect x="6" y="8" width="20" height="26" fill="#09090b" stroke="#ffffff" strokeWidth="1.5" rx="1" />
    <line x1="10" y1="14" x2="22" y2="14" stroke="#ef4444" strokeWidth="1.5" />
    <line x1="10" y1="19" x2="22" y2="19" stroke="#ffffff" strokeWidth="1.5" />
    <line x1="10" y1="24" x2="18" y2="24" stroke="#ffffff" strokeWidth="1.5" />
  </svg>
);

const ImageIcon = () => (
  <svg viewBox="0 0 32 32" className="w-7 h-7">
    <rect x="4" y="4" width="24" height="24" fill="#09090b" stroke="#ffffff" strokeWidth="1.5" rx="2" />
    <circle cx="10" cy="11" r="2.5" fill="#ef4444" />
    <polygon points="6,24 14,14 20,20 26,12 26,24" fill="#52525b" stroke="#ffffff" strokeWidth="1" />
  </svg>
);

const DocIcon = () => (
  <svg viewBox="0 0 32 32" className="w-7 h-7">
    <path d="M6 4 L20 4 L26 10 L26 28 L6 28 Z" fill="#09090b" stroke="#ffffff" strokeWidth="1.5" />
    <polygon points="20,4 20,10 26,10" fill="#71717a" stroke="#ffffff" strokeWidth="1" />
    <line x1="10" y1="14" x2="18" y2="14" stroke="#ef4444" strokeWidth="1.5" />
    <line x1="10" y1="19" x2="22" y2="19" stroke="#ffffff" strokeWidth="1.2" />
    <line x1="10" y1="23" x2="18" y2="23" stroke="#ffffff" strokeWidth="1.2" />
  </svg>
);

const InputDataIcon = () => (
  <svg viewBox="0 0 32 32" className="w-7 h-7">
    <rect x="4" y="4" width="24" height="24" fill="#09090b" stroke="#ffffff" strokeWidth="1.5" rx="2" />
    <circle cx="9" cy="10" r="1.5" fill="#ef4444" />
    <line x1="14" y1="10" x2="24" y2="10" stroke="#ffffff" strokeWidth="1.5" />
    <circle cx="9" cy="16" r="1.5" fill="#ef4444" />
    <line x1="14" y1="16" x2="24" y2="16" stroke="#ffffff" strokeWidth="1.5" />
    <circle cx="9" cy="22" r="1.5" fill="#ef4444" />
    <line x1="14" y1="22" x2="20" y2="22" stroke="#ffffff" strokeWidth="1.5" />
  </svg>
);

// ==================== MAIN ORCHESTRATION CANVAS & LIVE AGENT EXECUTION ====================

export default function OpsLiveOrchestrationTab({
  activeAgent,
  currentThought,
  planSteps,
  isLoading,
  onDispatchPrompt,
  briefingText,
  sessionId,
  onClearMemory
}) {
  const [quickInput, setQuickInput] = useState('');
  const [lastUserQuery, setLastUserQuery] = useState('Who is Virat Kohli?');

  // Dedicated Chatbot Vector Database Partition State
  const [vectorPartitionStats, setVectorPartitionStats] = useState({
    partition_name: 'ops_chatbot_memory',
    total_chatbot_vectors: 0,
    entries: [],
    status: 'ONLINE'
  });
  const [isPurgingVector, setIsPurgingVector] = useState(false);
  const [vectorPurgeAlert, setVectorPurgeAlert] = useState(false);

  // Poll dedicated chatbot vector database stats
  const fetchChatbotVectorStats = async () => {
    try {
      const url = sessionId ? `/api/v1/memory/chatbot-vector/?session_id=${sessionId}` : '/api/v1/memory/chatbot-vector/';
      const res = await fetch(url);
      if (res.ok) {
        const d = await res.json();
        setVectorPartitionStats(d);
      }
    } catch (e) {
      console.warn('Could not fetch chatbot vector stats:', e);
    }
  };

  useEffect(() => {
    fetchChatbotVectorStats();
    const interval = setInterval(fetchChatbotVectorStats, 5000);
    return () => clearInterval(interval);
  }, [sessionId, isLoading]);

  const handlePurgeVectorPartition = async () => {
    setIsPurgingVector(true);
    try {
      const url = sessionId ? `/api/v1/memory/chatbot-vector/?session_id=${sessionId}` : '/api/v1/memory/chatbot-vector/';
      await fetch(url, { method: 'DELETE' });
      retroSoundEngine.playMemoryErase();
      if (onClearMemory) onClearMemory();
      setVectorPurgeAlert(true);
      setTimeout(() => setVectorPurgeAlert(false), 3000);
      fetchChatbotVectorStats();
    } catch (e) {
      console.error(e);
    } finally {
      setIsPurgingVector(false);
    }
  };

  const isWebCrawlingActive = isLoading && (
    activeAgent?.toLowerCase().includes('crawl') ||
    activeAgent?.toLowerCase().includes('web') ||
    lastUserQuery?.toLowerCase().includes('who is') ||
    lastUserQuery?.toLowerCase().includes('quantum') ||
    lastUserQuery?.toLowerCase().includes('news') ||
    lastUserQuery?.toLowerCase().includes('theory')
  );

  const isAutomationActive = isLoading && (
    activeAgent?.toLowerCase().includes('auto') ||
    activeAgent?.toLowerCase().includes('tool') ||
    activeAgent?.toLowerCase().includes('dom') ||
    lastUserQuery?.toLowerCase().includes('instagram') ||
    lastUserQuery?.toLowerCase().includes('youtube') ||
    lastUserQuery?.toLowerCase().includes('terminal') ||
    lastUserQuery?.toLowerCase().includes('claude') ||
    lastUserQuery?.toLowerCase().includes('open ')
  );

  const handleQuickDispatch = (e) => {
    if (e) e.preventDefault();
    if (!quickInput.trim() || isLoading) return;
    setLastUserQuery(quickInput);
    if (onDispatchPrompt) onDispatchPrompt(quickInput);
    setQuickInput('');
  };

  const handleTestFlow = (prompt) => {
    setLastUserQuery(prompt);
    if (onDispatchPrompt) onDispatchPrompt(prompt);
  };

  return (
    <div className="space-y-4 font-mono select-none">
      
      {/* ==================== 1. TOP INTERACTIVE BENCHMARK & PRESETS ==================== */}
      <div className="retro-box p-3 space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <form onSubmit={handleQuickDispatch} className="flex items-center gap-2 flex-1 max-w-xl">
            <span className="text-red-500 font-bold text-xs">&gt; RUN DIRECTIVE:</span>
            <input
              type="text"
              value={quickInput}
              onChange={(e) => setQuickInput(e.target.value)}
              placeholder="e.g. 'Who is Virat Kohli?', 'Latest news on AI', 'In terminal run Claude'..."
              disabled={isLoading}
              className="flex-1 bg-black border border-zinc-700 px-3 py-1.5 text-xs text-white placeholder-zinc-500 outline-none focus:border-red-500"
            />
            <button
              type="submit"
              disabled={!quickInput.trim() || isLoading}
              className="retro-btn-red px-3 py-1.5 text-xs flex items-center gap-1 disabled:opacity-40"
            >
              {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              <span>DISPATCH</span>
            </button>
          </form>

          <div className="flex items-center gap-2 text-xs">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
            <span className="text-zinc-400 text-[11px]">ACTIVE MULTI-AGENT STATE:</span>
            <span className="text-white font-bold px-2 py-0.5 bg-black border border-red-700 text-[11px]">
              {isLoading ? (activeAgent || 'ORCHESTRATING...') : 'STANDBY READY'}
            </span>
          </div>
        </div>

        {/* Dual Mode Preset Chips: Web Crawling vs. DOM Automation */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-2 border-t border-zinc-800">
          
          {/* Preset Bank A: Live Web Crawling (Background Knowledge + Voice TTS) */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs bg-zinc-950/70 p-1.5 border border-zinc-800">
            <span className="text-red-400 font-bold text-[10px] flex items-center gap-1">
              <Globe className="w-3 h-3 text-red-500" />
              <span>WEB CRAWLING:</span>
            </span>
            <button
              onClick={() => handleTestFlow('Who is Virat Kohli?')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [1. Virat Kohli Bio]
            </button>
            <button
              onClick={() => handleTestFlow('Explain quantum computing')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [2. Quantum Theory]
            </button>
            <button
              onClick={() => handleTestFlow('Latest news on AI')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [3. Live AI News]
            </button>
            <button
              onClick={() => handleTestFlow('Explain Theory of Relativity')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [4. Relativity]
            </button>
          </div>

          {/* Preset Bank B: DOM & System Automation (Workstation & Browser DOM Control) */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs bg-zinc-950/70 p-1.5 border border-zinc-800">
            <span className="text-zinc-300 font-bold text-[10px] flex items-center gap-1">
              <Terminal className="w-3 h-3 text-red-500" />
              <span>DOM AUTOMATION:</span>
            </span>
            <button
              onClick={() => handleTestFlow('Go to Instagram and search for the song')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [5. Instagram Song]
            </button>
            <button
              onClick={() => handleTestFlow('In terminal run Claude')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [6. Claude CLI]
            </button>
            <button
              onClick={() => handleTestFlow('Open Calculator')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [7. Open Calculator]
            </button>
            <button
              onClick={() => handleTestFlow('Search about begin song on YouTube')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [8. YouTube Begin]
            </button>
          </div>

        </div>
      </div>

      {/* ==================== 2. MAIN ORCHESTRATION CANVAS DIAGRAM ==================== */}
      <div className="relative bg-[#1c1c1f] border-2 border-black rounded-lg p-6 shadow-2xl overflow-hidden min-h-[520px]">
        {/* Subtle retro scanline texture */}
        <div className="absolute inset-0 pointer-events-none opacity-40 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.3)_50%)] bg-[length:100%_4px]" />

        {/* Floating Siren Beacons (Exact retro positions) */}
        <div className="absolute top-4 left-72 z-20">
          <SirenBeacon isPulsing={isLoading} />
        </div>
        <div className="absolute top-4 right-12 z-20">
          <SirenBeacon isPulsing={isLoading} />
        </div>
        <div className="absolute top-64 right-10 z-20">
          <SirenBeacon isPulsing={isLoading} />
        </div>
        <div className="absolute top-80 right-48 z-20">
          <SirenBeacon isPulsing={isLoading} />
        </div>
        <div className="absolute bottom-8 left-16 z-20">
          <SirenBeacon isPulsing={isLoading} />
        </div>
        <div className="absolute bottom-28 right-80 z-20">
          <SirenBeacon isPulsing={isLoading} />
        </div>

        {/* Main Grid: Left Environment Box + Right Multi-Tier Engine */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 relative z-10">
          
          {/* ==================== LEFT: ENVIRONMENT v1.0 ==================== */}
          <div className="lg:col-span-4 border-2 border-dashed border-zinc-500 rounded-lg p-4 bg-[#141416]/90 relative flex flex-col justify-between space-y-4">
            <div className="absolute -top-3 left-4 bg-zinc-300 text-black px-2.5 py-0.5 font-black text-xs border border-black shadow">
              ENVIRONMENT v1.0
            </div>

            {/* Top: Person at workstation */}
            <div className="flex items-center justify-between pt-1">
              <UserAtWorkstation />
              <div className="flex-1 ml-2 bg-black border-2 border-red-600 rounded p-2 text-left relative">
                <div className="text-[10px] text-red-500 font-bold uppercase tracking-wider mb-0.5">
                  SYSTEM QUERY?
                </div>
                <div className="text-xs text-white truncate max-w-[150px] font-bold">
                  "{lastUserQuery}"
                </div>
                <div className="absolute -left-2 top-3 w-0 h-0 border-t-4 border-t-transparent border-r-8 border-r-red-600 border-b-4 border-b-transparent" />
              </div>
            </div>

            {/* Middle: Sensors Box */}
            <div className="bg-[#27272a] border border-black rounded p-2 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-red-500 text-base font-bold">🗲</span>
                <span className="text-xs text-white font-bold">Sensors</span>
              </div>
              <div className="text-[10px] text-zinc-300 bg-black px-2 py-0.5 border border-zinc-800 font-bold">
                [CTRL+ALT: ACTIVE]
              </div>
            </div>

            {/* Bottom: AGENT (Robot Avatar with Speech Bubble) */}
            <div className="flex flex-col items-center space-y-2">
              <div className="bg-black border-2 border-red-600 rounded-lg p-2.5 w-full flex items-center justify-center gap-3 relative shadow-[0_0_12px_rgba(239,68,68,0.4)]">
                <span className="absolute -top-2.5 px-2 bg-red-600 text-white font-black text-[10px] uppercase">
                  AGENT CORE
                </span>
                <RobotAgentAvatar isActive={isLoading} />
                <div className="text-left">
                  <div className="text-xs font-black text-white">J.A.R.V.I.S.</div>
                  <div className="text-[10px] text-zinc-400">Ambient AI OS</div>
                  <span className={`text-[9px] font-bold px-1.5 py-0.2 border ${
                    isLoading ? 'bg-red-950 text-red-400 border-red-700 animate-pulse' : 'bg-black text-white border-zinc-700'
                  }`}>
                    {isLoading ? '[EXECUTING]' : '[ONLINE]'}
                  </span>
                </div>
              </div>

              {/* Speech Bubble from Agent */}
              <div className="bg-black border border-red-600 rounded p-2 w-full text-xs text-zinc-200 relative leading-snug min-h-[46px]">
                <div className="text-[9px] text-red-400 font-bold uppercase mb-0.5">&gt; J.A.R.V.I.S. RESPONSE:</div>
                <div className="truncate-2-lines text-[11px] text-white">
                  {briefingText || "Yes, sir. Workstation systems standing by for directives."}
                </div>
              </div>
            </div>
          </div>

          {/* ==================== RIGHT: COGNITIVE ORCHESTRATION PIPELINE ==================== */}
          <div className="lg:col-span-8 flex flex-col justify-between space-y-4">
            
            {/* ROW 1: PERCEPTION ENGINE (Left) + DECISION CORE (Right) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Box 1: PERCEPTION ENGINE */}
              <div className="bg-[#27272a] border-2 border-black rounded-lg p-3 relative shadow-md">
                <div className="absolute -top-3 left-4 bg-zinc-200 text-black px-2.5 py-0.5 font-black text-xs border border-black flex items-center gap-2">
                  <span>PERCEPTION ENGINE</span>
                  <span className="w-6 h-2 bg-red-600 inline-block border border-black" />
                </div>

                <div className="mt-2 text-center text-[10px] text-red-400 font-bold uppercase tracking-wider mb-2">
                  — Inputs —
                </div>

                <div className="bg-[#1c1c1f] border border-black rounded p-2.5 grid grid-cols-3 gap-2 text-center">
                  <div className="flex flex-col items-center">
                    <ImageIcon />
                    <span className="text-[10px] font-bold text-white mt-1">IMAGE</span>
                    <span className="text-[9px] text-zinc-500">Screen</span>
                  </div>
                  <div className="flex flex-col items-center">
                    <DocIcon />
                    <span className="text-[10px] font-bold text-white mt-1">DOC / WEB</span>
                    <span className="text-[9px] text-zinc-500">Live DOM</span>
                  </div>
                  <div className="flex flex-col items-center">
                    <InputDataIcon />
                    <span className="text-[10px] font-bold text-white mt-1">INPUT_DATA</span>
                    <span className="text-[9px] text-zinc-500">Voice/Key</span>
                  </div>
                </div>
              </div>

              {/* Box 2: DECISION CORE */}
              <div className="bg-[#27272a] border-2 border-black rounded-lg p-3 relative shadow-md">
                <div className="absolute -top-3 left-4 bg-zinc-200 text-black px-2.5 py-0.5 font-black text-xs border border-black">
                  DECISION CORE
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3 text-center">
                  <div className="bg-[#1c1c1f] border border-black rounded p-2.5 flex flex-col items-center">
                    <DatabaseIcon />
                    <span className="text-[11px] font-bold text-white mt-1.5">Memory</span>
                    <span className="text-[9px] text-red-400 font-bold">ChromaDB</span>
                  </div>
                  <div className="bg-[#1c1c1f] border border-black rounded p-2.5 flex flex-col items-center">
                    <KnowledgeStackIcon />
                    <span className="text-[11px] font-bold text-white mt-1.5">Knowledge</span>
                    <span className="text-[9px] text-zinc-400 font-bold">Local RAG</span>
                  </div>
                </div>
              </div>
            </div>

            {/* ROW 2: ORCHESTRATION LOGIC (Brain + Neural Net) */}
            <div className="bg-[#27272a] border-2 border-black rounded-lg p-3 relative shadow-md">
              <div className="absolute -top-3 left-4 bg-red-600 text-white px-2.5 py-0.5 font-black text-xs border border-black">
                ORCHESTRATION LOGIC
              </div>

              <div className="mt-3 flex flex-col md:flex-row items-center justify-around gap-4 bg-[#1c1c1f] border border-black rounded p-3">
                <div className="flex items-center gap-3">
                  <BrainIcon />
                  <div>
                    <div className="text-xs font-bold text-white">SUPERVISOR ROUTER</div>
                    <div className="text-[10px] text-red-400 font-bold">qwen2.5:3b (Local)</div>
                    <div className="text-[9px] text-zinc-400">Classifies in &lt;50ms</div>
                  </div>
                </div>

                <div className="text-red-500 font-black text-xl hidden md:block">
                  ➔
                </div>

                <div className="flex items-center gap-3">
                  <NeuralNetIcon />
                  <div>
                    <div className="text-xs font-bold text-white">DEEP INTELLIGENCE</div>
                    <div className="text-[10px] text-red-400 font-bold">deepseek-r1:7b (Local)</div>
                    <div className="text-[9px] text-zinc-400">Chain-of-thought planner</div>
                  </div>
                </div>
              </div>

              {/* Real-time Thought Stream Status */}
              <div className="mt-2 text-[10px] text-zinc-400 flex items-center justify-between px-1">
                <span>&gt; ACTIVE_AGENT: <span className="text-white font-bold">{activeAgent || 'STANDBY'}</span></span>
                <span className="text-red-400 truncate max-w-xs">{currentThought || 'Standing by for prompt.'}</span>
              </div>
            </div>

            {/* ROW 3: DUAL SPECIALIZED ACTION UNITS */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* UNIT A: WEB CRAWLING AGENT */}
              <div className={`p-3 rounded-lg border-2 relative transition ${
                isWebCrawlingActive
                  ? 'bg-red-950/40 border-red-500 shadow-[0_0_15px_rgba(239,68,68,0.5)]'
                  : 'bg-[#27272a] border-black shadow-md'
              }`}>
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <Globe className="w-4 h-4 text-red-500" />
                    <span className="text-xs font-black text-white">WEB CRAWLING AGENT</span>
                  </div>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 border ${
                    isWebCrawlingActive ? 'bg-red-600 text-white animate-pulse border-white' : 'bg-black text-zinc-400 border-zinc-700'
                  }`}>
                    {isWebCrawlingActive ? 'CRAWLING LIVE' : 'IDLE / READY'}
                  </span>
                </div>
                <div className="text-[10px] text-zinc-400 leading-snug">
                  <div>• Engine: <span className="text-white">Crawlee 1.10 + ScrapeGraphAI</span></div>
                  <div>• Research: <span className="text-red-400">Person Bio, Theory, Live News</span></div>
                  <div className="text-[9px] text-zinc-500">Zero desktop browser pop-up</div>
                </div>
              </div>

              {/* UNIT B: DOM AUTOMATION AGENT */}
              <div className={`p-3 rounded-lg border-2 relative transition ${
                isAutomationActive
                  ? 'bg-red-950/40 border-red-500 shadow-[0_0_15px_rgba(239,68,68,0.5)]'
                  : 'bg-[#27272a] border-black shadow-md'
              }`}>
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <Terminal className="w-4 h-4 text-red-500" />
                    <span className="text-xs font-black text-white">DOM AUTOMATION AGENT</span>
                  </div>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 border ${
                    isAutomationActive ? 'bg-red-600 text-white animate-pulse border-white' : 'bg-black text-zinc-400 border-zinc-700'
                  }`}>
                    {isAutomationActive ? 'EXECUTING DOM' : 'IDLE / READY'}
                  </span>
                </div>
                <div className="text-[10px] text-zinc-400 leading-snug">
                  <div>• Engine: <span className="text-white">Playwright DOM + PyAutoGUI</span></div>
                  <div>• Actions: <span className="text-red-400">Instagram, YouTube, Terminal CLI</span></div>
                  <div className="text-[9px] text-zinc-500">Protected by Safety Gatekeeper</div>
                </div>
              </div>

            </div>

          </div>
        </div>

        {/* Footer Signature */}
        <div className="mt-4 pt-3 border-t border-zinc-800 flex items-center justify-between text-zinc-400 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-600 animate-ping" />
            <span className="text-[11px] text-zinc-300 font-bold">
              AUTONOMOUS SIGNAL FEEDBACK LOOP: 100% LOCAL WORKSTATION DEPLOYMENT
            </span>
          </div>

          <div className="flex items-center gap-1.5 font-black text-sm tracking-wider text-white">
            <Sparkles className="w-4 h-4 text-red-500" />
            <span>ORCHESTRATION ENGINE v0.2</span>
          </div>
        </div>
      </div>

      {/* ==================== 3. LIVE AGENT EXECUTION INSPECTOR ==================== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Left 6 Cols: Live Execution Telemetry & Thought Stream */}
        <div className="lg:col-span-6 retro-box p-3 space-y-2">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-1.5">
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-red-500 animate-pulse" />
              <span className="text-xs font-bold text-white">LIVE MULTI-AGENT THOUGHT STREAM</span>
            </div>
            <span className="text-[10px] text-red-400 font-bold bg-black px-2 py-0.5 border border-zinc-800">
              {isLoading ? '[STREAMING]' : '[STANDBY]'}
            </span>
          </div>

          {/* Real-time Thought Box */}
          <div className="bg-black border border-zinc-800 p-2.5 rounded min-h-[90px] text-xs space-y-1.5">
            <div className="text-zinc-500 text-[10px] uppercase">
              Target Directive: <span className="text-zinc-300 font-bold">"{lastUserQuery}"</span>
            </div>
            <div className="text-red-400 font-bold flex items-start gap-1.5">
              <span>&gt;</span>
              <span className="text-white">{currentThought || "All autonomous agent nodes standing by for instructions."}</span>
            </div>
          </div>

          {/* Multi-Step Checklist */}
          {planSteps && planSteps.length > 0 && (
            <div className="bg-zinc-950 border border-zinc-800 p-2 text-xs space-y-1">
              <div className="text-[10px] text-zinc-400 font-bold uppercase mb-1">
                Execution Steps ({planSteps.length}):
              </div>
              {planSteps.map((step, idx) => (
                <div key={idx} className="flex items-center gap-1.5 text-zinc-300 text-[11px]">
                  <CheckCircle2 className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
                  <span>{step}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right 6 Cols: Live Voice & Web Crawling Output Preview */}
        <div className="lg:col-span-6 retro-box p-3 space-y-2">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-1.5">
            <div className="flex items-center gap-2">
              <Volume2 className="w-4 h-4 text-red-500" />
              <span className="text-xs font-bold text-white">LIVE RESPONSE & VOICE OUTPUT</span>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] text-zinc-400">
              <ShieldCheck className="w-3.5 h-3.5 text-zinc-400" />
              <span>Piper Neural Voice</span>
            </div>
          </div>

          {/* Response Text Preview */}
          <div className="bg-black border border-zinc-800 p-2.5 rounded min-h-[90px] max-h-[140px] overflow-y-auto text-xs text-zinc-200">
            {briefingText ? (
              <div className="whitespace-pre-line text-[11px] leading-relaxed">
                {briefingText}
              </div>
            ) : (
              <div className="text-zinc-500 italic text-[11px] pt-4 text-center">
                Spoken voice output and live knowledge report will render here upon agent completion.
              </div>
            )}
          </div>

          {/* Engine Status Ticker */}
          <div className="flex items-center justify-between text-[10px] text-zinc-500 pt-1">
            <span>Crawlee: <span className="text-white">v1.10.3 Active</span></span>
            <span>ScrapeGraphAI: <span className="text-white">v2.3.0 Ready</span></span>
            <span>DOM Engine: <span className="text-white">Playwright Ready</span></span>
          </div>
        </div>

      </div>

      {/* ==================== 4. TRI-MODEL MULTI-AGENT ALLOCATION & RESPONSIBILITY MATRIX ==================== */}
      <div className="retro-box p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 pb-2">
          <div className="flex items-center gap-2">
            <CpuIcon className="w-4 h-4 text-red-500" />
            <span className="text-xs font-black text-white tracking-wider">
              === TRI-MODEL ALLOCATION MATRIX: WHICH MODEL DOES WHAT &amp; HOLDS WHAT AGENTS ===
            </span>
          </div>
          <span className="text-[10px] text-zinc-400 bg-black px-2 py-0.5 border border-zinc-800 font-mono">
            [100% LOCAL-FIRST OLLAMA ARCHITECTURE]
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
          
          {/* Model Card 1: Qwen 2.5 0.5B / 3B */}
          <div className="bg-black border-2 border-red-600/80 rounded p-3 flex flex-col justify-between space-y-3 shadow-md hover:border-red-500 transition">
            <div className="space-y-2">
              <div className="flex items-center justify-between border-b border-zinc-800 pb-1.5">
                <div>
                  <h4 className="text-xs font-black text-white">QWEN 2.5 (0.5B / 3B)</h4>
                  <p className="text-[10px] text-red-400 font-bold uppercase">Edge Fast Router &amp; Intent Engine</p>
                </div>
                <span className="px-1.5 py-0.5 bg-red-950 text-red-400 border border-red-700 text-[9px] font-bold">
                  &lt; 50MS
                </span>
              </div>

              <div>
                <span className="text-[10px] font-bold text-zinc-300 uppercase block mb-1">
                  &gt; What This Model Is Doing:
                </span>
                <p className="text-[11px] text-zinc-400 leading-snug">
                  Acts as the ultra-fast sub-50ms gateway. Ingests raw directives, classifies complexity (simple vs. complex), detects intent categories, and extracts critical parameters (target app, search terms, file names) before spinning up heavy weights.
                </p>
              </div>

              <div>
                <span className="text-[10px] font-bold text-red-400 uppercase block mb-1">
                  &gt; Agents Held Under This Model:
                </span>
                <ul className="text-[11px] text-zinc-300 space-y-1">
                  <li className="flex items-start gap-1.5">
                    <span className="text-red-500 font-black">•</span>
                    <span><strong className="text-white">Supervisor Router Agent:</strong> Classifies and routes tasks to DIRECT_TOOL, DEEP_SEARCH, AUTOMATION, or CODING flows.</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-red-500 font-black">•</span>
                    <span><strong className="text-white">Sensory Input Gatekeeper:</strong> Normalizes Wispr Flow audio transcripts, shortcut keys (Ctrl+Win, Ctrl+Alt), and mobile sync inputs.</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-red-500 font-black">•</span>
                    <span><strong className="text-white">Context Window Trimmer:</strong> Enforces sliding-window memory buffers to prevent token overflow.</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="pt-2 border-t border-zinc-800 flex items-center justify-between text-[10px] text-zinc-500">
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                ONLINE (Local)
              </span>
              <span>Subprocess: Fast C++ GGUF</span>
            </div>
          </div>

          {/* Model Card 2: DeepSeek-R1 7B / Qwen 2.5 Coder */}
          <div className="bg-black border-2 border-zinc-700 rounded p-3 flex flex-col justify-between space-y-3 shadow-md hover:border-zinc-500 transition">
            <div className="space-y-2">
              <div className="flex items-center justify-between border-b border-zinc-800 pb-1.5">
                <div>
                  <h4 className="text-xs font-black text-white">DEEPSEEK-R1 (7B) / CODER</h4>
                  <p className="text-[10px] text-zinc-300 font-bold uppercase">Deep Reasoner &amp; Synthesis Engine</p>
                </div>
                <span className="px-1.5 py-0.5 bg-zinc-900 text-zinc-300 border border-zinc-700 text-[9px] font-bold">
                  128K TOKENS
                </span>
              </div>

              <div>
                <span className="text-[10px] font-bold text-zinc-300 uppercase block mb-1">
                  &gt; What This Model Is Doing:
                </span>
                <p className="text-[11px] text-zinc-400 leading-snug">
                  Powers heavy chain-of-thought task decomposition, multi-step DAG planning, coding synthesis, terminal automation, and headless web research loops. Evaluates error recovery when tools fail.
                </p>
              </div>

              <div>
                <span className="text-[10px] font-bold text-red-400 uppercase block mb-1">
                  &gt; Agents Held Under This Model:
                </span>
                <ul className="text-[11px] text-zinc-300 space-y-1">
                  <li className="flex items-start gap-1.5">
                    <span className="text-red-500 font-black">•</span>
                    <span><strong className="text-white">DAG Task Planner Agent:</strong> Decomposes complex directives into ordered step-by-step dependency checklists.</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-red-500 font-black">•</span>
                    <span><strong className="text-white">Autonomous Developer Agent:</strong> Writes, edits, debugs code files, and checks syntax across directories.</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-red-500 font-black">•</span>
                    <span><strong className="text-white">Live Web Crawling Agent:</strong> Directs Crawlee 1.10 &amp; ScrapeGraphAI for person bios, theories, and live news.</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-red-500 font-black">•</span>
                    <span><strong className="text-white">DOM &amp; OS Automation Agent:</strong> Playwright DOM manipulation (Instagram/YouTube), desktop app opening &amp; CLI commands.</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-red-500 font-black">•</span>
                    <span><strong className="text-white">Safety Policy Sentinel:</strong> Pre-evaluates actions against safety rules to require human approval.</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="pt-2 border-t border-zinc-800 flex items-center justify-between text-[10px] text-zinc-500">
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                ONLINE (Local)
              </span>
              <span>Inference: Self-Reflective CoT</span>
            </div>
          </div>

          {/* Model Card 3: Llama 3.2 1B Instruct */}
          <div className="bg-black border-2 border-zinc-500 rounded p-3 flex flex-col justify-between space-y-3 shadow-md hover:border-zinc-300 transition">
            <div className="space-y-2">
              <div className="flex items-center justify-between border-b border-zinc-800 pb-1.5">
                <div>
                  <h4 className="text-xs font-black text-white">LLAMA 3.2 (1B INSTRUCT)</h4>
                  <p className="text-[10px] text-zinc-300 font-bold uppercase">Executive Voice &amp; Chatbot Persona</p>
                </div>
                <span className="px-1.5 py-0.5 bg-zinc-900 text-white border border-zinc-500 text-[9px] font-bold">
                  PERSONA
                </span>
              </div>

              <div>
                <span className="text-[10px] font-bold text-zinc-300 uppercase block mb-1">
                  &gt; What This Model Is Doing:
                </span>
                <p className="text-[11px] text-zinc-400 leading-snug">
                  Unifies all raw telemetry from tools, scrapers, and agents into a crisp, authoritative J.A.R.V.I.S. voice strictly formatted in '90s retro bullet points. Understands conversational follow-ups and pronouns.
                </p>
              </div>

              <div>
                <span className="text-[10px] font-bold text-red-400 uppercase block mb-1">
                  &gt; Agents Held Under This Model:
                </span>
                <ul className="text-[11px] text-zinc-300 space-y-1">
                  <li className="flex items-start gap-1.5">
                    <span className="text-red-500 font-black">•</span>
                    <span><strong className="text-white">J.A.R.V.I.S. Persona Agent:</strong> Delivers tactical military-grade briefings formatted with retro bullets ([•], [&gt;]).</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-red-500 font-black">•</span>
                    <span><strong className="text-white">Conversational Follow-Up Agent:</strong> Resolves follow-up pronouns ("him", "her", "it", "that", "tell me more") across all conversational subjects via vector database memory lookup.</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <span className="text-red-500 font-black">•</span>
                    <span><strong className="text-white">Speech Synthesis Dispatcher:</strong> Feeds final bullet text into Piper Neural TTS with zero cloud latency.</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="pt-2 border-t border-zinc-800 flex items-center justify-between text-[10px] text-zinc-500">
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                ONLINE (Local)
              </span>
              <span>Tone: '90s Tactical HUD</span>
            </div>
          </div>

        </div>
      </div>

      {/* ==================== 5. HOW IT IS ORCHESTRATED (LANGGRAPH PIPELINE) ==================== */}
      <div className="retro-box p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 pb-2">
          <div className="flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-red-500" />
            <span className="text-xs font-black text-white tracking-wider">
              === HOW IT IS ORCHESTRATED: LANGGRAPH MULTI-AGENT STATEGRAPH PIPELINE ===
            </span>
          </div>
          <span className="text-[10px] text-zinc-400 font-mono">
            [DETERMINISTIC EDGES + AUTONOMOUS AUTO-CORRECTION]
          </span>
        </div>

        {/* 6-Stage Visual Workflow Sequence */}
        <div className="grid grid-cols-1 md:grid-cols-6 gap-2 pt-1 text-xs">
          
          {/* Stage 1 */}
          <div className="bg-zinc-950 border border-zinc-800 p-2.5 rounded space-y-1 relative">
            <div className="flex items-center justify-between">
              <span className="text-red-500 font-black text-[10px]">STAGE 01</span>
              <span className="text-[9px] text-zinc-500">INPUT</span>
            </div>
            <div className="text-white font-bold text-[11px]">SENSORY INGESTION &amp; PRONOUN RESOLVER</div>
            <p className="text-[10px] text-zinc-400 leading-tight">
              Ingests text or Wispr Flow voice (Ctrl+Win). Performs semantic lookup across the dedicated vector database partition (ops_chatbot_memory) to resolve pronouns ("him", "her", "it", "that", "tell me more") for any entity or topic discussed.
            </p>
          </div>

          {/* Stage 2 */}
          <div className="bg-zinc-950 border border-red-900/60 p-2.5 rounded space-y-1 relative">
            <div className="flex items-center justify-between">
              <span className="text-red-500 font-black text-[10px]">STAGE 02</span>
              <span className="text-[9px] text-red-400 font-bold">ROUTER</span>
            </div>
            <div className="text-white font-bold text-[11px]">SUPERVISOR ROUTER (QWEN)</div>
            <p className="text-[10px] text-zinc-400 leading-tight">
              Sub-50ms classifier evaluates intent: DIRECT_TOOL (apps/files), DEEP_CRAWL (research), DOM_AUTO (browser/CLI), or CHATBOT.
            </p>
          </div>

          {/* Stage 3 */}
          <div className="bg-zinc-950 border border-zinc-800 p-2.5 rounded space-y-1 relative">
            <div className="flex items-center justify-between">
              <span className="text-red-500 font-black text-[10px]">STAGE 03</span>
              <span className="text-[9px] text-zinc-500">PLANNING</span>
            </div>
            <div className="text-white font-bold text-[11px]">DEEPSEEK-R1 DAG DECOMPOSITION</div>
            <p className="text-[10px] text-zinc-400 leading-tight">
              For complex tasks, builds ordered execution plan steps. Dispatches to Crawlee or Playwright DOM automation engine.
            </p>
          </div>

          {/* Stage 4 */}
          <div className="bg-zinc-950 border border-red-600/70 p-2.5 rounded space-y-1 relative">
            <div className="flex items-center justify-between">
              <span className="text-red-500 font-black text-[10px]">STAGE 04</span>
              <span className="text-[9px] text-red-400 font-bold">HITL GATE</span>
            </div>
            <div className="text-white font-bold text-[11px]">SAFETY SENTINEL &amp; PERMISSIONS</div>
            <p className="text-[10px] text-zinc-400 leading-tight">
              Intercepts system app launches, directory changes, or CLI executions. Halts for user authorization before proceeding.
            </p>
          </div>

          {/* Stage 5 */}
          <div className="bg-zinc-950 border border-zinc-800 p-2.5 rounded space-y-1 relative">
            <div className="flex items-center justify-between">
              <span className="text-red-500 font-black text-[10px]">STAGE 05</span>
              <span className="text-[9px] text-zinc-500">SYNTHESIS</span>
            </div>
            <div className="text-white font-bold text-[11px]">LLAMA 3.2 J.A.R.V.I.S. BULLET FORMATTER</div>
            <p className="text-[10px] text-zinc-400 leading-tight">
              Aggregates raw outputs and formats the briefing in '90s retro tactical HUD bullets ([•], [&gt;]) with zero cloud latency.
            </p>
          </div>

          {/* Stage 6 */}
          <div className="bg-zinc-950 border border-red-600 p-2.5 rounded space-y-1 relative">
            <div className="flex items-center justify-between">
              <span className="text-red-500 font-black text-[10px]">STAGE 06</span>
              <span className="text-[9px] text-zinc-400">OUTPUT</span>
            </div>
            <div className="text-white font-bold text-[11px]">PIPER TTS &amp; VECTOR DB PARTITION</div>
            <p className="text-[10px] text-zinc-400 leading-tight">
              Plays neural voice and automatically indexes every dialogue turn into the dedicated ops_chatbot_memory vector partition.
            </p>
          </div>

        </div>
      </div>

      {/* ==================== 6. DEDICATED VECTOR DATABASE PARTITION: CHATBOT MEMORY ==================== */}
      <div className="retro-box-red p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800 pb-2">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-red-500" />
            <span className="text-xs font-black text-white tracking-wider">
              === DEDICATED VECTOR DATABASE PARTITION: CHATBOT MEMORY (ops_chatbot_memory) ===
            </span>
          </div>

          {/* Partition Actions: Erase/Purge & Refresh */}
          <div className="flex items-center gap-2">
            <button
              onClick={handlePurgeVectorPartition}
              disabled={isPurgingVector}
              className="retro-btn px-2.5 py-1 text-xs text-red-400 hover:text-white hover:border-red-500 flex items-center gap-1.5 font-bold disabled:opacity-40"
              title="Purge all embeddings from the dedicated chatbot vector partition"
            >
              {isPurgingVector ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
              <span>[ ⟳ PURGE CHATBOT VECTOR DB ]</span>
            </button>

            <button
              onClick={fetchChatbotVectorStats}
              className="retro-btn px-2.5 py-1 text-xs text-zinc-300 hover:text-white flex items-center gap-1.5 font-bold"
              title="Refresh statistics for ops_chatbot_memory partition"
            >
              <RefreshCw className="w-3.5 h-3.5 text-zinc-400" />
              <span>[ REFRESH STATS ]</span>
            </button>
          </div>
        </div>

        {/* Vector Purged Notification Banner */}
        {vectorPurgeAlert && (
          <div className="bg-red-950/90 border border-red-500 text-white text-xs px-3 py-1.5 flex items-center justify-between font-bold animate-pulse">
            <span>[•] DEDICATED CHATBOT VECTOR DATABASE PARTITION PURGED &amp; ZEROED</span>
            <span className="text-[10px] text-red-300">OPS_CHATBOT_MEMORY CLEARED</span>
          </div>
        )}

        {/* Partition Architecture & Isolation Callout */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 text-xs">
          
          {/* Left 8 Cols: Architectural Explanation */}
          <div className="md:col-span-8 bg-black border border-zinc-800 p-3 rounded space-y-2">
            <div className="text-[10px] text-red-500 font-bold uppercase tracking-wider flex items-center gap-1.5">
              <HardDrive className="w-3.5 h-3.5" />
              <span>PARTITION ARCHITECTURE &amp; ZERO-POLLUTION ISOLATION</span>
            </div>
            <p className="text-zinc-300 text-[11px] leading-relaxed">
              The <strong className="text-white">ops_chatbot_memory</strong> vector collection is completely segregated from the codebase index (<code className="text-red-400">ops_codebase</code>) and documentation (<code className="text-zinc-400">ops_docs</code>). Chatbot multi-turn conversations and follow-up embeddings reside solely in this dedicated partition, ensuring conversational dialogue never pollutes project code search or RAG operations.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 border-t border-zinc-900 text-[10px]">
              <div>
                <span className="text-zinc-500 block">COLLECTION NAME:</span>
                <span className="text-white font-bold">ops_chatbot_memory</span>
              </div>
              <div>
                <span className="text-zinc-500 block">STORAGE ENGINE:</span>
                <span className="text-white font-bold">Local ChromaDB</span>
              </div>
              <div>
                <span className="text-zinc-500 block">EMBEDDING MODEL:</span>
                <span className="text-white font-bold">all-MiniLM-L6-v2 (384-d)</span>
              </div>
              <div>
                <span className="text-zinc-500 block">ISOLATION STATUS:</span>
                <span className="text-emerald-400 font-bold">STRICTLY PARTITIONED</span>
              </div>
            </div>
          </div>

          {/* Right 4 Cols: Live Telemetry Badges */}
          <div className="md:col-span-4 bg-black border border-zinc-800 p-3 rounded flex flex-col justify-between space-y-2">
            <div className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider">
              PARTITION LIVE TELEMETRY
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 text-[11px]">ACTIVE SESSION:</span>
                <span className="text-white font-mono text-[10px] bg-zinc-900 px-1.5 py-0.5 border border-zinc-800 truncate max-w-[130px]">
                  {sessionId || 'GLOBAL'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 text-[11px]">STORED CHAT VECTORS:</span>
                <span className="text-red-400 font-mono text-sm font-black">
                  {vectorPartitionStats.total_chatbot_vectors ?? 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 text-[11px]">SEARCH LATENCY:</span>
                <span className="text-white font-mono text-[11px]">&lt; 12 ms</span>
              </div>
            </div>
            <div className="pt-1.5 border-t border-zinc-900 text-[9px] text-zinc-500">
              * Purged automatically upon browser reload or via the Erase Memory button.
            </div>
          </div>

        </div>

        {/* Live Vector Feed / Table */}
        <div className="bg-black border border-zinc-800 rounded p-2.5 space-y-1.5 text-xs">
          <div className="flex items-center justify-between pb-1 border-b border-zinc-800 text-[10px] text-zinc-400">
            <span>DEDICATED PARTITION ENTRIES (RECENT EMBEDDINGS):</span>
            <span className="text-zinc-500">MAX 25 VECTORS</span>
          </div>

          {vectorPartitionStats.entries && vectorPartitionStats.entries.length > 0 ? (
            <div className="space-y-1 max-h-[160px] overflow-y-auto font-mono text-[11px]">
              {vectorPartitionStats.entries.map((entry, idx) => (
                <div key={idx} className="p-1.5 bg-zinc-950 border border-zinc-900 flex items-start justify-between gap-2">
                  <div className="flex-1 truncate">
                    <span className="text-red-500 font-bold uppercase mr-2">[{entry.role || 'USER'}]:</span>
                    <span className="text-zinc-200">{entry.text}</span>
                  </div>
                  <span className="text-[9px] text-zinc-600 flex-shrink-0">
                    {entry.id ? entry.id.slice(-8) : ''}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-4 text-center text-zinc-600 text-[11px] italic">
              [•] DEDICATED CHATBOT PARTITION IS CURRENTLY ZEROED // ZERO PERSISTED VECTORS
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
