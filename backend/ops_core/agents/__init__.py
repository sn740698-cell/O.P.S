"""
O.P.S. Specialized Agents Registry Module
"""

from ops_core.agents.base import BaseAgent, AgentResult
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

__all__ = [
    "BaseAgent",
    "AgentResult",
    "DeveloperAgent",
    "DebuggerAgent",
    "TesterAgent",
    "ReviewerAgent",
    "WebAgent",
    "ResearchAgent",
    "AutomationAgent",
    "BrowserAgent",
    "RAGAgent",
    "ResponseAgent"
]
