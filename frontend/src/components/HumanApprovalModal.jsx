import React, { useEffect, useRef } from 'react';
import {
  AlertTriangle,
  ShieldAlert,
  Loader2,
  CheckCircle2,
  XCircle,
  Database,
  ShieldCheck,
  RotateCcw,
  Terminal,
  Globe,
  FileCode,
  Folder,
  Layers,
  X
} from 'lucide-react';

/**
 * Reusable Human-in-the-Loop (HITL) Approval Modal.
 * Supports:
 * 1. Global Automation Engine Execution Approval (Desktop, Browser, Hybrid, File System)
 * 2. Conversation Refresh / Permanent Deletion Authorization
 * Strictly renders EXACTLY TWO buttons: DENY (default focus) and ACCEPT AND EXECUTE.
 * Prevents outside-click dismissal, Escape-key dismissal, and close (X) button dismissal.
 */
export default function HumanApprovalModal({
  isOpen,
  actionType = "",
  title = "HUMAN-IN-THE-LOOP // EXECUTION APPROVAL",
  subtitle = "",
  actionSummary = "",
  target = "",
  executionPlan = [],
  inputContent = "",
  expectedResult = "",
  isDestructive = false,
  riskLevel = "STANDARD",
  conversationId = "",
  approvalId = "",
  itemsToDelete = [],
  itemsNotDeleted = [],
  importantNotice = "",
  denyLabel = "DENY",
  denySublabel = "Cancel execution. No actions performed.",
  acceptLabel = "ACCEPT AND EXECUTE",
  acceptSublabel = "Authorize and begin execution.",
  loading = false,
  error = null,
  onAccept,
  onDeny
}) {
  const denyButtonRef = useRef(null);
  const acceptButtonRef = useRef(null);

  const isAutomation = Boolean(
    actionType?.startsWith('AUTOMATION') ||
    actionSummary ||
    target ||
    (executionPlan && executionPlan.length > 0)
  );

  // Focus the DENY button by default on open & lock keyboard Escape dismissal and trap Tab focus
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        denyButtonRef.current?.focus();
      }, 50);

      const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          e.stopPropagation();
          if (onDeny) onDeny();
          return;
        }

        if (e.key === 'Tab') {
          const focusableElements = [denyButtonRef.current, acceptButtonRef.current].filter(Boolean);
          if (focusableElements.length === 0) return;

          const firstElement = focusableElements[0];
          const lastElement = focusableElements[focusableElements.length - 1];

          if (e.shiftKey) {
            if (document.activeElement === firstElement) {
              e.preventDefault();
              lastElement.focus();
            }
          } else {
            if (document.activeElement === lastElement) {
              e.preventDefault();
              firstElement.focus();
            }
          }
        }
      };

      window.addEventListener('keydown', handleKeyDown, true);
      return () => window.removeEventListener('keydown', handleKeyDown, true);
    }
  }, [isOpen, onDeny]);

  if (!isOpen) return null;

  const handleBackdropClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (onDeny) onDeny();
  };

  const defaultItemsToDelete = itemsToDelete.length > 0 ? itemsToDelete : [
    "Permanently delete all messages belonging to the current conversation.",
    "Delete the conversation-specific context and stored summaries.",
    "Delete the associated LangGraph conversation checkpoints and persisted execution state.",
    "Delete temporary conversation-specific data and attachments owned exclusively by this conversation.",
    "Cancel or invalidate active generation and pending execution associated with the conversation wherever technically possible.",
    "Remove conversation-specific temporary caches.",
    "Generate a new unique conversation ID.",
    "Initialize a completely fresh conversation with no previous chat history."
  ];

  const defaultItemsNotDeleted = itemsNotDeleted.length > 0 ? itemsNotDeleted : [
    "O.P.S. long-term memory.",
    "User preferences and settings.",
    "Project files and source code.",
    "Shared RAG documents and knowledge base.",
    "Other conversations.",
    "Global application configuration."
  ];

  const defaultWarning = importantNotice || (
    "This operation is permanent and cannot be undone after successful backend deletion. Your previous conversation cannot be restored."
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/85 backdrop-blur-md font-mono select-none"
      onClick={handleBackdropClick}
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="hitl-title"
      aria-describedby="hitl-description"
    >
      <div
        className="relative w-full max-w-2xl bg-black border-2 border-red-600 rounded-none shadow-[0_0_50px_rgba(220,38,38,0.45)] text-zinc-100 p-5 sm:p-6 space-y-4 max-h-[92vh] overflow-y-auto animate-in fade-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Retro Scanner Top Accent Bar */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-600 via-white to-red-600 animate-pulse"></div>

        {/* Modal Header with Dismiss Button */}
        <div className="border-b border-zinc-800 pb-3 flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 min-w-0">
            <div className="p-2.5 bg-red-950 border border-red-600 text-red-500 rounded-none shrink-0">
              <ShieldAlert className="w-6 h-6 animate-pulse" />
            </div>
            <div className="space-y-0.5 min-w-0">
              <div className="text-[10px] uppercase font-bold tracking-widest text-red-400">
                [ HUMAN-IN-THE-LOOP AUTHORIZATION GATE ]
              </div>
              <h2 id="hitl-title" className="text-base sm:text-lg font-black tracking-wide text-white uppercase truncate">
                {isAutomation ? "HUMAN-IN-THE-LOOP // EXECUTION APPROVAL" : title}
              </h2>
              <div className="text-xs text-red-400 font-semibold tracking-wide truncate">
                &gt; {isAutomation ? (actionSummary || "Mandatory execution permission requested") : (subtitle || "Delete Current Conversation?")}
              </div>
              {conversationId && (
                <div className="text-[10px] text-zinc-500 font-mono pt-0.5 truncate">
                  Conversation: <span className="text-zinc-300 font-semibold">{conversationId}</span>
                  {approvalId && <> | Approval ID: <span className="text-zinc-400">{approvalId}</span></>}
                </div>
              )}
            </div>
          </div>
          <button
            type="button"
            onClick={onDeny}
            className="p-1 rounded text-zinc-400 hover:text-white hover:bg-zinc-800 transition shrink-0"
            title="Dismiss / Cancel [Escape]"
          >
            <X className="w-5 h-5 text-zinc-400 hover:text-red-400" />
          </button>
        </div>

        {/* Modal Body: Automation Approval OR Refresh Deletion Approval */}
        {isAutomation ? (
          <div id="hitl-description" className="space-y-3.5 text-xs text-zinc-300 leading-relaxed">
            {/* 1. ACTION SUMMARY */}
            <div className="p-3 bg-zinc-950 border border-zinc-800 space-y-1">
              <div className="font-bold text-[10px] uppercase tracking-wider text-red-400 flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5 text-red-400 shrink-0" />
                <span>ACTION SUMMARY:</span>
              </div>
              <p className="text-xs text-zinc-100 font-semibold leading-relaxed">
                {actionSummary || "Execute automation directive using controlled system tools."}
              </p>
            </div>

            {/* 2. TARGET */}
            <div className="p-3 bg-zinc-950 border border-zinc-800 space-y-1">
              <div className="font-bold text-[10px] uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                <Globe className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                <span>TARGET APPLICATION / WEBSITE / FILE / FOLDER:</span>
              </div>
              <p className="text-xs text-zinc-200 font-mono break-all bg-black/60 p-2 border border-zinc-800">
                {target || "System Desktop & Web Automation Engine"}
              </p>
            </div>

            {/* 3. EXECUTION PLAN */}
            <div className="p-3 bg-zinc-950 border border-zinc-800 space-y-2">
              <div className="font-bold text-[10px] uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>PROPOSED EXECUTION PLAN:</span>
              </div>
              {executionPlan && executionPlan.length > 0 ? (
                <ol className="list-none space-y-1 text-[11px] text-zinc-300 pl-0">
                  {executionPlan.map((op, idx) => (
                    <li key={idx} className="leading-snug flex items-start gap-2 bg-zinc-900/60 p-1.5 border-l-2 border-emerald-500">
                      <span className="text-emerald-400 font-mono shrink-0 font-bold">[{idx + 1}]</span>
                      <span className="text-zinc-200">{typeof op === 'string' ? op.replace(/^\d+\.\s*/, '') : (op.title || op.action)}</span>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="text-zinc-400 text-xs">Execute ordered automation pipeline steps.</p>
              )}
            </div>

            {/* 4. INPUT / CONTENT (if applicable) */}
            {inputContent && (
              <div className="p-3 bg-zinc-950 border border-zinc-800 space-y-1">
                <div className="font-bold text-[10px] uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                  <FileCode className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  <span>INPUT / CONTENT TO BE SUBMITTED OR WRITTEN:</span>
                </div>
                <pre className="text-[11px] text-zinc-200 font-mono bg-black/70 p-2 border border-zinc-800 overflow-x-auto whitespace-pre-wrap max-h-36">
                  {inputContent}
                </pre>
              </div>
            )}

            {/* 5. EXPECTED RESULT */}
            <div className="p-3 bg-zinc-950 border border-zinc-800 space-y-1">
              <div className="font-bold text-[10px] uppercase tracking-wider text-purple-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                <span>EXPECTED RESULT:</span>
              </div>
              <p className="text-xs text-zinc-300 leading-snug">
                {expectedResult || "Operations executed sequentially and verified on local environment."}
              </p>
            </div>

            {/* DESTRUCTIVE WARNING (if applicable) */}
            {isDestructive && (
              <div className="p-3 bg-red-950/70 border-2 border-red-600 text-red-200 space-y-1 animate-pulse">
                <div className="font-black text-xs uppercase tracking-wider text-red-400 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                  <span>DESTRUCTIVE OPERATION WARNING:</span>
                </div>
                <p className="text-[11px] leading-snug">
                  This operation deletes or permanently modifies resources on disk. Files removed will not be recoverable from system recycling.
                </p>
              </div>
            )}

            {/* Error Banner */}
            {error && (
              <div className="p-3 bg-red-900 border border-white text-white space-y-1">
                <div className="font-black text-xs uppercase tracking-wider flex items-center gap-1.5">
                  <XCircle className="w-4 h-4" />
                  <span>EXECUTION GATE ERROR:</span>
                </div>
                <p className="text-[11px] leading-snug">{error}</p>
              </div>
            )}
          </div>
        ) : (
          /* Conversation Deletion Refresh View */
          <div id="hitl-description" className="space-y-3.5 text-xs text-zinc-300 leading-relaxed">
            <p className="text-zinc-200">
              You are about to permanently delete your active O.P.S. conversation and start a completely new conversation.
            </p>

            <div className="p-3 bg-zinc-950 border border-zinc-800 space-y-2">
              <div className="font-bold text-[11px] uppercase tracking-wider text-red-400 flex items-center gap-1.5">
                <span>IF YOU ACCEPT, O.P.S. WILL PERFORM THE FOLLOWING OPERATIONS:</span>
              </div>
              <ol className="list-decimal list-inside space-y-1 text-[11px] text-zinc-300 pl-1">
                {defaultItemsToDelete.map((item, idx) => (
                  <li key={idx} className="leading-snug">{item}</li>
                ))}
              </ol>
            </div>

            <div className="p-3 bg-zinc-950 border border-zinc-800 space-y-2">
              <div className="font-bold text-[11px] uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>WHAT WILL NOT BE DELETED:</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-[11px] text-zinc-400 pl-1">
                {defaultItemsNotDeleted.map((item, idx) => (
                  <li key={idx} className="leading-snug text-zinc-300">{item}</li>
                ))}
              </ul>
            </div>

            <div className="p-3 bg-red-950/60 border-2 border-red-600 text-red-200 space-y-1">
              <div className="font-black text-xs uppercase tracking-wider text-red-400 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                <span>IMPORTANT:</span>
              </div>
              <p className="text-[11px] leading-snug">{defaultWarning}</p>
            </div>

            {error && (
              <div className="p-3 bg-red-900 border border-white text-white space-y-1 animate-pulse">
                <div className="font-black text-xs uppercase tracking-wider flex items-center gap-1.5">
                  <XCircle className="w-4 h-4" />
                  <span>BACKEND DELETION ERROR:</span>
                </div>
                <p className="text-[11px] leading-snug">{error}</p>
              </div>
            )}
          </div>
        )}

        {/* EXACTLY TWO BUTTONS: DENY (LEFT, DEFAULT FOCUS) and ACCEPT (RIGHT) */}
        <div className="sticky bottom-0 bg-black/95 pt-3 pb-1 border-t border-zinc-800 grid grid-cols-1 sm:grid-cols-2 gap-3 z-20 shadow-lg">
          {/* LEFT BUTTON: DENY (DEFAULT KEYBOARD FOCUS) */}
          <button
            ref={denyButtonRef}
            type="button"
            onClick={onDeny}
            disabled={loading}
            className="w-full p-3 bg-zinc-900 hover:bg-zinc-800 border-2 border-zinc-600 hover:border-zinc-400 focus:border-white focus:bg-zinc-800 focus:ring-2 focus:ring-white outline-none text-left transition disabled:opacity-40 group cursor-pointer"
            autoFocus
          >
            <div className="flex items-center justify-between">
              <span className="font-black text-sm text-white tracking-wider flex items-center gap-1.5">
                <XCircle className="w-4 h-4 text-zinc-400 group-hover:text-white" />
                <span>{denyLabel}</span>
              </span>
              <span className="text-[9px] text-zinc-500 uppercase tracking-widest font-mono">[ENTER]</span>
            </div>
            <div className="text-[11px] text-zinc-400 group-hover:text-zinc-200 mt-1">
              {denySublabel || (isAutomation ? "Cancel this automation step. No actions performed." : "Keep my conversation.")}
            </div>
          </button>

          {/* RIGHT BUTTON: ACCEPT AND EXECUTE */}
          <button
            ref={acceptButtonRef}
            type="button"
            onClick={onAccept}
            disabled={loading}
            className="w-full p-3 bg-red-700 hover:bg-red-600 focus:bg-red-600 border-2 border-red-500 hover:border-white focus:border-white focus:ring-2 focus:ring-red-400 outline-none text-left transition shadow-lg disabled:opacity-40 group cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <span className="font-black text-sm text-white tracking-wider flex items-center gap-1.5">
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 text-white" />
                )}
                <span>{loading ? "EXECUTING..." : (isAutomation ? "ACCEPT AND EXECUTE" : acceptLabel)}</span>
              </span>
              {loading ? (
                <span className="text-[9px] text-red-200 uppercase tracking-widest font-mono">PLEASE WAIT</span>
              ) : (
                <span className="text-[9px] text-red-200 uppercase tracking-widest font-mono">[CLICK]</span>
              )}
            </div>
            <div className="text-[11px] text-red-200 group-hover:text-white mt-1">
              {acceptSublabel || (isAutomation ? "Authorize and begin execution." : "Delete and start fresh.")}
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
