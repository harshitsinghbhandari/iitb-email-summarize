"""Experimental deadline extraction via Ollama function calling."""

from .function_calling import (
    DEADLINE_FUNCTION_MODEL,
    DEADLINE_TOOL,
    DeadlineFunctionCall,
    call_deadline_tool,
    extract_deadline_call,
)

__all__ = [
    "DEADLINE_FUNCTION_MODEL",
    "DEADLINE_TOOL",
    "DeadlineFunctionCall",
    "call_deadline_tool",
    "extract_deadline_call",
]
