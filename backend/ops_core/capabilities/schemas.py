"""
O.P.S. Capability & Tool Schemas
Defines capability definitions, risk classifications, tool call contracts, and verification specs.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Awaitable
from pydantic import BaseModel, Field
import time
import uuid


class RiskLevel(str, Enum):
    SAFE = "SAFE"                # E.g. read file, search web, status checks
    ELEVATED = "ELEVATED"        # E.g. create project, modify non-system source, launch browser
    DANGEROUS = "DANGEROUS"      # E.g. delete files, drop table, kill process, execute unknown script -> REQUIRES HUMAN APPROVAL
    FORBIDDEN = "FORBIDDEN"      # E.g. format drive, system root deletion, privilege escalation -> STRICTLY BLOCKED


class CapabilityDefinition(BaseModel):
    name: str                                # E.g. "filesystem.create_directory"
    category: str                            # E.g. "filesystem", "browser", "web", "terminal", "desktop", "rag"
    description: str
    risk: RiskLevel = RiskLevel.SAFE
    requires_confirmation: bool = False      # If True or risk == DANGEROUS, Safety Gate prompts user
    allowed_agents: List[str] = Field(default_factory=list)
    parameters_schema: Dict[str, Any] = Field(default_factory=dict)
    verification_method: Optional[str] = None # E.g. "filesystem.exists", "process.running", "test.passed"


class ToolCallRequest(BaseModel):
    tool_call_id: str = Field(default_factory=lambda: f"tc_{uuid.uuid4().hex[:8]}")
    capability: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    risk: RiskLevel = RiskLevel.SAFE
    requested_by: str                         # Agent name
    task_id: Optional[str] = None
    mission_id: Optional[str] = None
    session_id: Optional[str] = None
    verification_method: Optional[str] = None


class ToolCallResult(BaseModel):
    tool_call_id: str
    capability: str
    status: str                               # "SUCCESS", "FAILED", "BLOCKED", "DECLINED"
    result: Dict[str, Any] = Field(default_factory=dict)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: int = 0
    timestamp: float = Field(default_factory=time.time)
