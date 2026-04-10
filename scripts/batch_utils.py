#!/usr/bin/env python3
"""Stub: module moved to scripts/batch/batch_utils.py"""
import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _P

_f = _P(__file__).parent / "batch" / "batch_utils.py"
if __name__ == "__main__":
    import runpy
    runpy.run_path(str(_f), run_name="__main__")
else:
    _s = _ilu.spec_from_file_location("batch_utils", _f)
    _m = _ilu.module_from_spec(_s)
    _sys.modules[__name__] = _m
    _s.loader.exec_module(_m)
