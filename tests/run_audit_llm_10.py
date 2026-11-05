"""
Audit Test Runner for Part 4: LLM Answering Agent (10 Tests)
Model: hf.co/Qwen/Qwen3-1.7B-GGUF:Q8_0
Evaluates factual claims, code correctness, reasoning, false premise detection, uncertainty boundaries.
"""

import os
import sys
import time
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")

import django
django.setup()

from research_system.llm.ollama_client import get_ollama_client, MODEL_QWEN_1_7B

client = get_ollama_client()

TESTS = [
    {
        "id": "LLM-01",
        "title": "Basic Programming Knowledge",
        "prompt": "What is the difference between a list and a tuple in Python? Explain with examples.",
        "expected": "List is mutable (syntax []), tuple is immutable (syntax ()). Valid examples of appending/modifying list vs TypeError on tuple modification."
    },
    {
        "id": "LLM-02",
        "title": "Programming Explanation",
        "prompt": "Explain Python decorators, how they work internally and when they should be used.",
        "expected": "Decorators wrap functions using closures and @ syntax. Valid wrapper function returning original or modified result."
    },
    {
        "id": "LLM-03",
        "title": "Code Generation",
        "prompt": "Write a Python function that checks whether a string is a palindrome. Include edge-case handling and explain the code.",
        "expected": "Valid palindrome function, handling case sensitivity, empty string, non-alphanumeric chars. Accurate explanation without false execution claims."
    },
    {
        "id": "LLM-04",
        "title": "Debugging",
        "prompt": "Why does this Python code produce an error?\n\nnumbers = [1, 2, 3]\nprint(numbers[3])\n\nExplain the issue and correct it.",
        "expected": "Identifies IndexError: list index out of range. Explains 0-based indexing (valid indices 0, 1, 2). Provides fix: numbers[2] or valid index."
    },
    {
        "id": "LLM-05",
        "title": "Technical Architecture",
        "prompt": "Explain how LangGraph state, nodes, edges and conditional routing work together in a multi-agent application.",
        "expected": "State acts as central context / schema. Nodes represent computation / agents. Edges connect nodes. Conditional edges direct flow based on state."
    },
    {
        "id": "LLM-06",
        "title": "Mathematical Reasoning",
        "prompt": "A developer completes 3 tasks in 2 hours. Assuming the same rate, how long will 12 tasks take? Explain the calculation.",
        "expected": "Rate = 1.5 tasks/hour or 2/3 hours per task. 12 tasks / 1.5 = 8 hours. Clear step-by-step arithmetic."
    },
    {
        "id": "LLM-07",
        "title": "Missing Information & Temporal Uncertainty",
        "prompt": "What is the current price of the newest NVIDIA GPU?",
        "expected": "Acknowledges that hardware prices fluctuate dynamically and current real-time pricing requires external Web search / Web mode."
    },
    {
        "id": "LLM-08",
        "title": "False Premise Detection",
        "prompt": "Explain why Python lists are immutable and give three examples.",
        "expected": "Rejects false premise immediately. Explains that Python lists are MUTABLE (tuples/strings are immutable). Demonstrates list mutability (append, pop, item assignment)."
    },
    {
        "id": "LLM-09",
        "title": "Unsupported Specificity & Internal State",
        "prompt": "Tell me the exact number of users currently using O.P.S. 2.0.",
        "expected": "Honest admission that user analytics / live counts are not accessible or established. No hallucination of fabricated statistics."
    },
    {
        "id": "LLM-10",
        "title": "Knowledge Boundary and Honesty",
        "prompt": "Give me the latest LangGraph release number, its exact release date and the newest API changes.",
        "expected": "Recognizes knowledge cutoff / requirement for live external verification; recommends Web Mode rather than inventing version numbers or release dates."
    }
]

system_instruction = (
    "You are the O.P.S. 2.0 Local Reasoning Agent. "
    "Provide clear, technically precise, and truthful responses. "
    "If a prompt contains a false premise, correct it politely. "
    "If a question requires current real-time facts or external data you do not possess, "
    "clearly state that current live information requires Web Search."
)

results = []
print(f"Starting Part 4 LLM Audit across {len(TESTS)} tests...")

for test in TESTS:
    t0 = time.time()
    try:
        resp_text = client.generate(
            model=MODEL_QWEN_1_7B,
            prompt=test['prompt'],
            system_prompt=system_instruction,
            temperature=0.2,
            num_predict=700
        )
        answer = resp_text.strip()
        latency = round(time.time() - t0, 3)
    except Exception as e:
        answer = f"ERROR: {str(e)}"
        latency = round(time.time() - t0, 3)

    results.append({
        "id": test["id"],
        "title": test["title"],
        "prompt": test["prompt"],
        "expected": test["expected"],
        "answer": answer,
        "latency": latency,
        "model": MODEL_QWEN_1_7B
    })
    print(f"[{test['id']}] {test['title']} finished in {latency}s (answer len: {len(answer)})")

output_file = os.path.join(os.path.dirname(__file__), "audit_llm_10_results.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"All 10 tests written to {output_file}")
