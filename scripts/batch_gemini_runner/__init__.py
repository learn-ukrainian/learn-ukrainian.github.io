"""Batch Gemini Runner package.

Autonomous batch runner for curriculum generation using Gemini CLI.
Split from a monolithic module for maintainability (MI=A target).

Usage:
    from batch_gemini_runner import BatchRunner, show_failures, setup_logging
"""

import sys
from pathlib import Path

# Ensure scripts/ is on sys.path for sibling imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .report import show_failures
from .runner import BatchRunner
from .utils import (
    _filter_schema_for_track,
    _get_core_activity_examples,
    _get_seminar_activity_examples,
    setup_logging,
)

__all__ = [
    "BatchRunner",
    "_filter_schema_for_track",
    "_get_core_activity_examples",
    "_get_seminar_activity_examples",
    "setup_logging",
    "show_failures",
]
