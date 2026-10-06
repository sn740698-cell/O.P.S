"""
O.P.S. Web Superior Domain Agents
Hierarchy:
- Web Superior Agent (Superior | Qwen3 1.7B)
  ├── Web Prompt Understanding Agent (Sub-agent | Qwen3 1.7B)
  ├── ScrapeGraphAI Agent (Sub-agent | Llama 3.2 1B)
  ├── BeautifulSoup Agent (Sub-agent | Qwen3 0.6B)
  ├── Crawlee Agent (Sub-agent | Llama 3.2 1B)
  └── Retrieval Quality Agent (Sub-agent | Qwen3 1.7B) [Self-correction Loop]
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from ops_core.services.agents.base_agent import BaseOPSAgent, AgentTaskState
from ops_core.services.scraping_service import OPSScrapingService

logger = logging.getLogger("ops.agents.web")


# =========================================================================
# 1. Web Prompt Understanding Agent (Sub-agent | Qwen3 1.7B)
# =========================================================================
class WebPromptUnderstandingAgent(BaseOPSAgent):
    agent_id = "web_prompt_understanding_agent"
    agent_name = "Web Prompt Understanding Agent"
    level = "Sub-agent"
    assigned_model = "Qwen3 1.7B"
    allowed_tools = []
    parent_agent = "Web Superior Agent"
    downstream_destination = "ScrapeGraphAI / BeautifulSoup / Crawlee Agents"

    async def process(self, state: AgentTaskState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        prompt = (state.get("prompt") or state.get("original_prompt") or "").strip()
        gap_feedback = state.get("web_gap_feedback")
        loop_count = state.get("web_loop_count", 0)

        await self.emit_status(task_id, "PROCESSING", {"loop_count": loop_count})
        if gap_feedback:
            await self.emit_thought(task_id, f"Re-planning retrieval (Cycle {loop_count + 1}) based on quality feedback: '{gap_feedback}'")
        else:
            await self.emit_thought(task_id, f"Analyzing web research requirements for: '{prompt}'")

        system_instruction = (
            "You are the O.P.S. Web Prompt Understanding Agent (Model: Qwen3 1.7B).\n"
            "Analyze the information request and formulate extraction instructions.\n"
            "Determine:\n"
            "1. 'objective': Concise research goal\n"
            "2. 'required_facts': List of facts/aspects to look up\n"
            "3. 'freshness': 'current', 'historical', or 'timeless'\n"
            "4. 'search_query': Optimized web search query\n"
            "5. 'recommended_extractor': 'ScrapeGraphAI' (structured/tabular), 'BeautifulSoup' (direct HTML/articles), or 'Crawlee' (multi-page/pagination)\n\n"
            "Respond in JSON format."
        )

        feedback_ctx = f"\nPrevious attempt feedback (Address this in new plan): {gap_feedback}" if gap_feedback else ""
        
        try:
            res = self.ollama.client.generate(
                model=self.ollama.reasoning_model,
                prompt=f"{system_instruction}{feedback_ctx}\n\nUser Request: {prompt}",
                format="json",
                options={"temperature": 0.1}
            )
            data = json.loads(res.get("response", "{}"))
        except Exception as e:
            logger.warning(f"Web Prompt Understanding fallback: {e}")
            data = {
                "objective": prompt,
                "required_facts": ["Overview", "Key details", "Latest developments"],
                "freshness": "current" if any(k in prompt.lower() for k in ["latest", "news", "today", "recent"]) else "timeless",
                "search_query": prompt,
                "recommended_extractor": "BeautifulSoup"
            }

        await self.emit_thought(task_id, f"Research Plan created: Target query='{data.get('search_query')}', Extractor={data.get('recommended_extractor')}")
        await self.emit_status(task_id, "COMPLETED", {"understanding": data})

        return {
            "web_understanding": data,
            "active_agent": self.agent_name,
            "active_model": self.assigned_model
        }


# =========================================================================
# 2. ScrapeGraphAI Agent (Sub-agent | Llama 3.2 1B)
# =========================================================================
class ScrapeGraphAIAgent(BaseOPSAgent):
    agent_id = "scrapegraph_agent"
    agent_name = "ScrapeGraphAI Agent"
    level = "Sub-agent"
    assigned_model = "Llama 3.2 1B"
    allowed_tools = ["ScrapeGraphAI", "SchemaExtractor"]
    parent_agent = "Web Superior Agent"
    downstream_destination = "Retrieval Quality Agent"

    def __init__(self, scraping_service: Optional[OPSScrapingService] = None, **kwargs):
        super().__init__(**kwargs)
        self.scraping_service = scraping_service or OPSScrapingService()

    async def process(self, state: AgentTaskState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        understanding = state.get("web_understanding", {})
        query = understanding.get("search_query") or state.get("prompt", "")

        await self.emit_status(task_id, "PROCESSING", {"target": query})
        await self.emit_thought(task_id, f"Executing structured data extraction for: '{query}'")

        # Execute web intelligence with ScrapeGraphAI / live research
        res = await asyncio.to_thread(self.scraping_service.auto_research, query)

        raw_result = {
            "extractor": "ScrapeGraphAI",
            "query": query,
            "title": res.get("title", query),
            "content": res.get("summary") or res.get("text", "") or res.get("content", ""),
            "sources": res.get("sources", []),
            "key_facts": res.get("key_points", [])
        }

        await self.emit_thought(task_id, f"Extracted structured fields from {len(res.get('sources', []))} sources.")
        await self.emit_status(task_id, "COMPLETED", {"extracted_length": len(raw_result["content"])})

        return {
            "web_raw_results": [raw_result],
            "active_agent": self.agent_name,
            "active_model": self.assigned_model
        }


# =========================================================================
# 3. BeautifulSoup Agent (Sub-agent | Qwen3 0.6B)
# =========================================================================
class BeautifulSoupAgent(BaseOPSAgent):
    agent_id = "beautifulsoup_agent"
    agent_name = "BeautifulSoup Agent"
    level = "Sub-agent"
    assigned_model = "Qwen3 0.6B"
    allowed_tools = ["BeautifulSoup4", "HTMLSanitizer"]
    parent_agent = "Web Superior Agent"
    downstream_destination = "Retrieval Quality Agent"

    def __init__(self, scraping_service: Optional[OPSScrapingService] = None, **kwargs):
        super().__init__(**kwargs)
        self.scraping_service = scraping_service or OPSScrapingService()

    async def process(self, state: AgentTaskState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        understanding = state.get("web_understanding", {})
        query = understanding.get("search_query") or state.get("prompt", "")

        await self.emit_status(task_id, "PROCESSING", {"target": query})
        await self.emit_thought(task_id, f"Parsing HTML and extracting clean text/headings for: '{query}'")

        # Execute web intelligence with DOM sanitation
        res = await asyncio.to_thread(self.scraping_service.auto_research, query)

        raw_result = {
            "extractor": "BeautifulSoup4",
            "query": query,
            "title": res.get("title", query),
            "content": res.get("summary") or res.get("text", "") or res.get("content", ""),
            "sources": res.get("sources", []),
            "key_facts": res.get("key_points", [])
        }

        await self.emit_thought(task_id, f"Sanitized HTML and extracted clean content ({len(raw_result['content'])} chars).")
        await self.emit_status(task_id, "COMPLETED", {"extracted_length": len(raw_result["content"])})

        return {
            "web_raw_results": [raw_result],
            "active_agent": self.agent_name,
            "active_model": self.assigned_model
        }


# =========================================================================
# 4. Crawlee Agent (Sub-agent | Llama 3.2 1B)
# =========================================================================
class CrawleeAgent(BaseOPSAgent):
    agent_id = "crawlee_agent"
    agent_name = "Crawlee Agent"
    level = "Sub-agent"
    assigned_model = "Llama 3.2 1B"
    allowed_tools = ["Crawlee", "PageCrawler"]
    parent_agent = "Web Superior Agent"
    downstream_destination = "Retrieval Quality Agent"

    def __init__(self, scraping_service: Optional[OPSScrapingService] = None, **kwargs):
        super().__init__(**kwargs)
        self.scraping_service = scraping_service or OPSScrapingService()

    async def process(self, state: AgentTaskState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        understanding = state.get("web_understanding", {})
        query = understanding.get("search_query") or state.get("prompt", "")

        await self.emit_status(task_id, "PROCESSING", {"target": query})
        await self.emit_thought(task_id, f"Executing multi-page Crawlee crawl for: '{query}'")

        # Execute web crawl
        res = await asyncio.to_thread(self.scraping_service.auto_research, query)

        raw_result = {
            "extractor": "Crawlee",
            "query": query,
            "title": res.get("title", query),
            "content": res.get("summary") or res.get("text", "") or res.get("content", ""),
            "sources": res.get("sources", []),
            "key_facts": res.get("key_points", [])
        }

        await self.emit_thought(task_id, f"Completed crawl collection from {len(res.get('sources', []))} endpoints.")
        await self.emit_status(task_id, "COMPLETED", {"extracted_length": len(raw_result["content"])})

        return {
            "web_raw_results": [raw_result],
            "active_agent": self.agent_name,
            "active_model": self.assigned_model
        }


# =========================================================================
# 5. Retrieval Quality Agent (Sub-agent | Qwen3 1.7B) [Self-correction Loop]
# =========================================================================
class RetrievalQualityAgent(BaseOPSAgent):
    agent_id = "retrieval_quality_agent"
    agent_name = "Retrieval Agent"
    level = "Sub-agent"
    assigned_model = "Qwen3 1.7B"
    allowed_tools = []
    parent_agent = "Web Superior Agent"
    downstream_destination = "Result Agent OR Web Prompt Understanding (Loop)"

    MAX_RETRIES = 2

    async def process(self, state: AgentTaskState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        original_prompt = (state.get("original_prompt") or state.get("prompt") or "").strip()
        understanding = state.get("web_understanding", {})
        raw_results = state.get("web_raw_results", [])
        loop_count = state.get("web_loop_count", 0)

        await self.emit_status(task_id, "PROCESSING", {"check_cycle": loop_count + 1})
        await self.emit_thought(task_id, f"Evaluating quality, relevance, and completeness of retrieved data against objective: '{original_prompt}'")

        # Combine text for inspection
        combined_text = "\n".join([r.get("content", "") for r in raw_results if r.get("content")])
        
        # If extraction is completely empty, reject immediately
        if not combined_text or len(combined_text.strip()) < 30:
            is_sufficient = False
            feedback = "No substantive content retrieved. Refine query."
        else:
            system_instruction = (
                "You are the O.P.S. Retrieval Quality Agent (Model: Qwen3 1.7B).\n"
                "Your role is quality control: determine whether the collected data satisfies the user's original objective.\n"
                "Check:\n"
                "1. Relevance: Is it about the right person/topic?\n"
                "2. Completeness: Does it answer the question?\n"
                "3. Freshness: If user asked for 'latest' or 'today', is it current?\n\n"
                "Respond in JSON with:\n"
                "- 'is_sufficient': true / false\n"
                "- 'relevance_score': float (0.0 to 1.0)\n"
                "- 'gap_feedback': explanation if false\n"
                "- 'validated_summary': concise summary of verified facts"
            )

            try:
                res = self.ollama.client.generate(
                    model=self.ollama.reasoning_model,
                    prompt=f"{system_instruction}\n\nOriginal Request: {original_prompt}\n\nCollected Data:\n{combined_text[:3000]}",
                    format="json",
                    options={"temperature": 0.0}
                )
                eval_data = json.loads(res.get("response", "{}"))
                is_sufficient = eval_data.get("is_sufficient", True)
                feedback = eval_data.get("gap_feedback", "")
            except Exception as e:
                logger.warning(f"Retrieval evaluation fallback: {e}")
                is_sufficient = True
                feedback = ""

        # Enforce loop retry limit
        if not is_sufficient and loop_count >= self.MAX_RETRIES:
            logger.info(f"Retrieval loop reached max retries ({self.MAX_RETRIES}). Proceeding with best available data.")
            is_sufficient = True

        validation_result = {
            "is_sufficient": is_sufficient,
            "loop_count": loop_count,
            "gap_feedback": feedback if not is_sufficient else None,
            "raw_facts": {
                "objective": original_prompt,
                "retrieved_text": combined_text,
                "sources": [s for r in raw_results for s in r.get("sources", [])]
            }
        }

        if is_sufficient:
            await self.emit_thought(task_id, f"Retrieval validated! Data is accurate & sufficient for the original request.")
            await self.emit_status(task_id, "COMPLETED", {"status": "VALIDATED"})
        else:
            await self.emit_thought(task_id, f"Retrieval insufficient: '{feedback}'. Triggering re-planning loop to Web Understanding Agent.")
            await self.emit_status(task_id, "RETRYING", {"gap_feedback": feedback})

        return {
            "web_retrieval_validation": validation_result,
            "web_loop_count": loop_count + 1 if not is_sufficient else loop_count,
            "web_gap_feedback": feedback if not is_sufficient else None,
            "raw_facts": validation_result["raw_facts"],
            "result_type": "RESEARCH_RESULT" if "research" in original_prompt.lower() or "news" in original_prompt.lower() else "INFORMATION_RESULT",
            "active_agent": self.agent_name,
            "active_model": self.assigned_model
        }


# =========================================================================
# 6. Web Superior Agent (Superior | Qwen3 1.7B)
# =========================================================================
class WebSuperiorAgent(BaseOPSAgent):
    agent_id = "web_superior_agent"
    agent_name = "Web Agent"
    level = "Superior"
    assigned_model = "Qwen3 1.7B"
    allowed_tools = []
    parent_agent = "Router Agent"
    downstream_destination = "Result Agent"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.understanding_agent = WebPromptUnderstandingAgent(ollama_service=self.ollama)
        self.scrapegraph_agent = ScrapeGraphAIAgent(ollama_service=self.ollama)
        self.bs4_agent = BeautifulSoupAgent(ollama_service=self.ollama)
        self.crawlee_agent = CrawleeAgent(ollama_service=self.ollama)
        self.retrieval_agent = RetrievalQualityAgent(ollama_service=self.ollama)

    async def process(self, state: AgentTaskState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        prompt = state.get("prompt", "")

        await self.emit_status(task_id, "PROCESSING", {"domain": "WEB_RETRIEVAL"})
        await self.emit_thought(task_id, f"Web Superior Agent coordinating research sub-tree for: '{prompt}'")

        current_state = dict(state)
        current_state["web_loop_count"] = current_state.get("web_loop_count", 0)
        current_state["web_gap_feedback"] = None

        # Execute loop (Web Understanding -> Extractor -> Retrieval Quality Check -> Loop if needed)
        for cycle in range(self.retrieval_agent.MAX_RETRIES + 1):
            # 1. Web Prompt Understanding
            und_res = await self.understanding_agent.process(current_state)
            current_state.update(und_res)

            # 2. Select appropriate extractor
            rec = current_state.get("web_understanding", {}).get("recommended_extractor", "BeautifulSoup")
            if rec == "ScrapeGraphAI":
                ext_res = await self.scrapegraph_agent.process(current_state)
            elif rec == "Crawlee":
                ext_res = await self.crawlee_agent.process(current_state)
            else:
                ext_res = await self.bs4_agent.process(current_state)
            current_state.update(ext_res)

            # 3. Retrieval Quality Agent Validation
            ret_res = await self.retrieval_agent.process(current_state)
            current_state.update(ret_res)

            if current_state.get("web_retrieval_validation", {}).get("is_sufficient", True):
                break

        await self.emit_thought(task_id, "Web Superior Agent completed web retrieval cycle. Handing over to Result Agent.")
        await self.emit_status(task_id, "COMPLETED", {"domain": "WEB_RETRIEVAL"})

        return current_state
