"""
O.P.S. Canonical Supervisor
Coordinates routing, planning, agent delegation, mission execution, and response synthesis.
Never bypasses the Capability Registry, Safety Gate, or Ground-Truth Verifier.
"""

import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from ops_core.router.fast_router import FastRouter, RoutingDecision, ExecutionMode
from ops_core.orchestration.planner import Planner
from ops_core.orchestration.mission_manager import MissionManager, MissionState
from ops_core.capabilities.registry import CapabilityRegistry
from ops_core.tools.executor import ToolExecutor
from ops_core.services.event_bus import OPSEventBus
from ops_core.core.events import OPSEventType, create_event

from ops_core.agents.developer_agent import DeveloperAgent
from ops_core.agents.debugger_agent import DebuggerAgent
from ops_core.agents.tester_agent import TesterAgent
from ops_core.agents.reviewer_agent import ReviewerAgent
from ops_core.agents.web_agent import WebAgent
from ops_core.agents.research_agent import ResearchAgent
from ops_core.agents.automation_agent import AutomationAgent
from ops_core.agents.browser_agent import BrowserAgent
from ops_core.agents.rag_agent import RAGAgent
from ops_core.agents.response_agent import ResponseAgent

logger = logging.getLogger("ops.orchestration.supervisor")


class SupervisorResponse(BaseModel):
    mode: ExecutionMode
    status: str                              # "SUCCESS", "FAILED", "BLOCKED", "NEEDS_CLARIFICATION"
    content: str
    session_id: str
    mission_id: Optional[str] = None
    agent: Optional[str] = None
    tool: Optional[str] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class Supervisor:
    def __init__(self):
        self.router = FastRouter()
        self.planner = Planner()
        self.mission_manager = MissionManager()
        self.executor = ToolExecutor()
        
        # Instantiate specialized agents
        self.agents = {
            "developer": DeveloperAgent(executor=self.executor),
            "debugger": DebuggerAgent(executor=self.executor),
            "tester": TesterAgent(executor=self.executor),
            "reviewer": ReviewerAgent(executor=self.executor),
            "web": WebAgent(executor=self.executor),
            "research": ResearchAgent(executor=self.executor),
            "automation": AutomationAgent(executor=self.executor),
            "browser": BrowserAgent(executor=self.executor),
            "rag": RAGAgent(executor=self.executor),
            "response": ResponseAgent(executor=self.executor)
        }

    async def handle_request(
        self,
        user_input: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> SupervisorResponse:
        """
        Main entrypoint for all user requests from the Pop-up Cockpit.
        """
        context = context or {}
        context["session_id"] = session_id

        # 1. Fast Router determines mode & required agent/capability
        route: RoutingDecision = await self.router.route(user_input, context)
        logger.info(f"Router decision: mode={route.mode}, agent={route.suggested_agent}, capability={route.suggested_capability}")

        # Broadcast routing event
        await OPSEventBus.emit_thought_async(
            thought=f"Input routed to [{route.mode.value}] mode (Complexity: {route.estimated_complexity})",
            agent="Router"
        )

        # 2. Dispatch based on mode
        if route.mode == ExecutionMode.CHAT:
            return await self._handle_chat(user_input, session_id, route, context)
        elif route.mode == ExecutionMode.TASK:
            return await self._handle_task(user_input, session_id, route, context)
        elif route.mode == ExecutionMode.MISSION:
            return await self._handle_mission(user_input, session_id, route, context)
        elif route.mode == ExecutionMode.MEMORY:
            return await self._handle_memory(user_input, session_id, route, context)
        elif route.mode == ExecutionMode.CLARIFICATION:
            return await self._handle_clarification(user_input, session_id, route, context)
        else:
            return await self._handle_chat(user_input, session_id, route, context)

    async def _handle_chat(
        self,
        user_input: str,
        session_id: str,
        route: RoutingDecision,
        context: Dict[str, Any]
    ) -> SupervisorResponse:
        """
        Fast-path conversational response without executing unnecessary tools/plans.
        """
        response_agent = self.agents["response"]
        result = await response_agent.process(user_input, context={"session_id": session_id, "evidence": {}})
        return SupervisorResponse(
            mode=ExecutionMode.CHAT,
            status="SUCCESS",
            content=result.summary,
            session_id=session_id,
            agent="Response"
        )

    async def _handle_task(
        self,
        user_input: str,
        session_id: str,
        route: RoutingDecision,
        context: Dict[str, Any]
    ) -> SupervisorResponse:
        """
        Direct single-capability execution via specialized agent.
        """
        agent_key = route.suggested_agent or "automation"
        agent = self.agents.get(agent_key, self.agents["automation"])

        # Execute through agent
        res = await agent.process(user_input, context)
        
        # Ground through Response Agent
        synth = await self.agents["response"].process(
            directive=user_input,
            context={
                "session_id": session_id,
                "status": res.status,
                "evidence": res.evidence,
                "error": res.error
            }
        )

        return SupervisorResponse(
            mode=ExecutionMode.TASK,
            status=res.status,
            content=synth.summary,
            session_id=session_id,
            agent=agent.name,
            tool=route.suggested_capability,
            evidence=res.evidence,
            error=res.error
        )

    async def _handle_mission(
        self,
        user_input: str,
        session_id: str,
        route: RoutingDecision,
        context: Dict[str, Any]
    ) -> SupervisorResponse:
        """
        Multi-step mission decomposed by Planner and executed by Mission Manager.
        """
        # Step 1: Planner creates decomposition
        await OPSEventBus.emit_thought_async(
            thought=f"Formulating decomposition plan with Qwen3 1.7B...",
            agent="Planner"
        )
        plan = await self.planner.create_plan(user_input, context)

        # Step 2: Mission Manager executes with bounded recovery and verifier
        mission_record = await self.mission_manager.execute_mission(
            goal=user_input,
            plan=plan,
            session_id=session_id
        )

        # Step 3: Response Engine synthesizes final report
        evidence = {
            "mission_id": mission_record.mission_id,
            "status": mission_record.status.value,
            "steps_count": len(plan.steps),
            "completed_steps": len(mission_record.step_results),
            "step_results": {k: v.model_dump() for k, v in mission_record.step_results.items()}
        }

        synth = await self.agents["response"].process(
            directive=user_input,
            context={
                "session_id": session_id,
                "mission_id": mission_record.mission_id,
                "status": "SUCCESS" if mission_record.status == MissionState.COMPLETED else "FAILED",
                "evidence": evidence,
                "error": mission_record.error
            }
        )

        return SupervisorResponse(
            mode=ExecutionMode.MISSION,
            status="SUCCESS" if mission_record.status == MissionState.COMPLETED else "FAILED",
            content=synth.summary,
            session_id=session_id,
            mission_id=mission_record.mission_id,
            agent="Mission Manager",
            evidence=evidence,
            error=mission_record.error
        )

    async def _handle_memory(
        self,
        user_input: str,
        session_id: str,
        route: RoutingDecision,
        context: Dict[str, Any]
    ) -> SupervisorResponse:
        """
        Persistent memory indexing or retrieval.
        """
        rag_agent = self.agents["rag"]
        res = await rag_agent.process(user_input, context)
        synth = await self.agents["response"].process(
            directive=user_input,
            context={"session_id": session_id, "evidence": res.evidence, "status": res.status}
        )
        return SupervisorResponse(
            mode=ExecutionMode.MEMORY,
            status=res.status,
            content=synth.summary,
            session_id=session_id,
            agent="RAG",
            evidence=res.evidence
        )

    async def _handle_clarification(
        self,
        user_input: str,
        session_id: str,
        route: RoutingDecision,
        context: Dict[str, Any]
    ) -> SupervisorResponse:
        """
        Prompts user for essential missing specifications.
        """
        question = route.clarification_question or "Could you clarify the specific parameters or target for this action?"
        return SupervisorResponse(
            mode=ExecutionMode.CLARIFICATION,
            status="NEEDS_CLARIFICATION",
            content=question,
            session_id=session_id,
            agent="Supervisor"
        )
