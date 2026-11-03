import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from research_system.graph.state import ResearchState

# 4 Reasoning Agents
from research_system.graph.agents.request_understanding import request_understanding_node
from research_system.graph.agents.research_planner import research_planner_node
from research_system.graph.agents.evidence_analysis import evidence_analysis_node
from research_system.graph.agents.answer_generation import answer_generation_node

# 8 Execution Workers
from research_system.graph.workers.search_worker import search_worker_node
from research_system.graph.workers.url_selection_worker import url_selection_worker_node
from research_system.graph.workers.crawling_worker import crawling_worker_node
from research_system.graph.workers.browser_rendering_worker import browser_rendering_worker_node
from research_system.graph.workers.content_extraction_worker import content_extraction_worker_node
from research_system.graph.workers.content_processing_worker import content_processing_worker_node
from research_system.graph.workers.evidence_retrieval_worker import evidence_retrieval_worker_node
from research_system.graph.workers.citation_result_worker import citation_result_worker_node

# Adaptive Research Controller
from research_system.graph.controller import adaptive_research_controller_edge, adaptive_loop_prep_node

logger = logging.getLogger(__name__)

# Configured LangGraph Checkpointer
langgraph_checkpointer = MemorySaver()

def delete_conversation_checkpoint(conversation_id: str) -> bool:
    """
    Deletes the persisted checkpoint state for a specific conversation thread
    using the configured checkpointer's supported delete_thread functionality.
    """
    try:
        if hasattr(langgraph_checkpointer, "delete_thread"):
            langgraph_checkpointer.delete_thread(thread_id=conversation_id)
            logger.info(f"Deleted LangGraph checkpointer state for conversation {conversation_id}")
            return True
        return False
    except Exception as e:
        logger.warning(f"Failed to delete thread checkpoint for {conversation_id}: {e}")
        return False

def build_research_graph():
    """
    Constructs and compiles the canonical LangGraph Web Research Graph for O.P.S. 2.0.
    Consists of 4 Reasoning Agents, 8 Execution Workers, and 1 Adaptive Controller.
    Compiled with native thread checkpointer for conversation lifecycle management.
    """
    workflow = StateGraph(ResearchState)

    # 1. Register 4 Reasoning Agent Nodes
    workflow.add_node("request_understanding", request_understanding_node)
    workflow.add_node("research_planner", research_planner_node)
    workflow.add_node("evidence_analysis", evidence_analysis_node)
    workflow.add_node("answer_generation", answer_generation_node)

    # 2. Register 8 Execution Worker Nodes
    workflow.add_node("search_worker", search_worker_node)
    workflow.add_node("url_selection_worker", url_selection_worker_node)
    workflow.add_node("crawling_worker", crawling_worker_node)
    workflow.add_node("browser_rendering_worker", browser_rendering_worker_node)
    workflow.add_node("content_extraction_worker", content_extraction_worker_node)
    workflow.add_node("content_processing_worker", content_processing_worker_node)
    workflow.add_node("evidence_retrieval_worker", evidence_retrieval_worker_node)
    workflow.add_node("citation_result_worker", citation_result_worker_node)

    # 3. Register Adaptive Loop Prep Node
    workflow.add_node("adaptive_loop_prep", adaptive_loop_prep_node)

    # 4. Wire Execution Edges
    workflow.add_edge(START, "request_understanding")
    workflow.add_edge("request_understanding", "research_planner")
    workflow.add_edge("research_planner", "search_worker")
    workflow.add_edge("search_worker", "url_selection_worker")
    workflow.add_edge("url_selection_worker", "crawling_worker")
    workflow.add_edge("crawling_worker", "browser_rendering_worker")
    workflow.add_edge("browser_rendering_worker", "content_extraction_worker")
    workflow.add_edge("content_extraction_worker", "content_processing_worker")
    workflow.add_edge("content_processing_worker", "evidence_analysis")

    # 5. Adaptive Research Controller Conditional Routing
    workflow.add_conditional_edges(
        "evidence_analysis",
        adaptive_research_controller_edge,
        {
            "execute_another_search": "adaptive_loop_prep",
            "complete_research": "evidence_retrieval_worker"
        }
    )

    # Loop back from adaptive_loop_prep to search_worker
    workflow.add_edge("adaptive_loop_prep", "search_worker")

    # Synthesis path
    workflow.add_edge("evidence_retrieval_worker", "answer_generation")
    workflow.add_edge("answer_generation", "citation_result_worker")
    workflow.add_edge("citation_result_worker", END)

    return workflow.compile(checkpointer=langgraph_checkpointer)

# Precompiled graph instance ready for execution
research_graph = build_research_graph()
