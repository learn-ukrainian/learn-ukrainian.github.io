"""CLI entrypoint for python -m scripts.build.fresh (Part E2 subcommands)."""
import sys
from pathlib import Path

if __package__ in (None, ""):  # run as a file: put the repository root on sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.build.fresh.cli import main

if __name__ == "__main__":
    sys.exit(main())
