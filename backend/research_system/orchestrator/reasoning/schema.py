"""
O.P.S. 2.0 — Structured Reasoning Output Contract
Section 8: Typed Schema and Validation for Understanding & Planning Engine
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

# 7 Canonical Task Types
VALID_TASK_TYPES = [
    "ANSWER",
    "RESEARCH",
    "REASONING",
    "AUTOMATION",
    "DEVELOPMENT",
    "COMPOSITE",
    "CLARIFICATION"
]

# Answering Engine Modes
VALID_ANSWERING_ENGINES = ["LLM", "WEB", "HYBRID", "DOCUMENT", "NONE"]

# Automation Engine Modes
VALID_AUTOMATION_ENGINES = ["DESKTOP", "BROWSER", "HYBRID", "NONE"]

# Risk Levels
VALID_RISK_LEVELS = ["LOW", "MEDIUM", "HIGH"]


class SubtaskSpec(BaseModel):
    id: str
    domain: str = "DESKTOP"  # "DESKTOP" | "BROWSER" | "ANSWER" | "COORDINATOR"
    action: str
    target: str = ""
    value: str = ""
    executor: str = "desktop"
    dependencies: List[str] = Field(default_factory=list)
    resource_lock: Optional[str] = None
    requires_approval: bool = False


class ReasoningPlanContract(BaseModel):
    task_id: str
    task_type: str
    user_objective: str
    context_summary: str = ""
    answering_engine: str = "NONE"
    answering_tasks: List[str] = Field(default_factory=list)
    automation_engine: str = "NONE"
    automation_tasks: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    constraints: List[str] = Field(default_factory=list)
    preferences: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    clarification_required: bool = False
    clarification_question: Optional[str] = None
    execution_plan: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies: List[Dict[str, Any]] = Field(default_factory=list)
    parallel_groups: List[List[str]] = Field(default_factory=list)
    approval_required: bool = False
    approval_scope: List[str] = Field(default_factory=list)
    risk_level: str = "LOW"
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    reasoning_summary: str = ""

    @field_validator("task_type")
    def validate_task_type(cls, v):
        v_upper = v.upper()
        if v_upper not in VALID_TASK_TYPES:
            raise ValueError(f"Invalid task_type: '{v}'. Must be one of {VALID_TASK_TYPES}")
        return v_upper

    @field_validator("answering_engine")
    def validate_answering_engine(cls, v):
        v_upper = v.upper()
        if v_upper not in VALID_ANSWERING_ENGINES:
            return "NONE"
        return v_upper

    @field_validator("automation_engine")
    def validate_automation_engine(cls, v):
        v_upper = v.upper()
        if v_upper not in VALID_AUTOMATION_ENGINES:
            return "NONE"
        return v_upper

    @field_validator("risk_level")
    def validate_risk_level(cls, v):
        v_upper = v.upper()
        if v_upper not in VALID_RISK_LEVELS:
            return "LOW"
        return v_upper
