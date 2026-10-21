"""CLI entry point: python -m scripts.curriculum.validate <level> <slug>."""
import sys
from pathlib import Path

if __package__ in (None, ""):  # run as a file: put the repository root on sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    __package__ = "scripts.curriculum.validate"

from .validate import main

if __name__ == "__main__":
    sys.exit(main())
