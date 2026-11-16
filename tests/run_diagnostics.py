"""
Diagnostics runner for TestAutomationEngineFull.
Runs each test individually and reports status and error.
"""

import os
import sys
import unittest
import traceback

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")

import django
django.setup()

from tests.test_automation_engine_full import TestAutomationEngineFull

suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestAutomationEngineFull)
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

print("\n" + "="*50)
print(f"Total Tests: {result.testsRun}")
print(f"Failures: {len(result.failures)}")
print(f"Errors: {len(result.errors)}")
print("="*50)

if result.failures:
    print("\nFAILURES:")
    for f in result.failures:
        print(f[0], "\n", f[1])

if result.errors:
    print("\nERRORS:")
    for e in result.errors:
        print(e[0], "\n", e[1])
