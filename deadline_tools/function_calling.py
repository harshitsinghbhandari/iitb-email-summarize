"""Test bed for deadline extraction using Ollama function calling."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any

import requests

from summarize_mail.config import OLLAMA_BASE_URL

DEADLINE_FUNCTION_MODEL = os.getenv("DEADLINE_FUNCTION_MODEL", "functiongemma:270m")

DEADLINE_TOOL = {
    "type": "function",
    "function": {
        "name": "record_deadline",
        "description": "Record a deadline or important due date found in campus email content.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short human-readable title for the deadline.",
                },
                "due_date": {
                    "type": "string",
                    "description": "Due date in YYYY-MM-DD format when possible, otherwise the exact date text.",
                },
                "source_text": {
                    "type": "string",
                    "description": "The specific phrase or sentence that supports the deadline.",
                },
                "action_required": {
                    "type": "boolean",
                    "description": "Whether the student needs to do something before the date.",
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence from 0.0 to 1.0 that this is a real deadline.",
                },
            },
            "required": ["title", "due_date", "source_text", "action_required", "confidence"],
        },
    },
}


@dataclass(frozen=True)
class DeadlineFunctionCall:
    """Normalized result from the record_deadline tool call."""

    title: str
    due_date: str
    source_text: str
    action_required: bool
    confidence: float


def build_deadline_payload(email_content: str) -> dict[str, Any]:
    """Build the Ollama chat payload for function-calling deadline extraction."""
    return {
        "model": DEADLINE_FUNCTION_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You extract actionable student deadlines from campus emails. "
                    "If the content contains a deadline, call record_deadline exactly once. "
                    "If there is no deadline or due date, respond normally without calling a tool."
                ),
            },
            {
                "role": "user",
                "content": email_content,
            },
        ],
        "tools": [DEADLINE_TOOL],
        "stream": False,
        "options": {"temperature": 0},
    }


def extract_deadline_call(response_data: dict[str, Any]) -> DeadlineFunctionCall | None:
    """Extract and validate a record_deadline call from an Ollama chat response."""
    tool_calls = response_data.get("message", {}).get("tool_calls") or []
    for tool_call in tool_calls:
        function = tool_call.get("function", {})
        if function.get("name") != "record_deadline":
            continue

        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                return None

        if not isinstance(arguments, dict):
            return None

        required = {"title", "due_date", "source_text", "action_required", "confidence"}
        if not required.issubset(arguments):
            return None

        return DeadlineFunctionCall(
            title=str(arguments["title"]),
            due_date=str(arguments["due_date"]),
            source_text=str(arguments["source_text"]),
            action_required=bool(arguments["action_required"]),
            confidence=float(arguments["confidence"]),
        )

    return None


def call_deadline_tool(email_content: str, timeout: int = 60) -> DeadlineFunctionCall | None:
    """Call Ollama and return the normalized deadline function call, if any."""
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json=build_deadline_payload(email_content),
        timeout=timeout,
    )
    response.raise_for_status()
    return extract_deadline_call(response.json())
