#!/usr/bin/env python3
"""Autonomous Gemini Batch Runner -- thin wrapper.

The implementation lives in the batch_gemini_runner/ package.
This file preserves backward compatibility for CLI invocation and imports.
"""

import argparse
import sys
from pathlib import Path

# Ensure scripts/ is on sys.path for sibling imports
sys.path.insert(0, str(Path(__file__).parent))

from batch_gemini_runner import (  # noqa: E402
    BatchRunner,
    setup_logging,
    show_failures,
    _filter_schema_for_track,
    _get_core_activity_examples,
    _get_seminar_activity_examples,
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gemini Batch Runner")
    parser.add_argument("track", help="Track to process (e.g., bio, all)")
    parser.add_argument("--range", help="Range of modules (e.g., 1-10 or 5)")
    parser.add_argument(
        "--resume", action="store_true", help="Resume from last checkpoint"
    )
    parser.add_argument(
        "--from", dest="from_idx", type=int, help="Start from module index"
    )
    parser.add_argument(
        "--mode",
        choices=["build", "fix", "auto"],
        default="auto",
        help="Processing mode: build (all phases), fix (audit-driven), auto (detect per module)",
    )
    parser.add_argument(
        "--failures", action="store_true",
        help="Show failure queue instead of running batch",
    )
    parser.add_argument(
        "--max-consecutive-failures", type=int, default=3,
        help="Abort batch after N consecutive failures (0=disable, default=3)",
    )
    parser.add_argument(
        "--max-failure-rate", type=float, default=0.5,
        help="Abort batch if failure rate exceeds threshold (0=disable, default=0.5)",
    )
    parser.add_argument(
        "--retry-failures", action="store_true",
        help="Re-run only failed/stuck modules from the state file",
    )
    parser.add_argument(
        "--json-log", action="store_true",
        help="Use JSON structured logging instead of human-readable format",
    )

    args = parser.parse_args()
    setup_logging(json_mode=args.json_log)

    if args.failures:
        show_failures(args.track)
    else:
        runner = BatchRunner(
            args.track, args.range, args.resume, args.from_idx, args.mode,
            args.max_consecutive_failures, args.max_failure_rate,
            args.retry_failures,
        )
        runner.run_batch()
