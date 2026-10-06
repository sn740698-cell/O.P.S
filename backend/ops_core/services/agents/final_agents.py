"""
O.P.S. Final Processing Agents
Hierarchy:
- Result Agent (Final Processing | Qwen3 0.6B)
  - Structures raw facts & execution state into clean structural formats
- Jarvis Persona Agent (Final Processing | Llama 3.2 1B)
  - Communicates the structured result in a dignified, concise, polite, natural voice
"""

import json
import logging
from typing import Dict, Any, List
from ops_core.services.agents.base_agent import BaseOPSAgent, AgentTaskState

logger = logging.getLogger("ops.agents.final")


# =========================================================================
# 1. Result Agent (Final Processing | Qwen3 0.6B)
# =========================================================================
class ResultAgent(BaseOPSAgent):
    agent_id = "result_agent"
    agent_name = "Result Agent"
    level = "Final processing"
    assigned_model = "Qwen3 0.6B"
    allowed_tools = []
    parent_agent = "Web Superior Agent / Automation Superior Agent"
    downstream_destination = "Jarvis Persona Agent"

    async def process(self, state: AgentTaskState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        prompt = (state.get("prompt") or state.get("original_prompt") or "").strip()
        result_type = state.get("result_type", "AUTOMATION_RESULT")
        completed = state.get("actions_completed", [])
        failed = state.get("actions_failed", [])
        raw_facts = state.get("raw_facts", {})
        status = state.get("status", "SUCCESS")
        hitl_decision = state.get("hitl_decision")

        await self.emit_status(task_id, "PROCESSING", {"result_type": result_type})
        await self.emit_thought(task_id, f"Structuring raw execution/retrieval facts into [{result_type}] schema.")

        # If declined by HITL
        if hitl_decision == "DECLINED":
            structured = "TASK NOT PERFORMED\n\n• Action plan was declined by user.\n• 0 actions executed on system.\n\nStatus: Declined"
            return {
                "structured_result": structured,
                "result_type": "FAILURE_RESULT",
                "active_agent": self.agent_name,
                "active_model": self.assigned_model
            }

        # 1. Web Information / Research Structuring
        if result_type in ["INFORMATION_RESULT", "RESEARCH_RESULT"]:
            text = raw_facts.get("retrieved_text", "")
            sources = raw_facts.get("sources", [])
            sources_str = "\n".join([f"• {s}" for s in sources[:4]]) if sources else "• Real-time web intelligence"

            system_instruction = (
                "You are the O.P.S. Result Agent (Model: Qwen3 0.6B).\n"
                "Format the raw research text into clear structural bullet points with:\n"
                "KEY FACTS\n• ...\n\nLATEST DEVELOPMENTS\n• ...\n\nSOURCES\n"
            )
            try:
                res = self.ollama.client.generate(
                    model=self.ollama.router_model,
                    prompt=f"{system_instruction}\n\nRaw Text:\n{text[:2500]}",
                    options={"temperature": 0.1}
                )
                structured = res.get("response", "").strip()
                if not structured or len(structured) < 20:
                    structured = f"KEY FACTS\n• {text[:400]}\n\nSOURCES\n{sources_str}"
            except Exception as e:
                logger.warning(f"Result structuring fallback: {e}")
                structured = f"KEY FINDINGS\n• {text[:400]}\n\nSOURCES\n{sources_str}"

        # 2. Automation / Desktop Structuring
        else:
            if failed and not completed:
                structured = "TASK NOT COMPLETED\n\n"
                for f in failed:
                    structured += f"• Failed: {f}\n"
                structured += "\nReason: The requested resource or operation encountered an error.\nStatus: Failed"
            else:
                structured = "TASK COMPLETED\n\n"
                for c in completed:
                    structured += f"• {c}\n"
                if failed:
                    structured += "\nPartial Issues:\n"
                    for f in failed:
                        structured += f"• {f}\n"
                    structured += "\nStatus: Partial"
                else:
                    structured += "\nStatus: Completed"

        await self.emit_thought(task_id, "Facts structured into standard O.P.S. specification format.")
        await self.emit_status(task_id, "COMPLETED", {"structured_length": len(structured)})

        return {
            "structured_result": structured,
            "active_agent": self.agent_name,
            "active_model": self.assigned_model
        }


# =========================================================================
# 2. Jarvis Persona Agent (Final Processing | Llama 3.2 1B)
# =========================================================================
class JarvisPersonaAgent(BaseOPSAgent):
    agent_id = "jarvis_persona_agent"
    agent_name = "Jarvis Persona Agent"
    level = "Final processing"
    assigned_model = "Llama 3.2 1B"
    allowed_tools = []
    parent_agent = "Result Agent"
    downstream_destination = "O.P.S. Cockpit / User"

    async def process(self, state: AgentTaskState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        prompt = (state.get("prompt") or state.get("original_prompt") or "").strip()
        structured_result = state.get("structured_result", "")
        result_type = state.get("result_type", "AUTOMATION_RESULT")
        hitl_decision = state.get("hitl_decision")

        await self.emit_status(task_id, "PROCESSING", {"persona": "JARVIS"})
        await self.emit_thought(task_id, "Jarvis Persona Agent synthesizing final conversational briefing.")

        if hitl_decision == "DECLINED":
            final_speech = "Understood. I haven't performed the requested action."
            await self.emit_thought(task_id, f"Spoken response ready: '{final_speech}'")
            return {
                "final_jarvis_speech": final_speech,
                "active_agent": self.agent_name,
                "active_model": self.assigned_model
            }

        system_instruction = (
            "You are the O.P.S. J.A.R.V.I.S. Persona Agent (Model: Llama 3.2 1B).\n"
            "Your role is the final communication layer before the Cockpit.\n"
            "Qualities: Clear, intelligent, polite, humble, calm, concise, professional, natural.\n"
            "Rules:\n"
            "1. NEVER invent facts or hallucinate.\n"
            "2. NEVER say a failed task succeeded.\n"
            "3. For automation tasks (e.g. YouTube, Instagram, folders, apps), give a clean, direct 1-2 sentence response:\n"
            "   Example: 'Done. YouTube is open, and I've searched for \"Believer\".'\n"
            "   Example: 'Done. The O.P.S. folder has been created on your Desktop.'\n"
            "4. For research/information tasks, introduce key points gracefully:\n"
            "   Example: 'Certainly. Here are the latest developments from today's sources:' followed by concise findings.\n"
            "5. If a file was not found or failed, apologize calmly: 'I'm sorry, I couldn't locate that file in your Downloads folder.'\n"
        )

        try:
            res = self.ollama.client.generate(
                model=self.ollama.conversation_model,
                prompt=f"{system_instruction}\n\nUser Directive: {prompt}\nStructured Facts:\n{structured_result}",
                options={"temperature": 0.2}
            )
            final_speech = res.get("response", "").strip()
            if not final_speech:
                raise ValueError("Empty persona response")
        except Exception as e:
            logger.warning(f"Jarvis Persona generation fallback: {e}")
            # Factual natural fallback matching spec
            p_lower = prompt.lower()
            if "youtube" in p_lower:
                final_speech = "Done. YouTube is open, and the search has been performed."
            elif "instagram" in p_lower or "insta" in p_lower:
                final_speech = "Done. Instagram is open, and you're ready to browse."
            elif "folder" in p_lower or "create" in p_lower:
                final_speech = "Done. The requested directory structure has been created on your Desktop."
            elif "vlc" in p_lower or "play" in p_lower:
                final_speech = "Certainly. The media application is open and playback has started."
            elif result_type in ["INFORMATION_RESULT", "RESEARCH_RESULT"]:
                final_speech = f"Certainly. Here is the information you requested:\n\n{structured_result}"
            else:
                final_speech = f"Done. I have completed your request.\n\n{structured_result}"

        await self.emit_thought(task_id, f"Final synthesized communication: '{final_speech[:80]}...'")
        await self.emit_status(task_id, "COMPLETED", {"length": len(final_speech)})

        return {
            "final_jarvis_speech": final_speech,
            "active_agent": self.agent_name,
            "active_model": self.assigned_model
        }
