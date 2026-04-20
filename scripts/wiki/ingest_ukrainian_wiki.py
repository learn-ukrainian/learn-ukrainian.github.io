#!/usr/bin/env python3
"""CLI wrapper for ukrainian_wiki corpus ingestion."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from wiki.ukrainian_wiki_corpus import main
else:
    from .ukrainian_wiki_corpus import main


if __name__ == "__main__":
    raise SystemExit(main())
