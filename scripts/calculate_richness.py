#!/usr/bin/env python3
"""Compatibility entrypoint for scripts/scoring/calculate_richness.py."""
import importlib as _il
import runpy
import sys as _sys
from pathlib import Path as _P

_project_root = _P(__file__).resolve().parent.parent
if str(_project_root) not in _sys.path:
    _sys.path.insert(0, str(_project_root))

if __name__ == "__main__":
    runpy.run_module("scripts.scoring.calculate_richness", run_name="__main__")
else:
    _m = _il.import_module("scripts.scoring.calculate_richness")
    _sys.modules[__name__] = _m
