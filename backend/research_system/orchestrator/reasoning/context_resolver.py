"""
O.P.S. 2.0 — Conversation Context & Anaphora Resolver
Stage 1: Extracts antecedents, tracks active project/application state,
and applies user corrections across multi-turn sessions.
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("OPS.Reasoning.ContextResolver")


class ConversationContextResolver:
    """
    Analyzes historical conversational turns to resolve references,
    preserve established project parameters, and handle user corrections.
    """

    @classmethod
    def resolve_context(
        cls,
        current_query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Extracts active contextual state and resolves anaphora in current_query.
        """
        history = conversation_history or []
        if not history:
            return {
                "active_app": None,
                "active_project": None,
                "active_file": None,
                "active_language": None,
                "active_framework": None,
                "context_summary": "Initial turn; no prior conversational state.",
                "resolved_query": current_query,
                "is_correction": False,
                "is_continuation": False
            }

        # Scan history in chronological order
        active_app = None
        active_project = None
        active_file = None
        active_language = None
        active_framework = None
        last_action = None

        for turn in history:
            content = str(turn.get("content") or turn.get("text") or "").strip()
            c_low = content.lower()

            # Detect apps
            for app in ["vs code", "vscode", "notepad", "calculator", "chrome", "edge", "terminal"]:
                if app in c_low:
                    active_app = app

            # Detect files
            file_match = re.findall(r"([a-zA-Z0-9_\-\.]+\.(?:py|js|ts|tsx|jsx|html|css|json|md|txt|docx|pdf))", content)
            if file_match:
                active_file = file_match[-1]

            # Detect languages / frameworks
            if "typescript" in c_low or ".ts" in c_low:
                active_language = "TypeScript"
            elif "javascript" in c_low or ".js" in c_low:
                active_language = "JavaScript"
            elif "python" in c_low or ".py" in c_low:
                active_language = "Python"

            if "react" in c_low:
                active_framework = "React"
            elif "django" in c_low:
                active_framework = "Django"
            elif "fastapi" in c_low:
                active_framework = "FastAPI"
            elif "vue" in c_low:
                active_framework = "Vue"

            # Detect project
            proj_match = re.search(r"create\s+(?:a\s+)?([a-zA-Z0-9_\- ]+?\s+project)", content, re.IGNORECASE)
            if proj_match:
                active_project = proj_match.group(1).strip()
            elif active_framework:
                active_project = f"{active_framework} project"

        # Check if current_query is a correction or continuation
        q_low = current_query.lower()
        is_correction = any(w in q_low for w in ["instead", "actually", "change that", "rather than", "switch to", "not "])
        is_continuation = any(w in q_low for w in [
            "now add", "add a", "open it", "run it", "put it", "same", "also", "and then",
            "the other component", "the same feature"
        ]) or (len(current_query.split()) <= 4 and not any(q_low.startswith(p) for p in ["what", "who", "why", "how", "explain"]))

        # Apply correction overrides
        if "typescript" in q_low and "instead" in q_low:
            active_language = "TypeScript"
        elif "javascript" in q_low and "instead" in q_low:
            active_language = "JavaScript"
        elif "python" in q_low and "instead" in q_low:
            active_language = "Python"

        # Build context summary
        summary_parts = []
        if active_project:
            summary_parts.append(f"Project: {active_project}")
        if active_language:
            summary_parts.append(f"Language: {active_language}")
        if active_framework:
            summary_parts.append(f"Framework: {active_framework}")
        if active_file:
            summary_parts.append(f"Target File: {active_file}")
        if active_app:
            summary_parts.append(f"Active App: {active_app}")

        context_summary = "; ".join(summary_parts) if summary_parts else "Prior turns active but no explicit entity locked."

        # Pronoun & Anaphora Resolution in query string
        resolved_q = current_query
        if (" it" in q_low or q_low.startswith("it ")) and active_file:
            resolved_q = re.sub(r"\b(it|that file)\b", active_file, resolved_q, flags=re.IGNORECASE)
        elif (" it" in q_low or q_low.startswith("it ")) and active_project:
            resolved_q = re.sub(r"\b(it|the project)\b", active_project, resolved_q, flags=re.IGNORECASE)

        return {
            "active_app": active_app,
            "active_project": active_project,
            "active_file": active_file,
            "active_language": active_language,
            "active_framework": active_framework,
            "context_summary": context_summary,
            "resolved_query": resolved_q,
            "is_correction": is_correction,
            "is_continuation": is_continuation
        }
