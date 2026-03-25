#!/usr/bin/env python3
"""Stub: module moved to scripts/rag/prepare_grinchenko.py"""
import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _P

_spec = _ilu.spec_from_file_location(
    "scripts.rag.prepare_grinchenko",
    _P(__file__).resolve().parent / "rag" / "prepare_grinchenko.py",
)
_mod = _ilu.module_from_spec(_spec)
_sys.modules[__name__] = _mod
_spec.loader.exec_module(_mod)
