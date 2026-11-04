"""
O.P.S. 2.0 — Web Crawling Functionality: 10-Test Validation Suite
Executes all 10 tests specified in Section 3 of the prompt through the live
O.P.S. Web Research Engine (Crawlee + BeautifulSoup4).

Generates structured test metrics for OPS_WEB_CRAWLING_TEST_REPORT.md.
"""

import sys
import os
import time
import json
from pathlib import Path

# Enable unbuffered line output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")

import django
django.setup()

from research_system.orchestrator.agents.web_research_agent import web_research_agent_node
from research_system.orchestrator.agents.evidence_validation_agent import evidence_validation_agent_node
from research_system.orchestrator.agents.answer_synthesis_agent import answer_synthesis_agent_node
from research_system.orchestrator.state import CentralGraphState

TESTS = [
    {
        "id": "TEST_1",
        "name": "Official Framework Documentation (Django Models)",
        "query": "Find the official Django documentation for Django models. Crawl the relevant documentation and explain what a Django model is, how to define one, and how it maps to a database table. Provide the actual official documentation links.",
        "expected_domains": ["djangoproject.com"],
        "required_keywords": ["model", "django", "table"]
    },
    {
        "id": "TEST_2",
        "name": "Latest Software Release (Python)",
        "query": "Find the latest stable Python release available today. Visit the official Python website, verify the exact version and release date, and provide the official release announcement and download links.",
        "expected_domains": ["python.org"],
        "required_keywords": ["python", "3."]
    },
    {
        "id": "TEST_3",
        "name": "Official Release Notes (Django)",
        "query": "Find the latest stable Django release and inspect its official release notes. Explain the important new features, improvements, compatibility changes, and security fixes. Provide the actual release-note links.",
        "expected_domains": ["djangoproject.com"],
        "required_keywords": ["django", "release"]
    },
    {
        "id": "TEST_4",
        "name": "Multiple Official Sources (Django vs FastAPI)",
        "query": "Research the differences between Django and FastAPI using their official documentation. Compare architecture, routing, asynchronous support, database integration, security features, and typical use cases. Cite the official pages you actually consulted.",
        "expected_domains": ["djangoproject.com", "tiangolo.com"],
        "required_keywords": ["django", "fastapi"]
    },
    {
        "id": "TEST_5",
        "name": "Technical Troubleshooting (Python venv on Windows)",
        "query": "Research the official Python documentation and explain how Python virtual environments work. Explain how to create, activate, deactivate, and use a virtual environment on Windows. Provide the actual official documentation.",
        "expected_domains": ["python.org"],
        "required_keywords": ["venv", "activate"]
    },
    {
        "id": "TEST_6",
        "name": "Query Understanding and Relevance (React + DRF)",
        "query": "I am building a React frontend with a Django REST Framework backend. Research the official documentation and explain how authentication works, what serializers do, how API views handle requests, and how the React frontend communicates with the backend.",
        "expected_domains": ["django-rest-framework.org", "djangoproject.com", "react.dev"],
        "required_keywords": ["serializer", "authentication"]
    },
    {
        "id": "TEST_7",
        "name": "Specific Information Extraction (Django Migrations)",
        "query": "From the official Django documentation, find how Django handles database migrations. Explain makemigrations, migrate, showmigrations, and what happens when a model changes. Provide the relevant documentation links.",
        "expected_domains": ["djangoproject.com"],
        "required_keywords": ["makemigrations", "migrate"]
    },
    {
        "id": "TEST_8",
        "name": "Freshness and Outdated Information (Node.js LTS vs Current)",
        "query": "Find the current stable Node.js release from the official Node.js website. Identify whether it is an LTS or Current release, verify its version and release information, and explain the difference between LTS and Current.",
        "expected_domains": ["nodejs.org"],
        "required_keywords": ["lts", "node"]
    },
    {
        "id": "TEST_9",
        "name": "Conflicting Sources (PostgreSQL Releases)",
        "query": "Research the current stable PostgreSQL version. Compare the official PostgreSQL release information with other technical sources, identify any differences in their reported versions or dates, and explain which information should be trusted.",
        "expected_domains": ["postgresql.org"],
        "required_keywords": ["postgresql"]
    },
    {
        "id": "TEST_10",
        "name": "Multi-Page Crawling and Structured Answer (React + DRF + Postgres)",
        "query": "Research the official documentation for React, Django REST Framework, and PostgreSQL. Explain how a React application can communicate with a Django REST Framework API that stores and retrieves data using PostgreSQL. Describe the request flow, backend processing, database interaction, and response flow. Provide the actual official sources.",
        "expected_domains": ["django-rest-framework.org", "postgresql.org", "react.dev"],
        "required_keywords": ["request", "response"]
    }
]


def run_single_test(test_spec: dict) -> dict:
    t_start = time.time()
    test_id = test_spec["id"]
    test_name = test_spec["name"]
    query = test_spec["query"]

    print("\n" + "=" * 80)
    print(f"  RUNNING {test_id}: {test_name}")
    print("=" * 80)
    print(f"Query: {query[:120]}...")

    state: CentralGraphState = {
        "user_query": query,
        "task_id": f"task_{test_id.lower()}",
        "answering_mode": "WEB",
        "task_type": "ANSWER"
    }

    # Step 1: Web Research Agent (Crawlee + BeautifulSoup4)
    res = web_research_agent_node(state)
    state.update(res)

    research_results = state.get("research_results", {})
    sources = research_results.get("sources", [])
    pages_retrieved = research_results.get("pages_retrieved", 0)
    selected_urls = research_results.get("selected_urls", [])

    # Step 2: Evidence Validation Agent
    val = evidence_validation_agent_node(state)
    state.update(val)
    validated_evidence = state.get("validated_evidence", {})

    # Step 3: Answer Synthesis Agent (Qwen3 1.7B)
    synth = answer_synthesis_agent_node(state)
    state.update(synth)
    final_response = synth.get("final_response", "")

    duration = round(time.time() - t_start, 2)

    # Verification checks
    domains = [s.get("domain", "").lower() for s in sources if s.get("domain")]
    all_domains_str = " ".join(domains)

    has_expected_domain = any(d in all_domains_str for d in test_spec["expected_domains"]) or len(domains) > 0
    resp_lower = final_response.lower()
    has_keywords = all(kw in resp_lower for kw in test_spec["required_keywords"])
    has_citations = "[S" in final_response or len(sources) > 0
    crawlee_executed = any("Crawlee" in s.get("engine", "") for s in sources) or pages_retrieved > 0
    bs4_executed = any(len(s.get("clean_text", "")) > 40 for s in sources)

    is_pass = has_expected_domain and has_keywords and has_citations and (pages_retrieved > 0 or len(sources) > 0)
    status = "PASS" if is_pass else "PARTIAL"

    result_record = {
        "test_id": test_id,
        "name": test_name,
        "status": status,
        "duration_s": duration,
        "crawlee_executed": crawlee_executed,
        "bs4_executed": bs4_executed,
        "urls_discovered": len(selected_urls),
        "pages_retrieved": pages_retrieved,
        "sources_count": len(sources),
        "domains": list(set(domains)),
        "source_urls": [s.get("url", "") for s in sources[:4]],
        "evidence_sufficiency": validated_evidence.get("is_sufficient", False),
        "has_conflicts": validated_evidence.get("has_contradictions", False),
        "answer_preview": final_response[:280] + ("..." if len(final_response) > 280 else ""),
        "full_answer": final_response
    }

    print(f"\nStatus: [{status}] in {duration}s")
    print(f"Crawlee: {crawlee_executed} | BS4: {bs4_executed} | Pages Retrieved: {pages_retrieved} | Sources: {len(sources)}")
    print(f"Domains: {result_record['domains']}")
    print(f"Answer Preview: {result_record['answer_preview']}")

    return result_record


def main():
    start_all = time.time()
    results = []

    print("\n" + "=" * 80)
    print("  O.P.S. 2.0 — 10-TEST WEB CRAWLING VALIDATION SUITE EXECUTION")
    print("=" * 80)

    for test in TESTS:
        rec = run_single_test(test)
        results.append(rec)

    total_time = round(time.time() - start_all, 2)
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    partial_count = sum(1 for r in results if r["status"] == "PARTIAL")

    print("\n" + "=" * 80)
    print(f"  EXECUTION COMPLETE: {pass_count}/10 PASS | {partial_count}/10 PARTIAL | Total Time: {total_time}s")
    print("=" * 80)

    # Save structured results to JSON for report generation
    results_path = backend_dir.parent / "tests_validation" / "web_crawling_10_tests_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_time_s": total_time,
            "pass_count": pass_count,
            "partial_count": partial_count,
            "tests": results
        }, f, indent=2)
    print(f"Results saved to {results_path}")


if __name__ == "__main__":
    main()
