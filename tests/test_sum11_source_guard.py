"""Keep Soviet-occupation СУМ-11 out of tracked verification inputs."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.repo_invariant, pytest.mark.repo_wide, pytest.mark.reads_content]

ROOT = Path(__file__).resolve().parents[1]
SCOPES = (
    ":(glob)curriculum/**",
    ":(glob)scripts/data/**",
    ":(glob)scripts/build/phases/**",
    ":(glob)scripts/build/universal_rules/**",
    ":(glob)scripts/review/prompts/**",
    ":(glob)agents_extensions/shared/skills/**",
    ":(exclude,glob)curriculum/**/_archive/**",
    ":(exclude)scripts/data/stress_overrides.yaml",  # Owned by the separate gloss-source branch.
)
CONTRAST_ONLY_LINES = {
    "scripts/build/phases/linear-review-dim.md": "СУМ-11 is contrast-only",
    "scripts/build/phases/linear-review-dim.generated.md": "СУМ-11 headwords, apply heightened scrutiny",
}


def _source_references(revision: str | None = None) -> list[str]:
    cmd = [
        "git", "grep", "-n", "-I", "-i", "-E",
        "-e", r"(СУМ|SUM)[-‐‑‒–— ]?11|search_definitions",
    ]
    if revision:
        cmd.append(revision)
    cmd.extend(("--", *SCOPES))
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False, timeout=30)
    assert result.returncode in (0, 1), result.stderr
    references = []
    for line in result.stdout.splitlines():
        parts = line.split(":", 3 if revision else 2)
        path = parts[1] if revision else parts[0]
        source_line = parts[-1]
        if CONTRAST_ONLY_LINES.get(path, "\0") in source_line:
            continue
        references.append(line)
    return references


def test_sum11_is_not_a_tracked_verification_source() -> None:
    revision = os.environ.get("SUM11_GUARD_REV") or None
    references = _source_references(revision)
    assert not references, "СУМ-11 is contrast-only; remove verification inputs:\n" + "\n".join(references)
