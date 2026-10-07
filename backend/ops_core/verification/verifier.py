"""
O.P.S. Verifier & Critic Engine
Never trusts model statements as proof.
Compares expected outcomes against observed ground-truth evidence.
"""

import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ops_core.capabilities.schemas import ToolCallRequest, ToolCallResult
from ops_core.verification.ground_truth import GroundTruthInspector

logger = logging.getLogger("ops.verification.verifier")


class VerificationEvidence(BaseModel):
    verified: bool
    assertions_passed: List[str] = Field(default_factory=list)
    assertions_failed: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)


class Verifier:
    @classmethod
    async def verify_tool_execution(
        cls,
        capability: str,
        arguments: Dict[str, Any],
        raw_result: Dict[str, Any]
    ) -> VerificationEvidence:
        """Asynchronously verifies tool execution against physical state."""
        passed = []
        failed = []

        if capability in ["filesystem.write", "filesystem.create_directory"]:
            path = arguments.get("path")
            if path and GroundTruthInspector.check_file_exists(path):
                passed.append(f"File/directory exists: {path}")
            else:
                failed.append(f"File/directory does not exist on disk: {path}")

        elif capability == "filesystem.delete":
            path = arguments.get("path")
            if path and GroundTruthInspector.check_file_not_exists(path):
                passed.append(f"File deleted: {path}")
            else:
                failed.append(f"File still present: {path}")

        elif capability in ["terminal.execute", "terminal.run_tests"]:
            exit_code = raw_result.get("exit_code", -1)
            if exit_code == 0:
                passed.append(f"Command exited with code 0")
            else:
                failed.append(f"Non-zero exit code: {exit_code}")

        if raw_result.get("status") == "FAILED" and not failed:
            failed.append(raw_result.get("error", "Execution marked as failed."))

        is_verified = (len(failed) == 0 and len(passed) > 0)
        return VerificationEvidence(
            verified=is_verified,
            assertions_passed=passed,
            assertions_failed=failed,
            evidence=raw_result
        )

    @classmethod
    def verify_tool_result(cls, request: ToolCallRequest, result: ToolCallResult) -> bool:
        """
        Validates whether the executed tool actually achieved the requested physical ground-truth.
        Returns True if verified, False if failed.
        """
        if result.status != "SUCCESS":
            return False

        capability = request.capability
        args = request.arguments
        evidence = result.evidence or {}

        # 1. Filesystem Verifications
        if capability in ["filesystem.create_directory", "filesystem.write"]:
            path = args.get("path")
            verified = GroundTruthInspector.check_file_exists(path)
            if not verified:
                result.status = "FAILED"
                result.error = f"Verification failed: Path does not exist on disk after creation ({path})"
                return False

        elif capability == "filesystem.delete":
            path = args.get("path")
            verified = GroundTruthInspector.check_file_not_exists(path)
            if not verified:
                result.status = "FAILED"
                result.error = f"Verification failed: File still exists on disk after deletion ({path})"
                return False

        elif capability == "filesystem.move":
            src = args.get("source")
            dst = args.get("destination")
            verified = GroundTruthInspector.check_file_exists(dst) and GroundTruthInspector.check_file_not_exists(src)
            if not verified:
                result.status = "FAILED"
                result.error = "Verification failed: Move destination missing or source still present."
                return False

        # 2. Terminal & Test Verifications
        elif capability == "terminal.execute":
            exit_code = result.result.get("exit_code", -1)
            if exit_code != 0 and not args.get("allow_nonzero"):
                result.status = "FAILED"
                return False

        elif capability == "terminal.run_tests":
            exit_code = result.result.get("exit_code", -1)
            if exit_code != 0:
                result.status = "FAILED"
                result.error = "Test suite failed with non-zero exit code."
                return False

        # 3. Desktop Application Verification
        elif capability == "desktop.launch_app":
            app = args.get("app_name") or args.get("application")
            # If evidence confirms execution, mark verified
            if not evidence.get("process_running", False):
                result.status = "FAILED"
                result.error = f"Verification failed: Process '{app}' failed to launch."
                return False

        # 4. Web Search Verification
        elif capability.startswith("web."):
            content = result.result.get("content", "")
            if not content or len(content.strip()) < 10:
                result.status = "FAILED"
                result.error = "Web extraction returned empty evidence."
                return False

        return True
