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
  X
} from 'lucide-react';

/**
 * Reusable Human-in-the-Loop (HITL) Approval Modal.
 * Strictly renders EXACTLY TWO buttons: DENY (default focus) and ACCEPT.
 * Prevents outside-click dismissal, Escape-key dismissal, and close (X) button dismissal.
 */
export default function HumanApprovalModal({
  isOpen,
  title = "Human Approval Required",
  subtitle = "Delete Current Conversation?",
  conversationId = "",
  approvalId = "",
  itemsToDelete = [],
  itemsNotDeleted = [],
  importantNotice = "",
  denyLabel = "DENY",
  denySublabel = "Keep my conversation.",
  acceptLabel = "ACCEPT",
  acceptSublabel = "Delete and start fresh.",
  loading = false,
  error = null,
  onAccept,
  onDeny
}) {
  const denyButtonRef = useRef(null);
  const acceptButtonRef = useRef(null);

  // Focus the DENY button by default on open & lock keyboard Escape dismissal and trap Tab focus
  useEffect(() => {
    if (isOpen) {
      // Focus deny option as mandatory default
      setTimeout(() => {
        denyButtonRef.current?.focus();
      }, 50);

      // Dismiss on Escape key
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
            // Shift + Tab
            if (document.activeElement === firstElement) {
              e.preventDefault();
              lastElement.focus();
            }
          } else {
            // Tab
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

  // Backdrop click dismisses modal
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
                {title}
              </h2>
              <div className="text-xs text-red-400 font-semibold tracking-wide truncate">
                &gt; {subtitle}
              </div>
              {conversationId && (
                <div className="text-[10px] text-zinc-500 font-mono pt-0.5 truncate">
                  Target Conversation: <span className="text-zinc-300 font-semibold">{conversationId}</span>
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

        {/* Main Operational Explanation */}
        <div id="hitl-description" className="space-y-3.5 text-xs text-zinc-300 leading-relaxed">
          <p className="text-zinc-200">
            You are about to permanently delete your active O.P.S. conversation and start a completely new conversation.
          </p>

          {/* Section: If you accept */}
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

          {/* Section: What will NOT be deleted */}
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

          {/* Section: IMPORTANT Notice */}
          <div className="p-3 bg-red-950/60 border-2 border-red-600 text-red-200 space-y-1">
            <div className="font-black text-xs uppercase tracking-wider text-red-400 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
              <span>IMPORTANT:</span>
            </div>
            <p className="text-[11px] leading-snug">
              {defaultWarning}
            </p>
          </div>

          {/* Recoverable Backend Error Banner */}
          {error && (
            <div className="p-3 bg-red-900 border border-white text-white space-y-1 animate-pulse">
              <div className="font-black text-xs uppercase tracking-wider flex items-center gap-1.5">
                <XCircle className="w-4 h-4" />
                <span>BACKEND DELETION ERROR:</span>
              </div>
              <p className="text-[11px] leading-snug">{error}</p>
              <div className="text-[10px] text-red-200 pt-0.5">
                The conversation state was preserved intact. You may safely select Deny to resume.
              </div>
            </div>
          )}
        </div>

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
              {denySublabel}
            </div>
          </button>

          {/* RIGHT BUTTON: ACCEPT */}
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
                <span>{loading ? "PROCESSING DELETION..." : acceptLabel}</span>
              </span>
              {loading ? (
                <span className="text-[9px] text-red-200 uppercase tracking-widest font-mono">PLEASE WAIT</span>
              ) : (
                <span className="text-[9px] text-red-200 uppercase tracking-widest font-mono">[CLICK]</span>
              )}
            </div>
            <div className="text-[11px] text-red-200 group-hover:text-white mt-1">
              {acceptSublabel}
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
