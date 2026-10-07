"""
O.P.S. Canonical Capability Registry
The single source of truth for all registered agent capabilities and tools.
Agents can only select and execute registered capabilities.
"""

from typing import Dict, Any, Optional, List, Callable, Awaitable
import logging
from ops_core.capabilities.schemas import CapabilityDefinition, RiskLevel, ToolCallRequest, ToolCallResult
from ops_core.core.errors import OPSError, OPSErrorCode

logger = logging.getLogger("ops.capabilities.registry")


class CapabilityRegistry:
    _instance = None
    _capabilities: Dict[str, CapabilityDefinition] = {}
    _executors: Dict[str, Callable[[ToolCallRequest], Awaitable[ToolCallResult]]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CapabilityRegistry, cls).__new__(cls)
            cls._capabilities = {}
            cls._executors = {}
            cls._instance._register_default_capabilities()
        return cls._instance

    def _register_default_capabilities(self):
        """Registers canonical capabilities defined by the O.P.S. specification."""
        
        # 1. Filesystem Capabilities
        self.register(
            CapabilityDefinition(
                name="filesystem.read",
                category="filesystem",
                description="Reads the contents of a local file safely with slice/line limits.",
                risk=RiskLevel.SAFE,
                allowed_agents=["developer", "debugger", "tester", "reviewer", "automation", "rag", "web"],
                verification_method="filesystem.exists"
            )
        )
        self.register(
            CapabilityDefinition(
                name="filesystem.write",
                category="filesystem",
                description="Creates or updates a file on disk.",
                risk=RiskLevel.ELEVATED,
                allowed_agents=["developer", "debugger", "automation"],
                verification_method="filesystem.content_matches"
            )
        )
        self.register(
            CapabilityDefinition(
                name="filesystem.create_directory",
                category="filesystem",
                description="Creates a directory path on disk.",
                risk=RiskLevel.SAFE,
                allowed_agents=["developer", "automation"],
                verification_method="filesystem.exists"
            )
        )
        self.register(
            CapabilityDefinition(
                name="filesystem.move",
                category="filesystem",
                description="Moves or renames a file/directory.",
                risk=RiskLevel.ELEVATED,
                allowed_agents=["automation", "developer"],
                verification_method="filesystem.exists"
            )
        )
        self.register(
            CapabilityDefinition(
                name="filesystem.delete",
                category="filesystem",
                description="Deletes a file or directory. High risk operation.",
                risk=RiskLevel.DANGEROUS,
                requires_confirmation=True,
                allowed_agents=["automation", "developer"],
                verification_method="filesystem.not_exists"
            )
        )
        self.register(
            CapabilityDefinition(
                name="filesystem.list_directory",
                category="filesystem",
                description="Lists files and subdirectories in a target path.",
                risk=RiskLevel.SAFE,
                allowed_agents=["automation", "developer", "tester", "rag"],
                verification_method=None
            )
        )

        # 2. Browser Capabilities (Playwright)
        self.register(
            CapabilityDefinition(
                name="browser.open",
                category="browser",
                description="Launches or opens a web browser to a target URL.",
                risk=RiskLevel.SAFE,
                allowed_agents=["browser", "automation", "web"],
                verification_method="browser.url_loaded"
            )
        )
        self.register(
            CapabilityDefinition(
                name="browser.navigate",
                category="browser",
                description="Navigates an active browser page to a specific URL or route.",
                risk=RiskLevel.SAFE,
                allowed_agents=["browser", "automation"],
                verification_method="browser.url_loaded"
            )
        )
        self.register(
            CapabilityDefinition(
                name="browser.click",
                category="browser",
                description="Clicks a DOM element matching a CSS or text selector.",
                risk=RiskLevel.ELEVATED,
                allowed_agents=["browser", "automation"],
                verification_method="browser.element_state"
            )
        )
        self.register(
            CapabilityDefinition(
                name="browser.type",
                category="browser",
                description="Types text into an input field or search bar on the web page.",
                risk=RiskLevel.SAFE,
                allowed_agents=["browser", "automation"],
                verification_method="browser.input_filled"
            )
        )
        self.register(
            CapabilityDefinition(
                name="browser.extract",
                category="browser",
                description="Extracts sanitized text or DOM content from the active browser page.",
                risk=RiskLevel.SAFE,
                allowed_agents=["browser", "web", "research"],
                verification_method=None
            )
        )

        # 3. Web Research & Scraping Capabilities
        self.register(
            CapabilityDefinition(
                name="web.search",
                category="web",
                description="Searches live internet documentation, articles, and APIs.",
                risk=RiskLevel.SAFE,
                allowed_agents=["web", "research", "rag"],
                verification_method="web.results_found"
            )
        )
        self.register(
            CapabilityDefinition(
                name="web.crawl",
                category="web",
                description="Recursively crawls multi-page site documentation with Crawlee.",
                risk=RiskLevel.SAFE,
                allowed_agents=["web", "research"],
                verification_method="web.crawl_completed"
            )
        )
        self.register(
            CapabilityDefinition(
                name="web.extract_structured",
                category="web",
                description="Extracts structured schema data using ScrapeGraphAI.",
                risk=RiskLevel.SAFE,
                allowed_agents=["web", "research"],
                verification_method="web.schema_extracted"
            )
        )
        self.register(
            CapabilityDefinition(
                name="web.parse_html",
                category="web",
                description="Sanitizes and extracts clean HTML paragraphs and links with BeautifulSoup4.",
                risk=RiskLevel.SAFE,
                allowed_agents=["web", "research"],
                verification_method=None
            )
        )

        # 4. Terminal & Command Execution Capabilities
        self.register(
            CapabilityDefinition(
                name="terminal.execute",
                category="terminal",
                description="Executes a sandboxed shell/CLI command with stdout/stderr capture.",
                risk=RiskLevel.ELEVATED,
                allowed_agents=["developer", "debugger", "tester", "automation"],
                verification_method="terminal.exit_code_zero"
            )
        )
        self.register(
            CapabilityDefinition(
                name="terminal.run_tests",
                category="terminal",
                description="Executes project test suites (e.g. pytest, npm test, vitest).",
                risk=RiskLevel.SAFE,
                allowed_agents=["tester", "debugger", "developer"],
                verification_method="tests.passed"
            )
        )

        # 5. Desktop & Application Automation (PyAutoGUI + OS APIs)
        self.register(
            CapabilityDefinition(
                name="desktop.launch_app",
                category="desktop",
                description="Launches an installed native desktop application (VLC, Spotify, VS Code, etc.).",
                risk=RiskLevel.ELEVATED,
                allowed_agents=["automation"],
                verification_method="process.running"
            )
        )
        self.register(
            CapabilityDefinition(
                name="desktop.open_file",
                category="desktop",
                description="Opens a local document or folder in its default system viewer.",
                risk=RiskLevel.SAFE,
                allowed_agents=["automation", "developer"],
                verification_method="filesystem.exists"
            )
        )
        self.register(
            CapabilityDefinition(
                name="desktop.hotkey",
                category="desktop",
                description="Sends simulated keyboard shortcuts via PyAutoGUI.",
                risk=RiskLevel.ELEVATED,
                allowed_agents=["automation"],
                verification_method=None
            )
        )

        # 6. RAG & Persistent Knowledge Capabilities
        self.register(
            CapabilityDefinition(
                name="rag.search",
                category="rag",
                description="Retrieves semantic embeddings from persistent ChromaDB index.",
                risk=RiskLevel.SAFE,
                allowed_agents=["rag", "developer", "research"],
                verification_method=None
            )
        )
        self.register(
            CapabilityDefinition(
                name="rag.ingest",
                category="rag",
                description="Indexes project files and documents into persistent ChromaDB memory.",
                risk=RiskLevel.SAFE,
                allowed_agents=["rag", "developer"],
                verification_method="rag.document_indexed"
            )
        )
        self.register(
            CapabilityDefinition(
                name="rag.index",
                category="rag",
                description="Indexes text content or files into persistent ChromaDB memory.",
                risk=RiskLevel.SAFE,
                allowed_agents=["rag", "developer", "research"],
                verification_method="rag.document_indexed"
            )
        )

    def register(self, capability: CapabilityDefinition, executor: Optional[Callable[[ToolCallRequest], Awaitable[ToolCallResult]]] = None):
        """Registers a capability definition and optional executor."""
        self._capabilities[capability.name] = capability
        if executor:
            self._executors[capability.name] = executor
        logger.debug(f"Registered capability: {capability.name} [{capability.risk.value}]")

    def register_executor(self, capability_name: str, executor: Callable[[ToolCallRequest], Awaitable[ToolCallResult]]):
        """Binds an executable tool handler to a capability name."""
        if capability_name not in self._capabilities:
            raise OPSError(
                code=OPSErrorCode.TOOL_NOT_FOUND,
                message=f"Cannot bind executor for unregistered capability: {capability_name}"
            )
        self._executors[capability_name] = executor

    def get(self, name: str) -> Optional[CapabilityDefinition]:
        return self._capabilities.get(name)

    def get_executor(self, name: str) -> Optional[Callable[[ToolCallRequest], Awaitable[ToolCallResult]]]:
        return self._executors.get(name)

    def list_all(self) -> List[CapabilityDefinition]:
        return list(self._capabilities.values())

    def list_for_agent(self, agent_name: str) -> List[CapabilityDefinition]:
        return [
            cap for cap in self._capabilities.values()
            if not cap.allowed_agents or agent_name.lower() in [a.lower() for a in cap.allowed_agents]
        ]
