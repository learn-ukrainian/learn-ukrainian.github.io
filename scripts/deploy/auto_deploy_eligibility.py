"""Pages auto-deploy eligibility CLI for the deploy-pages workflow (#5356, #8306).

The decision and its fail-closed rule live in the machinery reader
``scripts/ci/deploy_paths.py``; which paths are content and which are site code
is product data in ``scripts/curriculum/deploy_paths.v1.json``. This command
reads the NUL-delimited changed-path list, asks the reader, and writes the
fixed-format workflow outputs and job summary.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import scripts  # noqa: F401  (binds the product roots for the installed release)

# isort: split

from lu_machinery.ci.deploy_paths import AutoDeployDecision, decide_auto_deploy


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
