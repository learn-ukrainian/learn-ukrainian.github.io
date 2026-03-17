#!/usr/bin/env python3
"""Stub: module moved to scripts/tools/image_review_server.py"""
import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _P

_f = _P(__file__).parent / "tools" / "image_review_server.py"
if __name__ == "__main__":
    import runpy; runpy.run_path(str(_f), run_name="__main__")
else:
    _s = _ilu.spec_from_file_location("image_review_server", _f)
    _m = _ilu.module_from_spec(_s)
    _sys.modules[__name__] = _m
    _s.loader.exec_module(_m)
