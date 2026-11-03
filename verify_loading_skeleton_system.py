"""
Automated Verification Suite for O.P.S. 2.0 AI Response Loading Skeleton & Generation Animation.
Validates:
1. Reusable skeleton components architecture (SkeletonBase, LoadingStatusIndicator,
   TextGenerationSkeleton, StructuredResponseSkeleton, CodeGenerationSkeleton,
   ResearchSkeleton, CockpitLoadingSkeleton, PageLoadingSkeleton).
2. Intelligent Loading States mapping (Thinking, Planning, Generating, Searching,
   Retrieving, Processing, Executing, Verifying, Connecting, Neutral).
3. Query-based Skeleton Variation Detection (Text, Structured, Code, Research).
4. CSS Shimmer Animation & Accessibility (ops-skeleton-shimmer, prefers-reduced-motion).
5. Integration into Main Application (OpsBriefingCard.jsx).
6. Integration into Pop-up Cockpit (SeparatePopupCockpit.jsx).
7. Integration into Universal Views (OpsUserMemoriesTab.jsx).
8. Progressive Streaming & Stop Generation support.
"""

import os
import sys
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
SKELETONS_DIR = os.path.join(FRONTEND_DIR, "src", "components", "skeletons")

def check(name, condition, details=""):
    status = "[PASS]" if condition else "[FAIL]"
    print(f"{status} {name}")
    if not condition and details:
        print(f"       ERROR: {details}")
    return condition

def test_component_architecture():
    print("\n--- 1. Testing Reusable Skeleton Component Architecture ---")
    files = [
        "SkeletonBase.jsx",
        "LoadingStatusIndicator.jsx",
        "TextGenerationSkeleton.jsx",
        "StructuredResponseSkeleton.jsx",
        "CodeGenerationSkeleton.jsx",
        "ResearchSkeleton.jsx",
        "CockpitLoadingSkeleton.jsx",
        "PageLoadingSkeleton.jsx",
        "index.js"
    ]
    for f in files:
        path = os.path.join(SKELETONS_DIR, f)
        check(f"Skeleton component exists: {f}", os.path.exists(path))

def test_intelligent_loading_states():
    print("\n--- 2. Testing Intelligent Loading States Mapping ---")
    indicator_file = os.path.join(SKELETONS_DIR, "LoadingStatusIndicator.jsx")
    with open(indicator_file, "r", encoding="utf-8") as f:
        content = f.read()

    expected_states = [
        ("thinking", "Thinking..."),
        ("planning", "Planning your request..."),
        ("generating", "Generating response..."),
        ("searching", "Searching for information..."),
        ("retrieving", "Retrieving relevant information..."),
        ("processing", "Processing your request..."),
        ("executing", "Executing your task..."),
        ("verifying", "Verifying the result..."),
        ("connecting", "Connecting to the service..."),
        ("neutral", "Working on your request...")
    ]

    for key, label in expected_states:
        found = f"'{key}'" in content or f'"{key}"' in content or f"{key}:" in content
        label_found = label in content
        check(f"Loading state configured: {key} -> '{label}'", found and label_found)

    # Verify resolveLoadingStateKey function exists
    check("resolveLoadingStateKey function defined", "resolveLoadingStateKey" in content)

def test_skeleton_variations():
    print("\n--- 3. Testing Skeleton Variations & Intent Detection ---")
    cockpit_skeleton_file = os.path.join(SKELETONS_DIR, "CockpitLoadingSkeleton.jsx")
    with open(cockpit_skeleton_file, "r", encoding="utf-8") as f:
        content = f.read()

    check("detectSkeletonVariation function defined", "detectSkeletonVariation" in content)
    check("Code generation skeleton detection", "q.includes('python')" in content and "return 'code'" in content)
    check("Structured response skeleton detection", "q.includes('compare')" in content and "return 'structured'" in content)
    check("Research response skeleton detection", "q.includes('research')" in content and "return 'research'" in content)
    check("Text response fallback", "return 'text'" in content)

    # Check variation components
    code_file = os.path.join(SKELETONS_DIR, "CodeGenerationSkeleton.jsx")
    with open(code_file, "r", encoding="utf-8") as f:
        code_content = f.read()
    check("Code skeleton contains indented lines and terminal badge", "pl-4" in code_content and "Terminal" in code_content)

    struct_file = os.path.join(SKELETONS_DIR, "StructuredResponseSkeleton.jsx")
    with open(struct_file, "r", encoding="utf-8") as f:
        struct_content = f.read()
    check("Structured skeleton contains heading and bullet point markers", "rounded-full" in struct_content and "Heading" in struct_content)

    research_file = os.path.join(SKELETONS_DIR, "ResearchSkeleton.jsx")
    with open(research_file, "r", encoding="utf-8") as f:
        research_content = f.read()
    check("Research skeleton contains citation pill badges", "Globe" in research_content and "BookOpen" in research_content)

    text_file = os.path.join(SKELETONS_DIR, "TextGenerationSkeleton.jsx")
    with open(text_file, "r", encoding="utf-8") as f:
        text_content = f.read()
    check("Text skeleton has variable line widths", 'width="94%"' in text_content and 'width="82%"' in text_content)

def test_css_shimmer_and_accessibility():
    print("\n--- 4. Testing CSS Shimmer Animation & Accessibility ---")
    css_file = os.path.join(FRONTEND_DIR, "src", "index.css")
    with open(css_file, "r", encoding="utf-8") as f:
        css = f.read()

    check("ops-shimmer keyframes defined", "@keyframes ops-shimmer" in css)
    check("ops-skeleton-shimmer class defined", ".ops-skeleton-shimmer" in css)
    check("prefers-reduced-motion media query respected", "@media (prefers-reduced-motion: reduce)" in css)

    base_file = os.path.join(SKELETONS_DIR, "SkeletonBase.jsx")
    with open(base_file, "r", encoding="utf-8") as f:
        base_content = f.read()
    check("SkeletonBase applies aria-hidden for accessibility", 'aria-hidden="true"' in base_content)

    cockpit_skeleton_file = os.path.join(SKELETONS_DIR, "CockpitLoadingSkeleton.jsx")
    with open(cockpit_skeleton_file, "r", encoding="utf-8") as f:
        c_content = f.read()
    check("CockpitLoadingSkeleton sets aria-live and aria-busy", 'aria-live="polite"' in c_content and 'aria-busy="true"' in c_content)

def test_main_app_integration():
    print("\n--- 5. Testing Main Application Integration (OpsBriefingCard.jsx) ---")
    briefing_file = os.path.join(FRONTEND_DIR, "src", "components", "OpsBriefingCard.jsx")
    with open(briefing_file, "r", encoding="utf-8") as f:
        content = f.read()

    check("OpsBriefingCard imports CockpitLoadingSkeleton", "import CockpitLoadingSkeleton" in content)
    check("OpsBriefingCard uses CockpitLoadingSkeleton during isLoading", "<CockpitLoadingSkeleton" in content)
    check("OpsBriefingCard passes activeTaskPrompt, agent, thought, streamingChunk, onStopExecution",
          "query={activeTaskPrompt}" in content and "streamingChunk={streamingChunk}" in content and "onStopExecution={onStopExecution}" in content)

def test_cockpit_integration():
    print("\n--- 6. Testing Pop-up Cockpit Integration (SeparatePopupCockpit.jsx) ---")
    cockpit_file = os.path.join(FRONTEND_DIR, "src", "components", "SeparatePopupCockpit.jsx")
    with open(cockpit_file, "r", encoding="utf-8") as f:
        content = f.read()

    check("SeparatePopupCockpit imports CockpitLoadingSkeleton", "import CockpitLoadingSkeleton" in content)
    check("SeparatePopupCockpit uses CockpitLoadingSkeleton with compact={true}",
          "<CockpitLoadingSkeleton" in content and "compact={true}" in content)
    check("SeparatePopupCockpit passes currentTaskPrompt, agent, thought, streamingChunk, stop handler",
          "query={currentTaskPrompt}" in content and "streamingChunk={streamingChunk}" in content and "onStopExecution={handleEmergencyHalt}" in content)

def test_universal_skeletons():
    print("\n--- 7. Testing Universal Loading Skeletons (OpsUserMemoriesTab.jsx) ---")
    memories_file = os.path.join(FRONTEND_DIR, "src", "components", "OpsUserMemoriesTab.jsx")
    with open(memories_file, "r", encoding="utf-8") as f:
        content = f.read()

    check("OpsUserMemoriesTab imports PageLoadingSkeleton", "import PageLoadingSkeleton" in content)
    check("OpsUserMemoriesTab renders PageLoadingSkeleton when isLoading", "<PageLoadingSkeleton" in content)

def main():
    print("======================================================================")
    print(" O.P.S. 2.0 — AI RESPONSE LOADING SKELETON VERIFICATION SUITE         ")
    print("======================================================================")
    test_component_architecture()
    test_intelligent_loading_states()
    test_skeleton_variations()
    test_css_shimmer_and_accessibility()
    test_main_app_integration()
    test_cockpit_integration()
    test_universal_skeletons()
    print("\n======================================================================")
    print(" SKELETON VERIFICATION COMPLETE                                       ")
    print("======================================================================")

if __name__ == "__main__":
    main()
