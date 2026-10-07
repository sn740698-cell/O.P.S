"""
O.P.S. Standard Classified Failure & Error Types
Every system failure must be classified and structured.
"""

from enum import Enum
from typing import Optional, Dict, Any
import time


class OPSErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    PERMISSION_TIMEOUT = "PERMISSION_TIMEOUT"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    WEB_EXTRACTION_ERROR = "WEB_EXTRACTION_ERROR"
    MODEL_ERROR = "MODEL_ERROR"
    VERIFICATION_ERROR = "VERIFICATION_ERROR"
    SAFETY_BLOCK = "SAFETY_BLOCK"
    USER_CANCELLED = "USER_CANCELLED"
    MAX_RETRIES_EXCEEDED = "MAX_RETRIES_EXCEEDED"
    UNSUPPORTED_CAPABILITY = "UNSUPPORTED_CAPABILITY"


class OPSError(Exception):
    def __init__(
        self,
        code: OPSErrorCode,
        message: str,
        technical_detail: Optional[str] = None,
        task_id: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        agent: Optional[str] = None,
        recoverable: bool = False,
        retry_count: int = 0
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.technical_detail = technical_detail or message
        self.task_id = task_id
        self.tool_call_id = tool_call_id
        self.agent = agent
        self.recoverable = recoverable
        self.retry_count = retry_count
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.code.value,
            "message": self.message,
            "technical_detail": self.technical_detail,
            "task_id": self.task_id,
            "tool_call_id": self.tool_call_id,
            "agent": self.agent,
            "recoverable": self.recoverable,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp
        }
