"""
O.P.S. Agent Subsystem Package
Authoritative Architecture implementation based on O.P.S. — Agent Architecture & Build Specification.
"""

from ops_core.services.agents.base_agent import BaseOPSAgent, AgentTaskState
from ops_core.services.agents.prompt_template_agent import PromptTemplateAgent
from ops_core.services.agents.router_agent import RouterAgent
from ops_core.services.agents.web_agents import (
    WebSuperiorAgent,
    WebPromptUnderstandingAgent,
    ScrapeGraphAIAgent,
    BeautifulSoupAgent,
    CrawleeAgent,
    RetrievalQualityAgent,
)
from ops_core.services.agents.automation_agents import (
    AutomationSuperiorAgent,
    AutomationPromptUnderstandingAgent,
    HITLApprovalGate,
    OpenWebAgent,
    InstalledAppsAgent,
    OpenFileAgent,
    DesktopControlAgent,
)
from ops_core.services.agents.final_agents import (
    ResultAgent,
    JarvisPersonaAgent,
)

__all__ = [
    "BaseOPSAgent",
    "AgentTaskState",
    "PromptTemplateAgent",
    "RouterAgent",
    "WebSuperiorAgent",
    "WebPromptUnderstandingAgent",
    "ScrapeGraphAIAgent",
    "BeautifulSoupAgent",
    "CrawleeAgent",
    "RetrievalQualityAgent",
    "AutomationSuperiorAgent",
    "AutomationPromptUnderstandingAgent",
    "HITLApprovalGate",
    "OpenWebAgent",
    "InstalledAppsAgent",
    "OpenFileAgent",
    "DesktopControlAgent",
    "ResultAgent",
    "JarvisPersonaAgent",
]
