"""
O.P.S. Canonical Planner Agent (Qwen3 1.7B)
Decomposes complex goals into explicit, ordered, verifiable steps with assigned agents and capabilities.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from ops_core.services.ollama_service import OPSOllamaService

logger = logging.getLogger("ops.orchestration.planner")


class PlanStep(BaseModel):
    step_id: int
    description: str
    assigned_agent: str                      # "developer", "tester", "debugger", "automation", "browser", "web", "rag"
    capability: str                          # Registered capability name
    arguments: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[int] = Field(default_factory=list)
    verification_method: Optional[str] = None


class MissionPlan(BaseModel):
    goal: str
    steps: List[PlanStep] = Field(default_factory=list)
    estimated_complexity: str = "MEDIUM"


class Planner:
    def __init__(self, ollama_service: Optional[OPSOllamaService] = None):
        self.ollama = ollama_service or OPSOllamaService()

    async def create_plan(self, goal: str, context: Optional[Dict[str, Any]] = None) -> MissionPlan:
        """
        Uses Qwen3 1.7B to formulate an ordered plan of verifiable steps.
        """
        system_instruction = (
            "You are the O.P.S. Lead Planner (Model: Qwen3 1.7B).\n"
            "Convert the user's high-level goal into an explicit, ordered sequence of verifiable execution steps.\n"
            "Allowed Agents: ['developer', 'tester', 'debugger', 'automation', 'browser', 'web', 'research', 'rag']\n"
            "Allowed Capabilities:\n"
            "- filesystem.read, filesystem.write, filesystem.create_directory, filesystem.delete, filesystem.list_directory\n"
            "- terminal.execute, terminal.run_tests\n"
            "- browser.open, browser.navigate, browser.click, browser.type\n"
            "- web.search, web.crawl\n"
            "- desktop.launch_app, desktop.open_file\n\n"
            "Respond in structured JSON format:\n"
            "{\n"
            '  "goal": "...",\n'
            '  "estimated_complexity": "MEDIUM",\n'
            '  "steps": [\n'
            "    {\n"
            '      "step_id": 1,\n'
            '      "description": "Inspect environment or create directories",\n'
            '      "assigned_agent": "developer",\n'
            '      "capability": "filesystem.create_directory",\n'
            '      "arguments": {"path": "..."},\n'
            '      "depends_on": []\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        try:
            res = self.ollama.client.generate(
                model=self.ollama.reasoning_model,  # Qwen3 1.7B
                prompt=f"{system_instruction}\n\nGoal: {goal}",
                format="json",
                options={"temperature": 0.1, "num_predict": 256}
            )
            raw = json.loads(res.get("response", "{}"))
            steps_data = raw.get("steps", [])
            steps = [PlanStep(**s) for s in steps_data]
            if not steps:
                steps = [
                    PlanStep(
                        step_id=1,
                        description=f"Execute: {goal}",
                        assigned_agent="developer" if "build" in goal.lower() or "fix" in goal.lower() else "automation",
                        capability="terminal.execute" if "test" in goal.lower() or "build" in goal.lower() else "desktop.launch_app",
                        arguments={"command": goal}
                    )
                ]
            return MissionPlan(goal=goal, steps=steps, estimated_complexity=raw.get("estimated_complexity", "MEDIUM"))
        except Exception as e:
            logger.warning(f"Planner fallback: {e}")
            return MissionPlan(
                goal=goal,
                steps=[
                    PlanStep(
                        step_id=1,
                        description=f"Execute: {goal}",
                        assigned_agent="developer",
                        capability="terminal.execute",
                        arguments={"command": goal}
                    )
                ]
            )
