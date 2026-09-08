"""Tests for the GitHub Actions file-plane pytest shard partition (#7816).

Covers acceptance criteria 1-3 of the ci-shard-balance-2026-09-07 brief:
- `scripts/ci/pytest_shards.py` `plan-files` (LPT file partitioning) and
  `file-durations` (JUnit duration snapshot refresh).
- `tests/conftest.py`'s `pytest_ignore_collect` allowlist hook.
- `.github/workflows/ci.yml`'s pytest job shape (declared shard count, no
  modulo split, `-n logical`, per-shard JUnit upload, docs_skills lane
  untouched).
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ci.pytest_shards import (
    _file_from_junit_id,
    aggregate_junit_file_durations,
    assert_set_integrity,
    assign_files,
    load_durations,
    write_file_durations,
    write_file_shard_plan,
)
from scripts.ci.pytest_shards import (
    main as pytest_shards_main,
)
from tests.conftest import (
    LU_PYTEST_SHARD_FILES_ENV_VAR,
    _load_shard_allowlist,
    pytest_ignore_collect,
)

pytestmark = pytest.mark.repo_invariant

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github" / "workflows" / "ci.yml"

_SAMPLE_PATHS = [
    "tests/test_a.py",
    "tests/test_b.py",
    "tests/audit/test_c.py",
    "tests/audit/test_d.py",
    "tests/wiki/test_e.py",
]


# =============================================================================
# plan-files: partitioning
# =============================================================================


def test_assign_files_partition_is_complete_and_disjoint() -> None:
    durations = {"tests/test_a.py": 10.0, "tests/test_b.py": 1.0}
    shards = assign_files(_SAMPLE_PATHS, 3, durations)
    assert len(shards) == 3
    assert_set_integrity(_SAMPLE_PATHS, shards)  # raises on overlap/omission/empty shard


def test_write_file_shard_plan_is_deterministic(tmp_path: Path) -> None:
    durations = {"tests/test_a.py": 10.0, "tests/audit/test_c.py": 3.0}
    outputs = []
    for _ in range(2):
        output = tmp_path / "allowlist.txt"
        weights = write_file_shard_plan(
            paths=_SAMPLE_PATHS, shard_id=1, shard_count=4, durations=durations, output=output
        )
        outputs.append((output.read_text(encoding="utf-8"), weights))
    assert outputs[0] == outputs[1]


def test_write_file_shard_plan_median_fallback_empty_history(tmp_path: Path) -> None:
    """Zero duration history: every file falls back to weight 1.0 (no observed weights)."""
    output = tmp_path / "allowlist.txt"
    weights = write_file_shard_plan(paths=_SAMPLE_PATHS, shard_id=1, shard_count=5, durations={}, output=output)
    # 5 files across 5 shards, each weight 1.0 -> every shard gets exactly one file.
    assert {entry["predicted_seconds"] for entry in weights} == {1.0}
    assert {entry["file_count"] for entry in weights} == {1}


def test_write_file_shard_plan_median_fallback_for_unknown_file(tmp_path: Path) -> None:
    """A file missing from history uses the median of the *known* weights, not 1.0."""
    durations = {"tests/test_a.py": 10.0, "tests/test_b.py": 20.0}  # median of knowns = 15.0
    output = tmp_path / "allowlist.txt"
    weights = write_file_shard_plan(
        paths=["tests/test_a.py", "tests/test_b.py", "tests/audit/test_c.py"],
        shard_id=1,
        shard_count=3,
        durations=durations,
        output=output,
    )
    predicted = {entry["shard_id"]: entry["predicted_seconds"] for entry in weights}
    assert sorted(predicted.values()) == [10.0, 15.0, 20.0]


def test_write_file_shard_plan_reports_every_shard_weight(tmp_path: Path) -> None:
    output = tmp_path / "allowlist.txt"
    weights = write_file_shard_plan(
        paths=_SAMPLE_PATHS, shard_id=2, shard_count=4, durations={}, output=output
    )
    assert [entry["shard_id"] for entry in weights] == [1, 2, 3, 4]
    assert sum(entry["file_count"] for entry in weights) == len(_SAMPLE_PATHS)


def test_write_file_shard_plan_rejects_duplicate_candidate_paths(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="duplicate"):
        write_file_shard_plan(
            paths=["tests/test_a.py", "tests/test_a.py"],
            shard_id=1,
            shard_count=2,
            durations={},
            output=tmp_path / "allowlist.txt",
        )


def test_write_file_shard_plan_rejects_out_of_range_shard_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="shard_id"):
        write_file_shard_plan(
            paths=_SAMPLE_PATHS, shard_id=5, shard_count=4, durations={}, output=tmp_path / "allowlist.txt"
        )


def test_plan_files_cli_writes_sorted_allowlist_and_prints_all_weights(tmp_path, monkeypatch, capsys) -> None:
    durations_path = tmp_path / "durations.json"
    durations_path.write_text(json.dumps({"tests/test_a.py": 5.0}), encoding="utf-8")
    output = tmp_path / "shard.txt"
    monkeypatch.setattr(sys, "stdin", io.StringIO("\n".join(reversed(_SAMPLE_PATHS)) + "\n"))

    exit_code = pytest_shards_main(
        ["plan-files", "--shard-id", "1", "--shard-count", "4", "--durations", str(durations_path), "--output", str(output)]
    )

    assert exit_code == 0
    assert output.read_text(encoding="utf-8").splitlines() == sorted(output.read_text(encoding="utf-8").splitlines())
    printed = capsys.readouterr().out
    assert len(re.findall(r"^shard \d/4:", printed, re.MULTILINE)) == 4


def test_plan_files_cli_rejects_corrupt_snapshot_json(tmp_path, monkeypatch, capsys) -> None:
    durations_path = tmp_path / "durations.json"
    durations_path.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", io.StringIO("\n".join(_SAMPLE_PATHS) + "\n"))

    exit_code = pytest_shards_main(
        [
            "plan-files",
            "--shard-id",
            "1",
            "--shard-count",
            "4",
            "--durations",
            str(durations_path),
            "--output",
            str(tmp_path / "shard.txt"),
        ]
    )

    assert exit_code == 1
    assert "pytest shard error" in capsys.readouterr().err


def test_plan_files_cli_rejects_wrong_shaped_snapshot(tmp_path, monkeypatch) -> None:
    durations_path = tmp_path / "durations.json"
    durations_path.write_text(json.dumps(["not", "a", "dict"]), encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", io.StringIO("\n".join(_SAMPLE_PATHS) + "\n"))

    exit_code = pytest_shards_main(
        [
            "plan-files",
            "--shard-id",
            "1",
            "--shard-count",
            "4",
            "--durations",
            str(durations_path),
            "--output",
            str(tmp_path / "shard.txt"),
        ]
    )

    assert exit_code == 1


def test_plan_files_missing_durations_file_uses_median_fallback(tmp_path, monkeypatch) -> None:
    """A committed-but-absent snapshot path behaves like a cache miss, not corruption."""
    assert load_durations(tmp_path / "does-not-exist.json") == {}


# =============================================================================
# file-durations: JUnit aggregation
# =============================================================================


def test_file_from_junit_id_strips_trailing_class_chain() -> None:
    assert _file_from_junit_id("tests.audit.test_config_invariants") == "tests/audit/test_config_invariants.py"
    assert (
        _file_from_junit_id("tests.foo.test_bar.TestSelectPrimaryMatch") == "tests/foo/test_bar.py"
    )
    assert _file_from_junit_id("tests.test_scrape_diasporiana") == "tests/test_scrape_diasporiana.py"


def test_file_from_junit_id_unmappable_returns_none() -> None:
    assert _file_from_junit_id("some.module.without.a.test.segment") is None


_JUNIT_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
<testsuite name="pytest">
{cases}
</testsuite>
</testsuites>
"""


def _write_junit(path: Path, cases: list[str]) -> Path:
    path.write_text(_JUNIT_TEMPLATE.format(cases="\n".join(cases)), encoding="utf-8")
    return path


def test_aggregate_junit_file_durations_sums_per_file(tmp_path: Path) -> None:
    junit = _write_junit(
        tmp_path / "one.xml",
        [
            '<testcase classname="tests.test_a" name="test_x" time="1.5" />',
            '<testcase classname="tests.test_a" name="test_y" time="2.5" />',
            '<testcase classname="tests.test_b" name="test_z" time="0.25" />',
        ],
    )
    durations, unmapped = aggregate_junit_file_durations([junit])
    assert durations == {"tests/test_a.py": 4.0, "tests/test_b.py": 0.25}
    assert unmapped == 0


def test_aggregate_junit_file_durations_dedupes_reruns_by_max(tmp_path: Path) -> None:
    first = _write_junit(tmp_path / "shard-1.xml", ['<testcase classname="tests.test_a" name="test_x" time="1.0" />'])
    second = _write_junit(tmp_path / "shard-1-retry.xml", ['<testcase classname="tests.test_a" name="test_x" time="9.0" />'])
    durations, unmapped = aggregate_junit_file_durations([first, second])
    assert durations == {"tests/test_a.py": 9.0}
    assert unmapped == 0


def test_aggregate_junit_file_durations_skips_unmappable_testcases(tmp_path: Path) -> None:
    junit = _write_junit(
        tmp_path / "one.xml",
        [
            '<testcase classname="" name="not.a.mappable.id" time="0.0" />',
            '<testcase classname="tests.test_a" name="test_x" time="1.0" />',
        ],
    )
    durations, unmapped = aggregate_junit_file_durations([junit])
    assert durations == {"tests/test_a.py": 1.0}
    assert unmapped == 1


def test_write_file_durations_sorted_and_rounded(tmp_path: Path) -> None:
    junit = _write_junit(
        tmp_path / "one.xml",
        [
            '<testcase classname="tests.test_b" name="test_x" time="1.23456" />',
            '<testcase classname="tests.test_a" name="test_x" time="2.0" />',
        ],
    )
    output = tmp_path / "out.json"
    summary = write_file_durations(junit_paths=[junit], output=output)
    assert summary["files"] == 2
    raw = output.read_text(encoding="utf-8")
    payload = json.loads(raw)
    assert payload == {"tests/test_a.py": 2.0, "tests/test_b.py": 1.235}
    assert list(json.loads(raw).keys()) == sorted(payload)  # sorted keys on disk


def test_write_file_durations_raises_when_nothing_mappable(tmp_path: Path) -> None:
    junit = _write_junit(tmp_path / "one.xml", ['<testcase classname="" name="unmappable.id" time="1.0" />'])
    with pytest.raises(RuntimeError, match="zero mappable"):
        write_file_durations(junit_paths=[junit], output=tmp_path / "out.json")


# =============================================================================
# tests/conftest.py: pytest_ignore_collect allowlist hook
# =============================================================================


@pytest.fixture(autouse=True)
def _clear_allowlist_cache():
    _load_shard_allowlist.cache_clear()
    yield
    _load_shard_allowlist.cache_clear()


def test_pytest_ignore_collect_inert_without_env_var(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv(LU_PYTEST_SHARD_FILES_ENV_VAR, raising=False)
    a_file = tmp_path / "test_x.py"
    a_file.write_text("", encoding="utf-8")
    assert pytest_ignore_collect(a_file, config=None) is None
    assert pytest_ignore_collect(tmp_path, config=None) is None


def test_pytest_ignore_collect_directories_never_filtered(tmp_path, monkeypatch) -> None:
    allowlist_path = tmp_path / "allowlist.txt"
    allowlist_path.write_text("tests/test_only_allowed.py\n", encoding="utf-8")
    monkeypatch.setenv(LU_PYTEST_SHARD_FILES_ENV_VAR, str(allowlist_path))
    a_dir = tmp_path / "some_dir"
    a_dir.mkdir()
    assert pytest_ignore_collect(a_dir, config=None) is False


def test_pytest_ignore_collect_honours_allowlist(tmp_path, monkeypatch) -> None:
    repo_root = tmp_path
    allowed = repo_root / "tests" / "test_allowed.py"
    disallowed = repo_root / "tests" / "test_disallowed.py"
    allowed.parent.mkdir(parents=True, exist_ok=True)
    allowed.write_text("", encoding="utf-8")
    disallowed.write_text("", encoding="utf-8")
    allowlist_path = tmp_path / "allowlist.txt"
    allowlist_path.write_text("tests/test_allowed.py\n", encoding="utf-8")
    monkeypatch.setenv(LU_PYTEST_SHARD_FILES_ENV_VAR, str(allowlist_path))
    monkeypatch.setattr("tests.conftest._REPO_ROOT", repo_root.resolve())

    assert pytest_ignore_collect(allowed, config=None) is False
    assert pytest_ignore_collect(disallowed, config=None) is True
    assert pytest_ignore_collect(allowed.parent, config=None) is False


def test_pytest_ignore_collect_ignores_non_test_files(tmp_path, monkeypatch) -> None:
    allowlist_path = tmp_path / "allowlist.txt"
    allowlist_path.write_text("tests/test_only_allowed.py\n", encoding="utf-8")
    monkeypatch.setenv(LU_PYTEST_SHARD_FILES_ENV_VAR, str(allowlist_path))
    conftest_file = tmp_path / "tests" / "conftest.py"
    conftest_file.parent.mkdir(parents=True, exist_ok=True)
    conftest_file.write_text("", encoding="utf-8")
    assert pytest_ignore_collect(conftest_file, config=None) is True


def test_planned_shard_collects_build_tests_through_directory(tmp_path) -> None:
    """The CI entry path must not let pytest's default `build` exclusion win."""
    tracked = subprocess.run(
        ["git", "ls-files", "--", "tests"], cwd=_REPO_ROOT,
        capture_output=True, text=True, check=True, timeout=30,
    ).stdout.splitlines()
    paths = [path for path in tracked if re.search(r"/test_[^/]+\.py$", path)]
    durations = load_durations(_REPO_ROOT / "scripts/ci/pytest-file-durations.json")
    target = "tests/build/test_linear_pipeline.py"
    owners = []
    for shard_id in range(1, 5):
        allowlist = tmp_path / f"shard-{shard_id}.txt"
        write_file_shard_plan(
            paths=paths, shard_id=shard_id, shard_count=4,
            durations=durations, output=allowlist,
        )
        if target in allowlist.read_text().splitlines():
            owners.append(allowlist)
    assert len(owners) == 1
    env = {**os.environ, LU_PYTEST_SHARD_FILES_ENV_VAR: str(owners[0])}
    collected = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "--collect-only", "-q",
         "-o", "addopts=", "-m", "not atlas_release and not slow"],
        cwd=_REPO_ROOT, env=env, capture_output=True, text=True, timeout=90,
    )
    assert collected.returncode == 0, collected.stdout + collected.stderr
    assert any(line.startswith(target + "::") for line in collected.stdout.splitlines()), collected.stdout


def test_load_shard_allowlist_missing_file_raises_loudly(monkeypatch) -> None:
    monkeypatch.setenv(LU_PYTEST_SHARD_FILES_ENV_VAR, "/nonexistent/allowlist.txt")
    with pytest.raises(RuntimeError, match="unreadable"):
        _load_shard_allowlist()


def test_load_shard_allowlist_unreadable_raises_loudly(tmp_path, monkeypatch) -> None:
    a_dir = tmp_path / "a-directory"
    a_dir.mkdir()
    monkeypatch.setenv(LU_PYTEST_SHARD_FILES_ENV_VAR, str(a_dir))
    with pytest.raises(RuntimeError, match="unreadable"):
        _load_shard_allowlist()


def test_load_shard_allowlist_empty_raises_loudly(tmp_path, monkeypatch) -> None:
    allowlist_path = tmp_path / "allowlist.txt"
    allowlist_path.write_text("\n\n   \n", encoding="utf-8")
    monkeypatch.setenv(LU_PYTEST_SHARD_FILES_ENV_VAR, str(allowlist_path))
    with pytest.raises(RuntimeError, match="empty"):
        _load_shard_allowlist()


def test_load_shard_allowlist_duplicate_entry_raises_loudly(tmp_path, monkeypatch) -> None:
    allowlist_path = tmp_path / "allowlist.txt"
    allowlist_path.write_text("tests/test_a.py\ntests/test_a.py\n", encoding="utf-8")
    monkeypatch.setenv(LU_PYTEST_SHARD_FILES_ENV_VAR, str(allowlist_path))
    with pytest.raises(RuntimeError, match="duplicate"):
        _load_shard_allowlist()


def test_load_shard_allowlist_malformed_entry_raises_loudly(tmp_path, monkeypatch) -> None:
    allowlist_path = tmp_path / "allowlist.txt"
    allowlist_path.write_text("tests/not_a_test_module.py\n", encoding="utf-8")
    monkeypatch.setenv(LU_PYTEST_SHARD_FILES_ENV_VAR, str(allowlist_path))
    with pytest.raises(RuntimeError, match="malformed"):
        _load_shard_allowlist()


# =============================================================================
# .github/workflows/ci.yml: pytest job shape
# =============================================================================


def _ci_text() -> str:
    return _CI.read_text(encoding="utf-8")


def test_ci_yml_declares_shard_count_once() -> None:
    ci_text = _ci_text()
    assert re.search(r"(?m)^\s*PYTEST_SHARD_COUNT:\s*'4'\s*$", ci_text), "shard count must be declared once at workflow env level"
    assert "int(os.environ[\"PYTEST_SHARD_COUNT\"])" in ci_text, "changes job must read the declared shard count, not hardcode it"
    assert "${{ env.PYTEST_SHARD_COUNT }}" in ci_text, "pytest job must read the same declared shard count"


def test_ci_yml_plan_files_called_with_declared_shard_count() -> None:
    ci_text = _ci_text()
    assert "pytest_shards.py plan-files" in ci_text
    assert '--shard-id "$SHARD" --shard-count "$SHARD_COUNT"' in ci_text
    assert "scripts/ci/pytest-file-durations.json" in ci_text


def test_ci_yml_no_modulo_split_remains() -> None:
    ci_text = _ci_text()
    assert "sed -n" not in ci_text, "the modulo file split (#7658) must not return"
    assert "~4p" not in ci_text


def test_ci_yml_uses_n_logical_on_all_four_vcpus() -> None:
    ci_text = _ci_text()
    assert "-n logical" in ci_text
    assert "-n auto" not in ci_text


def test_ci_yml_fails_on_worker_crash() -> None:
    ci_text = _ci_text()
    assert "--max-worker-restart=0" in ci_text


def test_ci_yml_docs_only_lane_untouched() -> None:
    ci_text = _ci_text()
    match = re.search(
        r'if \[ "\$DOCS_ONLY" = "true" \]; then\n(.*?)\n\s*exit 0\n\s*fi',
        ci_text,
        re.DOTALL,
    )
    assert match is not None
    docs_branch = match.group(1)
    assert "pytest tests -m docs_skills --strict-markers --timeout=120" in docs_branch
    assert "--durations" not in docs_branch
    assert "--junitxml" not in docs_branch
    assert "plan-files" not in docs_branch


def test_ci_yml_uploads_per_shard_junit_artifact() -> None:
    ci_text = _ci_text()
    assert "upload-artifact@" in ci_text
    assert "pytest-shard-*.xml" in ci_text
    assert "pytest-junit-shard-${{ matrix.shard }}" in ci_text


def test_ci_yml_junit_upload_fails_loudly_outside_docs_only() -> None:
    """A non-docs_only run that produces no JUnit report is a real gap, not a
    silent no-op: only the docs_only lane (which skips the junitxml path
    entirely) may swallow a missing report."""
    ci_text = _ci_text()
    assert (
        "if-no-files-found: ${{ needs.changes.outputs.docs_only == 'true' && 'ignore' || 'error' }}"
        in ci_text
    )
    assert "if-no-files-found: ignore\n" not in ci_text


def test_ci_yml_run_pytest_reports_slowest_tests() -> None:
    ci_text = _ci_text()
    assert "--durations=25" in ci_text


def test_ci_yml_samples_memory_around_pytest_step() -> None:
    """4-worker memory headroom is unverified (ci-shard-balance-2026-09-07);
    a sampled series is the only way to catch a peak between two snapshots."""
    ci_text = _ci_text()
    assert "Start memory sampler" in ci_text
    assert "Stop memory sampler" in ci_text
    assert "mem-shard-" in ci_text
    assert "mem-sample-shard-${{ matrix.shard }}" in ci_text
    assert "pytest_rss_mib=" in ci_text
    assert "sampling_interval_seconds=15" in ci_text
