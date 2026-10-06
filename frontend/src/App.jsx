import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Activity,
  Shield,
  Smartphone,
  Cpu,
  Power,
  Volume2,
  Terminal,
  Radio,
  Eye
} from 'lucide-react';

import LiveConnectionStatus from './components/LiveConnectionStatus';
import OpsCommandCore from './components/OpsCommandCore';
import OpsTriModelStatus from './components/OpsTriModelStatus';
import OpsTerminalConsole from './components/OpsTerminalConsole';
import OpsBriefingCard from './components/OpsBriefingCard';
import OpsMobileDrawer from './components/OpsMobileDrawer';
import OpsLiveOrchestrationTab from './components/OpsLiveOrchestrationTab';
import OpsUserMemoriesTab from './components/OpsUserMemoriesTab';
import OpsHeart from './components/OpsHeart';
import OpsSplashClean from './components/OpsSplashClean';
import OpsSecurityModal from './components/OpsSecurityModal';
import { retroSoundEngine } from './utils/retroSounds';


export default function App() {
  // Splash Screen Display State (5 second retro intro on boot)
  const [showSplash, setShowSplash] = useState(true);
  const handleSplashDone = useCallback(() => setShowSplash(false), []);

  // Temporary Chat Session Identifier (RAM-only; reloads create a fresh ID automatically)
  const [sessionId, setSessionId] = useState(() => 'sess_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9));

  // Backend & WS Status
  const [backendHealth, setBackendHealth] = useState('checking');
  const [wsStatuses, setWsStatuses] = useState({
    agent: false,
    permissions: false,
    terminal: false,
    mobile: false
  });

  // Autonomous Pipeline State
  const [isLoading, setIsLoading] = useState(false);
  const [activeAgent, setActiveAgent] = useState('');
  const [currentThought, setCurrentThought] = useState('');
  const [planSteps, setPlanSteps] = useState([]);
  const [activeCategory, setActiveCategory] = useState('');
  const [briefingText, setBriefingText] = useState('');
  const [currentTaskPrompt, setCurrentTaskPrompt] = useState('');
  const [conversationHistory, setConversationHistory] = useState([]);

  // Feeds
  const [searchResults, setSearchResults] = useState([]);
  const [lastScrape, setLastScrape] = useState(null);
  const [terminalLogs, setTerminalLogs] = useState([]);
  const [activePermissionReq, setActivePermissionReq] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);

  // Voice & UI Modals & Navigation Tabs
  const [isListening, setIsListening] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('cockpit'); // 'cockpit', 'orchestration'

  // WebSocket references
  const agentWs = useRef(null);
  const permWs = useRef(null);
  const termWs = useRef(null);
  const mobileWs = useRef(null);

  const getWsUrl = (path) => {
    const loc = window.location;
    const protocol = loc.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${loc.host}${path}`;
  };

  const checkHealth = async () => {
    try {
      const resp = await fetch('/api/v1/health/');
      if (resp.ok) setBackendHealth('online');
      else setBackendHealth('error');
    } catch {
      setBackendHealth('offline');
    }
  };

  const loadAuditLogs = async () => {
    try {
      const resp = await fetch('/api/v1/audit/logs/');
      if (resp.ok) {
        const data = await resp.json();
        setAuditLogs(data.results || data || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Connect WebSockets
  useEffect(() => {
    checkHealth();
    loadAuditLogs();
    const interval = setInterval(checkHealth, 10000);

    // 1. Agent WebSocket
    const connectAgentWs = () => {
      try {
        const ws = new WebSocket(getWsUrl('/ws/agent/'));
        agentWs.current = ws;
        ws.onopen = () => setWsStatuses((prev) => ({ ...prev, agent: true }));
        ws.onclose = () => {
          setWsStatuses((prev) => ({ ...prev, agent: false }));
          setTimeout(connectAgentWs, 3000);
        };
        ws.onmessage = (e) => {
          try {
            const data = JSON.parse(e.data);
            const timeStr = new Date().toLocaleTimeString();
            if (data.event === 'task_started') {
              setIsLoading(true);
              setActiveAgent(data.agent || 'Prompt Template Agent');
              setCurrentThought(data.thought || `Directive received: "${data.prompt}"`);
              if (data.prompt) setCurrentTaskPrompt(data.prompt);
              setBriefingText('');
              setPlanSteps([]);
              setTerminalLogs((prev) => [
                ...prev.slice(-150),
                { stream: 'ops_event', data: `>> [TASK INITIATED] "${data.prompt || 'Directive'}"`, timestamp: timeStr }
              ]);
            } else if (data.event === 'agent_thought') {
              setIsLoading(true);
              setCurrentThought(`${data.agent}: ${data.thought}`);
              setActiveAgent(data.agent || '');
              setTerminalLogs((prev) => [
                ...prev.slice(-150),
                { stream: 'ops_thought', data: `[${data.agent || 'AGENT'}] ${data.thought}`, timestamp: timeStr }
              ]);
            } else if (data.event === 'agent_plan') {
              setPlanSteps(data.plan || data.plan_steps || []);
              setTerminalLogs((prev) => [
                ...prev.slice(-150),
                { stream: 'ops_thought', data: `[PLAN] ${(data.plan || []).join(' -> ')}`, timestamp: timeStr }
              ]);
            } else if (data.event === 'agent_status') {
              if (data.status === 'EXECUTING' || data.status === 'THINKING') {
                setIsLoading(true);
              } else if (data.status === 'IDLE' || data.status === 'COMPLETED') {
                setIsLoading(false);
              }
            } else if (data.event === 'task_completed') {
              setBriefingText(data.final_answer || '');
              if (data.plan && data.plan.length > 0) {
                setPlanSteps(data.plan);
              }
              setTerminalLogs((prev) => [
                ...prev.slice(-150),
                { stream: 'ops_success', data: `[TASK COMPLETED] ${data.intent || 'SUCCESS'}`, timestamp: timeStr }
              ]);
              if (
                data.intent === 'WORKSTATION_MEMORY_CAPTURE' ||
                data.category === 'WORKSTATION_MEMORY_CAPTURE' ||
                (data.final_answer && (data.final_answer.includes('COMMITTED TO POSTGRESQL') || data.final_answer.includes('WORKSTATION MEMORY COMMITTED')))
              ) {
                retroSoundEngine.playMemoryStore();
                window.dispatchEvent(new CustomEvent('ops_memory_added'));
              }
              setIsLoading(false);
              setActiveAgent('');
              setCurrentThought('Task execution complete.');
              loadAuditLogs();
            } else if (data.event === 'memory_added') {
              retroSoundEngine.playMemoryStore();
              window.dispatchEvent(new CustomEvent('ops_memory_added'));
            } else if (data.event === 'task_failed') {
              setBriefingText(`Execution Error: ${data.error}`);
              setIsLoading(false);
              setActiveAgent('');
              setCurrentThought(`Execution Failed: ${data.error}`);
              setTerminalLogs((prev) => [
                ...prev.slice(-150),
                { stream: 'stderr', data: `[ERROR] ${data.error}`, timestamp: timeStr }
              ]);
            }
          } catch (err) {
            console.error(err);
          }
        };
      } catch (err) {
        console.error(err);
      }
    };

    // 2. Permissions WebSocket
    const connectPermWs = () => {
      try {
        const ws = new WebSocket(getWsUrl('/ws/permissions/'));
        permWs.current = ws;
        ws.onopen = () => setWsStatuses((prev) => ({ ...prev, permissions: true }));
        ws.onclose = () => {
          setWsStatuses((prev) => ({ ...prev, permissions: false }));
          setTimeout(connectPermWs, 3000);
        };
        ws.onmessage = (e) => {
          try {
            const data = JSON.parse(e.data);
            if (data.event === 'permission_request') {
              setActivePermissionReq(data);
            } else if (data.event === 'permission_resolved' || data.event === 'permission_acknowledged') {
              setActivePermissionReq(null);
              loadAuditLogs();
            }
          } catch (err) {
            console.error(err);
          }
        };
      } catch (err) {
        console.error(err);
      }
    };

    // 3. Terminal WebSocket
    const connectTermWs = () => {
      try {
        const ws = new WebSocket(getWsUrl('/ws/terminal/'));
        termWs.current = ws;
        ws.onopen = () => setWsStatuses((prev) => ({ ...prev, terminal: true }));
        ws.onclose = () => {
          setWsStatuses((prev) => ({ ...prev, terminal: false }));
          setTimeout(connectTermWs, 3000);
        };
        ws.onmessage = (e) => {
          try {
            const data = JSON.parse(e.data);
            if (data.event === 'terminal_log') {
              setTerminalLogs((prev) => [...prev.slice(-150), data]);
            }
          } catch (err) {
            console.error(err);
          }
        };
      } catch (err) {
        console.error(err);
      }
    };

    // 4. Mobile WebSocket
    const connectMobileWs = () => {
      try {
        const ws = new WebSocket(getWsUrl('/ws/mobile/'));
        mobileWs.current = ws;
        ws.onopen = () => setWsStatuses((prev) => ({ ...prev, mobile: true }));
        ws.onclose = () => {
          setWsStatuses((prev) => ({ ...prev, mobile: false }));
          setTimeout(connectMobileWs, 3000);
        };
        ws.onmessage = (e) => {
          try {
            const data = JSON.parse(e.data);
            if (data.event === 'emergency_halt') {
              alert(`🚨 EMERGENCY SYSTEM HALT: ${data.reason}`);
              setIsLoading(false);
              setActiveAgent('');
              setCurrentThought('SYSTEM EMERGENCY HALT TRIGGERED');
              loadAuditLogs();
            }
          } catch (err) {
            console.error(err);
          }
        };
      } catch (err) {
        console.error(err);
      }
    };

    connectAgentWs();
    connectPermWs();
    connectTermWs();
    connectMobileWs();

    return () => {
      clearInterval(interval);
      if (agentWs.current) agentWs.current.close();
      if (permWs.current) permWs.current.close();
      if (termWs.current) termWs.current.close();
      if (mobileWs.current) mobileWs.current.close();
    };
  }, []);

  // Universal Command Dispatcher
  const handleDispatchCommand = async (prompt) => {
    setIsLoading(true);
    setCurrentTaskPrompt(prompt);
    setBriefingText('');
    setPlanSteps([]);
    setActiveAgent('Prompt Template Agent');
    setCurrentThought(`Routing directive: "${prompt}"...`);
    
    // Add user turn immediately to conversation history
    setConversationHistory((prev) => [...prev, { role: 'user', text: prompt }]);

    const timeStr = new Date().toLocaleTimeString();
    setTerminalLogs((prev) => [
      ...prev.slice(-150),
      { stream: 'ops_event', data: `>> [USER DIRECTIVE] "${prompt}"`, timestamp: timeStr }
    ]);

    try {
      const resp = await fetch('/api/v1/agent/run/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, session_id: sessionId })
      });
      const data = await resp.json();
      const botAnswer = data.final_answer || JSON.stringify(data, null, 2);
      setBriefingText(botAnswer);
      setActiveCategory(data.category || '');
      setPlanSteps(data.plan || []);

      // Add bot turn to conversation history
      setConversationHistory((prev) => [
        ...prev,
        { role: 'bot', text: botAnswer, category: data.category, plan: data.plan }
      ]);

      // Play retro sound whenever something is added to memory
      if (
        data.intent === 'WORKSTATION_MEMORY_CAPTURE' ||
        data.category === 'WORKSTATION_MEMORY_CAPTURE' ||
        data.tool_output?.action === 'workstation_memory_capture' ||
        (data.final_answer && (data.final_answer.includes('COMMITTED TO POSTGRESQL') || data.final_answer.includes('WORKSTATION MEMORY COMMITTED')))
      ) {
        retroSoundEngine.playMemoryStore();
        window.dispatchEvent(new CustomEvent('ops_memory_added'));
      }

      // If browser search output present, feed it to the browser cards
      if (data.browser_output?.search_result?.results) {
        setSearchResults(data.browser_output.search_result.results);
      } else if (data.browser_output?.scrape_result) {
        setLastScrape(data.browser_output.scrape_result);
      }

      loadAuditLogs();
    } catch (err) {
      const errMsg = `Error: ${err.message}`;
      setBriefingText(errMsg);
      setConversationHistory((prev) => [...prev, { role: 'bot', text: errMsg, isError: true }]);
    } finally {
      setIsLoading(false);
      setActiveAgent('');
      setCurrentThought('Standing by.');
    }
  };

  // Erase Temporary Conversation Memory & Reset Session
  const handleClearMemory = async () => {
    try {
      await fetch(`/api/v1/memory/?session_id=${sessionId}`, { method: 'DELETE' });
      await fetch(`/api/v1/memory/chatbot-vector/?session_id=${sessionId}`, { method: 'DELETE' });
      await fetch(`/api/v1/memory/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
    } catch (e) {
      console.warn('Memory purge error:', e);
    }
    const newSessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
    setSessionId(newSessionId);
    setBriefingText('');
    setPlanSteps([]);
    setCurrentTaskPrompt('');
    setConversationHistory([]);
    setCurrentThought('[•] MEMORY PURGED // FRESH SESSION INITIALIZED');
    setTerminalLogs((prev) => [
      ...prev.slice(-150),
      { stream: 'ops_event', data: `[SESSION REFRESH] Active context wiped. New session: ${newSessionId}`, timestamp: new Date().toLocaleTimeString() }
    ]);
    retroSoundEngine.playMemoryErase();
  };

  // Direct Terminal Execution
  const handleExecuteTerminal = async (command) => {
    try {
      await fetch('/api/v1/automation/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'terminal', command })
      });
    } catch (e) {
      console.error(e);
    }
  };

  // Speak Text via Piper TTS
  const handleSpeakText = async (text) => {
    try {
      const clean = text.replace(/[#*`_]/g, '');
      const resp = await fetch('/api/v1/voice/synthesize/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: clean.slice(0, 300) })
      });
      const data = await resp.json();
      if (data.audio_base64) {
        const audio = new Audio(`data:audio/wav;base64,${data.audio_base64}`);
        audio.play().catch((e) => console.log('Autoplay prevented:', e));
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Toggle Voice
  const handleToggleVoice = async () => {
    setIsListening((prev) => !prev);
    try {
      const resp = await fetch('/api/v1/voice/toggle/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enable: !isListening })
      });
      const data = await resp.json();
      if (data.transcript) {
        handleDispatchCommand(data.transcript);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Emergency Halt
  const handleEmergencyHalt = async () => {
    try {
      await fetch('/api/v1/mobile/emergency-halt/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'Emergency Halt via O.P.S. Master HUD' })
      });
      setIsLoading(false);
      setActiveAgent('');
      setCurrentThought('🚨 SYSTEM EMERGENCY HALT TRIGGERED');
      loadAuditLogs();
    } catch (e) {
      console.error(e);
    }
  };

  // Resolve Permission
  const handleResolvePermission = async (requestId, decision) => {
    if (permWs.current && permWs.current.readyState === WebSocket.OPEN) {
      permWs.current.send(JSON.stringify({
        action: 'permission_response',
        request_id: requestId,
        decision: decision
      }));
    }
    try {
      await fetch('/api/v1/permissions/resolve/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: requestId, decision: decision })
      });
    } catch (err) {
      console.warn('REST permission resolve fallback notice:', err);
    }
    setActivePermissionReq(null);
    loadAuditLogs();
  };

  return (
    <>
      {showSplash && <OpsSplashClean onDone={handleSplashDone} />}
      <OpsSecurityModal
        activeRequest={activePermissionReq}
        onResolvePermission={handleResolvePermission}
        auditLogs={auditLogs}
      />
      <div className="retro-scanlines min-h-screen bg-[#050505] text-zinc-100 flex flex-col font-mono selection:bg-red-600 selection:text-white">
        {/* 90s Retro Tactical HUD Header */}
        <header className="border-b border-zinc-800 bg-black sticky top-0 z-40 px-4 py-2">
          <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
            {/* Logo & Subtitle */}
            <div className="flex items-center gap-2.5">
              <div className="px-2 py-0.5 bg-red-600 text-white font-black text-xs border border-red-500 shadow-sm">
                OPS
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-sm tracking-wider text-white">O.P.S an over engineered program system</span>
                </div>
              </div>
            </div>
          </div>
        </header>

      {/* 90s Retro Navigation Tab Bar */}
      <nav className="bg-black border-b border-zinc-800 px-4 py-1.5 sticky top-[45px] z-30">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center gap-2 text-xs">
          <button
            onClick={() => setActiveTab('cockpit')}
            className={`px-3 py-1.5 font-bold transition flex items-center gap-1.5 ${
              activeTab === 'cockpit'
                ? 'bg-red-600 text-white border-2 border-red-500 shadow-md'
                : 'bg-zinc-950 text-zinc-400 border border-zinc-800 hover:text-white hover:border-zinc-600'
            }`}
          >
            <span>[ 01: COMMAND COCKPIT ]</span>
          </button>

          <button
            onClick={() => setActiveTab('orchestration')}
            className={`px-3 py-1.5 font-bold transition flex items-center gap-1.5 ${
              activeTab === 'orchestration'
                ? 'bg-red-600 text-white border-2 border-red-500 shadow-md'
                : 'bg-zinc-950 text-zinc-400 border border-zinc-800 hover:text-white hover:border-zinc-600'
            }`}
          >
            <span>[ 02: LIVE ORCHESTRATION & AGENTS ]</span>
          </button>

          <button
            onClick={() => setActiveTab('memories')}
            className={`px-3 py-1.5 font-bold transition flex items-center gap-1.5 ${
              activeTab === 'memories'
                ? 'bg-red-600 text-white border-2 border-red-500 shadow-md'
                : 'bg-zinc-950 text-zinc-400 border border-zinc-800 hover:text-white hover:border-zinc-600'
            }`}
          >
            <span>[ 03: MY WORKSTATION MEMORIES ]</span>
          </button>
        </div>
      </nav>

      {/* Main HUD Cockpit Body */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-4 space-y-4">
        {/* TAB 1: Main Operational Cockpit */}
        {activeTab === 'cockpit' && (
          <div className="space-y-4">
            {/* Top Dashboard Row: Command & Tri-Model Telemetry on Left, Ops Heart Brain on Right */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-stretch">
              <div className="lg:col-span-9 xl:col-span-9 flex flex-col gap-2.5">
                {/* Local-First Tri-Model Architecture */}
                <OpsTriModelStatus />

                {/* Central JARVIS-Style Command & Voice Core */}
                <OpsCommandCore
                  onDispatchCommand={handleDispatchCommand}
                  isLoading={isLoading}
                  activeAgent={activeAgent}
                  currentThought={currentThought}
                  onToggleVoice={handleToggleVoice}
                  isListening={isListening}
                  onEmergencyHalt={handleEmergencyHalt}
                  sessionId={sessionId}
                  onRefreshSession={handleClearMemory}
                />
              </div>

              {/* Right-Top Corner: Ops Heart (Neural Living Brain of O.P.S.) */}
              <div className="lg:col-span-3 xl:col-span-3 flex flex-col min-h-[190px]">
                <OpsHeart className="h-full" />
              </div>
            </div>

            {/* Dual Live Workstation Grid: Terminal on Left, Query Output on Right */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Column 1: Live Sandbox Terminal & Process Console */}
              <OpsTerminalConsole
                terminalLogs={terminalLogs}
                onExecuteCommand={handleExecuteTerminal}
                onClearLogs={() => setTerminalLogs([])}
                activeTaskPrompt={currentTaskPrompt}
                activeAgent={activeAgent}
                currentThought={currentThought}
                isLoading={isLoading}
                planSteps={planSteps}
                sessionId={sessionId}
              />

              {/* Column 2: Synthesized Executive Briefing & HITL Inline Surface */}
              <OpsBriefingCard
                briefingText={briefingText}
                activeTaskPrompt={currentTaskPrompt}
                isLoading={isLoading}
                currentThought={currentThought}
                activeAgent={activeAgent}
                planSteps={planSteps}
                activeCategory={activeCategory}
                onSpeakText={handleSpeakText}
                activePermissionReq={activePermissionReq}
                onResolvePermission={handleResolvePermission}
                conversationHistory={conversationHistory}
              />
            </div>
          </div>
        )}

        {/* TAB 2: Live Multi-Agent Orchestration & Fleet Inspector */}
        {activeTab === 'orchestration' && (
          <OpsLiveOrchestrationTab
            activeAgent={activeAgent}
            currentThought={currentThought}
            planSteps={planSteps}
            isLoading={isLoading}
            onDispatchPrompt={handleDispatchCommand}
            briefingText={briefingText}
            sessionId={sessionId}
            onClearMemory={handleClearMemory}
          />
        )}

        {/* TAB 3: User Personal Workstation Memories (PostgreSQL ops_db) */}
        {activeTab === 'memories' && (
          <OpsUserMemoriesTab onDispatchCommand={handleDispatchCommand} />
        )}
      </main>

      {/* Mobile Companion Pairing Drawer */}
      <OpsMobileDrawer
        isOpen={isMobileOpen}
        onClose={() => setIsMobileOpen(false)}
      />
    </div>
    </>
  );
}
