"""
O.P.S. 2.0 — Understanding and Reasoning Agent
Connects Qwen3 1.7B with multi-stage context resolution,
schema contract parsing, and deterministic self-correction.
"""

import json
import time
import logging
from typing import Dict, Any, List, Optional

from research_system.llm.ollama_client import ollama_client, MODEL_QWEN_1_7B
from .schema import ReasoningPlanContract
from .context_resolver import ConversationContextResolver
from .validator import ReasoningPlanValidator
from .prompt_engine import QWEN_1_7B_UNDERSTANDING_SYSTEM_PROMPT, build_understanding_user_prompt

logger = logging.getLogger("OPS.Reasoning.UnderstandingAgent")


class AdvancedPromptUnderstandingAgent:
    """
    Main understanding and reasoning engine powered by Qwen3 1.7B.
    Orchestrates the 6-stage understanding pipeline.
    """

    def __init__(self, model_name: str = MODEL_QWEN_1_7B):
        self.model_name = model_name

    def understand_and_plan(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes full multi-stage pipeline:
        Stage 1: Context resolution
        Stage 2-6: Model reasoning + structured contract synthesis
        Stage 9: Deterministic validation & self-correction
        """
        t0 = time.time()
        tid = task_id or f"task_{int(time.time() * 1000)}"

        # Stage 1: Context & Anaphora Resolution
        context_res = ConversationContextResolver.resolve_context(query, conversation_history)
        context_summary = context_res.get("context_summary", "")
        resolved_q = context_res.get("resolved_query", query)

        # Stage 2-6: Prompt synthesis and LLM inference
        user_prompt = build_understanding_user_prompt(query, context_summary, resolved_q)

        raw_contract = None
        try:
            resp_str = ollama_client.generate(
                model=self.model_name,
                prompt=user_prompt,
                system_prompt=QWEN_1_7B_UNDERSTANDING_SYSTEM_PROMPT,
                json_mode=True,
                temperature=0.1,
                timeout=30.0
            )

            # Clean JSON markdown if wrapped
            clean_json = resp_str.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[-1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()

            parsed_data = json.loads(clean_json)
            parsed_data["task_id"] = tid
            raw_contract = ReasoningPlanContract(**parsed_data)

        except Exception as e:
            logger.warning(f"Model generation or parsing fallback notice: {e}")
            # Create standard deterministic baseline contract
            raw_contract = self._build_fallback_contract(query, tid, context_res)

        # Stage 9: Deterministic Validation & Self-Correction Gate
        validated_contract, was_valid, corrections = ReasoningPlanValidator.validate_and_correct(
            contract=raw_contract,
            raw_query=query,
            context=context_res
        )

        duration = round(time.time() - t0, 3)
        result_dict = validated_contract.model_dump()
        result_dict["latency_s"] = duration
        result_dict["corrections_applied"] = corrections
        result_dict["context"] = context_res

        logger.info(
            f"Understood directive: Type={result_dict['task_type']} | "
            f"AnsEngine={result_dict['answering_engine']} | "
            f"AutoEngine={result_dict['automation_engine']} in {duration}s"
        )
        return result_dict

    def _build_fallback_contract(self, query: str, task_id: str, context: Dict[str, Any]) -> ReasoningPlanContract:
        """Constructs an initial structured contract when model parsing needs a scaffold."""
        q_low = query.lower()

        # Check for explanation / concept queries
        if any(p in q_low for p in ["explain", "how do i", "what is", "difference between", "tell me about"]):
            return ReasoningPlanContract(
                task_id=task_id,
                task_type="ANSWER",
                user_objective=f"Provide technical explanation for: {query}",
                answering_engine="LLM",
                automation_engine="NONE",
                confidence=0.95,
                reasoning_summary="Identified informational inquiry; routed to LLM Mode."
            )

        # Check for explicit search web keyword directives
        if "search web" in q_low or "search the web" in q_low or bool(re.search(r"\bsearch\s+(?:the\s+)?web\b", q_low)):
            return ReasoningPlanContract(
                task_id=task_id,
                task_type="RESEARCH",
                user_objective=f"Search the web and retrieve answers for: {query}",
                answering_engine="WEB",
                automation_engine="NONE",
                confidence=0.99,
                reasoning_summary="Explicit 'search web' directive routed directly to WEB Mode in Answering Engine."
            )

        # Check for web research queries
        if any(w in q_low for w in ["latest", "recent", "current version", "who won", "news"]):
            return ReasoningPlanContract(
                task_id=task_id,
                task_type="RESEARCH",
                user_objective=f"Research external facts for: {query}",
                answering_engine="WEB",
                automation_engine="NONE",
                confidence=0.95,
                reasoning_summary="Identified requirement for external fresh facts; routed to Web Mode."
            )

        # Check for automation queries
        return ReasoningPlanContract(
            task_id=task_id,
            task_type="AUTOMATION",
            user_objective=f"Execute system operation: {query}",
            answering_engine="NONE",
            automation_engine="DESKTOP",
            confidence=0.90,
            approval_required=True,
            reasoning_summary="Identified actionable directive; routed to Automation Engine."
        )
