import React, { useState } from 'react';
import { Sparkles, Loader2 } from 'lucide-react';
import { retroSoundEngine } from '../utils/retroSounds';

// ==================== PIXEL ART SVG ICONS ====================

const SirenBeacon = ({ className = "w-4 h-4", isPulsing = false }) => (
  <div className={`relative inline-block ${className} ${isPulsing ? 'animate-bounce' : ''}`}>
    <svg viewBox="0 0 24 24" className="w-full h-full drop-shadow-[0_0_6px_rgba(239,68,68,0.8)]">
      <rect x="5" y="16" width="14" height="4" fill="#27272a" stroke="#000000" strokeWidth="1" />
      <path d="M7 16 C7 9, 17 9, 17 16 Z" fill="#ef4444" stroke="#000000" strokeWidth="1" />
      <path d="M9 13 C9 11, 12 10, 14 10" stroke="#ffffff" strokeWidth="1.2" strokeLinecap="round" fill="none" />
      <line x1="12" y1="5" x2="12" y2="8" stroke="#ef4444" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="4" y1="8" x2="7" y2="10" stroke="#ef4444" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="20" y1="8" x2="17" y2="10" stroke="#ef4444" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  </div>
);

// Feature 1 Icon: Magnifying Glass + Filter Funnel
const MagnifyingFunnelIcon = () => (
  <svg viewBox="0 0 48 40" className="w-12 h-10 flex-shrink-0">
    {/* Magnifying Glass */}
    <circle cx="16" cy="16" r="9" fill="#09090b" stroke="#ef4444" strokeWidth="2.5" />
    <circle cx="16" cy="16" r="6" fill="#18181b" />
    <path d="M13 13 C13 11, 15 9, 17 9" stroke="#ffffff" strokeWidth="1.2" strokeLinecap="round" fill="none" />
    <line x1="23" y1="23" x2="31" y2="31" stroke="#ef4444" strokeWidth="3" strokeLinecap="round" />
    {/* Filter Funnel */}
    <polygon points="34,8 46,8 42,16 42,24 38,22 38,16" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    {/* Sparkles */}
    <rect x="28" y="6" width="2" height="2" fill="#ffffff" />
    <rect x="30" y="10" width="2" height="2" fill="#ffffff" />
  </svg>
);

// Feature 2 Icon: Bar Chart with Rising Trend Arrow
const BarChartTrendIcon = () => (
  <svg viewBox="0 0 48 40" className="w-12 h-10 flex-shrink-0">
    {/* Axes */}
    <line x1="6" y1="34" x2="42" y2="34" stroke="#000000" strokeWidth="2" />
    <line x1="6" y1="6" x2="6" y2="34" stroke="#000000" strokeWidth="2" />
    {/* Bars */}
    <rect x="10" y="24" width="5" height="10" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    <rect x="18" y="18" width="5" height="16" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    <rect x="26" y="12" width="5" height="22" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    <rect x="34" y="8" width="5" height="26" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    {/* Upward Zigzag Arrow */}
    <polyline points="10,20 20,14 28,10 38,4" stroke="#000000" strokeWidth="2.5" fill="none" strokeLinecap="round" />
    <polygon points="36,2 42,3 40,8" fill="#000000" />
  </svg>
);

// Feature 3 Icon: Cloud with Red Bidirectional Sync Arrows
const CloudSyncIcon = () => (
  <svg viewBox="0 0 48 40" className="w-12 h-10 flex-shrink-0">
    {/* Cloud Shape */}
    <path
      d="M12 26 C8 26, 6 22, 9 18 C8 12, 16 10, 19 13 C23 7, 34 8, 35 14 C39 14, 42 18, 39 23 C41 26, 38 27, 36 27 Z"
      fill="#09090b"
      stroke="#ffffff"
      strokeWidth="1.8"
    />
    {/* Up Arrow */}
    <line x1="20" y1="36" x2="20" y2="24" stroke="#ef4444" strokeWidth="2.5" />
    <polyline points="16,28 20,23 24,28" stroke="#ef4444" strokeWidth="2.5" fill="none" strokeLinecap="round" />
    {/* Down Arrow */}
    <line x1="28" y1="24" x2="28" y2="36" stroke="#ef4444" strokeWidth="2.5" />
    <polyline points="24,32 28,37 32,32" stroke="#ef4444" strokeWidth="2.5" fill="none" strokeLinecap="round" />
  </svg>
);

// Feature 4 Icon: Stacked Documents with Red PDF Tag
const DocPdfIcon = () => (
  <svg viewBox="0 0 48 40" className="w-12 h-10 flex-shrink-0">
    {/* Back Page */}
    <rect x="8" y="6" width="22" height="28" fill="#27272a" stroke="#ffffff" strokeWidth="1.5" rx="1" />
    {/* Front Page */}
    <rect x="14" y="10" width="22" height="26" fill="#09090b" stroke="#ffffff" strokeWidth="1.5" rx="1" />
    <line x1="18" y1="16" x2="30" y2="16" stroke="#ffffff" strokeWidth="1.5" />
    <line x1="18" y1="21" x2="30" y2="21" stroke="#ffffff" strokeWidth="1.5" />
    <line x1="18" y1="26" x2="26" y2="26" stroke="#ffffff" strokeWidth="1.5" />
    {/* Red PDF Badge */}
    <rect x="24" y="25" width="16" height="10" fill="#ef4444" stroke="#000000" strokeWidth="1" rx="1" />
    <text x="26" y="32" fill="#ffffff" fontSize="6" fontWeight="bold" fontFamily="monospace">PDF</text>
  </svg>
);

// Feature 5 Icon: Team Avatars with Speech Bubble
const CollabChatIcon = () => (
  <svg viewBox="0 0 48 40" className="w-12 h-10 flex-shrink-0">
    {/* User 1 */}
    <circle cx="14" cy="24" r="5" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    <path d="M6 36 C6 31, 22 31, 22 36 Z" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    {/* User 2 */}
    <circle cx="34" cy="24" r="5" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    <path d="M26 36 C26 31, 42 31, 42 36 Z" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    {/* Chat Bubble */}
    <rect x="22" y="6" width="16" height="12" rx="2" fill="#09090b" stroke="#ffffff" strokeWidth="1.5" />
    <line x1="26" y1="10" x2="34" y2="10" stroke="#ef4444" strokeWidth="1.2" />
    <line x1="26" y1="14" x2="31" y2="14" stroke="#ffffff" strokeWidth="1.2" />
    <polygon points="26,18 24,22 29,18" fill="#09090b" stroke="#ffffff" strokeWidth="1" />
  </svg>
);

// Feature 6 Icon: Dual Avatars & Chat Tasks
const DesktopChatIcon = () => (
  <svg viewBox="0 0 48 40" className="w-12 h-10 flex-shrink-0">
    {/* User 1 */}
    <circle cx="16" cy="20" r="5" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    <path d="M8 32 C8 27, 24 27, 24 32 Z" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    {/* User 2 */}
    <circle cx="32" cy="20" r="5" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    <path d="M24 32 C24 27, 40 27, 40 32 Z" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    {/* Top Speech bubble */}
    <rect x="18" y="4" width="14" height="10" rx="2" fill="#09090b" stroke="#ffffff" strokeWidth="1.5" />
    <line x1="21" y1="7" x2="28" y2="7" stroke="#ef4444" strokeWidth="1" />
    <line x1="21" y1="10" x2="26" y2="10" stroke="#ffffff" strokeWidth="1" />
  </svg>
);

// Feature 7 Icon: Plugs & Connectors
const PlugConnectIcon = () => (
  <svg viewBox="0 0 48 40" className="w-12 h-10 flex-shrink-0">
    {/* Top Left Plug */}
    <rect x="6" y="8" width="12" height="10" rx="1" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    <line x1="18" y1="11" x2="22" y2="11" stroke="#000000" strokeWidth="2" />
    <line x1="18" y1="15" x2="22" y2="15" stroke="#000000" strokeWidth="2" />
    {/* Right Female Socket */}
    <rect x="24" y="10" width="10" height="12" rx="1" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    <rect x="22" y="12" width="2" height="8" fill="#000000" />
    {/* Bottom USB Cable Plug */}
    <rect x="8" y="24" width="12" height="8" rx="1" fill="#ef4444" stroke="#000000" strokeWidth="1" />
    <rect x="20" y="25" width="6" height="6" fill="#d4d4d8" stroke="#000000" strokeWidth="1" />
    {/* Dashed connector line */}
    <line x1="26" y1="28" x2="34" y2="28" stroke="#ffffff" strokeWidth="1.5" strokeDasharray="2,2" />
  </svg>
);

// Center Brain Icon
const CenterBrainNode = () => (
  <svg viewBox="0 0 54 44" className="w-12 h-10 animate-pulse">
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

// ==================== MAIN COMPONENT ====================

export default function OpsFeatureIndexTab({ onDispatchPrompt, onOpenMobile, onToggleVoice }) {
  const [activeStatus, setActiveStatus] = useState('ALL SYSTEMS GO');
  const [activeFeature, setActiveFeature] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);

  const handleTriggerFeature = async (featureName, promptAction) => {
    setActiveFeature(featureName);
    setIsExecuting(true);
    setActiveStatus(`EXECUTING: ${featureName.toUpperCase()}`);
    retroSoundEngine.playAppear();

    try {
      if (promptAction === 'MOBILE') {
        if (onOpenMobile) onOpenMobile();
        setActiveStatus('PAIRED WITH MOBILE COMPANION');
      } else if (onDispatchPrompt) {
        await onDispatchPrompt(promptAction);
        setActiveStatus(`DONE: ${featureName.toUpperCase()}`);
      }
    } catch (e) {
      setActiveStatus(`ERROR: ${e.message}`);
    } finally {
      setIsExecuting(false);
      setTimeout(() => {
        setActiveStatus('ALL SYSTEMS GO');
        setActiveFeature(null);
      }, 4000);
    }
  };

  return (
    <div className="space-y-4 font-mono select-none">
      {/* ==================== APPLICATION FEATURES CANVAS ==================== */}
      <div className="relative bg-[#1c1c1f] border-2 border-black rounded-lg p-6 shadow-2xl overflow-hidden min-h-[640px]">
        {/* Subtle scanline overlay */}
        <div className="absolute inset-0 pointer-events-none opacity-40 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.3)_50%)] bg-[length:100%_4px]" />

        {/* Floating Siren Beacons (Exact positions as photo) */}
        <div className="absolute top-4 left-10 z-20">
          <SirenBeacon isPulsing={isExecuting} />
        </div>
        <div className="absolute top-4 left-32 z-20">
          <SirenBeacon isPulsing={isExecuting} />
        </div>
        <div className="absolute top-4 right-32 z-20">
          <SirenBeacon isPulsing={isExecuting} />
        </div>
        <div className="absolute top-4 right-10 z-20">
          <SirenBeacon isPulsing={isExecuting} />
        </div>
        <div className="absolute top-72 right-12 z-20">
          <SirenBeacon isPulsing={isExecuting} />
        </div>
        <div className="absolute bottom-60 right-64 z-20">
          <SirenBeacon isPulsing={isExecuting} />
        </div>

        {/* ==================== HEADER BANNER ==================== */}
        <div className="flex items-center justify-center mb-6 relative z-10">
          <div className="inline-flex items-center bg-[#27272a] border-2 border-black rounded-md overflow-hidden shadow-lg">
            <div className="bg-[#ef4444] px-4 py-1.5 text-white font-black text-sm tracking-wider flex items-center gap-1.5">
              <span>APPLICATION FEATURES</span>
            </div>
            <div className="bg-[#e4e4e7] px-4 py-1.5 text-black font-black text-sm tracking-wider">
              <span>DASHBOARD</span>
            </div>
          </div>
        </div>

        {/* ==================== THE 3-ROW FEATURES FLOW GRID ==================== */}
        <div className="space-y-4 relative z-10">
          
          {/* ROW 1: FEATURE 1 ➔ FEATURE 2 ➔ FEATURE 3 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
            
            {/* FEATURE 1: SMART SEARCH & FILTER */}
            <div
              onClick={() => handleTriggerFeature('Universal Launcher', 'Open Instagram')}
              className={`bg-[#27272a] border-2 border-black rounded-lg p-3 relative shadow-md cursor-pointer hover:border-red-500 transition ${
                activeFeature === 'Universal Launcher' ? 'ring-2 ring-red-500 bg-[#323238]' : ''
              }`}
            >
              <div className="absolute -top-3 left-3 bg-[#fca5a5] text-black px-2 py-0.5 font-black text-[10px] border border-black">
                FEATURE 1: SMART SEARCH &amp; FILTER
              </div>
              <div className="flex items-center gap-3 pt-2">
                <MagnifyingFunnelIcon />
                <div>
                  <div className="text-xs font-bold text-white">Find data instantly.</div>
                  <div className="text-xs text-zinc-300">Filter by category.</div>
                  <div className="text-[10px] text-red-400 font-bold mt-1">[Click: Open Instagram]</div>
                </div>
              </div>
            </div>

            {/* FEATURE 2: REAL-TIME ANALYTICS */}
            <div
              onClick={() => handleTriggerFeature('Real-Time Analytics', 'Explain O.P.S. architecture')}
              className={`bg-[#27272a] border-2 border-black rounded-lg p-3 relative shadow-md cursor-pointer hover:border-red-500 transition ${
                activeFeature === 'Real-Time Analytics' ? 'ring-2 ring-red-500 bg-[#323238]' : ''
              }`}
            >
              <div className="absolute -top-3 left-3 bg-[#fca5a5] text-black px-2 py-0.5 font-black text-[10px] border border-black">
                FEATURE 2: REAL-TIME ANALYTICS
              </div>
              <div className="flex items-center gap-3 pt-2">
                <BarChartTrendIcon />
                <div>
                  <div className="text-xs font-bold text-white">Live performance metrics.</div>
                  <div className="text-xs text-zinc-300">Instant insights.</div>
                  <div className="text-[10px] text-red-400 font-bold mt-1">[Click: System Health]</div>
                </div>
              </div>
            </div>

            {/* FEATURE 3: CLOUD SYNC / MOBILE SYNC */}
            <div
              onClick={() => handleTriggerFeature('Mobile Companion', 'MOBILE')}
              className={`bg-[#27272a] border-2 border-black rounded-lg p-3 relative shadow-md cursor-pointer hover:border-red-500 transition ${
                activeFeature === 'Mobile Companion' ? 'ring-2 ring-red-500 bg-[#323238]' : ''
              }`}
            >
              <div className="absolute -top-3 left-3 bg-[#fca5a5] text-black px-2 py-0.5 font-black text-[10px] border border-black">
                FEATURE 3: CLOUD SYNC
              </div>
              <div className="flex items-center gap-3 pt-2">
                <CloudSyncIcon />
                <div>
                  <div className="text-xs font-bold text-white">Access data from any device.</div>
                  <div className="text-xs text-zinc-300">Secure storage.</div>
                  <div className="text-[10px] text-red-400 font-bold mt-1">[Click: Open Pairing Drawer]</div>
                </div>
              </div>
            </div>

          </div>

          {/* ROW 2: FEATURE 4 (Left) ↔ BRAIN NODE (Center) ➔ FEATURE 5 (Right) */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
            
            {/* FEATURE 4: AUTOMATED REPORTING (Left) */}
            <div
              onClick={() => handleTriggerFeature('Automated Reporting', 'Tell me a witty quote in J.A.R.V.I.S. style')}
              className={`md:col-span-5 bg-[#27272a] border-2 border-black rounded-lg p-3 relative shadow-md cursor-pointer hover:border-red-500 transition ${
                activeFeature === 'Automated Reporting' ? 'ring-2 ring-red-500 bg-[#323238]' : ''
              }`}
            >
              <div className="absolute -top-3 left-3 bg-[#fca5a5] text-black px-2 py-0.5 font-black text-[10px] border border-black">
                FEATURE 4:
              </div>
              <div className="flex items-center gap-3 pt-2">
                <DocPdfIcon />
                <div>
                  <div className="text-xs font-black text-white uppercase">AUTOMATED REPORTING</div>
                  <div className="text-xs text-zinc-300 leading-snug">Generate and schedule custom reports.</div>
                  <div className="text-[10px] text-red-400 font-bold mt-1">[Click: Executive Briefing]</div>
                </div>
              </div>
            </div>

            {/* CENTER BRAIN NODE WITH BIDIRECTIONAL ARROWS */}
            <div className="md:col-span-2 flex items-center justify-center py-2">
              <div className="flex items-center gap-1">
                <span className="text-red-500 font-black text-base hidden md:inline">◄</span>
                <CenterBrainNode />
                <span className="text-red-500 font-black text-base hidden md:inline">►</span>
              </div>
            </div>

            {/* FEATURE 5: COLLABORATION TOOLS (Right) */}
            <div
              onClick={() => handleTriggerFeature('Collaboration Tools', 'Check security permission gatekeeper')}
              className={`md:col-span-5 bg-[#27272a] border-2 border-black rounded-lg p-3 relative shadow-md cursor-pointer hover:border-red-500 transition ${
                activeFeature === 'Collaboration Tools' ? 'ring-2 ring-red-500 bg-[#323238]' : ''
              }`}
            >
              <div className="absolute -top-3 left-3 bg-[#fca5a5] text-black px-2 py-0.5 font-black text-[10px] border border-black">
                FEATURE 5:
              </div>
              <div className="flex items-center gap-3 pt-2">
                <CollabChatIcon />
                <div>
                  <div className="text-xs font-black text-white uppercase">COLLABORATION TOOLS</div>
                  <div className="text-xs text-zinc-300 leading-snug">Team chat, tasks, and project sharing.</div>
                  <div className="text-[10px] text-red-400 font-bold mt-1">[Click: HITL Approval Guard]</div>
                </div>
              </div>
            </div>

          </div>

          {/* ROW 3: FEATURE 6 (Left) ➔ FEATURE 7 (Center) ➔ STATUS MONITOR (Right) */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
            
            {/* FEATURE 6: AUTOMATED REPORTING / TASKS */}
            <div
              onClick={() => handleTriggerFeature('Task Connectors', 'Open Calculator')}
              className={`md:col-span-4 bg-[#27272a] border-2 border-black rounded-lg p-3 relative shadow-md cursor-pointer hover:border-red-500 transition ${
                activeFeature === 'Task Connectors' ? 'ring-2 ring-red-500 bg-[#323238]' : ''
              }`}
            >
              <div className="absolute -top-3 left-3 bg-[#fca5a5] text-black px-2 py-0.5 font-black text-[10px] border border-black">
                FEATURE 4:
              </div>
              <div className="flex items-center gap-3 pt-2">
                <DesktopChatIcon />
                <div>
                  <div className="text-xs font-black text-white uppercase">AUTOMATED REPORTING</div>
                  <div className="text-xs text-zinc-300 leading-snug">Connect to tasks, schedule custom reports.</div>
                  <div className="text-[10px] text-red-400 font-bold mt-1">[Click: Launch Calculator]</div>
                </div>
              </div>
            </div>

            {/* FEATURE 7: API INTEGRATION HUB */}
            <div
              onClick={() => handleTriggerFeature('API Integration Hub', 'dir backend')}
              className={`md:col-span-4 bg-[#27272a] border-2 border-black rounded-lg p-3 relative shadow-md cursor-pointer hover:border-red-500 transition ${
                activeFeature === 'API Integration Hub' ? 'ring-2 ring-red-500 bg-[#323238]' : ''
              }`}
            >
              <div className="absolute -top-3 left-3 bg-[#fca5a5] text-black px-2 py-0.5 font-black text-[10px] border border-black">
                FEATURE 6:
              </div>
              <div className="flex items-center gap-3 pt-2">
                <PlugConnectIcon />
                <div>
                  <div className="text-xs font-black text-white uppercase">API INTEGRATION HUB</div>
                  <div className="text-xs text-zinc-300 leading-snug">Connect to external services and tools.</div>
                  <div className="text-[10px] text-red-400 font-bold mt-1">[Click: Terminal Execution]</div>
                </div>
              </div>
            </div>

            {/* STATUS MONITOR: GLOWING RED CRT SCREEN */}
            <div className="md:col-span-4 bg-[#121214] border-2 border-black rounded-lg p-3.5 flex flex-col items-center justify-center text-center shadow-2xl relative overflow-hidden">
              <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1">
                SYSTEM TELEMETRY
              </div>
              <div className="text-sm font-black text-red-600 tracking-wider">
                STATUS:
              </div>
              <div className="text-base font-black text-red-500 tracking-wider mt-0.5 drop-shadow-[0_0_8px_rgba(239,68,68,0.7)] animate-pulse">
                {activeStatus}
              </div>
              <div className="mt-1 text-[9px] text-zinc-500">
                100% OFFLINE LOCAL ARCHITECTURE
              </div>
            </div>

          </div>

        </div>

        {/* ==================== BOTTOM SIGNATURE ==================== */}
        <div className="mt-6 pt-3 border-t border-zinc-800 flex items-center justify-between text-zinc-400 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-600 animate-ping" />
            <span className="text-[11px] text-zinc-300 font-bold">
              CLICK ANY FEATURE BLOCK TO EXECUTE LIVE CAPABILITY
            </span>
          </div>

          <div className="flex items-center gap-1.5 font-black text-sm tracking-wider text-white">
            <Sparkles className="w-4 h-4 text-red-500" />
            <span>ORCHESTRATION ENGINE v0.1</span>
          </div>
        </div>

      </div>
    </div>
  );
}
