"""Run Hermes oneshot mode with the user prompt supplied on stdin."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):  # run as a file: put the repository root on sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"} or len(args) != 1:
        sys.stderr.write("usage: scripts.ai_agent_bridge._hermes_stdin MODEL\n")
        return 0 if args and args[0] in {"-h", "--help"} else 2

    # Optional dependency: import only when a model was actually requested.
    from hermes_cli.oneshot import run_oneshot

    prompt = sys.stdin.read()
    return run_oneshot(prompt, model=args[0])


if __name__ == "__main__":
    raise SystemExit(main())
