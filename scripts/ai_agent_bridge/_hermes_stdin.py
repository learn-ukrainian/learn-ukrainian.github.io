"""Run Hermes oneshot mode with the user prompt supplied on stdin."""

from __future__ import annotations

import sys

from hermes_cli.oneshot import run_oneshot


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        sys.stderr.write("usage: scripts.ai_agent_bridge._hermes_stdin MODEL\n")
        return 2

    prompt = sys.stdin.read()
    return run_oneshot(prompt, model=args[0])


if __name__ == "__main__":
    raise SystemExit(main())
