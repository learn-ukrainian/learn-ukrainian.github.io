"""Fail-closed eligibility decision for Pages auto-deploys (#5356).

Curriculum certification remains authoritative for learner-facing content.  This
module permits the Pages workflow to redeploy a main revision automatically only
when *every* path since the last successful deployment is known site code.  The
denylist takes precedence over the site allowlist and an unknown path is drift.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

# These paths can change published learner content even though two of them live
# under ``site/``.  Keep this list explicit: a new content surface must be added
# here before an automatic deployment can cross it.
CONTENT_PATH_PREFIXES = (
    "curriculum/",
    "site/src/content/",
    "site/src/data/",
)

# This is deliberately broad enough for regular Astro UI, style, asset, and
# dependency changes, but it does not grant permission to any path outside the
# site tree.  ``CONTENT_PATH_PREFIXES`` is always evaluated first.
SITE_CODE_PATH_PREFIXES = ("site/",)


@dataclass(frozen=True)
class AutoDeployDecision:
    """A machine-readable result safe to write to ``GITHUB_OUTPUT``."""

    deploy: bool
    reason: str


def _has_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def decide_auto_deploy(changed_paths: Iterable[str]) -> AutoDeployDecision:
    """Classify a NUL-safe git path sequence with a deny-by-default policy."""
    paths = tuple(changed_paths)
    if not paths:
        return AutoDeployDecision(deploy=False, reason="no_changed_paths")

    for path in paths:
        if _has_prefix(path, CONTENT_PATH_PREFIXES):
            return AutoDeployDecision(deploy=False, reason="content_drift")
        if not _has_prefix(path, SITE_CODE_PATH_PREFIXES):
            return AutoDeployDecision(deploy=False, reason="unknown_path")

    return AutoDeployDecision(deploy=True, reason="site_code_only")


def read_nul_delimited_paths(path: Path) -> tuple[str, ...]:
    """Read ``git diff --name-only -z`` output without misparsing odd filenames."""
    raw_paths = path.read_bytes().split(b"\0")
    return tuple(
        raw_path.decode("utf-8", errors="surrogateescape")
        for raw_path in raw_paths
        if raw_path
    )


def write_github_output(path: Path, decision: AutoDeployDecision) -> None:
    """Append fixed-format action outputs; never interpolate repository paths."""
    with path.open("a", encoding="utf-8") as output:
        output.write(f"deploy={'true' if decision.deploy else 'false'}\n")
        output.write(f"reason={decision.reason}\n")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--changed-paths",
        type=Path,
        required=True,
        help="NUL-delimited path list produced by git diff --name-only -z.",
    )
    parser.add_argument(
        "--github-output",
        type=Path,
        required=True,
        help="GitHub Actions output file to append.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    decision = decide_auto_deploy(read_nul_delimited_paths(args.changed_paths))
    write_github_output(args.github_output, decision)
    print(f"auto-deploy eligibility: {decision.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
