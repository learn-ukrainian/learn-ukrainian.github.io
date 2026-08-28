#!/usr/bin/env python3
"""Accept a restored CI venv or force the lock-minus-live-ML install path.

GitHub Actions ``cache-hit: true`` is not proof the tree is usable: a runner
image Python bump can leave ``.venv/bin/python`` as a dangling symlink. This
helper is fail-open toward a fresh install (never fail-closed on a bad cache)
and fail-closed for the later pytest/coverage steps that consume the venv.

Required imports match the lock-minus-live-ML profile used by fastlane and
the four shards: ``pytest`` is the runner; ``coverage`` is already in
``requirements-lock.txt`` and lets coverage-floor reuse the same tree.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REQUIRED_IMPORTS: tuple[str, ...] = ("pytest", "coverage")


def _truthy(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def accept_ci_venv(venv: Path, *, restore_hit: bool) -> bool:
    """Return True only when restore claimed a hit and the venv can import."""
    if not restore_hit:
        return False
    python = venv / "bin" / "python"
    if not (python.is_file() or python.is_symlink()):
        return False
    probe = "import " + ", ".join(REQUIRED_IMPORTS)
    try:
        subprocess.run(
            [str(python), "-c", probe],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    return True


def _write_github_output(cache_hit: bool) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT", "").strip()
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as handle:
        handle.write(f"cache-hit={'true' if cache_hit else 'false'}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--venv",
        default=os.environ.get("CI_VENV", ".venv"),
        help="virtualenv directory (default: $CI_VENV or .venv)",
    )
    parser.add_argument(
        "--restore-hit",
        default=os.environ.get("RESTORE_HIT", "false"),
        help="actions/cache restore cache-hit (default: $RESTORE_HIT or false)",
    )
    args = parser.parse_args(argv)
    accepted = accept_ci_venv(Path(args.venv), restore_hit=_truthy(str(args.restore_hit)))
    _write_github_output(accepted)
    print(f"cache-hit={'true' if accepted else 'false'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
