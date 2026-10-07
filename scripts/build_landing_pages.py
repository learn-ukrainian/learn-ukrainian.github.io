#!/usr/bin/env python3
"""Compatibility entrypoint for non-arc landing generation and read-only --check.

Run with --help for usage, outputs and exit codes from the owning producer.
"""
import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _P

_f = _P(__file__).parent / "build" / "build_landing_pages.py"
if __name__ == "__main__":
    import runpy
    runpy.run_path(str(_f), run_name="__main__")
else:
    _s = _ilu.spec_from_file_location("build_landing_pages", _f)
    _m = _ilu.module_from_spec(_s)
    _sys.modules[__name__] = _m
    _s.loader.exec_module(_m)
