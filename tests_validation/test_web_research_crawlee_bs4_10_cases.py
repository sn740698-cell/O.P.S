"""
O.P.S. 2.0 — Web Research Engine Redesign Validation (10 Scenarios)
Crawlee + BeautifulSoup4 Comprehensive Verification Suite.

Scenarios:
1. Latest stable Django version & release date
2. Latest stable Python version & release date
3. Latest stable Node.js release
4. Latest React release information
5. Explanation of a specific Django middleware feature (CsrfViewMiddleware)
6. Extraction of a table from official documentation (converted to Markdown)
7. Comparison of Django and FastAPI using official documentation evidence
8. Multi-source research across distinct official domains
9. Conflicting or outdated source detection and resolution
10. Query where reliable evidence cannot be found (verifies honest failure reporting)
"""

import sys
import os
import time
import re
from pathlib import Path

# Enable automatic unbuffered output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")

import django
django.setup()

from research_system.graph.workers.crawling_worker import CrawleeWebCrawler, _normalize_url
from research_system.graph.workers.content_extraction_worker import extract_with_bs4, _convert_table_to_markdown
from research_system.orchestrator.agents.web_research_agent import web_research_agent_node, _understand_and_decompose_query
from research_system.orchestrator.agents.evidence_validation_agent import evidence_validation_agent_node, _check_freshness_and_conflicts
from research_system.orchestrator.agents.answer_synthesis_agent import answer_synthesis_agent_node
from research_system.orchestrator.state import CentralGraphState
from bs4 import BeautifulSoup


def print_header(title: str):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)


def test_scenario_1_django_version():
    """1. Latest stable Django version and release date."""
    print_header("Scenario 1: Latest Stable Django Version & Release Date")
    query = "What is the latest stable Django version and when was it released?"
    
    state: CentralGraphState = {
        "user_query": query,
        "task_id": "test_s1",
        "answering_mode": "WEB",
        "task_type": "ANSWER"
    }

    res = web_research_agent_node(state)
    state.update(res)
    val = evidence_validation_agent_node(state)
    state.update(val)
    synth = answer_synthesis_agent_node(state)
    
    answer = synth.get("final_response", "")
    sources = state.get("research_results", {}).get("sources", [])
    
    print(f"Sources retrieved: {len(sources)}")
    for s in sources[:3]:
        print(f"  [{s.get('source_id')}] {s.get('title')} ({s.get('domain')})")
    
    print("\nSynthesized Answer Preview:")
    print(answer[:400] + ("..." if len(answer) > 400 else ""))
    
    assert len(sources) > 0, "Should have retrieved at least 1 source"
    has_django_source = any("djangoproject.com" in s.get("domain", "") for s in sources)
    assert has_django_source, "Should have retrieved official djangoproject.com domain"
    assert "5.1" not in answer or "6." in answer or "5.2" in answer, "Should not present outdated Django 5.1 as latest"
    assert "[S" in answer, "Answer must contain verified [S1], [S2] citation tags"
    print("\n[PASS] Scenario 1 verified successfully.")


def test_scenario_2_python_version():
    """2. Latest stable Python version and release date."""
    print_header("Scenario 2: Latest Stable Python Version & Release Date")
    query = "What is the latest stable Python 3 version and release date?"
    
    state: CentralGraphState = {
        "user_query": query,
        "task_id": "test_s2",
        "answering_mode": "WEB",
        "task_type": "ANSWER"
    }

    res = web_research_agent_node(state)
    state.update(res)
    val = evidence_validation_agent_node(state)
    state.update(val)
    synth = answer_synthesis_agent_node(state)
    
    answer = synth.get("final_response", "")
    sources = state.get("research_results", {}).get("sources", [])
    
    print(f"Sources retrieved: {len(sources)}")
    for s in sources[:3]:
        print(f"  [{s.get('source_id')}] {s.get('title')} ({s.get('domain')})")

    assert len(sources) > 0
    has_python_source = any("python.org" in s.get("domain", "") for s in sources)
    assert has_python_source, "Should prioritize official python.org domain"
    assert "3." in answer, "Should report Python 3 series version"
    assert "[S" in answer, "Must include citation tags"
    print("\n[PASS] Scenario 2 verified successfully.")


def test_scenario_3_nodejs_release():
    """3. Latest stable Node.js release."""
    print_header("Scenario 3: Latest Stable Node.js Release")
    query = "What is the latest stable LTS Node.js release?"
    
    state: CentralGraphState = {
        "user_query": query,
        "task_id": "test_s3",
        "answering_mode": "WEB",
        "task_type": "ANSWER"
    }

    res = web_research_agent_node(state)
    state.update(res)
    val = evidence_validation_agent_node(state)
    state.update(val)
    synth = answer_synthesis_agent_node(state)
    
    answer = synth.get("final_response", "")
    sources = state.get("research_results", {}).get("sources", [])
    
    print(f"Sources retrieved: {len(sources)}")
    has_node_source = any("nodejs.org" in s.get("domain", "") or "github.com" in s.get("domain", "") for s in sources)
    assert has_node_source or len(sources) > 0
    assert "[S" in answer
    print("\n[PASS] Scenario 3 verified successfully.")


def test_scenario_4_react_release():
    """4. Latest React release information."""
    print_header("Scenario 4: Latest React Release Information")
    query = "What is the latest React release and its primary new features?"
    
    state: CentralGraphState = {
        "user_query": query,
        "task_id": "test_s4",
        "answering_mode": "WEB",
        "task_type": "ANSWER"
    }

    res = web_research_agent_node(state)
    state.update(res)
    val = evidence_validation_agent_node(state)
    state.update(val)
    synth = answer_synthesis_agent_node(state)
    
    answer = synth.get("final_response", "")
    sources = state.get("research_results", {}).get("sources", [])
    
    print(f"Sources retrieved: {len(sources)}")
    assert len(sources) > 0
    assert "React" in answer
    print("\n[PASS] Scenario 4 verified successfully.")


def test_scenario_5_django_middleware():
    """5. Technical explanation of a specific Django middleware feature."""
    print_header("Scenario 5: Django CsrfViewMiddleware Explanation")
    query = "How does Django CsrfViewMiddleware work according to official documentation?"
    
    state: CentralGraphState = {
        "user_query": query,
        "task_id": "test_s5",
        "answering_mode": "WEB",
        "task_type": "ANSWER"
    }

    res = web_research_agent_node(state)
    state.update(res)
    val = evidence_validation_agent_node(state)
    state.update(val)
    synth = answer_synthesis_agent_node(state)
    
    answer = synth.get("final_response", "")
    print(answer[:350] + "...")
    assert "csrf" in answer.lower(), "Should explain CSRF protection"
    print("\n[PASS] Scenario 5 verified successfully.")


def test_scenario_6_table_extraction():
    """6. Extraction of a table from official documentation into Markdown."""
    print_header("Scenario 6: HTML Table Extraction to Markdown via BeautifulSoup4")
    
    raw_html = """
    <html><body>
    <h1>Django Supported Versions</h1>
    <table border="1" class="version-table">
      <thead>
        <tr><th>Version</th><th>Release Date</th><th>Status</th><th>End of Life</th></tr>
      </thead>
      <tbody>
        <tr><td>6.1</td><td>April 2026</td><td>Future</td><td>Dec 2026</td></tr>
        <tr><td>6.0</td><td>Dec 2025</td><td>Main Feature</td><td>April 2026</td></tr>
        <tr><td>5.2 LTS</td><td>April 2025</td><td>Current Stable LTS</td><td>April 2028</td></tr>
        <tr><td>5.1</td><td>August 2024</td><td>Extended Support</td><td>April 2025</td></tr>
      </tbody>
    </table>
    </body></html>
    """
    
    extracted = extract_with_bs4(raw_html, "https://docs.djangoproject.com/en/dev/internals/release-process/")
    tables = extracted.get("tables", [])
    
    print("Extracted Tables Count:", len(tables))
    assert len(tables) > 0, "Must extract at least one markdown table"
    table_md = tables[0]
    print("\nGenerated Markdown Table:\n" + table_md)
    
    assert "| Version | Release Date | Status | End of Life |" in table_md
    assert "| --- | --- | --- | --- |" in table_md
    assert "| 5.2 LTS | April 2025 | Current Stable LTS | April 2028 |" in table_md
    assert extracted.get("extraction_status") == "SUCCESS"
    print("\n[PASS] Scenario 6 verified successfully.")


def test_scenario_7_comparison_django_fastapi():
    """7. Comparison of Django and FastAPI using official documentation evidence."""
    print_header("Scenario 7: Django vs FastAPI Official Comparison")
    query = "Compare Django and FastAPI using official documentation evidence"
    
    state: CentralGraphState = {
        "user_query": query,
        "task_id": "test_s7",
        "answering_mode": "WEB",
        "task_type": "ANSWER"
    }

    res = web_research_agent_node(state)
    state.update(res)
    val = evidence_validation_agent_node(state)
    state.update(val)
    synth = answer_synthesis_agent_node(state)
    
    answer = synth.get("final_response", "")
    sources = state.get("research_results", {}).get("sources", [])
    
    print(f"Sources retrieved: {len(sources)}")
    domains = {s.get("domain", "") for s in sources}
    print("Domains retrieved:", domains)
    
    # Verify no arbitrary fabricated RPS claims like "Django handles exactly 1420 rps vs FastAPI 9420 rps"
    has_arbitrary_rps = bool(re.search(r"\b\d{4,6}\s*(?:req|rps|requests\s*per\s*second)\b", answer, re.IGNORECASE))
    assert not has_arbitrary_rps, "Should not hallucinate arbitrary specific RPS benchmarks"
    assert "Django" in answer and "FastAPI" in answer
    print("\n[PASS] Scenario 7 verified successfully.")


def test_scenario_8_multisource_official():
    """8. Multi-source research across two distinct official sources."""
    print_header("Scenario 8: Multi-Source Research Across Distinct Official Domains")
    
    crawler = CrawleeWebCrawler(max_requests_per_crawl=3, max_retries=1)
    test_urls = [
        "https://www.djangoproject.com",
        "https://www.python.org"
    ]
    pages = crawler.crawl(test_urls)
    
    print(f"Pages crawled: {len(pages)}")
    domains = {p.get("domain") for p in pages if p.get("domain")}
    print(f"Distinct domains: {domains}")
    
    assert len(domains) >= 2, "Should crawl multiple distinct official domains"
    assert any("djangoproject.com" in d for d in domains)
    assert any("python.org" in d for d in domains)
    for p in pages:
        assert p.get("engine") == "Crawlee BeautifulSoupCrawler"
        assert p.get("status_code") == 200
    print("\n[PASS] Scenario 8 verified successfully.")


def test_scenario_9_conflict_detection():
    """9. Conflicting or outdated source detection."""
    print_header("Scenario 9: Conflict & Outdated Source Resolution")
    
    mock_sources = [
        {
            "source_id": "S1",
            "title": "Old Blog Article (2023)",
            "url": "https://random-tech-blog.com/django-release-2023",
            "domain": "random-tech-blog.com",
            "clean_text": "The latest stable version is Django 5.1 released in October 2023.",
            "tables": []
        },
        {
            "source_id": "S2",
            "title": "Official Django Project Download",
            "url": "https://www.djangoproject.com/download/",
            "domain": "www.djangoproject.com",
            "clean_text": "The latest official release is Django 6.1.3.",
            "tables": ["| Series | Latest Release |\n| --- | --- |\n| 6.1 | 6.1.3 |"]
        }
    ]
    
    freshness = _check_freshness_and_conflicts(mock_sources, "What is the latest stable Django version?")
    print("Freshness & Conflict check:", freshness)
    
    assert freshness["has_conflicts"] is True, "Must detect conflict between secondary and official source"
    assert "6.1.3" in freshness["official_versions"], "Official version must be captured"
    print("\n[PASS] Scenario 9 verified successfully.")


def test_scenario_10_unverifiable_honest_reporting():
    """10. Query where reliable evidence cannot be found (verifies honest failure reporting)."""
    print_header("Scenario 10: Unverifiable Query (Honest Failure Reporting)")
    query = "What is the exact hyperspace warp factor of the fictitious QuantumFlux-9988X framework?"
    
    state: CentralGraphState = {
        "user_query": query,
        "task_id": "test_s10",
        "answering_mode": "WEB",
        "task_type": "ANSWER",
        "research_results": {"sources": [], "chunks": []},
        "validated_evidence": {"is_sufficient": False, "validated_sources": [], "valid_passages": []}
    }

    synth = answer_synthesis_agent_node(state)
    answer = synth.get("final_response", "")
    
    print("\nHonest Response Delivered:")
    print(answer)
    
    assert "could not be verified" in answer.lower() or "unverified" in answer.lower(), "Must honestly state evidence could not be verified"
    assert "warp factor" not in answer or "does not guess" in answer, "Must not hallucinate fictitious facts"
    print("\n[PASS] Scenario 10 verified successfully.")


if __name__ == "__main__":
    t_start = time.time()
    print_header("O.P.S. 2.0 — CRAWLEE + BEAUTIFULSOUP4 10-SCENARIO VERIFICATION SUITE")
    
    test_scenario_6_table_extraction()
    test_scenario_8_multisource_official()
    test_scenario_9_conflict_detection()
    test_scenario_10_unverifiable_honest_reporting()
    test_scenario_1_django_version()
    test_scenario_2_python_version()
    test_scenario_3_nodejs_release()
    test_scenario_4_react_release()
    test_scenario_5_django_middleware()
    test_scenario_7_comparison_django_fastapi()

    elapsed = round(time.time() - t_start, 2)
    print_header(f"ALL 10 SCENARIOS PASSED IN {elapsed}s")
