"""The CI shard split must be a PARTITION of the test suite.

Sharding is how the gate runs at all (#5776: the single-session design never
completed once). But a sharding bug is invisible in the worst way — every shard
goes green while some tests simply never ran. That is the exact failure class the
gate reboot exists to end (#3873 #4888 #4936 #5351 #5354, all "a required check
passed while pytest was skipped").

So the split expression is extracted from `.github/workflows/ci.yml` and executed
here. If someone edits the shard logic in YAML and breaks coverage of the suite,
this fails — the workflow is not a place where logic can hide from tests.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
SHARD_COUNT = 4


def _split_expression() -> str:
    """The one-liner the workflow feeds to `python -c`, read from the YAML itself."""
    text = WORKFLOW.read_text(encoding="utf-8")
    match = re.search(r'split_py="(?P<expr>[^"]+)"', text)
    assert match, "shard split expression not found in ci.yml — did the shard job change shape?"
    return match.group("expr")


def _shard_files(shard: int) -> list[str]:
    out = subprocess.run(
        [sys.executable, "-c", _split_expression(), str(shard)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=60,
        check=True,
    )
    return [line for line in out.stdout.splitlines() if line.strip()]


@pytest.fixture(scope="module")
def shards() -> list[list[str]]:
    return [_shard_files(i) for i in range(1, SHARD_COUNT + 1)]


def test_shards_cover_every_test_file(shards: list[list[str]]) -> None:
    """Union of all shards == every test file. A dropped file is a silent hole."""
    expected = sorted(str(p.relative_to(REPO_ROOT)) for p in (REPO_ROOT / "tests").rglob("test_*.py"))
    union = sorted(f for shard in shards for f in shard)
    missing = sorted(set(expected) - set(union))
    assert not missing, f"{len(missing)} test file(s) belong to NO shard and would never run: {missing[:10]}"
    assert union == expected


def test_shards_do_not_overlap(shards: list[list[str]]) -> None:
    """A file in two shards wastes a runner and double-counts coverage."""
    union = [f for shard in shards for f in shard]
    duplicates = sorted({f for f in union if union.count(f) > 1})
    assert not duplicates, f"file(s) in more than one shard: {duplicates[:10]}"


def test_no_shard_is_empty(shards: list[list[str]]) -> None:
    """An empty shard means the split silently collapsed — the job would pass trivially."""
    empty = [i + 1 for i, shard in enumerate(shards) if not shard]
    assert not empty, f"shard(s) {empty} are empty; the gate would pass without running them"


def test_shards_are_balanced_within_one_file(shards: list[list[str]]) -> None:
    """Round-robin over a sorted list; sizes must differ by at most one."""
    sizes = [len(shard) for shard in shards]
    assert max(sizes) - min(sizes) <= 1, f"unbalanced shard sizes {sizes}"


def test_split_is_deterministic() -> None:
    """Two invocations must agree, or reruns would test a different subset."""
    assert _shard_files(1) == _shard_files(1)


def test_split_does_not_consult_the_diff() -> None:
    """The invariant the whole reboot exists to protect.

    Five main-breaking regressions shipped because a required check chose tests
    from the changed-file set. The split may depend on the FILE LIST and nothing
    else — no git, no diff, no base ref.
    """
    expr = _split_expression()
    for forbidden in ("git", "diff", "GITHUB_BASE_REF", "changed", "HEAD", "origin/"):
        assert forbidden not in expr, (
            f"shard split references {forbidden!r}; it must depend only on the test file list"
        )
