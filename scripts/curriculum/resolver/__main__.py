"""CLI: python -m scripts.curriculum.resolver {resolve,questions,apply,check} <level> <slug> <n>."""
import sys
from pathlib import Path

if __package__ in (None, ""):  # run as a file: put the repository root on sys.path
    _script_dir = Path(__file__).resolve().parent
    # File launch puts this directory ahead of the stdlib. tokenize.py here
    # would shadow the stdlib module that dataclasses imports.
    _kept: list[str] = []
    for _entry in sys.path:
        if not _entry:
            _kept.append(_entry)
            continue
        try:
            if Path(_entry).resolve() == _script_dir:
                continue
        except OSError:
            pass
        _kept.append(_entry)
    sys.path[:] = _kept
    sys.path.insert(0, str(_script_dir.parents[2]))
    __package__ = "scripts.curriculum.resolver"

from .stream import main

if __name__ == "__main__":
    sys.exit(main())
