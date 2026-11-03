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
import OpsHeart from './components/OpsHeart';
import OpsSplashClean from './components/OpsSplashClean';
import OpsSecurityModal from './components/OpsSecurityModal';
import HumanApprovalModal from './components/HumanApprovalModal';
import { retroSoundEngine } from './utils/retroSounds';

export default function App() {
  // Splash Screen Display State (5 second retro intro on boot)
  const [showSplash, setShowSplash] = useState(true);
  const handleSplashDone = useCallback(() => setShowSplash(false), []);

  // Continuous Conversation Lifecycle (Module: Chat Management & Lifecycle)
  const [conversationId, setConversationId] = useState(() => {
    return localStorage.getItem('ops_conversation_id') || ('conv_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8));
  });
  const [sessionId, setSessionId] = useState(() => 'sess_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9));

  // Human-in-the-Loop (HITL) Approval Modal State
  const [isHitlModalOpen, setIsHitlModalOpen] = useState(false);
  const [pendingApproval, setPendingApproval] = useState(null);
  const [isHitlLoading, setIsHitlLoading] = useState(false);
  const [hitlError, setHitlError] = useState(null);

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
  const [streamingChunk, setStreamingChunk] = useState('');
  const [activeMode, setActiveMode] = useState(null); // 'LLM' | 'WEB' | 'HYBRID'
  const [modeReason, setModeReason] = useState('');
  const [activeStages, setActiveStages] = useState([]);
  const [currentStage, setCurrentStage] = useState('');
  const [researchTelemetry, setResearchTelemetry] = useState({
    sourcesCount: 0,
    pagesCount: 0,
    domains: [],
    evidenceStatus: ''
  });

  // Feeds & Live Orchestration Events
  const [liveEvents, setLiveEvents] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [lastScrape, setLastScrape] = useState(null);
  const [terminalLogs, setTerminalLogs] = useState([]);
  const [activePermissionReq, setActivePermissionReq] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);

  // Voice & UI Modals & Navigation Tabs
  const [isListening, setIsListening] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('cockpit'); // 'cockpit', 'orchestration', 'memories'

  // WebSocket and Stream references
  const agentWs = useRef(null);
  const permWs = useRef(null);
  const termWs = useRef(null);
  const mobileWs = useRef(null);
  const sseRef = useRef(null);
  const abortCtrlRef = useRef(null);

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
        setAuditLogs(data.results || data.events || data || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Load Active Conversation Chronological History from Backend on Boot
  const loadConversation = useCallback(async (convId) => {
    try {
      const endpoint = convId ? `/api/chat/conversations/${convId}/` : '/api/chat/conversations/active/';
      const resp = await fetch(endpoint);
      if (resp.ok) {
        const data = await resp.json();
        if (data.conversation_id && data.conversation_id !== conversationId) {
          setConversationId(data.conversation_id);
          localStorage.setItem('ops_conversation_id', data.conversation_id);
        }
        if (data.messages && data.messages.length > 0) {
          const loadedHistory = data.messages.map((m) => ({
            role: m.role,
            text: m.content,
            status: m.status,
            category: m.metadata?.response_mode || m.metadata?.mode || 'LLM',
            plan: m.metadata?.plan,
            citations: m.metadata?.citations,
            summary: m.metadata?.conversation_summary
          }));
          setConversationHistory(loadedHistory);

          const lastBot = [...data.messages].reverse().find((m) => m.role === 'assistant');
          if (lastBot) {
            setBriefingText(lastBot.content);
            if (lastBot.metadata?.plan) setPlanSteps(lastBot.metadata.plan);
          }
        }
      } else if (resp.status === 404) {
        const activeResp = await fetch('/api/chat/conversations/active/');
        if (activeResp.ok) {
          const activeData = await activeResp.json();
          if (activeData.conversation_id) {
            setConversationId(activeData.conversation_id);
            localStorage.setItem('ops_conversation_id', activeData.conversation_id);
          }
        }
      }
    } catch (e) {
      console.warn('Conversation load notice:', e);
    }
  }, [conversationId]);

  // Connect WebSockets and Initial Conversation
  useEffect(() => {
    checkHealth();
    loadAuditLogs();
    loadConversation(conversationId);
    const interval = setInterval(checkHealth, 10000);

    // 1. Agent WebSocket
    const connectAgentWs = () => {
      try {
        const ws = new WebSocket(getWsUrl('/ws/agent/'));
        agentWs.current = ws;
        ws.onopen = () => setWsStatuses((prev) => ({ ...prev, agent: true }));
        ws.onclose = () => {
          setWsStatuses((prev) => ({ ...prev, agent: false }));
          setTimeout(connectAgentWs, 20000);
        };
        ws.onmessage = (e) => {
          try {
            const data = JSON.parse(e.data);
            if (data.event_type || data.event_id || data.agent || data.status) {
              const structuredEvt = {
                ...data,
                timestamp: data.timestamp || Date.now() / 1000
              };
              setLiveEvents((prev) => [...prev.slice(-300), structuredEvt]);
              if (data.event_type === 'ROUTER_STARTED' || data.event_type === 'SUPERVISOR_STARTED') {
                setIsLoading(true);
                setActiveAgent(data.agent?.name || 'Router');
                setCurrentThought(data.message || 'Routing directive...');
              } else if (data.event_type === 'AGENT_STARTED' || data.event_type === 'AGENT_THINKING') {
                setIsLoading(true);
                setActiveAgent(data.agent?.name || data.agent?.id || 'Specialist Agent');
                setCurrentThought(data.message || data.thought || 'Processing...');
              } else if (data.event_type === 'PLAN_CREATED') {
                const steps = data.metadata?.plan?.steps || data.plan || [];
                if (steps.length > 0) setPlanSteps(steps);
              }
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
          setTimeout(connectPermWs, 20000);
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
          setTimeout(connectTermWs, 20000);
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

    // 4. Mobile Companion WebSocket
    const connectMobileWs = () => {
      try {
        const ws = new WebSocket(getWsUrl('/ws/mobile/'));
        mobileWs.current = ws;
        ws.onopen = () => setWsStatuses((prev) => ({ ...prev, mobile: true }));
        ws.onclose = () => {
          setWsStatuses((prev) => ({ ...prev, mobile: false }));
          setTimeout(connectMobileWs, 20000);
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
      if (sseRef.current) {
        try { sseRef.current.close(); } catch (_) {}
        sseRef.current = null;
      }
      if (abortCtrlRef.current) {
        try { abortCtrlRef.current.abort(); } catch (_) {}
        abortCtrlRef.current = null;
      }
    };
  }, [conversationId, loadConversation]);

  // Desktop Overlay & Human-in-the-Loop Real-Time Gate Listeners
  useEffect(() => {
    // 1. Periodically check for backend PENDING Human-in-the-Loop approvals (every 2.5s)
    const checkPendingApprovals = async () => {
      try {
        const resp = await fetch(`/api/chat/approvals/pending/?conversation_id=${conversationId}`);
        if (resp.ok) {
          const data = await resp.json();
          if (data.approvals && data.approvals.length > 0) {
            const topAppr = data.approvals[0];
            setPendingApproval((prev) => {
              if (prev?.approval_id === topAppr.approval_id) return prev;
              return topAppr;
            });
            setIsHitlModalOpen(true);
          }
        }
      } catch (err) {
        // silent background check
      }
    };

    const approvalInterval = setInterval(checkPendingApprovals, 2500);

    // 2. Custom Window Event: Quick Action (Ctrl + Alt + Space)
    const handleQuickAction = () => {
      const inputEl = document.getElementById('ops-command-input');
      if (inputEl) {
        inputEl.focus();
        inputEl.select();
      }
    };

    // 3. Custom Window Event: Direct HITL Approval trigger from Desktop Overlay
    const handleDesktopHitl = (e) => {
      if (e.detail) {
        setPendingApproval(e.detail);
        setIsHitlModalOpen(true);
      }
    };

    window.addEventListener('ops:quick-action', handleQuickAction);
    window.addEventListener('ops:hitl-approval', handleDesktopHitl);

    return () => {
      clearInterval(approvalInterval);
      window.removeEventListener('ops:quick-action', handleQuickAction);
      window.removeEventListener('ops:hitl-approval', handleDesktopHitl);
    };
  }, [conversationId]);

  // Continuous Conversation Command Dispatcher
  const handleDispatchCommand = async (prompt, inputType = 'text') => {
    if (!prompt || !prompt.trim() || isLoading) return;
    setIsLoading(true);
    setCurrentTaskPrompt(prompt);
    setStreamingChunk('');
    setActiveMode(null);
    setModeReason('Analyzing directive intent...');
    setActiveStages(['Understanding request', 'Classifying intent', 'Preparing reasoning context', 'Generating answer', 'Completing response']);
    setCurrentStage('Understanding request');
    setResearchTelemetry({ sourcesCount: 0, pagesCount: 0, domains: [], evidenceStatus: '' });
    setPlanSteps([]);
    setActiveAgent('Request Understanding Agent');
    setCurrentThought(`Analyzing directive: "${prompt}"...`);

    // Add user turn immediately to conversation history
    setConversationHistory((prev) => [...prev, { role: 'user', text: prompt }]);

    const timeStr = new Date().toLocaleTimeString();
    setTerminalLogs((prev) => [
      ...prev.slice(-150),
      { stream: 'ops_event', data: `>> [USER DIRECTIVE] "${prompt}"`, timestamp: timeStr }
    ]);

    const requestId = 'req_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7);

    // Close any previous SSE stream or abort pending request
    if (sseRef.current) {
      try { sseRef.current.close(); } catch (_) {}
      sseRef.current = null;
    }
    if (abortCtrlRef.current) {
      try { abortCtrlRef.current.abort(); } catch (_) {}
    }
    const abortCtrl = new AbortController();
    abortCtrlRef.current = abortCtrl;

    // Connect to Real-Time LangGraph Server-Sent Events (SSE) Stream
    try {
      const sseSource = new EventSource(`/api/chat/conversations/${conversationId}/events/`);
      sseRef.current = sseSource;

      sseSource.onmessage = (e) => {
        try {
          const evt = JSON.parse(e.data);
          if (evt.event_type === 'STREAM_CONNECTED' || evt.event_type === 'STREAM_CLOSED') return;
          if (evt.event_type === 'text_chunk' && evt.chunk) {
            setStreamingChunk((prev) => prev + evt.chunk);
            return;
          }
          if (evt.event_type === 'MODE_SELECTED' || evt.event_type === 'MODE_CHANGED') {
            const m = evt.response_mode || evt.new_mode;
            if (m) setActiveMode(m);
            if (evt.mode_reason || evt.reason) setModeReason(evt.mode_reason || evt.reason);
            if (evt.stages) setActiveStages(evt.stages);
            if (evt.current_stage) setCurrentStage(evt.current_stage);
            if (evt.safe_task_summary) setCurrentThought(evt.safe_task_summary);
            return;
          }
          if (evt.event_type === 'SEARCH_COMPLETED') {
            setResearchTelemetry((prev) => ({
              ...prev,
              sourcesCount: evt.sources_discovered || prev.sourcesCount
            }));
            if (evt.current_stage) setCurrentStage(evt.current_stage);
            return;
          }
          if (evt.event_type === 'PAGE_RETRIEVED') {
            setResearchTelemetry((prev) => ({
              ...prev,
              pagesCount: evt.pages_retrieved || prev.pagesCount,
              domains: evt.domains || prev.domains
            }));
            if (evt.current_stage) setCurrentStage(evt.current_stage);
            return;
          }
          if (evt.event_type === 'EVIDENCE_VALIDATED') {
            setResearchTelemetry((prev) => ({
              ...prev,
              evidenceStatus: evt.evidence_status || 'Validated'
            }));
            if (evt.current_stage) setCurrentStage(evt.current_stage);
            return;
          }
          if (evt.event_type === 'ANSWER_GENERATING') {
            if (evt.current_stage) setCurrentStage(evt.current_stage);
            return;
          }
          if (evt.event_type === 'NODE_THOUGHT') {
            if (evt.safe_output_summary) {
              setCurrentThought((prev) => {
                const chunk = evt.safe_output_summary;
                return (prev && prev.length < 240) ? (prev + chunk) : chunk;
              });
            }
            return;
          }
          if (evt.event_type === 'response_completed') {
            const finalVal = evt.final_answer || evt.content;
            if (finalVal) setStreamingChunk(finalVal);
          }
          setLiveEvents((prev) => [...prev.slice(-300), evt]);
          if (evt.component_name) {
            setActiveAgent(evt.component_name);
          }
          if (evt.safe_task_summary) {
            setCurrentThought(evt.safe_task_summary);
          }
        } catch (err) {
          console.warn('SSE parse warning:', err);
        }
      };
      sseSource.onerror = () => {
        // SSE errors can happen on close; do not close aggressively
      };
    } catch (e) {
      console.warn('SSE connection warning:', e);
    }

    try {
      // Primary: Conversation Messages Endpoint with Multi-Turn Context
      let resp = await fetch(`/api/chat/conversations/${conversationId}/messages/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: prompt, input_type: inputType, request_id: requestId }),
        signal: abortCtrl.signal
      });

      // Fallback: Web Research Execute Endpoint
      if (!resp.ok) {
        resp = await fetch('/api/v1/ops/execute/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt, conversation_id: conversationId, session_id: sessionId, request_id: requestId }),
          signal: abortCtrl.signal
        });
      }

      const data = await resp.json();
      const botAnswer = data.content || data.final_answer || data.response || (data.error ? `⚠️ ${data.error}` : "Directive acknowledged.");
      setBriefingText(botAnswer);
      setStreamingChunk('');
      setActiveCategory(data.mode || 'WEB_RESEARCH');
      if (data.plan) setPlanSteps(data.plan);

      // Add bot turn to conversation history
      setConversationHistory((prev) => [
        ...prev,
        {
          role: 'bot',
          text: botAnswer,
          category: data.mode || 'WEB_RESEARCH',
          plan: data.plan,
          citations: data.citations,
          summary: data.conversation_summary
        }
      ]);

      loadAuditLogs();
    } catch (err) {
      if (err.name === 'AbortError') {
        // Ignored, user stopped generation
      } else {
        const errMsg = `Error: ${err.message}`;
        setBriefingText(errMsg);
        setConversationHistory((prev) => [...prev, { role: 'bot', text: errMsg, isError: true }]);
      }
    } finally {
      if (sseRef.current) {
        try { sseRef.current.close(); } catch (_) {}
        sseRef.current = null;
      }
      abortCtrlRef.current = null;
      setIsLoading(false);
      setActiveAgent('');
      setCurrentThought('Standing by.');
      setStreamingChunk('');
    }
  };

  // Emergency Halt / Stop Generation
  const handleEmergencyHalt = async () => {
    if (abortCtrlRef.current) {
      try { abortCtrlRef.current.abort(); } catch (_) {}
      abortCtrlRef.current = null;
    }
    if (sseRef.current) {
      try { sseRef.current.close(); } catch (_) {}
      sseRef.current = null;
    }

    try {
      await fetch(`/api/chat/conversations/${conversationId}/cancel/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (e) {
      console.error('Stop execution notice:', e);
    }

    if (streamingChunk) {
      const stoppedText = streamingChunk + "\n\n*[⏹ Generation stopped by user]*";
      setBriefingText(stoppedText);
      setConversationHistory((prev) => [
        ...prev,
        { role: 'bot', text: stoppedText, category: 'CANCELLED' }
      ]);
    } else {
      setBriefingText("*[⏹ Generation stopped by user]*");
    }

    setIsLoading(false);
    setActiveAgent('');
    setCurrentThought('⏹ SYSTEM EXECUTION HALTED (Context Preserved)');
    setStreamingChunk('');
    loadAuditLogs();
  };

  // Step 1 of HITL: Request Approval from Backend and Open Popup
  const handleRequestRefreshApproval = async () => {
    setHitlError(null);
    setIsHitlLoading(true);
    try {
      const resp = await fetch(`/api/chat/conversations/${conversationId}/refresh-approval/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.error || `Failed to create pending approval (${resp.status})`);
      }

      const data = await resp.json();
      setPendingApproval(data);
      setIsHitlModalOpen(true);
    } catch (err) {
      console.error('Refresh approval initiation error:', err);
      setCurrentThought(`[ERROR] Approval request failed: ${err.message}`);
    } finally {
      setIsHitlLoading(false);
    }
  };

  // Step 2: User Selects DENY in HITL Popup
  const handleDenyApproval = async () => {
    if (pendingApproval?.approval_id) {
      try {
        await fetch(`/api/chat/conversations/${conversationId}/refresh-approval/${pendingApproval.approval_id}/deny/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
      } catch (e) {
        console.warn('Deny approval notification notice:', e);
      }
    }
    setIsHitlModalOpen(false);
    setPendingApproval(null);
    setHitlError(null);
    setCurrentThought('Human approval DENIED. Active conversation preserved intact.');
    loadAuditLogs();
  };

  // Step 3: User Selects ACCEPT in HITL Popup
  const handleAcceptApproval = async () => {
    if (!pendingApproval?.approval_id) return;
    setIsHitlLoading(true);
    setHitlError(null);

    try {
      const resp = await fetch(`/api/chat/conversations/${conversationId}/refresh-approval/${pendingApproval.approval_id}/accept/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.error || `Server returned error status ${resp.status}`);
      }

      const data = await resp.json();
      const newConvId = data.new_conversation_id || ('conv_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8));

      // Update Active Conversation ID
      setConversationId(newConvId);
      setSessionId('sess_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9));
      localStorage.setItem('ops_conversation_id', newConvId);

      // Reset Active Chat Interface
      setConversationHistory([]);
      setLiveEvents([]);
      setBriefingText('');
      setPlanSteps([]);
      setCurrentTaskPrompt('');
      setCurrentThought('Active conversation permanently reset. Fresh session initialized.');
      setStreamingChunk('');

      // Play retro memory erase sound
      retroSoundEngine.playMemoryErase();
      setIsHitlModalOpen(false);
      setPendingApproval(null);
      loadAuditLogs();
    } catch (err) {
      setHitlError(err.message || 'Failed to permanently delete conversation.');
    } finally {
      setIsHitlLoading(false);
    }
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

  // Toggle Voice Input
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
        handleDispatchCommand(data.transcript, 'voice');
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Resolve HITL Permission
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

      {/* HITL Security Confirmation Modal (Automations) */}
      <OpsSecurityModal
        activeRequest={activePermissionReq}
        onResolvePermission={handleResolvePermission}
        auditLogs={auditLogs}
      />

      {/* Reusable Human-in-the-Loop (HITL) Approval Modal */}
      <HumanApprovalModal
        isOpen={isHitlModalOpen}
        title="Human Approval Required"
        subtitle="Delete Current Conversation?"
        conversationId={conversationId}
        approvalId={pendingApproval?.approval_id}
        loading={isHitlLoading}
        error={hitlError}
        onAccept={handleAcceptApproval}
        onDeny={handleDenyApproval}
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
                  onRefreshSession={handleRequestRefreshApproval}
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
                conversationId={conversationId}
                onRefreshConversation={handleRequestRefreshApproval}
                onStopExecution={handleEmergencyHalt}
                streamingChunk={streamingChunk}
                activeMode={activeMode}
                modeReason={modeReason}
                stages={activeStages}
                currentStage={currentStage}
                researchTelemetry={researchTelemetry}
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
            streamingChunk={streamingChunk}
            activeTaskPrompt={currentTaskPrompt}
            conversationHistory={conversationHistory}
            onSpeakText={handleSpeakText}
            sessionId={conversationId}
            onClearMemory={handleRequestRefreshApproval}
            onStopExecution={handleEmergencyHalt}
            liveEvents={liveEvents}
          />
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
