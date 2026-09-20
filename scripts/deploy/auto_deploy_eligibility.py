"""Fail-closed eligibility decision for Pages auto-deploys (#5356, #8306).

Curriculum certification remains authoritative for learner-facing content.  This
module permits the Pages workflow to redeploy a main revision automatically only
when *every* path since the last successful deployment is known site code.  The
denylist takes precedence over the site allowlist and an unknown path is drift.
"""

from __future__ import annotations

import argparse
import os
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

# These paths can change published learner content even though some live under
# ``site/`` or ``data/``. Keep this list explicit: a new content surface must
# be added here before an automatic deployment can cross it.
CONTENT_PATH_PREFIXES = (
    "curriculum/",
    "data/",
    "site/src/content/",
    "site/src/data/",
    "site/src/lib/lexicon/curated-heteronyms.ts",
)

# Exact release-pointer files under ``site/src/data/``.  A pointer bump only
# retargets an already-published Release asset; it is not curriculum/content
# drift.  Everything else under ``site/src/data/`` stays denied (#6733).
SITE_CODE_PATH_EXCEPTIONS = frozenset(
    {
        "site/src/data/lexicon-practice-deck.pointer.json",
        "site/src/data/lexicon-manifest.pointer.json",
    }
)

# This is deliberately broad enough for regular Astro UI, style, asset, and
# dependency changes, but it does not grant permission to any path outside the
# site tree or shared frontend packages.  ``CONTENT_PATH_PREFIXES`` is always
# evaluated first unless the path is an exact ``SITE_CODE_PATH_EXCEPTIONS`` entry.
SITE_CODE_PATH_PREFIXES = (
    "site/",
    "packages/activity-kit/",
)


@dataclass(frozen=True)
class AutoDeployDecision:
    """A machine-readable result safe to write to ``GITHUB_OUTPUT``."""

    deploy: bool
    reason: str
    offending_paths: tuple[str, ...] = ()


def _has_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def decide_auto_deploy(changed_paths: Iterable[str]) -> AutoDeployDecision:
    """Classify a NUL-safe git path sequence with a deny-by-default policy."""
    paths = tuple(changed_paths)
    if not paths:
        return AutoDeployDecision(deploy=False, reason="no_changed_paths", offending_paths=())

    content_drift_paths: list[str] = []
    unknown_paths: list[str] = []

    for path in paths:
        if path in SITE_CODE_PATH_EXCEPTIONS:
            # Still require the site-code prefix so a typo'd exception cannot
            # open non-site paths.
            if not _has_prefix(path, SITE_CODE_PATH_PREFIXES):
                unknown_paths.append(path)
            continue
        if _has_prefix(path, CONTENT_PATH_PREFIXES):
            content_drift_paths.append(path)
            continue
        if not _has_prefix(path, SITE_CODE_PATH_PREFIXES):
            unknown_paths.append(path)
            continue

    if content_drift_paths:
        return AutoDeployDecision(
            deploy=False,
            reason="content_drift",
            offending_paths=tuple(content_drift_paths),
        )

    if unknown_paths:
        return AutoDeployDecision(
            deploy=False,
            reason="unknown_path",
            offending_paths=tuple(unknown_paths),
        )

    return AutoDeployDecision(deploy=True, reason="site_code_only", offending_paths=())


def read_nul_delimited_paths(path: Path) -> tuple[str, ...]:
    """Read ``git diff --name-only -z`` output without misparsing odd filenames."""
    raw_paths = path.read_bytes().split(b"\0")
    return tuple(raw_path.decode("utf-8", errors="surrogateescape") for raw_path in raw_paths if raw_path)


def write_github_output(path: Path, decision: AutoDeployDecision) -> None:
    """Append fixed-format action outputs; never interpolate repository paths."""
    with path.open("a", encoding="utf-8") as output:
        output.write(f"deploy={'true' if decision.deploy else 'false'}\n")
        output.write(f"reason={decision.reason}\n")


def format_step_summary(decision: AutoDeployDecision) -> str:
    """Format a Markdown job summary for GITHUB_STEP_SUMMARY."""
    lines: list[str] = []
    if decision.deploy:
        lines.append("### 🚀 Pages Auto-Deploy: Eligible")
        lines.append("All changed paths since the last successful deployment are verified site code.")
    else:
        lines.append("### ⚠️ Pages Auto-Deploy: Skipped")
        lines.append(f"- **Decision**: `{decision.reason}`")
        if decision.offending_paths:
            count = len(decision.offending_paths)
            lines.append(f"- **Offending Paths ({count})**:")
            preview_limit = 20
            for p in decision.offending_paths[:preview_limit]:
                lines.append(f"  - `{p}`")
            if count > preview_limit:
                lines.append(f"  - *... and {count - preview_limit} more*")
        elif decision.reason == "no_changed_paths":
            lines.append("- **Detail**: No changed files detected in commit diff.")
    lines.append("")
    return "\n".join(lines)


def write_step_summary(path: Path, decision: AutoDeployDecision) -> None:
    """Append markdown summary to GitHub Actions step summary file."""
    content = format_step_summary(decision)
    with path.open("a", encoding="utf-8") as summary_file:
        summary_file.write(content)


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
    parser.add_argument(
        "--github-step-summary",
        type=Path,
        default=None,
        help="Optional GitHub Actions step summary file to append.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    decision = decide_auto_deploy(read_nul_delimited_paths(args.changed_paths))
    write_github_output(args.github_output, decision)

    summary_path = args.github_step_summary or (
        Path(os.environ["GITHUB_STEP_SUMMARY"]) if "GITHUB_STEP_SUMMARY" in os.environ else None
    )
    if summary_path is not None:
        write_step_summary(summary_path, decision)

    print(f"auto-deploy eligibility: {decision.reason}")
    if not decision.deploy:
        offending_count = len(decision.offending_paths)
        offending_preview = (
            f" ({offending_count} offending path{'s' if offending_count != 1 else ''})" if offending_count else ""
        )
        print(
            "::warning title=Pages Auto-Deploy Skipped::"
            f"Pages auto-deploy was skipped: {decision.reason}{offending_preview}. "
            "See job summary for details."
        )
        if decision.offending_paths:
            for p in decision.offending_paths[:10]:
                print(f"  offending: {p}")
            if len(decision.offending_paths) > 10:
                print(f"  ... and {len(decision.offending_paths) - 10} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
