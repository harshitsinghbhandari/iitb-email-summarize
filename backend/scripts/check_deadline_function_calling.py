#!/usr/bin/env python3
"""Run a live local Ollama function-calling check for deadline extraction."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from deadline_tools.function_calling import (
    DEADLINE_FUNCTION_MODEL,
    call_deadline_tool,
)  # noqa: E402

SAMPLE_EMAIL = """
Subject: CS 101 Assignment 4

Please submit Assignment 4 on Moodle by 11:59 PM on April 30, 2026.
Late submissions will not be accepted.
"""


def main() -> int:
    print(f"Testing Ollama function calling with model: {DEADLINE_FUNCTION_MODEL}")
    print("Make sure Ollama is running and the model is pulled:")
    print(f"  ollama pull {DEADLINE_FUNCTION_MODEL}")
    print("\nCalling model. This can take a bit the first time...\n")

    try:
        deadline = call_deadline_tool(SAMPLE_EMAIL, timeout=120)
    except Exception as exc:
        print("Function-calling check failed.")
        print(exc)
        return 1

    if deadline is None:
        print("Model responded, but did not call record_deadline.")
        return 1

    print("Function call worked.")
    print(deadline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
