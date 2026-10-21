#!/usr/bin/env python3
"""Entry point for the decision journal check.

Implementation lives in scripts/audit/check_decisions.py, including overdue
review_by rows from scripts/config/stack_pins.yaml.
"""

import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _P

_target = _P(__file__).resolve().parent / "audit" / "check_decisions.py"

if __name__ == "__main__":
    import runpy

    runpy.run_path(str(_target), run_name="__main__")
else:
    _spec = _ilu.spec_from_file_location("check_decisions", _target)
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules[__name__] = _mod
    _spec.loader.exec_module(_mod)
