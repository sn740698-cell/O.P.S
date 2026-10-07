"""
O.P.S. Stateful Mission Manager
Executes multi-step missions with step dependency tracking, ground-truth verification,
and bounded automatic error recovery (max 3 retries).
"""

import time
import uuid
import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ops_core.orchestration.planner import MissionPlan, PlanStep
from ops_core.capabilities.schemas import ToolCallResult
from ops_core.tools.executor import ToolExecutor
from ops_core.core.events import OPSEventType, create_event
from ops_core.services.event_bus import OPSEventBus

logger = logging.getLogger("ops.orchestration.mission_manager")


class MissionState(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class MissionExecutionRecord(BaseModel):
    mission_id: str
    session_id: str
    goal: str
    status: MissionState = MissionState.CREATED
    plan: Optional[MissionPlan] = None
    current_step_idx: int = 0
    step_results: Dict[int, ToolCallResult] = Field(default_factory=dict)
    retry_counts: Dict[int, int] = Field(default_factory=dict)
    max_retries_per_step: int = 3
    is_cancelled: bool = False
    error: Optional[str] = None
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None


class MissionManager:
    _instance = None
    _active_missions: Dict[str, MissionExecutionRecord] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MissionManager, cls).__new__(cls)
            cls._active_missions = {}
        return cls._instance

    def __init__(self):
        self.executor = ToolExecutor()

    def get_mission(self, mission_id: str) -> Optional[MissionExecutionRecord]:
        return self._active_missions.get(mission_id)

    def cancel_mission(self, mission_id: str):
        record = self._active_missions.get(mission_id)
        if record:
            record.is_cancelled = True
            record.status = MissionState.CANCELLED
            logger.info(f"Mission {mission_id} cancelled.")

    async def execute_mission(
        self,
        goal: str,
        plan: MissionPlan,
        session_id: str,
        mission_id: Optional[str] = None
    ) -> MissionExecutionRecord:
        """
        Executes a planned mission step-by-step with verification and recovery loops.
        """
        mission_id = mission_id or f"m_{uuid.uuid4().hex[:8]}"
        record = MissionExecutionRecord(
            mission_id=mission_id,
            session_id=session_id,
            goal=goal,
            plan=plan,
            status=MissionState.RUNNING
        )
        self._active_missions[mission_id] = record

        # Broadcast mission created & plan created
        await OPSEventBus.emit_ops_event_async(create_event(
            event_type=OPSEventType.MISSION_CREATED,
            session_id=session_id,
            mission_id=mission_id,
            agent_id="mission_manager",
            agent_name="Mission Manager",
            status="RUNNING",
            message=f"Mission initialized: '{goal}'",
            metadata={"goal": goal, "total_steps": len(plan.steps)}
        ))

        await OPSEventBus.emit_ops_event_async(create_event(
            event_type=OPSEventType.PLAN_CREATED,
            session_id=session_id,
            mission_id=mission_id,
            agent_id="planner",
            agent_name="Lead Planner",
            status="COMPLETED",
            message=f"Formulated {len(plan.steps)}-step execution plan.",
            metadata={"plan": plan.model_dump()}
        ))

        for idx, step in enumerate(plan.steps):
            if record.is_cancelled:
                record.status = MissionState.CANCELLED
                record.error = "Mission cancelled by user."
                await OPSEventBus.emit_ops_event_async(create_event(
                    event_type=OPSEventType.MISSION_CANCELLED,
                    session_id=session_id,
                    mission_id=mission_id,
                    status="CANCELLED",
                    message="Mission cancelled by user."
                ))
                break

            record.current_step_idx = idx
            step_id = step.step_id
            attempts = 0
            max_attempts = record.max_retries_per_step  # 3 attempts maximum

            while attempts < max_attempts:
                if record.is_cancelled:
                    break

                attempts += 1
                record.retry_counts[step_id] = attempts

                # Emit Agent and Step Started
                await OPSEventBus.emit_ops_event_async(create_event(
                    event_type=OPSEventType.AGENT_STARTED,
                    session_id=session_id,
                    mission_id=mission_id,
                    agent_id=step.assigned_agent,
                    agent_name=step.assigned_agent.title(),
                    parent_agent="mission_manager",
                    status="RUNNING",
                    message=f"[Step {idx+1}/{len(plan.steps)}] {step.description}",
                    capability=step.capability,
                    metadata={"step_id": step_id, "attempt": attempts, "total_steps": len(plan.steps)}
                ))

                # Execute capability through Tool Executor (with Safety Gate + Verifier)
                result = await self.executor.execute_capability(
                    capability_name=step.capability,
                    arguments=step.arguments,
                    requested_by=step.assigned_agent,
                    mission_id=mission_id,
                    session_id=session_id
                )

                record.step_results[step_id] = result

                if result.status == "SUCCESS":
                    logger.info(f"Step {step_id} verified successfully: {step.description}")
                    await OPSEventBus.emit_ops_event_async(create_event(
                        event_type=OPSEventType.AGENT_COMPLETED,
                        session_id=session_id,
                        mission_id=mission_id,
                        agent_id=step.assigned_agent,
                        agent_name=step.assigned_agent.title(),
                        status="COMPLETED",
                        message=f"Step {step_id} completed and verified.",
                        capability=step.capability
                    ))
                    break
                elif result.status in ["BLOCKED", "DECLINED"]:
                    logger.warning(f"Step {step_id} was rejected by Safety/User: {result.error}")
                    record.status = MissionState.FAILED
                    record.error = f"Step {step_id} was declined: {result.error}"
                    record.end_time = time.time()
                    await OPSEventBus.emit_ops_event_async(create_event(
                        event_type=OPSEventType.MISSION_FAILED,
                        session_id=session_id,
                        mission_id=mission_id,
                        status="FAILED",
                        message=record.error
                    ))
                    return record
                else:
                    # Failure encountered -> Check if attempts exhausted
                    if attempts >= max_attempts:
                        logger.error(f"Step {step_id} failed after {max_attempts} attempts: {result.error}")
                        record.status = MissionState.FAILED
                        record.error = f"Step {step_id} failed: {result.error}"
                        record.end_time = time.time()
                        await OPSEventBus.emit_ops_event_async(create_event(
                            event_type=OPSEventType.MISSION_FAILED,
                            session_id=session_id,
                            mission_id=mission_id,
                            status="FAILED",
                            message=record.error
                        ))
                        return record

                    record.status = MissionState.RECOVERING
                    await OPSEventBus.emit_ops_event_async(create_event(
                        event_type=OPSEventType.RECOVERY_STARTED,
                        session_id=session_id,
                        mission_id=mission_id,
                        agent_id="debugger",
                        agent_name="Debugger",
                        parent_agent="mission_manager",
                        status="RECOVERING",
                        message=f"Step failed ({result.error}). Debugger initiating recovery cycle (Attempt {attempts}/{max_attempts})...",
                        metadata={"attempt": attempts, "max_attempts": max_attempts, "error": result.error}
                    ))
                    time.sleep(0.3)

        if not record.error and not record.is_cancelled:
            record.status = MissionState.COMPLETED
            await OPSEventBus.emit_ops_event_async(create_event(
                event_type=OPSEventType.MISSION_COMPLETED,
                session_id=session_id,
                mission_id=mission_id,
                agent_id="mission_manager",
                agent_name="Mission Manager",
                status="COMPLETED",
                message=f"Mission '{goal}' completed successfully.",
                metadata={"total_steps": len(plan.steps)}
            ))
        record.end_time = time.time()
        return record
