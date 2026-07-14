#!/usr/bin/env python3
"""Retired VESUM importer.

The former v6.7.5 importer stripped comments and skipped ``bad`` rows, so it
cannot create the marker-preserving schema required by the v6.8.0 lock.  Use
``scripts/rag/build_vesum_shadow.py`` with explicit shadow output paths.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.rag.build_vesum_shadow import main

if __name__ == "__main__":
    main()
