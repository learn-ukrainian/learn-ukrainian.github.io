#!/usr/bin/env python3
"""Pre-commit: regenerate the lesson component schema.

``docs/lesson-schema.yaml`` is a committed representation of the public lesson
component interfaces.  It must be refreshed whenever one of its source
components changes; otherwise the contracts checks fail only after a PR reaches
CI.  The matching pre-commit entry invokes this helper and then requires the
refreshed schema to be staged, following the Atlas lexicon fingerprint pattern.

The generator remains the single implementation of schema construction.  This
small wrapper gives the local guard a stable, testable entry point and prints a
clear confirmation of the file it refreshed.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build import generate_lesson_schema


def main() -> int:
    """Regenerate the committed lesson schema through its canonical generator."""
    result = generate_lesson_schema.main()
    if result == 0:
        print("Lesson schema written: docs/lesson-schema.yaml")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
