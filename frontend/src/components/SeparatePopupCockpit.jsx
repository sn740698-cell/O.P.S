import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  RotateCcw,
  Send,
  Square,
  Loader2,
  Terminal,
  Bot,
  Volume2,
  Cpu,
  ShieldAlert,
  Sparkles,
  X,
  Paperclip,
  FileText,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

import UserMessage from './UserMessage';
import AssistantMessage from './AssistantMessage';
import MarkdownRenderer from './MarkdownRenderer';
import HumanApprovalModal from './HumanApprovalModal';
import CockpitLoadingSkeleton, { inferInitialModeAndEngine, DEFAULT_PIPELINE_STAGES } from './skeletons/CockpitLoadingSkeleton';
import { retroSoundEngine } from '../utils/retroSounds';

export function engineFromMode(mode) {
  if (!mode) return null;
  const m = mode.toUpperCase();
  if (['DESKTOP', 'BROWSER', 'HYBRID AUTO', 'HYBRID_AUTO', 'AUTOMATION'].some(k => m.includes(k))) return 'AUTOMATION';
  if (m === 'COMPOSITE') return 'COMPOSITE';
  return 'ANSWERING';
}

export function resolveCategoryFromContent(text) {
  if (!text || typeof text !== 'string') return null;
  if (text.includes('DESKTOP AUTOMATION') || text.includes('[DESKTOP]')) return 'DESKTOP';
  if (text.includes('BROWSER AUTOMATION') || text.includes('[BROWSER]')) return 'BROWSER';
  if (text.includes('HYBRID AUTOMATION') || text.includes('[HYBRID AUTO]')) return 'HYBRID AUTO';
  if (text.includes('COMPOSITE EXECUTION') || text.includes('[COMPOSITE]')) return 'COMPOSITE';
  if (text.includes('WEB MODE RESPONSE') || text.includes('[WEB]')) return 'WEB';
  if (text.includes('LLM MODE RESPONSE') || text.includes('[LLM]')) return 'LLM';
  if (text.includes('DOCUMENT MODE') || text.includes('DOCUMENT PASSAGE') || text.includes('[DOC]')) return 'DOCUMENT';
  return null;
}

export default function SeparatePopupCockpit() {
  // Continuous Conversation Lifecycle (Module: Chat Management & Lifecycle)
  const [conversationId, setConversationId] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    const urlConv = params.get('conv_id');
    if (urlConv) return urlConv;
    return (
      localStorage.getItem('ops_conversation_id') ||
      localStorage.getItem('ops_cockpit_conversation_id') ||
      ''
    );
  });

  const [conversationHistory, setConversationHistory] = useState([]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [currentTaskPrompt, setCurrentTaskPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentThought, setCurrentThought] = useState('');
  const [activeAgent, setActiveAgent] = useState('');
  const [streamingChunk, setStreamingChunk] = useState('');

  // Engine & Automatic Response Modes State
  const [activeEngine, setActiveEngine] = useState(null); // 'ANSWERING' | 'AUTOMATION' | 'COMPOSITE'
  const [activeMode, setActiveMode] = useState(null); // 'LLM' | 'WEB' | 'HYBRID' | 'DOCUMENT' | 'DESKTOP' | 'BROWSER'
  const [modeReason, setModeReason] = useState('');
  const [activeStages, setActiveStages] = useState([]);
  const [currentStage, setCurrentStage] = useState('');
  const [automationTelemetry, setAutomationTelemetry] = useState(null);
  const [researchTelemetry, setResearchTelemetry] = useState({
    sourcesCount: 0,
    pagesCount: 0,
    domains: [],
    evidenceStatus: ''
  });

  // Temporary Document RAG State (Pinecone Ephemeral Intelligence)
  const [attachedDocs, setAttachedDocs] = useState([]);
  const [isUploadingDoc, setIsUploadingDoc] = useState(false);
  const [docUploadStatus, setDocUploadStatus] = useState('');
  const [docUploadProgress, setDocUploadProgress] = useState(0);
  const [docError, setDocError] = useState(null);
  const fileInputRef = useRef(null);

  // Human-in-the-Loop (HITL) State
  const [isHitlModalOpen, setIsHitlModalOpen] = useState(false);
  const [pendingApproval, setPendingApproval] = useState(null);
  const [isHitlLoading, setIsHitlLoading] = useState(false);
  const [hitlError, setHitlError] = useState(null);
  const dismissedApprovalsRef = useRef(new Set());

  // Dynamic Window Sizing & Dragging State
  const [isResizing, setIsResizing] = useState(false);
  const [liveResizeDims, setLiveResizeDims] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 480,
    height: typeof window !== 'undefined' ? window.innerHeight : 680
  });

  useEffect(() => {
    const handleWinResize = () => {
      setLiveResizeDims({ width: window.innerWidth, height: window.innerHeight });
    };
    window.addEventListener('resize', handleWinResize);
    return () => window.removeEventListener('resize', handleWinResize);
  }, []);

  const scrollRef = useRef(null);
  const mainContainerRef = useRef(null);
  const inputRef = useRef(null);
  const sseRef = useRef(null);
  const abortCtrlRef = useRef(null);
  const isUserScrolledUp = useRef(false);
  const scrollRafRef = useRef(null);
  const broadcastChannelRef = useRef(null);

  // Synchronized state refs to prevent interval / effect dependency loops
  const isHitlModalOpenRef = useRef(isHitlModalOpen);
  isHitlModalOpenRef.current = isHitlModalOpen;
  const pendingApprovalRef = useRef(pendingApproval);
  pendingApprovalRef.current = pendingApproval;
  const isLoadingRef = useRef(isLoading);
  isLoadingRef.current = isLoading;

  // Single persistent BroadcastChannel instance across component lifecycle
  useEffect(() => {
    try {
      if (typeof BroadcastChannel !== 'undefined') {
        broadcastChannelRef.current = new BroadcastChannel('ops_cockpit_channel');
      }
    } catch (_) {}
    return () => {
      if (broadcastChannelRef.current) {
        try { broadcastChannelRef.current.close(); } catch (_) {}
        broadcastChannelRef.current = null;
      }
    };
  }, []);

  const postCockpitBroadcast = useCallback((msg) => {
    try {
      if (broadcastChannelRef.current) {
        broadcastChannelRef.current.postMessage(msg);
      }
    } catch (_) {}
  }, []);

  // Deduplicating and atomic message state updater: updates existing assistant turn in-place to prevent duplication
  const updateOrAppendAssistantTurn = useCallback((newTurn) => {
    setConversationHistory((prev) => {
      const last = prev[prev.length - 1];
      if (last && (last.role === 'assistant' || last.role === 'bot')) {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...last,
          text: newTurn.text,
          content: newTurn.content || newTurn.text,
          category: newTurn.category || last.category,
          plan: newTurn.plan || last.plan,
          citations: (newTurn.citations && newTurn.citations.length > 0) ? newTurn.citations : (last.citations || []),
          summary: newTurn.summary || last.summary,
          status: newTurn.status || last.status,
          isError: newTurn.isError ?? last.isError
        };
        return updated;
      }
      return [
        ...prev,
        {
          role: 'assistant',
          text: newTurn.text,
          content: newTurn.content || newTurn.text,
          category: newTurn.category || 'LLM',
          plan: newTurn.plan,
          citations: newTurn.citations || [],
          summary: newTurn.summary,
          status: newTurn.status,
          isError: newTurn.isError
        }
      ];
    });
  }, []);

  // Clean up any lingering SSE or aborted requests on unmount
  useEffect(() => {
    return () => {
      if (sseRef.current) {
        try { sseRef.current.close(); } catch (_) {}
        sseRef.current = null;
      }
      if (abortCtrlRef.current) {
        try { abortCtrlRef.current.abort(); } catch (_) {}
        abortCtrlRef.current = null;
      }
      if (scrollRafRef.current) {
        cancelAnimationFrame(scrollRafRef.current);
      }
    };
  }, []);

  // Monitor user scroll position to avoid forceful auto-scroll when reading history
  const handleScroll = useCallback(() => {
    if (!mainContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = mainContainerRef.current;
    isUserScrolledUp.current = (scrollHeight - scrollTop - clientHeight > 120);
  }, []);

  // Stable, glitch-free instant auto-scroll for streaming chunks without smooth-scroll jumping
  useEffect(() => {
    if (isUserScrolledUp.current) return;
    if (scrollRafRef.current) cancelAnimationFrame(scrollRafRef.current);
    scrollRafRef.current = requestAnimationFrame(() => {
      if (mainContainerRef.current && !isUserScrolledUp.current) {
        mainContainerRef.current.scrollTop = mainContainerRef.current.scrollHeight;
      }
    });
    return () => {
      if (scrollRafRef.current) cancelAnimationFrame(scrollRafRef.current);
    };
  }, [streamingChunk, currentThought]);

  // Instant scroll on discrete turn additions or loading state completion
  useEffect(() => {
    if (isUserScrolledUp.current) return;
    if (scrollRafRef.current) cancelAnimationFrame(scrollRafRef.current);
    scrollRafRef.current = requestAnimationFrame(() => {
      if (mainContainerRef.current && !isUserScrolledUp.current) {
        mainContainerRef.current.scrollTop = mainContainerRef.current.scrollHeight;
      }
    });
  }, [conversationHistory.length, isLoading]);

  // Load Active Conversation from Backend
  const loadConversation = useCallback(async (convId) => {
    try {
      const endpoint = convId ? `/api/chat/conversations/${convId}/` : '/api/chat/conversations/active/';
      const resp = await fetch(endpoint);
      if (resp.ok) {
        const data = await resp.json();
        if (data.conversation_id && data.conversation_id !== conversationId) {
          setConversationId(data.conversation_id);
          localStorage.setItem('ops_conversation_id', data.conversation_id);
          localStorage.setItem('ops_cockpit_conversation_id', data.conversation_id);
        }
        if (data.messages && data.messages.length > 0) {
          const loadedHistory = data.messages.map((m) => {
            const cat = m.metadata?.response_mode || m.metadata?.mode || resolveCategoryFromContent(m.content) || 'LLM';
            return {
              role: m.role === 'user' ? 'user' : 'assistant',
              text: m.content,
              content: m.content,
              status: m.status,
              category: cat,
              plan: m.metadata?.plan,
              citations: m.metadata?.citations,
              summary: m.metadata?.conversation_summary
            };
          });
          setConversationHistory(loadedHistory);
          const lastAsst = [...loadedHistory].reverse().find(m => m.role === 'assistant');
          if (lastAsst?.category) {
            setActiveMode(lastAsst.category);
            setActiveEngine(engineFromMode(lastAsst.category));
          }
        }
      } else if (resp.status === 404) {
        const activeResp = await fetch('/api/chat/conversations/active/');
        if (activeResp.ok) {
          const activeData = await activeResp.json();
          if (activeData.conversation_id) {
            setConversationId(activeData.conversation_id);
            localStorage.setItem('ops_conversation_id', activeData.conversation_id);
            localStorage.setItem('ops_cockpit_conversation_id', activeData.conversation_id);
            if (activeData.messages && activeData.messages.length > 0) {
              const loadedHistory = activeData.messages.map((m) => {
                const cat = m.metadata?.response_mode || m.metadata?.mode || resolveCategoryFromContent(m.content) || 'LLM';
                return {
                  role: m.role === 'user' ? 'user' : 'assistant',
                  text: m.content,
                  content: m.content,
                  status: m.status,
                  category: cat,
                  plan: m.metadata?.plan,
                  citations: m.metadata?.citations,
                  summary: m.metadata?.conversation_summary
                };
              });
              setConversationHistory(loadedHistory);
              const lastAsst = [...loadedHistory].reverse().find(m => m.role === 'assistant');
              if (lastAsst?.category) {
                setActiveMode(lastAsst.category);
                setActiveEngine(engineFromMode(lastAsst.category));
              }
            }
          }
        }
      }
    } catch (e) {
      console.warn('Cockpit conversation load notice:', e);
    }
  }, []);

  // Query and latch onto active conversation on boot
  useEffect(() => {
    loadConversation(conversationId);
  }, []);

  // Load attached documents whenever conversationId changes
  useEffect(() => {
    if (!conversationId) return;
    const fetchDocs = async () => {
      try {
        const resp = await fetch(`/api/chat/conversations/${conversationId}/documents/`);
        if (resp.ok) {
          const data = await resp.json();
          if (data.active_documents) {
            setAttachedDocs(data.active_documents);
          }
        }
      } catch (_) {}
    };
    fetchDocs();
  }, [conversationId]);

  // Synchronize active conversation with browser window via storage events
  useEffect(() => {
    const handleStorageChange = (e) => {
      if ((e.key === 'ops_conversation_id' || e.key === 'ops_cockpit_conversation_id') && e.newValue && e.newValue !== conversationId) {
        setConversationId(e.newValue);
        loadConversation(e.newValue);
      }
    };
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [conversationId, loadConversation]);

  // Persistent Real-Time LangGraph SSE Stream for active conversation
  useEffect(() => {
    if (!conversationId) return;

    let sseSource = null;
    let reconnectTimer = null;
    let isMounted = true;

    const connectSse = () => {
      if (!isMounted) return;
      try {
        if (sseRef.current) {
          try { sseRef.current.close(); } catch (_) {}
          sseRef.current = null;
        }

        sseSource = new EventSource(`/api/chat/conversations/${conversationId}/events/`);
        sseRef.current = sseSource;

        sseSource.onmessage = (evt) => {
          try {
            const parsed = JSON.parse(evt.data);
            if (parsed.event_type === 'STREAM_CONNECTED' || parsed.event_type === 'STREAM_CLOSED') return;

            // Universal Real-Time Telemetry & Pipeline State Synchronizer
            if (parsed.current_stage) setCurrentStage(parsed.current_stage);
            if (parsed.stages && Array.isArray(parsed.stages) && parsed.stages.length > 0) setActiveStages(parsed.stages);
            if (parsed.safe_task_summary) setCurrentThought(parsed.safe_task_summary);
            if (parsed.safe_output_summary && !parsed.safe_task_summary) setCurrentThought(parsed.safe_output_summary);
            if (parsed.component_name) setActiveAgent(parsed.component_name);
            if (parsed.active_engine) setActiveEngine(parsed.active_engine);
            if (parsed.response_mode) setActiveMode(parsed.response_mode);
            if (parsed.mode_reason || parsed.reason) setModeReason(parsed.mode_reason || parsed.reason);

            // 0. Directive started (dispatched from Cockpit or Browser)
            if (parsed.event_type === 'REQUEST_STARTED') {
              setIsLoading(true);
              setStreamingChunk('');
              const promptText = parsed.query || parsed.directive || (parsed.safe_task_summary ? parsed.safe_task_summary.replace(/^Analyzing directive:\s*['"]?/, '').replace(/['"]?\.\.\.$/, '') : '');
              if (promptText) {
                setCurrentTaskPrompt(promptText);
                setConversationHistory((prev) => {
                  const last = prev[prev.length - 1];
                  if (last && last.role === 'user') {
                    // Already have active user turn for this request
                    return prev;
                  }
                  return [...prev, { role: 'user', text: promptText, content: promptText }];
                });
              }
              const effMode = parsed.response_mode || inferInitialModeAndEngine(promptText).mode;
              const effEngine = parsed.active_engine || engineFromMode(effMode);
              setActiveEngine(effEngine);
              setActiveMode(effMode);
              if (parsed.mode_reason) setModeReason(parsed.mode_reason);
              if (parsed.stages) setActiveStages(parsed.stages);
              if (parsed.current_stage) setCurrentStage(parsed.current_stage);
              if (parsed.safe_task_summary) setCurrentThought(parsed.safe_task_summary);
              return;
            }

            // Engine Selected Event
            if (parsed.event_type === 'ENGINE_SELECTED') {
              const effMode = parsed.response_mode || activeMode;
              const eng = parsed.active_engine || parsed.engine || engineFromMode(effMode);
              if (eng) setActiveEngine(eng);
              if (parsed.response_mode) setActiveMode(parsed.response_mode);
              if (parsed.current_agent) setActiveAgent(parsed.current_agent);
              if (parsed.stages) setActiveStages(parsed.stages);
              if (parsed.current_stage) setCurrentStage(parsed.current_stage);
              if (parsed.safe_task_summary) setCurrentThought(parsed.safe_task_summary);
              return;
            }

            // Document Ingestion Progress
            if (parsed.event_type === 'DOCUMENT_INGESTION_PROGRESS') {
              setIsUploadingDoc(true);
              if (parsed.safe_task_summary) setDocUploadStatus(parsed.safe_task_summary);
              if (parsed.progress_percent) setDocUploadProgress(parsed.progress_percent);
              return;
            }

            // 1. Text typewriter token chunks
            if (parsed.event_type === 'text_chunk' && parsed.chunk) {
              setIsLoading(true);
              setStreamingChunk((prev) => prev + parsed.chunk);
              postCockpitBroadcast({
                type: 'TOKEN_CHUNK',
                chunk: parsed.chunk,
                conversationId: conversationId
              });
              return;
            }

            // 2. Mode selected / dynamic mode change
            if (parsed.event_type === 'MODE_SELECTED' || parsed.event_type === 'MODE_CHANGED') {
              const m = parsed.response_mode || parsed.new_mode;
              if (m) {
                setActiveMode(m);
                setActiveEngine(parsed.active_engine || engineFromMode(m));
              }
              if (parsed.current_agent) setActiveAgent(parsed.current_agent);
              if (parsed.mode_reason || parsed.reason) setModeReason(parsed.mode_reason || parsed.reason);
              if (parsed.stages) setActiveStages(parsed.stages);
              if (parsed.current_stage) setCurrentStage(parsed.current_stage);
              if (parsed.safe_task_summary) setCurrentThought(parsed.safe_task_summary);
              return;
            }

            // Agent Execution Status Events
            if (parsed.event_type === 'AGENT_STARTED' || parsed.event_type === 'AGENT_PROGRESS' || parsed.event_type === 'NODE_STARTED') {
              const agentLabel = parsed.component_name || parsed.agent_name || parsed.node_id;
              if (agentLabel) setActiveAgent(agentLabel);
              if (parsed.active_engine) setActiveEngine(parsed.active_engine);
              if (parsed.response_mode) setActiveMode(parsed.response_mode);
              if (parsed.current_stage) setCurrentStage(parsed.current_stage);
              if (parsed.safe_task_summary) setCurrentThought(parsed.safe_task_summary);
              return;
            }

            // Multi-Agent Superior & Specialist Automation Events
            if (parsed.event_type && (parsed.event_type.startsWith('agent.') || parsed.event_type.startsWith('coordinator.'))) {
              setAutomationTelemetry((prev) => ({
                ...prev,
                superiorAgent: parsed.superior_agent || prev?.superiorAgent || (parsed.coordinator ? 'Hybrid Coordinator' : 'Superior Agent'),
                specialistAgent: parsed.specialist_agent || prev?.specialistAgent || parsed.component_name,
                action: parsed.safe_task_summary || parsed.action || 'Executing specialist directive',
                verificationStatus: parsed.execution_status === 'COMPLETED' ? 'Verified ✅' : (parsed.execution_status || 'In Progress'),
                coordinator: parsed.coordinator || prev?.coordinator
              }));
              if (parsed.specialist_agent) setActiveAgent(parsed.specialist_agent);
              if (parsed.safe_task_summary) setCurrentThought(parsed.safe_task_summary);
              if (parsed.current_stage) setCurrentStage(parsed.current_stage);
              return;
            }

            // Automation Telemetry Events
            if (parsed.event_type === 'AUTOMATION_PLAN_READY') {
              setAutomationTelemetry({
                targetApp: parsed.target_app || 'Application',
                action: parsed.action || 'Executing plan',
                verificationStatus: 'Plan Ready'
              });
              if (parsed.current_stage) setCurrentStage(parsed.current_stage);
              return;
            }
            if (parsed.event_type === 'AUTOMATION_STEP_STARTED') {
              setAutomationTelemetry((prev) => ({
                ...prev,
                targetApp: parsed.target_app || prev?.targetApp || 'System',
                action: parsed.action || parsed.safe_task_summary || 'Executing step',
                verificationStatus: 'Executing...'
              }));
              if (parsed.current_stage) setCurrentStage(parsed.current_stage);
              if (parsed.safe_task_summary) setCurrentThought(parsed.safe_task_summary);
              return;
            }
            if (parsed.event_type === 'AUTOMATION_STEP_COMPLETED') {
              setAutomationTelemetry((prev) => ({
                ...prev,
                verificationStatus: 'Step Verified ✅'
              }));
              if (parsed.current_stage) setCurrentStage(parsed.current_stage);
              return;
            }
            if (parsed.event_type === 'AUTOMATION_VERIFIED') {
              setAutomationTelemetry((prev) => ({
                ...prev,
                verificationStatus: 'Window/State Verified ✅'
              }));
              if (parsed.current_stage) setCurrentStage(parsed.current_stage);
              return;
            }

            // 3. Research telemetry events
            if (parsed.event_type === 'SEARCH_COMPLETED') {
              setResearchTelemetry((prev) => ({
                ...prev,
                sourcesCount: parsed.sources_discovered || parsed.sources_count || prev.sourcesCount
              }));
              if (parsed.current_stage) setCurrentStage(parsed.current_stage);
              if (parsed.safe_task_summary) setCurrentThought(parsed.safe_task_summary);
              return;
            }
            if (parsed.event_type === 'PAGE_RETRIEVED') {
              setResearchTelemetry((prev) => ({
                ...prev,
                pagesCount: parsed.pages_retrieved || parsed.pages_count || prev.pagesCount,
                domains: parsed.domains || prev.domains
              }));
              if (parsed.current_stage) setCurrentStage(parsed.current_stage);
              if (parsed.safe_task_summary) setCurrentThought(parsed.safe_task_summary);
              return;
            }
            if (parsed.event_type === 'EVIDENCE_VALIDATED') {
              setResearchTelemetry((prev) => ({
                ...prev,
                evidenceStatus: parsed.evidence_status || 'Validated'
              }));
              if (parsed.current_stage) setCurrentStage(parsed.current_stage);
              if (parsed.safe_task_summary) setCurrentThought(parsed.safe_task_summary);
              return;
            }

            // 4. Processing stage updates
            if (
              parsed.event_type === 'RESEARCH_STARTED' ||
              parsed.event_type === 'REASONING_STARTED' ||
              parsed.event_type === 'ANSWER_GENERATING'
            ) {
              if (parsed.response_mode) setActiveMode(parsed.response_mode);
              if (parsed.current_stage) setCurrentStage(parsed.current_stage);
              if (parsed.safe_task_summary) setCurrentThought(parsed.safe_task_summary);
              return;
            }

            // 4.5 Human-in-the-Loop Approval Required Event
            if (parsed.event_type === 'APPROVAL_REQUIRED') {
              const apprObj = {
                approval_id: parsed.approval_id,
                action_type: parsed.action_type || 'AUTOMATION_ACTION',
                description: parsed.approval_reason || parsed.safe_task_summary || 'Human authorization required for action.',
                conversation_id: parsed.conversation_id || conversationId,
                metadata: {
                  action_summary: parsed.approval_reason || parsed.safe_task_summary,
                  target: parsed.target || parsed.target_application || parsed.target_url || parsed.target_file_path || 'System Target',
                  target_application: parsed.target_application,
                  target_url: parsed.target_url,
                  target_file_path: parsed.target_file_path,
                  execution_plan: parsed.execution_plan,
                  input_content: parsed.input_content,
                  expected_result: parsed.expected_result,
                  risk_level: parsed.risk_level || 'HIGH',
                  is_destructive: parsed.is_destructive
                }
              };
              setPendingApproval(apprObj);
              setIsHitlModalOpen(true);
              setIsLoading(false);
              setStreamingChunk('');
              setCurrentThought('Execution paused at Human-in-the-Loop authorization gate.');
              setCurrentStage('Waiting for Human Approval');
              retroSoundEngine.playBeep(440, 0.15);
              return;
            }

            // 5. Final completion
            if (parsed.event_type === 'response_completed') {
              const finalVal = parsed.final_answer || parsed.content;
              const finalMode = parsed.response_mode || parsed.mode || resolveCategoryFromContent(finalVal) || activeMode || 'LLM';
              const finalEng = parsed.active_engine || engineFromMode(finalMode);
              setActiveEngine(finalEng);
              setActiveMode(finalMode);
              if (finalVal) {
                updateOrAppendAssistantTurn({
                  text: finalVal,
                  content: finalVal,
                  category: finalMode,
                  citations: parsed.citations || [],
                  summary: parsed.conversation_summary
                });
              }
              setIsLoading(false);
              setStreamingChunk('');
              setActiveAgent('Result Formatter');
              setCurrentThought('');
              setCurrentStage('Completed');
              retroSoundEngine.playBeep(520, 0.08);
              return;
            }

            // 6. Cancellation & Failure
            if (parsed.event_type === 'response_cancelled') {
              setConversationHistory((prev) => [
                ...prev,
                {
                  role: 'assistant',
                  text: "*[⏹ Generation stopped by user]*",
                  content: "*[⏹ Generation stopped by user]*",
                  category: 'CANCELLED'
                }
              ]);
              setIsLoading(false);
              setStreamingChunk('');
              return;
            }

            if (parsed.event_type === 'response_failed') {
              setConversationHistory((prev) => [
                ...prev,
                {
                  role: 'assistant',
                  text: `⚠️ Error: ${parsed.error_details || 'Execution failed.'}`,
                  content: `⚠️ Error: ${parsed.error_details || 'Execution failed.'}`,
                  isError: true
                }
              ]);
              setIsLoading(false);
              setStreamingChunk('');
              return;
            }

            if (parsed.event_type === 'NODE_THOUGHT') {
              if (parsed.safe_output_summary) {
                setCurrentThought((prev) => {
                  const chunk = parsed.safe_output_summary;
                  return (prev && prev.length < 240) ? (prev + ' ' + chunk) : chunk;
                });
              }
              return;
            }

            if (parsed.current_stage) setCurrentStage(parsed.current_stage);
            if (parsed.safe_task_summary) setCurrentThought(parsed.safe_task_summary);
            if (parsed.component_name) setActiveAgent(parsed.component_name);
          } catch (err) {
            // ignore parse error
          }
        };

        sseSource.onerror = () => {
          if (sseSource) {
            try { sseSource.close(); } catch (_) {}
          }
          if (isMounted) {
            clearTimeout(reconnectTimer);
            reconnectTimer = setTimeout(connectSse, 3000);
          }
        };
      } catch (e) {
        console.warn("Cockpit persistent SSE connection error:", e);
      }
    };

    connectSse();

    return () => {
      isMounted = false;
      clearTimeout(reconnectTimer);
      if (sseSource) {
        try { sseSource.close(); } catch (_) {}
      }
      sseRef.current = null;
    };
  }, [conversationId]);

  // Periodically check for backend PENDING Human-in-the-Loop approvals (decoupled from modal state to prevent render loops)
  const checkPendingApprovals = useCallback(async () => {
    // Guard: Do not poll without a valid conversation ID
    if (!conversationId || conversationId === 'undefined' || conversationId === 'null') {
      return;
    }
    try {
      const resp = await fetch(`/api/chat/approvals/pending/?conversation_id=${encodeURIComponent(conversationId)}`);
      if (resp.ok) {
        const data = await resp.json();
        if (data.approvals && data.approvals.length > 0) {
          const topAppr = data.approvals[0];
          // If already dismissed by user in this session, do not re-surface
          if (dismissedApprovalsRef.current.has(topAppr.approval_id)) {
            return;
          }
          setPendingApproval((prev) => {
            if (prev?.approval_id === topAppr.approval_id) return prev;
            return topAppr;
          });
          setIsHitlModalOpen(true);
        } else {
          // If no pending approvals exist for this conversation, close any open modal
          const currPending = pendingApprovalRef.current;
          if (isHitlModalOpenRef.current && currPending?.conversation_id === conversationId && (!currPending?.approval_id || dismissedApprovalsRef.current.has(currPending?.approval_id))) {
            setIsHitlModalOpen(false);
            setPendingApproval(null);
          }
        }
      }
    } catch (err) {
      // silent check
    }
  }, [conversationId]);

  // Real-Time Event & Approval Listener
  useEffect(() => {
    checkPendingApprovals();
    const approvalInterval = setInterval(checkPendingApprovals, 2500);

    // 2. Custom Window Event: Quick Action (Ctrl + Alt + Space)
    const handleQuickAction = () => {
      inputRef.current?.focus();
      inputRef.current?.select();
    };

    // 3. Custom Window Event: Desktop HITL Alert
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
  }, [conversationId, checkPendingApprovals]);

  // Text-To-Speech Playback
  const handleSpeakText = (text) => {
    if (!text || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    // Strip markdown formatting for cleaner speech
    const cleanSpeech = text
      .replace(/##\s*📌?\s*Discussion So Far[\s\S]*/gi, '')
      .replace(/\[\d+\]/g, '')
      .replace(/[*_#`|]/g, '')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanSpeech.slice(0, 500));
    utterance.rate = 1.05;
    utterance.pitch = 0.95;
    window.speechSynthesis.speak(utterance);
  };

  // Dispatch Command to Django Backend
  const handleDispatchCommand = async (e) => {
    if (e) e.preventDefault();
    const prompt = inputPrompt.trim();
    if (!prompt || isLoading) return;

    const initial = inferInitialModeAndEngine(prompt);

    setInputPrompt('');
    setCurrentTaskPrompt(prompt);
    setIsLoading(true);
    setStreamingChunk('');
    setActiveEngine(initial.engine);
    setActiveMode(initial.mode);
    setModeReason(initial.reason);
    setActiveStages(DEFAULT_PIPELINE_STAGES[initial.mode] || DEFAULT_PIPELINE_STAGES.LLM);
    setCurrentStage(DEFAULT_PIPELINE_STAGES[initial.mode]?.[0] || 'Understanding request');
    setAutomationTelemetry(null);
    setResearchTelemetry({ sourcesCount: 0, pagesCount: 0, domains: [], evidenceStatus: '' });
    setActiveAgent('Global Intent Router');
    setCurrentThought(`Analyzing directive: "${prompt}"...`);

    // Add user turn immediately
    setConversationHistory((prev) => [...prev, { role: 'user', text: prompt, content: prompt }]);
    retroSoundEngine.playKeyClick();

    // Cross-window sync with browser UI execution tabs
    try {
      localStorage.setItem('ops_active_query', prompt);
      localStorage.setItem('ops_conversation_id', conversationId);
      localStorage.setItem('ops_query_timestamp', Date.now().toString());
      postCockpitBroadcast({
        type: 'QUERY_STARTED',
        query: prompt,
        conversationId: conversationId,
        timestamp: Date.now()
      });
    } catch (_) {}

    const requestId = 'req_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7);

    if (abortCtrlRef.current) {
      try { abortCtrlRef.current.abort(); } catch (_) {}
    }
    const abortCtrl = new AbortController();
    abortCtrlRef.current = abortCtrl;

    try {
      const resp = await fetch(`/api/chat/conversations/${conversationId}/messages/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: prompt, input_type: 'text', request_id: requestId, active_documents: attachedDocs }),
        signal: abortCtrl.signal
      });

      if (resp.status === 409) {
        const conflictData = await resp.json().catch(() => ({}));
        throw new Error(conflictData.error || "Approval pending for this session.");
      }

      if (!resp.ok) {
        throw new Error(`Execution error (${resp.status})`);
      }

      const data = await resp.json();
      if (data.status === 'waiting_for_approval' || data.status === 'pending_approval' || data.approval_id) {
        const apprObj = {
          approval_id: data.approval_id,
          action_type: data.action_type || (['DESKTOP', 'BROWSER', 'HYBRID AUTO'].includes(data.response_mode || data.mode || initial.mode) ? 'AUTOMATION_ACTION' : 'SYSTEM_ACTION'),
          description: data.approval_reason || data.description || 'Human authorization required for action.',
          conversation_id: data.conversation_id || conversationId,
          metadata: {
            action_summary: data.approval_reason || data.description || 'Authorize system execution',
            target: data.target || data.target_application || data.target_url || data.target_file_path || 'System Target',
            target_application: data.target_application,
            target_url: data.target_url,
            target_file_path: data.target_file_path,
            execution_plan: data.execution_plan || data.plan,
            input_content: data.input_content,
            expected_result: data.expected_result,
            risk_level: data.risk_level || 'HIGH',
            is_destructive: data.is_destructive
          }
        };
        setPendingApproval(apprObj);
        setIsHitlModalOpen(true);
        setIsLoading(false);
        checkPendingApprovals();
      }
      const botAnswer = data.content || data.final_answer || data.response || "Task completed.";
      const finalCategory = data.response_mode || data.mode || resolveCategoryFromContent(botAnswer) || initial.mode || 'LLM';
      const finalEngine = data.active_engine || engineFromMode(finalCategory);

      setActiveEngine(finalEngine);
      setActiveMode(finalCategory);

      postCockpitBroadcast({
        type: 'QUERY_COMPLETED',
        query: prompt,
        finalAnswer: botAnswer,
        mode: finalCategory,
        engine: finalEngine,
        conversationId: conversationId
      });

      updateOrAppendAssistantTurn({
        text: botAnswer,
        content: botAnswer,
        category: finalCategory,
        plan: data.plan || data.execution_plan,
        citations: data.citations || [],
        summary: data.conversation_summary
      });

      retroSoundEngine.playBeep(520, 0.08);
    } catch (err) {
      if (err.name === 'AbortError') {
        // Ignored, stopped by user
      } else {
        setConversationHistory((prev) => [
          ...prev,
          { role: 'assistant', text: `⚠️ Error: ${err.message}`, content: `⚠️ Error: ${err.message}`, isError: true }
        ]);
      }
    } finally {
      abortCtrlRef.current = null;
      setIsLoading(false);
      setCurrentThought('');
      setStreamingChunk('');
      setActiveAgent('');
    }
  };

  // Emergency Halt / Cancel
  const handleEmergencyHalt = async () => {
    if (abortCtrlRef.current) {
      try { abortCtrlRef.current.abort(); } catch (_) {}
      abortCtrlRef.current = null;
    }

    try {
      await fetch(`/api/chat/conversations/${conversationId}/cancel/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (e) {
      console.warn("Halt error:", e);
    }

    if (streamingChunk) {
      setConversationHistory((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: streamingChunk + "\n\n*[⏹ Generation stopped by user]*",
          content: streamingChunk + "\n\n*[⏹ Generation stopped by user]*",
          category: 'CANCELLED'
        }
      ]);
    } else {
      setConversationHistory((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: "*[⏹ Generation stopped by user]*",
          content: "*[⏹ Generation stopped by user]*",
          category: 'CANCELLED'
        }
      ]);
    }

    setIsLoading(false);
    setActiveAgent('');
    setCurrentThought('⏹ Generation cancelled.');
    setStreamingChunk('');
  };

  // Temporary Document RAG: Upload and Index
  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset input so re-selecting same file works
    e.target.value = '';

    const validExtensions = ['pdf', 'docx', 'doc', 'txt', 'md', 'csv', 'json', 'py', 'js', 'html', 'log'];
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!validExtensions.includes(ext)) {
      setDocError(`Unsupported format '.${ext}'. Please choose a PDF (.pdf) or Word (.docx) document.`);
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      setDocError('File size exceeds the 25 MB limit.');
      return;
    }

    setDocError(null);
    setIsUploadingDoc(true);
    setDocUploadProgress(15);
    setDocUploadStatus('Receiving document...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      setDocUploadProgress(35);
      setDocUploadStatus('Extracting content...');
      const resp = await fetch(`/api/chat/conversations/${conversationId}/documents/upload/`, {
        method: 'POST',
        body: formData,
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.error || `Upload failed (${resp.status})`);
      }

      const data = await resp.json();
      setDocUploadProgress(100);
      setDocUploadStatus('Indexed & Ready');
      if (data.active_documents) {
        setAttachedDocs(data.active_documents);
      }
      retroSoundEngine?.playSuccess?.();
      setTimeout(() => {
        setIsUploadingDoc(false);
        setDocUploadStatus('');
      }, 1500);
    } catch (err) {
      setDocError(err.message);
      setIsUploadingDoc(false);
      setDocUploadStatus('');
      retroSoundEngine?.playError?.();
    }
  };

  // Temporary Document RAG: Remove Document
  const handleRemoveDoc = async (docId) => {
    try {
      const resp = await fetch(`/api/chat/conversations/${conversationId}/documents/${docId}/`, {
        method: 'DELETE',
      });
      if (resp.ok) {
        const data = await resp.json();
        setAttachedDocs(data.active_documents || []);
      }
    } catch (err) {
      console.warn("Failed to remove document:", err);
    }
  };

  // HITL: Request Refresh Approval
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
        throw new Error(errData.error || `Failed to initiate approval (${resp.status})`);
      }

      const data = await resp.json();
      setPendingApproval(data);
      setIsHitlModalOpen(true);
    } catch (err) {
      setCurrentThought(`[ERROR] Approval request failed: ${err.message}`);
    } finally {
      setIsHitlLoading(false);
    }
  };

  // HITL: Deny Decision
  const handleDenyApproval = async () => {
    const apprId = pendingApproval?.approval_id;
    if (apprId) {
      dismissedApprovalsRef.current.add(apprId);
      try {
        // 1. Universal approval responder endpoint
        const resp = await fetch(`/api/chat/approvals/${apprId}/respond/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ decision: 'reject', action: 'deny', conversation_id: conversationId })
        }).catch(() => null);

        const data = resp ? await resp.json().catch(() => ({})) : {};
        const cancelMsg = data?.message || data?.final_answer || "O.P.S. execution cancelled. No automation actions were performed.";

        setConversationHistory((prev) => [
          ...prev,
          {
            role: 'assistant',
            text: cancelMsg,
            content: cancelMsg,
            category: 'AUTOMATION',
            isCancelled: true
          }
        ]);
      } catch (e) {
        console.warn("Deny error:", e);
      }
    }
    setIsHitlModalOpen(false);
    setPendingApproval(null);
    setHitlError(null);
    setCurrentThought('DENIED — NO ACTIONS EXECUTED');
  };

  // HITL: Accept Decision
  const handleAcceptApproval = async () => {
    const apprId = pendingApproval?.approval_id;
    if (!apprId) return;
    setIsHitlLoading(true);
    setHitlError(null);
    dismissedApprovalsRef.current.add(apprId);

    try {
      if (pendingApproval?.action_type === 'PERMANENT_CONVERSATION_DELETION' || pendingApproval?.action_type === 'CONVERSATION_REFRESH') {
        const resp = await fetch(
          `/api/chat/conversations/${conversationId}/refresh-approval/${apprId}/accept/`,
          { method: 'POST', headers: { 'Content-Type': 'application/json' } }
        );

        if (!resp.ok) {
          const errData = await resp.json().catch(() => ({}));
          throw new Error(errData.error || `Server error (${resp.status})`);
        }

        const data = await resp.json();
        const nextConvId = data.new_conversation_id;

        // Reset state for clean session
        setConversationId(nextConvId);
        localStorage.setItem('ops_cockpit_conversation_id', nextConvId);
        localStorage.setItem('ops_conversation_id', nextConvId);

        postCockpitBroadcast({
          type: 'SESSION_RESET',
          newConversationId: nextConvId
        });
        setConversationHistory([]);
        setStreamingChunk('');
        setAttachedDocs([]);
        setDocError(null);
        setIsUploadingDoc(false);
        setCurrentThought('Fresh conversation initialized. Temporary document session cleared.');
        setIsHitlModalOpen(false);
        setPendingApproval(null);
        retroSoundEngine.playMemoryErase();
      } else {
        setCurrentThought('APPROVED — EXECUTION STARTING');
        const resp = await fetch(`/api/chat/approvals/${apprId}/respond/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ decision: 'approve', action: 'accept', conversation_id: conversationId })
        });
        if (!resp.ok) {
          const errData = await resp.json().catch(() => ({}));
          throw new Error(errData.error || `Server error (${resp.status})`);
        }
        const data = await resp.json();
        setIsHitlModalOpen(false);
        setPendingApproval(null);
        setCurrentThought('COMPLETED');

        const botAnswer = data.final_answer || data.content || data.response || "Automation execution completed.";
        const finalCategory = data.response_mode || data.mode || activeMode || 'AUTOMATION';
        const finalEngine = data.active_engine || 'AUTOMATION';

        setActiveEngine(finalEngine);
        setActiveMode(finalCategory);

        updateOrAppendAssistantTurn({
          text: botAnswer,
          content: botAnswer,
          category: finalCategory,
          plan: data.plan || data.step_results,
          summary: data.conversation_summary
        });
        retroSoundEngine.playBeep(780, 0.12);
      }
    } catch (err) {
      setHitlError(err.message);
      setCurrentThought(`FAILED: ${err.message}`);
    } finally {
      setIsHitlLoading(false);
    }
  };

  // Dynamic Desktop Window Drag / Move Handler
  const handleHeaderMouseDown = (e) => {
    if (e.button !== 0) return;
    if (e.target.closest('button, input, textarea, a, select')) return;

    // Immediately trigger native Qt / Windows system move
    try {
      document.title = `ops://drag/${Date.now()}`;
    } catch (_) {}
  };

  // Dynamic Desktop Window Edge/Corner Resizing Handler
  const handleResizePointerDown = (edge, e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();

    // Trigger native Qt / Windows system resize
    try {
      document.title = `ops://resize/${edge}/${Date.now()}`;
    } catch (_) {}
  };

  // Close Cockpit Window
  const handleCloseCockpit = () => {
    try {
      document.title = `ops://close/${Date.now()}`;
      const iframe = document.createElement('iframe');
      iframe.style.display = 'none';
      iframe.src = 'ops://close';
      document.body.appendChild(iframe);
      setTimeout(() => iframe.remove(), 80);
      window.close();
    } catch {
      window.close();
    }
  };

  return (
    <div className="relative flex flex-col h-full w-full bg-[#08080a]/95 backdrop-blur-md text-zinc-100 font-mono select-none overflow-hidden border border-zinc-800 shadow-2xl">
      {/* Live Resizing HUD Dimension Badge */}
      {isResizing && (
        <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 pointer-events-none px-4 py-2 bg-black/90 border border-red-500/80 rounded shadow-2xl text-red-400 font-mono text-xs tracking-wider flex items-center gap-2 backdrop-blur-md animate-pulse">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
          <span>RESIZING // {liveResizeDims.width} × {liveResizeDims.height} PX</span>
        </div>
      )}

      {/* Dynamic Native Window Resize Grips (Edges & Corners) */}
      {/* 4 Edges with generous 10px hit area and subtle hover feedback */}
      <div onPointerDown={(e) => handleResizePointerDown('top', e)} className="absolute top-0 left-6 right-6 h-2.5 cursor-n-resize z-40 hover:bg-red-500/10 transition-colors" title="Resize Top" />
      <div onPointerDown={(e) => handleResizePointerDown('bottom', e)} className="absolute bottom-0 left-6 right-6 h-2.5 cursor-s-resize z-40 hover:bg-red-500/10 transition-colors" title="Resize Bottom" />
      <div onPointerDown={(e) => handleResizePointerDown('left', e)} className="absolute top-6 bottom-6 left-0 w-2.5 cursor-w-resize z-40 hover:bg-red-500/10 transition-colors" title="Resize Left" />
      <div onPointerDown={(e) => handleResizePointerDown('right', e)} className="absolute top-6 bottom-6 right-0 w-2.5 cursor-e-resize z-40 hover:bg-red-500/10 transition-colors" title="Resize Right" />

      {/* 4 Corners with generous 28x28px hit area */}
      <div onPointerDown={(e) => handleResizePointerDown('top-left', e)} className="absolute top-0 left-0 w-7 h-7 cursor-nw-resize z-50 hover:bg-red-500/20 transition-colors" title="Resize Top-Left" />
      <div onPointerDown={(e) => handleResizePointerDown('top-right', e)} className="absolute top-0 right-0 w-7 h-7 cursor-ne-resize z-50 hover:bg-red-500/20 transition-colors" title="Resize Top-Right" />
      <div onPointerDown={(e) => handleResizePointerDown('bottom-left', e)} className="absolute bottom-0 left-0 w-7 h-7 cursor-sw-resize z-50 hover:bg-red-500/20 transition-colors" title="Resize Bottom-Left" />
      <div onPointerDown={(e) => handleResizePointerDown('bottom-right', e)} className="absolute bottom-0 right-0 w-7 h-7 cursor-se-resize z-50 hover:bg-red-500/20 transition-colors" title="Resize Bottom-Right" />

      {/* Human-in-the-Loop Modal Inside Separate Cockpit Window */}
      <HumanApprovalModal
        isOpen={isHitlModalOpen}
        actionType={pendingApproval?.action_type}
        title={pendingApproval?.action_type?.startsWith('AUTOMATION') ? "HUMAN-IN-THE-LOOP // EXECUTION APPROVAL" : "Human Approval Required"}
        subtitle={pendingApproval?.description || (pendingApproval?.action_type?.startsWith('AUTOMATION') ? "Authorize system automation task execution?" : "Delete Current Conversation?")}
        actionSummary={pendingApproval?.metadata?.action_summary || pendingApproval?.description}
        target={pendingApproval?.metadata?.target || pendingApproval?.target || pendingApproval?.metadata?.target_application || pendingApproval?.target_application || pendingApproval?.metadata?.target_file_path || pendingApproval?.metadata?.target_url}
        executionPlan={pendingApproval?.metadata?.execution_plan || pendingApproval?.execution_plan || pendingApproval?.metadata?.steps || pendingApproval?.plan}
        inputContent={pendingApproval?.metadata?.input_content || pendingApproval?.input_content}
        expectedResult={pendingApproval?.metadata?.expected_result || pendingApproval?.expected_result}
        isDestructive={pendingApproval?.metadata?.is_destructive || pendingApproval?.is_destructive}
        riskLevel={pendingApproval?.metadata?.risk_level || pendingApproval?.risk_level}
        denyLabel="DENY"
        denySublabel={pendingApproval?.action_type?.startsWith('AUTOMATION') ? "Cancel this automation step. No actions performed." : "Keep my conversation."}
        acceptLabel={pendingApproval?.action_type?.startsWith('AUTOMATION') ? "ACCEPT AND EXECUTE" : "ACCEPT"}
        acceptSublabel={pendingApproval?.action_type?.startsWith('AUTOMATION') ? "Authorize and begin execution." : "Delete and start fresh."}
        conversationId={conversationId}
        approvalId={pendingApproval?.approval_id}
        loading={isHitlLoading}
        error={hitlError}
        onAccept={handleAcceptApproval}
        onDeny={handleDenyApproval}
      />

      {/* Top Futuristic Accent Bar */}
      <div className="h-0.5 bg-gradient-to-r from-red-600 via-white/80 to-red-600 shrink-0"></div>

      {/* 4.A: DRAGGABLE PROFESSIONAL COCKPIT HEADER */}
      <header
        onMouseDown={handleHeaderMouseDown}
        className="h-11 px-3.5 bg-black/95 border-b border-zinc-800/80 flex items-center justify-between shrink-0 select-none z-30 cursor-grab active:cursor-grabbing"
        title="Click and drag to move Cockpit anywhere on your desktop"
      >
        {/* Assistant Identity & Status Tag */}
        <div className="flex items-center gap-2 min-w-0">
          <div className="relative flex items-center justify-center shrink-0">
            <span className="w-2 h-2 rounded-full bg-red-600 animate-ping absolute opacity-75"></span>
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 relative"></span>
          </div>
          <div className="flex items-center gap-1.5 min-w-0">
            <span className="px-1.5 py-0.5 bg-red-600 text-white font-black text-[11px] border border-red-500 shadow-sm tracking-wider shrink-0">
              O.P.S.
            </span>
            <span className="text-[10px] font-bold tracking-wider text-zinc-400 uppercase truncate">
              // COCKPIT
            </span>
          </div>

          {/* Status Indicator */}
          {isLoading ? (
            <span className="px-1.5 py-0.5 text-[9px] font-bold bg-red-950/80 border border-red-800 text-red-400 animate-pulse font-mono shrink-0">
              [BUSY: {activeAgent || 'THINKING'}]
            </span>
          ) : (
            <span className="px-1.5 py-0.5 text-[9px] font-bold bg-zinc-950 border border-zinc-800 text-zinc-400 font-mono shrink-0 hidden sm:inline">
              [STANDBY]
            </span>
          )}
        </div>

        {/* Right Header Controls: Refresh & Close (Non-draggable interactive buttons) */}
        <div className="flex items-center gap-1 shrink-0" onMouseDown={(e) => e.stopPropagation()}>
          {/* Refresh Button with Approved HITL Behavior */}
          <button
            type="button"
            onClick={handleRequestRefreshApproval}
            disabled={isLoading}
            className="p-1.5 rounded text-zinc-400 hover:text-red-400 hover:bg-zinc-900 border border-transparent hover:border-zinc-700 transition disabled:opacity-40"
            title="Permanently Delete Active Conversation & Refresh"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          {/* Window Close Button */}
          <button
            type="button"
            onClick={handleCloseCockpit}
            className="p-1.5 rounded text-zinc-400 hover:text-white hover:bg-zinc-800/80 transition"
            title="Close Cockpit [Ctrl + Alt + Space]"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* 4.A.2: COMPACT ACTIVE AGENT / CURRENT OPERATION TOP BAR */}
      <div className="px-3.5 py-1.5 bg-zinc-950/95 border-b border-zinc-800/80 flex items-center justify-between font-mono text-[10px] text-zinc-400 select-none overflow-x-auto whitespace-nowrap shadow-inner z-20">
        <div className="flex items-center gap-2.5">
          <span className="flex items-center gap-1">
            <span className="text-zinc-500 font-bold uppercase">ACTIVE ENGINE:</span>
            <span className={`font-black tracking-wide ${
              activeEngine === 'COMPOSITE' ? 'text-rose-400 font-extrabold animate-pulse' :
              activeEngine === 'AUTOMATION' ? 'text-cyan-400 font-extrabold' :
              activeEngine === 'ANSWERING' ? 'text-sky-400 font-extrabold' : 'text-zinc-300'
            }`}>
              {activeEngine || (isLoading ? 'ROUTING' : 'STANDBY')}
            </span>
          </span>
        </div>
        <div className="flex items-center gap-1.5 pl-2">
          <span className="text-zinc-500 font-bold uppercase">STATUS:</span>
          <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
            isLoading
              ? 'bg-amber-950/80 text-amber-300 border border-amber-800 animate-pulse'
              : 'bg-emerald-950/80 text-emerald-400 border border-emerald-800'
          }`}>
            {isLoading ? 'RUNNING' : 'STANDBY'}
          </span>
        </div>
      </div>

      {/* 4.B: MAIN CONVERSATION AREA */}
      <main
        ref={mainContainerRef}
        onScroll={handleScroll}
        className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden px-4 py-3 space-y-3.5 select-text font-mono overscroll-contain"
      >
        {conversationHistory.length === 0 && !isLoading ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-zinc-500 space-y-3 p-4 my-auto select-none">
            <div className="p-3 bg-zinc-950 border border-zinc-800 rounded-lg shadow-inner">
              <Bot className="w-8 h-8 text-red-500/80 stroke-1 animate-pulse" />
            </div>
            <div className="space-y-1.5">
              <h2 className="text-xs font-bold text-zinc-200 uppercase tracking-widest">
                === O.P.S. DESKTOP COCKPIT ===
              </h2>
              <div className="text-[11px] text-zinc-400 max-w-xs leading-relaxed font-mono space-y-1">
                <p>Continuous AI session active.</p>
                <div className="p-2 bg-zinc-950/80 border border-zinc-800/80 rounded text-[10px] text-left space-y-0.5 text-zinc-400">
                  <p><span className="text-red-400 font-bold">[Ctrl + Alt]</span>: Open Cockpit</p>
                  <p><span className="text-red-400 font-bold">[Ctrl + Alt + Space]</span>: Close Cockpit</p>
                  <p><span className="text-zinc-300 font-bold">Drag Header</span>: Move window</p>
                  <p><span className="text-zinc-300 font-bold">Drag Edges</span>: Resize window</p>
                </div>
              </div>

              {/* Standby Mode Engine Preview */}
              <div className="w-full max-w-xs p-2.5 bg-black/90 border border-zinc-800 rounded-lg space-y-2 text-left shadow-md">
                <div className="flex items-center justify-between text-[10px] font-bold text-zinc-300 border-b border-zinc-800/80 pb-1.5">
                  <span className="uppercase tracking-wider">DUAL EXECUTION ENGINES:</span>
                  <span className="text-emerald-400 font-mono text-[9px] animate-pulse">[ONLINE]</span>
                </div>
                {/* Answering Engine */}
                <div className="space-y-1">
                  <span className="text-[9px] text-zinc-400 font-bold uppercase">Answering Engine:</span>
                  <div className="grid grid-cols-4 gap-1 font-mono text-[9px]">
                    <div className="p-1 rounded bg-blue-950/40 border border-blue-800/60 text-center font-bold text-blue-400">LLM</div>
                    <div className="p-1 rounded bg-emerald-950/40 border border-emerald-800/60 text-center font-bold text-emerald-400">WEB</div>
                    <div className="p-1 rounded bg-purple-950/40 border border-purple-800/60 text-center font-bold text-purple-400">HYBRID</div>
                    <div className="p-1 rounded bg-amber-950/40 border border-amber-800/60 text-center font-bold text-amber-400">DOC</div>
                  </div>
                </div>
                {/* Automation Engine */}
                <div className="space-y-1 pt-1 border-t border-zinc-900">
                  <span className="text-[9px] text-zinc-400 font-bold uppercase">Automation Engine:</span>
                  <div className="grid grid-cols-3 gap-1 font-mono text-[9px]">
                    <div className="p-1 rounded bg-cyan-950/40 border border-cyan-800/60 text-center font-bold text-cyan-400">DESKTOP</div>
                    <div className="p-1 rounded bg-indigo-950/40 border border-indigo-800/60 text-center font-bold text-indigo-400">BROWSER</div>
                    <div className="p-1 rounded bg-rose-950/40 border border-rose-800/60 text-center font-bold text-rose-400">HYBRID AUTO</div>
                  </div>
                </div>
                <p className="text-[10px] text-zinc-500 leading-tight pt-1">
                  Semantic intent auto-routes directives across local intelligence, web research, and system automation.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <>
            {conversationHistory.map((turn, idx) => (
              <div key={idx} className="min-w-0 max-w-full break-words">
                {turn.role === 'user' ? (
                  <UserMessage turn={turn} />
                ) : (
                  <AssistantMessage
                    turn={turn}
                    idx={idx}
                    onSpeakText={handleSpeakText}
                  />
                )}
              </div>
            ))}

            {/* Live Streaming Response or Intelligent Animated Skeleton */}
            {isLoading && (
              <div className="min-w-0 max-w-full break-words">
                <CockpitLoadingSkeleton
                  query={currentTaskPrompt}
                  activeEngine={activeEngine}
                  activeAgent={activeAgent}
                  currentThought={currentThought}
                  streamingChunk={streamingChunk}
                  onStopExecution={handleEmergencyHalt}
                  compact={true}
                  activeMode={activeMode}
                  modeReason={modeReason}
                  stages={activeStages}
                  currentStage={currentStage}
                  researchTelemetry={researchTelemetry}
                  automationTelemetry={automationTelemetry}
                />
              </div>
            )}
          </>
        )}
        <div ref={scrollRef} />
      </main>

      {/* 4.C: COMPACT MESSAGE INPUT AREA */}
      <footer className="shrink-0 p-3 bg-black/95 border-t border-zinc-800/80 z-20">
        {/* Temporary Attached Documents Bar & Upload Progress */}
        {(attachedDocs.length > 0 || isUploadingDoc || docError) && (
          <div className="mb-2 p-1.5 rounded bg-zinc-950/90 border border-zinc-800 flex flex-wrap items-center gap-1.5 text-[11px] font-mono shadow-sm">
            {attachedDocs.map((doc) => (
              <div
                key={doc.doc_id}
                className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-amber-950/50 border border-amber-500/50 text-amber-200"
                title={`${doc.doc_name} (${doc.page_count} page${doc.page_count !== 1 ? 's' : ''}, ${doc.chunk_count} passages)`}
              >
                <FileText className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                <span className="max-w-[130px] truncate">{doc.doc_name}</span>
                <span className="text-[9px] px-1 bg-amber-500/20 text-amber-300 rounded font-bold">
                  {doc.page_count}p
                </span>
                <button
                  type="button"
                  onClick={() => handleRemoveDoc(doc.doc_id)}
                  className="hover:text-red-400 text-zinc-400 transition"
                  title="Remove document from temporary session"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}

            {isUploadingDoc && (
              <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-blue-950/50 border border-blue-500/50 text-blue-200 animate-pulse">
                <Loader2 className="w-3 h-3 text-blue-400 animate-spin shrink-0" />
                <span>{docUploadStatus || 'Indexing...'}</span>
              </div>
            )}

            {docError && (
              <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-red-950/50 border border-red-500/50 text-red-300">
                <AlertCircle className="w-3 h-3 text-red-400 shrink-0" />
                <span className="max-w-[220px] truncate">{docError}</span>
                <button type="button" onClick={() => setDocError(null)} className="hover:text-white">
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}
          </div>
        )}

        <form onSubmit={handleDispatchCommand} className="flex items-center gap-2 w-full min-w-0">
          {/* Document Attachment Button & Hidden File Input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.doc,.txt,.md,.csv,.json,.py,.js,.html,.log"
            onChange={handleFileUpload}
            className="hidden"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading || isUploadingDoc}
            className={`w-9 h-9 p-0 rounded border transition shrink-0 flex items-center justify-center ${
              attachedDocs.length > 0
                ? 'bg-amber-950/50 text-amber-300 border-amber-500/60 shadow-sm'
                : 'bg-zinc-900 text-zinc-400 hover:text-amber-300 border-zinc-700 hover:border-amber-500/50'
            } disabled:opacity-40`}
            title="Attach temporary document (.pdf, .docx, .doc)"
          >
            <Paperclip className="w-4 h-4" />
          </button>

          <input
            ref={inputRef}
            id="ops-command-input"
            type="text"
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            placeholder={
              attachedDocs.length > 0
                ? `Ask anything about ${attachedDocs[0].doc_name}...`
                : "Command O.P.S. (e.g. 'Explain RAG', 'Compare Rust and Go')..."
            }
            disabled={isLoading}
            className="flex-1 min-w-0 h-9 px-3 bg-zinc-950 border border-zinc-700/80 focus:border-red-500 focus:ring-1 focus:ring-red-500 rounded text-xs text-white placeholder-zinc-500 outline-none transition font-mono shadow-inner disabled:opacity-60"
            autoFocus
          />

          {/* Send / Stop Button */}
          {isLoading ? (
            <button
              type="button"
              onClick={handleEmergencyHalt}
              className="h-9 px-3.5 bg-red-950 hover:bg-red-900 text-red-300 border border-red-700 rounded transition flex items-center gap-1.5 font-bold text-xs shrink-0 shadow-sm"
              title="Stop ongoing generation"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>STOP</span>
            </button>
          ) : (
            <button
              type="submit"
              disabled={!inputPrompt.trim()}
              className="h-9 px-4 bg-red-600 hover:bg-red-500 text-white border border-red-500 rounded transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5 font-bold text-xs shadow-md shrink-0"
              title="Send directive [ENTER]"
            >
              <Send className="w-3.5 h-3.5" />
              <span>SEND</span>
            </button>
          )}
        </form>

        <div className="flex items-center justify-between text-[9px] text-zinc-500 pt-2 px-0.5 select-none">
          <span>[Ctrl + Alt]: Open | [Ctrl + Alt + Space]: Close</span>
          <div className="flex items-center gap-2">
            <span>[Enter]: Send</span>
            {/* Visual tactical resize grip */}
            <div
              onPointerDown={(e) => handleResizePointerDown('bottom-right', e)}
              className="cursor-se-resize p-0.5 hover:text-red-400 text-zinc-600 transition-colors flex items-end justify-end shrink-0"
              title="Drag to resize window"
            >
              <svg className="w-2.5 h-2.5" viewBox="0 0 10 10" fill="none" stroke="currentColor">
                <line x1="9" y1="1" x2="1" y2="9" strokeWidth="1.2" strokeLinecap="round" />
                <line x1="9" y1="4.5" x2="4.5" y2="9" strokeWidth="1.2" strokeLinecap="round" />
                <line x1="9" y1="8" x2="8" y2="9" strokeWidth="1.2" strokeLinecap="round" />
              </svg>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
