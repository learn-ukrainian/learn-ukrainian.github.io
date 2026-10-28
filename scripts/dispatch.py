"""Command-line entry point for the minimal dispatcher."""

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.dispatcher.primary import exec_primary


def main() -> int:
    # Imported here so a linked worktree's stale dispatcher modules never load before the re-exec.
    from scripts.dispatcher.cli import main as cli_main

    return cli_main()


if __name__ == "__main__":
    exec_primary(sys.argv[1:])
    raise SystemExit(main())
