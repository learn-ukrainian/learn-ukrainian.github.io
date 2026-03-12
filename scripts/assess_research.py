#!/usr/bin/env python3
"""Stub: module moved to scripts/research/assess_research.py"""
import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _P

_research_dir = str(_P(__file__).parent / "research")
if _research_dir not in _sys.path:
    _sys.path.insert(0, _research_dir)
_f = _P(__file__).parent / "research" / "assess_research.py"
if __name__ == "__main__":
    import runpy

    runpy.run_path(str(_f), run_name="__main__")
else:
    _s = _ilu.spec_from_file_location("assess_research", _f)
    _m = _ilu.module_from_spec(_s)
    _sys.modules[__name__] = _m
    _s.loader.exec_module(_m)
