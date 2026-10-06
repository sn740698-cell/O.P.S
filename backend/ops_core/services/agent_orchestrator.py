"""
O.P.S. Complete Multi-Agent Orchestrator
Implementation strictly conforms to: O.P.S. — Agent Architecture & Build Specification

Pipeline Architecture:
1. Core Agents:
   - Prompt Template Agent (Qwen3 0.6B)
   - Understand Prompt / Router Agent (Qwen3 1.7B)
2. Superior Agents:
   - Web Superior Agent (Qwen3 1.7B) [Web Prompt Understanding -> Extractor -> Retrieval Quality Loop]
   - Automation Superior Agent (Qwen3 1.7B) [Automation Prompt Understanding -> HITL Gate -> Execution Routing]
3. Final Processing:
   - Result Agent (Qwen3 0.6B)
   - Jarvis Persona Agent (Llama 3.2 1B)
"""

import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END

from ops_core.services.event_bus import OPSEventBus
from ops_core.services.ollama_service import OPSOllamaService
from ops_core.services.session_memory import OPSSessionMemoryManager
from ops_core.services.workstation_memory_service import OPSWorkstationMemoryService

from ops_core.services.agents.base_agent import AgentTaskState
from ops_core.services.agents.prompt_template_agent import PromptTemplateAgent
from ops_core.services.agents.router_agent import RouterAgent
from ops_core.services.agents.web_agents import WebSuperiorAgent
from ops_core.services.agents.automation_agents import AutomationSuperiorAgent
from ops_core.services.agents.final_agents import ResultAgent, JarvisPersonaAgent

logger = logging.getLogger("ops.agent_orchestrator")


class OPSMultiAgentOrchestrator:
    """
    Authoritative Orchestrator executing the complete O.P.S. 4-tier agent hierarchy.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(OPSMultiAgentOrchestrator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self.ollama = OPSOllamaService()
        self.memory = OPSSessionMemoryManager()
        self.workstation_memory = OPSWorkstationMemoryService()

        # Instantiate all 14 agents + superiors
        self.prompt_template_agent = PromptTemplateAgent(ollama_service=self.ollama)
        self.router_agent = RouterAgent(ollama_service=self.ollama)
        self.web_superior_agent = WebSuperiorAgent(ollama_service=self.ollama)
        self.automation_superior_agent = AutomationSuperiorAgent(ollama_service=self.ollama)
        self.result_agent = ResultAgent(ollama_service=self.ollama)
        self.jarvis_persona_agent = JarvisPersonaAgent(ollama_service=self.ollama)

        # Build LangGraph Workflow
        self._graph = self._build_workflow_graph()
        self._initialized = True
        logger.info("O.P.S. Complete Authoritative Agent Orchestrator initialized successfully.")

    def _build_workflow_graph(self):
        graph = StateGraph(AgentTaskState)

        # 1. Define Nodes
        graph.add_node("prompt_template", self._node_prompt_template)
        graph.add_node("router", self._node_router)
        graph.add_node("web_superior", self._node_web_superior)
        graph.add_node("automation_superior", self._node_automation_superior)
        graph.add_node("result_agent", self._node_result_agent)
        graph.add_node("jarvis_persona", self._node_jarvis_persona)

        # 2. Set Entry Point
        graph.set_entry_point("prompt_template")

        # 3. Core Transitions
        graph.add_edge("prompt_template", "router")

        # 4. Conditional Routing from Router Agent (WEB vs AUTOMATION)
        graph.add_conditional_edges(
            "router",
            self._route_domain_decision,
            {
                "WEB": "web_superior",
                "AUTOMATION": "automation_superior"
            }
        )

        # 5. Superiors merge into Result Agent
        graph.add_edge("web_superior", "result_agent")
        graph.add_edge("automation_superior", "result_agent")

        # 6. Result Agent to Jarvis Persona
        graph.add_edge("result_agent", "jarvis_persona")
        graph.add_edge("jarvis_persona", END)

        return graph.compile()

    def _route_domain_decision(self, state: AgentTaskState) -> str:
        domain = state.get("route_domain", "WEB")
        return "AUTOMATION" if domain == "AUTOMATION" else "WEB"

    # =========================================================================
    # Node Wrappers
    # =========================================================================
    async def _node_prompt_template(self, state: AgentTaskState) -> Dict[str, Any]:
        return await self.prompt_template_agent.process(state)

    async def _node_router(self, state: AgentTaskState) -> Dict[str, Any]:
        return await self.router_agent.process(state)

    async def _node_web_superior(self, state: AgentTaskState) -> Dict[str, Any]:
        return await self.web_superior_agent.process(state)

    async def _node_automation_superior(self, state: AgentTaskState) -> Dict[str, Any]:
        return await self.automation_superior_agent.process(state)

    async def _node_result_agent(self, state: AgentTaskState) -> Dict[str, Any]:
        return await self.result_agent.process(state)

    async def _node_jarvis_persona(self, state: AgentTaskState) -> Dict[str, Any]:
        return await self.jarvis_persona_agent.process(state)

    # =========================================================================
    # Async Runner API
    # =========================================================================
    async def run_task_async(
        self,
        prompt: str,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
        source: str = "web_ui",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Main entry point for executing user requests through the O.P.S. multi-agent system.
        """
        task_id = task_id or str(uuid.uuid4())
        session_id = session_id or f"sess_{int(time.time())}"
        start_time = time.time()

        # Resolve multi-turn contextual prompt using active session state
        resolved_prompt = self.memory.resolve_contextual_prompt(session_id, prompt)

        initial_state: AgentTaskState = {
            "task_id": task_id,
            "session_id": session_id,
            "prompt": resolved_prompt,
            "original_prompt": prompt,
            "status": "PROCESSING",
            "actions_completed": [],
            "actions_failed": [],
            "raw_facts": {},
            "execution_log": []
        }

        # Emit initial task started event
        await OPSEventBus.emit_task_started_async(
            task_id=task_id,
            prompt=resolved_prompt,
            agent="Prompt Template Agent"
        )

        try:
            # Execute through LangGraph workflow
            final_state = await self._graph.ainvoke(initial_state)

            final_speech = final_state.get("final_jarvis_speech") or final_state.get("structured_result") or "Done."
            structured_res = final_state.get("structured_result", "")
            domain = final_state.get("route_domain", "WEB")
            plan = final_state.get("action_plan") or final_state.get("actions_completed") or []

            duration_ms = int((time.time() - start_time) * 1000)

            # Emit final task completed event
            await OPSEventBus.emit_task_completed_async(
                task_id=task_id,
                final_answer=final_speech,
                category=domain,
                plan=plan,
                details={"structured_result": structured_res, "duration_ms": duration_ms}
            )

            # Record turn in active multi-turn session memory
            try:
                self.memory.add_turn(
                    session_id=session_id,
                    user_prompt=prompt,
                    assistant_response=final_speech,
                    plan_steps=plan,
                    tool_logs=final_state.get("actions_completed", []),
                    structured_data={"domain": domain, "structured_result": structured_res}
                )
            except Exception as e:
                logger.debug(f"Session memory save notice: {e}")

            return {
                "task_id": task_id,
                "session_id": session_id,
                "status": "COMPLETED",
                "route_domain": domain,
                "structured_result": structured_res,
                "final_answer": final_speech,
                "plan": plan,
                "duration_ms": duration_ms,
                "state": final_state
            }

        except Exception as e:
            logger.error(f"Error in O.P.S. multi-agent pipeline execution: {e}", exc_info=True)
            error_msg = f"I encountered an issue executing that directive: {str(e)}"
            await OPSEventBus.emit_task_completed_async(
                task_id=task_id,
                final_answer=error_msg,
                category="ERROR",
                plan=[],
                details={"error": str(e), "duration_ms": int((time.time() - start_time) * 1000)}
            )
            return {
                "task_id": task_id,
                "session_id": session_id,
                "status": "ERROR",
                "error": str(e),
                "final_answer": error_msg
            }
