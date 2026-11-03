"""
O.P.S. 2.0 Central LangGraph State Definition
Section 7: Shared Typed State across 4 Groups and 13 Components
"""

from typing import TypedDict, List, Dict, Any, Optional


class CentralGraphState(TypedDict, total=False):
    # Identifiers
    task_id: str
    conversation_id: str
    request_id: str
    user_query: str

    # Routing and Classifications
    task_type: str              # 'ANSWER' | 'AUTOMATION' | 'COMPOSITE' | 'CLARIFICATION'
    answering_mode: str         # 'LLM' | 'WEB' | 'HYBRID'
    automation_mode: str        # 'DESKTOP' | 'BROWSER' | 'HYBRID'
    user_goal: str
    routing_result: Dict[str, Any]

    # Planning & Agent Progression
    execution_plan: List[Dict[str, Any]]
    current_agent: str
    active_agents: List[str]
    completed_agents: List[str]
    pending_agents: List[str]
    agent_status: Dict[str, str]  # agent_id -> 'IDLE' | 'ACTIVE' | 'COMPLETED' | 'SKIPPED' | 'WAITING_FOR_APPROVAL' | 'FAILED'
    task_dependencies: Dict[str, Any]

    # Engine Outcomes
    local_reasoning_output: str
    research_results: Dict[str, Any]
    validated_evidence: Dict[str, Any]
    automation_results: Dict[str, Any]
    verification_results: Dict[str, Any]

    # Temporary Document RAG
    attached_documents: List[Dict[str, Any]]
    rag_retrieval_active: bool
    retrieved_document_chunks: List[Dict[str, Any]]

    # Human-in-the-Loop & Safety
    approval_required: bool
    approval_status: str        # 'NONE' | 'PENDING' | 'APPROVED' | 'REJECTED'
    approval_id: Optional[str]
    approval_reason: Optional[str]
    clarification_required: bool
    clarification_prompt: Optional[str]
    clarification_response: Optional[str]

    # Execution Control & Diagnostics
    retry_count: int
    errors: List[str]
    final_response: str
    source_references: List[Dict[str, Any]]
    task_status: str            # 'RECEIVED' | 'PLANNING' | 'WAITING_FOR_APPROVAL' | 'EXECUTING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
    timestamps: Dict[str, float]
