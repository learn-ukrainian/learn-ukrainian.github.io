"""Compatibility entry point for generate_synthetic_manifest (#8307)."""

from __future__ import annotations

import sys

from scripts.benchmarks.generate_synthetic_manifest import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
