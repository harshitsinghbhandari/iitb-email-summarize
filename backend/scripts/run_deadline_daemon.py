#!/usr/bin/env python3
"""Run the deadline extraction daemon."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from deadline_tools.daemon import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
