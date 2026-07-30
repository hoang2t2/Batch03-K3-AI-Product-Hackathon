#!/usr/bin/env python3
"""Run the local Track Advisor application."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from track_advisor.presentation.server import run


if __name__ == "__main__":
    run()
