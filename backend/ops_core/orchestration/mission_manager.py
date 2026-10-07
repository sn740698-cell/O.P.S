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

        # Broadcast mission started
        await OPSEventBus.emit_thought_async(
            thought=f"Mission started: '{goal}' ({len(plan.steps)} steps planned)",
            agent="Mission Manager",
            task_id=mission_id
        )

        for idx, step in enumerate(plan.steps):
            if record.is_cancelled:
                record.status = MissionState.CANCELLED
                record.error = "Mission cancelled by user."
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

                await OPSEventBus.emit_thought_async(
                    thought=f"[Step {idx+1}/{len(plan.steps)}] {step.description} (Agent: {step.assigned_agent}, Tool: {step.capability})",
                    agent=step.assigned_agent.title(),
                    task_id=mission_id
                )

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
                    break
                elif result.status in ["BLOCKED", "DECLINED"]:
                    logger.warning(f"Step {step_id} was rejected by Safety/User: {result.error}")
                    record.status = MissionState.FAILED
                    record.error = f"Step {step_id} was declined: {result.error}"
                    record.end_time = time.time()
                    return record
                else:
                    # Failure encountered -> Check if attempts exhausted
                    if attempts >= max_attempts:
                        logger.error(f"Step {step_id} failed after {max_attempts} attempts: {result.error}")
                        record.status = MissionState.FAILED
                        record.error = f"Step {step_id} failed: {result.error}"
                        record.end_time = time.time()
                        return record

                    record.status = MissionState.RECOVERING
                    await OPSEventBus.emit_thought_async(
                        thought=f"Step failed ({result.error}). Debugger initiating recovery cycle (Attempt {attempts}/{max_attempts})...",
                        agent="Debugger",
                        task_id=mission_id
                    )
                    time.sleep(0.3)

        if not record.error and not record.is_cancelled:
            record.status = MissionState.COMPLETED
        record.end_time = time.time()
        return record
