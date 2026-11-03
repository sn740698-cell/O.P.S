"""
O.P.S. 2.0 — Conversation Summary Service
Maintains the continuous '📌 Discussion So Far' summary for active conversations.
Updated dynamically after each completed assistant turn, preserving key topics,
decisions, requirements, and completed tasks.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from research_system.llm.ollama_client import ollama_client, MODEL_QWEN_1_7B

logger = logging.getLogger("OPS.ConversationSummary")

SUMMARY_HEADING = "## 📌 Discussion So Far"


def extract_summary_from_text(text: str) -> Optional[str]:
    """
    Extracts the '📌 Discussion So Far' section from a generated response if present.
    Supports ##, ###, bold, or plain variations.
    """
    if not text:
        return None
    pattern = r"(?:#{1,4}\s*📌?\s*Discussion So Far.*?\n|\*\*📌?\s*Discussion So Far\*\*:?\s*\n?)([\s\S]*)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        summary_body = match.group(1).strip()
        if summary_body:
            return summary_body
    return None


def generate_updated_summary(
    previous_summary: str,
    conversation_turns: List[Dict[str, str]],
    latest_query: str,
    latest_answer: str
) -> str:
    """
    Generates an updated, concise bullet-point summary of the active conversation.
    Integrates prior summary with latest user directive and assistant resolution.
    """
    # Clean previous summary
    prior_bullets = []
    if previous_summary:
        for line in previous_summary.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*") or line.startswith("•"):
                prior_bullets.append(line.lstrip("-*• ").strip())

    # Build prompt for summary generation
    history_lines = []
    for turn in conversation_turns[-8:]:
        role = turn.get("role", "user").upper()
        content = turn.get("content", turn.get("text", ""))[:200]
        history_lines.append(f"{role}: {content}")

    if latest_query:
        history_lines.append(f"USER: {latest_query[:200]}")
    if latest_answer:
        # Strip existing summary from latest answer to avoid recursion
        clean_answer = re.sub(r"##\s*📌?\s*Discussion So Far[\s\S]*", "", latest_answer).strip()
        history_lines.append(f"ASSISTANT: {clean_answer[:250]}")

    conversation_context = "\n".join(history_lines)

    system_prompt = (
        "You are the Conversation Summarizer for O.P.S. 2.0. "
        "Your role is to maintain a concise, high-level summary of the active conversation. "
        "Rules:\n"
        "1. Write 3 to 7 short, clear bullet points summarizing key topics discussed, decisions made, "
        "requirements established, tasks completed, or unresolved items.\n"
        "2. Do NOT repeat the entire dialogue word-for-word.\n"
        "3. Remove outdated points if the user reversed or changed a previous decision.\n"
        "4. Do NOT invent information that was not discussed.\n"
        "5. Respond ONLY with bullet points starting with '- '."
    )

    user_prompt = (
        f"Prior Summary Bullets:\n"
        + ("\n".join(f"- {b}" for b in prior_bullets) if prior_bullets else "None (New session)")
        + f"\n\nRecent Conversation Turns:\n{conversation_context}\n\n"
        "Provide the updated bullet points:"
    )

    try:
        raw_output = ollama_client.generate(
            model=MODEL_QWEN_1_7B,
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            timeout=6.0
        )
        lines = [l.strip() for l in raw_output.split("\n") if l.strip().startswith(("-", "*", "•"))]
        if lines:
            cleaned_bullets = [re.sub(r"^[-*•]\s*", "- ", l) for l in lines]
            return "\n".join(cleaned_bullets[:8])
    except Exception as e:
        logger.warning(f"Ollama summary generation failed: {e}. Generating structured fallback.")

    # High-quality deterministic fallback
    bullets = list(prior_bullets)
    if latest_query:
        # Synthesize concise bullet for the latest turn
        topic = latest_query[:60].strip()
        bullets.append(f"Explored and addressed user directive regarding: '{topic}'.")

    # Deduplicate while preserving order and limit to latest 6 bullets
    seen = set()
    unique_bullets = []
    for b in bullets:
        norm = b.lower().strip()
        if norm not in seen and len(norm) > 5:
            seen.add(norm)
            unique_bullets.append(b)

    final_bullets = unique_bullets[-6:]
    return "\n".join(f"- {b}" for b in final_bullets)


def attach_summary_to_response(
    response_text: str,
    summary_bullets: str
) -> str:
    """
    Ensures the response text ends cleanly with the '## 📌 Discussion So Far' section.
    """
    clean_text = re.sub(r"\n*##\s*📌?\s*Discussion So Far[\s\S]*$", "", response_text).strip()
    if not summary_bullets.strip():
        return clean_text

    formatted_summary = f"\n\n{SUMMARY_HEADING}\n\n{summary_bullets.strip()}"
    return clean_text + formatted_summary
