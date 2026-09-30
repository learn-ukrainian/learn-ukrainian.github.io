"""CI pytest sharding, the whole-run report, and merge-queue reuse.

- ``scripts/ci/split_tests.py``: the static duration-balanced file split.
- ``tests/conftest.py``: the ``LU_PYTEST_SHARD_FILES`` allowlist hook each
  shard collects through.
- ``scripts/ci/pytest_report.py``: partition, executed-test and
  needs_artifact-skip checks over every shard.
- ``scripts/ci/reuse_green_run.py``: the merge-queue reuse decision.
- ``.github/workflows/ci.yml``: the pytest job flags these rely on.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.ci import pytest_report, reuse_green_run
from scripts.ci.split_tests import assign, junit_file_seconds
from scripts.ci.split_tests import main as split_main
from tests.conftest import LU_PYTEST_SHARD_FILES_ENV_VAR, _load_shard_allowlist, pytest_ignore_collect

pytestmark = pytest.mark.usefixtures("_clear_allowlist_cache")

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github" / "workflows" / "ci.yml"


# =============================================================================
# scripts/ci/split_tests.py
# =============================================================================

_FILES = [f"tests/test_{name}.py" for name in "abcdefghij"]


@pytest.mark.parametrize("shard_count", [1, 2, 3, 7, 10, 16])
def test_split_is_a_partition(shard_count: int) -> None:
    durations = {name: float(index + 1) for index, name in enumerate(_FILES[:6])}
    shards = assign(_FILES, durations, shard_count)
    flat = [name for shard in shards for name in shard]
    assert len(shards) == shard_count
    assert sorted(flat) == sorted(_FILES)
    assert len(flat) == len(set(flat))


def test_split_ignores_input_order_and_balances_by_duration() -> None:
    durations = {"tests/test_a.py": 10.0, "tests/test_b.py": 6.0, "tests/test_c.py": 5.0, "tests/test_d.py": 1.0}
    forward = assign(list(durations), durations, 2)
    backward = assign(list(reversed(durations)), durations, 2)
    assert forward == backward
    # LPT: a(10) | b(6); c(5) joins b (6 < 10); d(1) joins a (10 < 11).
    assert forward == [["tests/test_a.py", "tests/test_d.py"], ["tests/test_b.py", "tests/test_c.py"]]


def test_split_gives_unrecorded_files_the_median() -> None:
    durations = {"tests/test_a.py": 1.0, "tests/test_b.py": 3.0, "tests/test_c.py": 100.0}
    shards = assign([*durations, "tests/test_new.py"], durations, 2)
    # median 3.0: the new file is placed like test_b, never dropped.
    assert shards == [["tests/test_c.py"], ["tests/test_a.py", "tests/test_b.py", "tests/test_new.py"]]


def test_split_rejects_duplicates_and_zero_shards() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        assign(["tests/test_a.py", "tests/test_a.py"], {}, 2)
    with pytest.raises(ValueError, match="at least 1"):
        assign(["tests/test_a.py"], {}, 0)


def test_split_cli_prints_one_shard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    durations = tmp_path / "durations.json"
    durations.write_text(json.dumps({"tests/test_a.py": 5.0, "tests/test_b.py": 1.0}), encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", __import__("io").StringIO("tests/test_a.py\ntests/test_b.py\n"))
    assert split_main(["split", "--shard", "2", "--of", "2", "--durations", str(durations)]) == 0
    assert capsys.readouterr().out == "tests/test_b.py\n"
    with pytest.raises(SystemExit):
        split_main(["split", "--shard", "3", "--of", "2", "--durations", str(durations)])


def test_durations_sum_testcase_time_per_file(tmp_path: Path) -> None:
    junit = tmp_path / "junit.xml"
    junit.write_text(
        """<testsuites><testsuite>
<testcase classname="tests.audit.test_x" name="test_one" time="1.5"/>
<testcase classname="tests.audit.test_x.TestGroup" name="test_two" time="2.0"/>
<testcase classname="tests.test_y" name="test_three[a.b]" time="0.25"/>
<testcase classname="" name="tests.broken" time="9"/>
</testsuite></testsuites>""",
        encoding="utf-8",
    )
    assert junit_file_seconds([junit]) == {"tests/audit/test_x.py": 3.5, "tests/test_y.py": 0.25}


def test_committed_durations_are_seconds_per_test_file() -> None:
    """Stale or missing entries only cost balance (see split_tests), never coverage."""
    durations = json.loads((_REPO_ROOT / "scripts/ci/pytest-file-durations.json").read_text(encoding="utf-8"))
    assert durations
    for name, seconds in durations.items():
        assert re.fullmatch(r"tests/(?:.+/)?test_[^/]+\.py", name), name
        assert isinstance(seconds, (int, float)) and seconds >= 0, name


@pytest.mark.slow
def test_planned_shard_collects_build_tests_through_directory(tmp_path: Path) -> None:
    """The CI entry path must not let pytest's default `build` exclusion win."""
    tracked = subprocess.run(
        ["git", "ls-files", "--", "tests"], cwd=_REPO_ROOT, capture_output=True, text=True, check=True, timeout=30
    ).stdout.splitlines()
    paths = [path for path in tracked if re.search(r"/test_[^/]+\.py$", path)]
    durations = json.loads((_REPO_ROOT / "scripts/ci/pytest-file-durations.json").read_text(encoding="utf-8"))
    target = "tests/build/test_linear_pipeline.py"
    owners = [shard for shard in assign(paths, durations, 16) if target in shard]
    assert len(owners) == 1
    allowlist = tmp_path / "shard.txt"
    allowlist.write_text("\n".join(owners[0]) + "\n", encoding="utf-8")
    env = {**os.environ, LU_PYTEST_SHARD_FILES_ENV_VAR: str(allowlist)}
    collected = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "--collect-only",
            "-q",
            "-o",
            "addopts=",
            "-m",
            "not atlas_release and not slow",
        ],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert collected.returncode == 0, collected.stdout + collected.stderr
    assert any(line.startswith(target + "::") for line in collected.stdout.splitlines()), collected.stdout


# =============================================================================
# tests/conftest.py: pytest_ignore_collect allowlist hook
# =============================================================================


@pytest.fixture
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


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (None, "unreadable"),
        ("\n\n   \n", "empty"),
        ("tests/test_a.py\ntests/test_a.py\n", "duplicate"),
        ("tests/not_a_test_module.py\n", "malformed"),
    ],
)
def test_load_shard_allowlist_fails_loudly(tmp_path, monkeypatch, content: str | None, message: str) -> None:
    allowlist_path = tmp_path / "allowlist.txt"
    if content is None:
        allowlist_path.mkdir()  # a directory is unreadable as a file
    else:
        allowlist_path.write_text(content, encoding="utf-8")
    monkeypatch.setenv(LU_PYTEST_SHARD_FILES_ENV_VAR, str(allowlist_path))
    with pytest.raises(RuntimeError, match=message):
        _load_shard_allowlist()


def test_load_shard_allowlist_missing_file_raises_loudly(monkeypatch) -> None:
    monkeypatch.setenv(LU_PYTEST_SHARD_FILES_ENV_VAR, "/nonexistent/allowlist.txt")
    with pytest.raises(RuntimeError, match="unreadable"):
        _load_shard_allowlist()


# =============================================================================
# scripts/ci/pytest_report.py
# =============================================================================


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True, timeout=30
    ).stdout.strip()


def _report_repo(tmp_path: Path, expected_skips: str) -> Path:
    repo = tmp_path / "repo"
    (repo / "tests" / "sub").mkdir(parents=True)
    (repo / "tests" / "test_a.py").write_text("", encoding="utf-8")
    (repo / "tests" / "sub" / "test_b.py").write_text("", encoding="utf-8")
    (repo / "tests" / "helper.py").write_text("", encoding="utf-8")
    expected = repo / pytest_report.EXPECTED_ARTIFACT_SKIPS
    expected.parent.mkdir(parents=True)
    expected.write_text("# one id per line\n" + expected_skips, encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "init")
    return repo


def _shard(results: Path, number: int, files: list[str], cases: str) -> None:
    directory = results / f"pytest-junit-shard-{number}"
    directory.mkdir(parents=True)
    (directory / f"pytest-shard-{number}-files.txt").write_text(
        "".join(f"{name}\n" for name in files), encoding="utf-8"
    )
    (directory / f"pytest-shard-{number}.xml").write_text(
        f"<testsuites><testsuite>{cases}</testsuite></testsuites>", encoding="utf-8"
    )


_PASS_A = '<testcase classname="tests.test_a" name="test_ok" time="1"/>'
_SKIP_B = (
    '<testcase classname="tests.sub.test_b" name="test_artifact" time="0">'
    '<skipped message="needs_artifact: data/x.json missing"/></testcase>'
)


def test_report_passes_a_complete_run_and_records_the_tree(tmp_path: Path) -> None:
    repo = _report_repo(tmp_path, "tests.sub.test_b::test_artifact\n")
    results = tmp_path / "results"
    _shard(results, 1, ["tests/test_a.py"], _PASS_A)
    _shard(results, 2, ["tests/sub/test_b.py"], _SKIP_B)
    record = tmp_path / "out" / "tested-tree.json"

    assert pytest_report.main(["--results", str(results), "--root", str(repo), "--record", str(record)]) == 0

    assert json.loads(record.read_text(encoding="utf-8")) == {
        "tier": "full",
        "tree": _git(repo, "rev-parse", "HEAD^{tree}"),
        "sha": _git(repo, "rev-parse", "HEAD"),
        "tests": 2,
    }


@pytest.mark.parametrize(
    ("shards", "expected_skips", "problem"),
    [
        ([(1, ["tests/test_a.py"], _PASS_A)], "", "ran on no shard"),
        (
            [(1, ["tests/test_a.py", "tests/sub/test_b.py"], _PASS_A), (2, ["tests/sub/test_b.py"], _SKIP_B)],
            "",
            "more than one shard",
        ),
        (
            [(1, ["tests/test_a.py", "tests/sub/test_b.py", "tests/test_gone.py"], _PASS_A)],
            "",
            "not tracked test files",
        ),
        ([(1, ["tests/test_a.py", "tests/sub/test_b.py"], _PASS_A + _SKIP_B)], "", "unexpected needs_artifact skips"),
        (
            [(1, ["tests/test_a.py", "tests/sub/test_b.py"], _PASS_A)],
            "tests.sub.test_b::test_artifact\n",
            "did not skip",
        ),
    ],
)
def test_report_fails_closed(tmp_path: Path, capsys, shards, expected_skips: str, problem: str) -> None:
    repo = _report_repo(tmp_path, expected_skips)
    results = tmp_path / "results"
    for number, files, cases in shards:
        _shard(results, number, files, cases)
    record = tmp_path / "tested-tree.json"

    assert pytest_report.main(["--results", str(results), "--root", str(repo), "--record", str(record)]) == 1

    assert problem in capsys.readouterr().err
    assert not record.exists()


def test_report_fails_when_a_shard_uploaded_no_junit(tmp_path: Path, capsys) -> None:
    repo = _report_repo(tmp_path, "")
    results = tmp_path / "results"
    _shard(results, 1, ["tests/test_a.py", "tests/sub/test_b.py"], _PASS_A)
    (results / "pytest-junit-shard-1" / "pytest-shard-1.xml").unlink()

    assert (
        pytest_report.main(["--results", str(results), "--root", str(repo), "--record", str(tmp_path / "r.json")]) == 1
    )
    assert "no JUnit report" in capsys.readouterr().err


# =============================================================================
# scripts/ci/reuse_green_run.py
# =============================================================================

_TREE = "1" * 40


def _record(tree: str = _TREE, tier: str = "full"):
    return lambda: {"tier": tier, "tree": tree}


def test_reuse_when_a_green_full_run_tested_the_identical_tree() -> None:
    decision = reuse_green_run.decide(_TREE, [("11", _record())])
    assert decision.reuse and decision.run_id == "11"


def test_no_reuse_for_a_different_tree() -> None:
    decision = reuse_green_run.decide(_TREE, [("11", _record(tree="2" * 40))])
    assert not decision.reuse and "differs" in decision.reason


def test_no_reuse_when_the_run_was_not_the_full_tier() -> None:
    decision = reuse_green_run.decide(_TREE, [("11", _record(tier="fast")), ("10", lambda: None)])
    assert not decision.reuse
    assert "is not 'full'" in decision.reason and "no ci-tested-tree record" in decision.reason


def test_reuse_takes_the_first_matching_candidate() -> None:
    decision = reuse_green_run.decide(_TREE, [("12", lambda: None), ("11", _record()), ("10", _record())])
    assert decision.run_id == "11"


def test_lookup_failure_runs_the_full_suite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(*_args, **_kwargs):
        raise subprocess.CalledProcessError(1, ["gh"], stderr="HTTP 502")

    monkeypatch.setattr(reuse_green_run, "lookup", broken)
    output = tmp_path / "output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    for name in ("REPO", "HEAD_SHA", "HEAD_REF"):
        monkeypatch.setenv(name, "x")

    assert reuse_green_run.main() == 0
    assert output.read_text(encoding="utf-8") == "reuse=false\nrun_id=\n"


def test_a_record_that_fails_to_load_runs_the_full_suite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def unreadable() -> dict:
        raise json.JSONDecodeError("bad", "", 0)

    monkeypatch.setattr(reuse_green_run, "lookup", lambda *_args: reuse_green_run.decide(_TREE, [("11", unreadable)]))
    output = tmp_path / "output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    for name in ("REPO", "HEAD_SHA", "HEAD_REF"):
        monkeypatch.setenv(name, "x")

    assert reuse_green_run.main() == 0
    assert output.read_text(encoding="utf-8").startswith("reuse=false\n")


@pytest.mark.parametrize(
    ("ref", "number"),
    [
        ("refs/heads/gh-readonly-queue/main/pr-9237-" + "e" * 40, 9237),
        ("gh-readonly-queue/main/pr-7-" + "0" * 40, 7),
    ],
)
def test_queued_pr_number(ref: str, number: int) -> None:
    assert reuse_green_run.queued_pr_number(ref) == number


def test_queued_pr_number_rejects_other_refs() -> None:
    with pytest.raises(ValueError):
        reuse_green_run.queued_pr_number("refs/heads/main")


# =============================================================================
# .github/workflows/ci.yml wiring
# =============================================================================


def _jobs() -> dict:
    return yaml.safe_load(_CI.read_text(encoding="utf-8"))["jobs"]


def _run_pytest_script() -> str:
    return next(step["run"] for step in _jobs()["pytest"]["steps"] if step.get("name") == "Run pytest")


def test_pytest_job_runs_the_full_non_slow_tier_through_the_split() -> None:
    script = _run_pytest_script()
    assert 'python3 -m scripts.ci.split_tests split --shard "$SHARD" --of "$SHARDS"' in script
    assert 'export LU_PYTEST_SHARD_FILES="ci-artifacts/pytest-shard-${SHARD}-files.txt"' in script
    assert "-m 'not atlas_release and not slow' --strict-markers" in script
    for flag in (
        "-n logical",
        "--dist=worksteal",
        "--max-worker-restart=0",
        "--timeout=120",
        "--timeout-method=thread",
        "--durations=25",
    ):
        assert flag in script
    assert "-n auto" not in script
    assert "scripts.ci.pg_skip_guard" in script


def test_pytest_matrix_is_contiguous_and_counted_by_the_job() -> None:
    pytest_job = _jobs()["pytest"]
    shards = pytest_job["strategy"]["matrix"]["shard"]
    assert shards == list(range(1, len(shards) + 1))
    env = next(step["env"] for step in pytest_job["steps"] if step.get("name") == "Run pytest")
    assert env == {"SHARD": "${{ matrix.shard }}", "SHARDS": "${{ strategy.job-total }}"}


def test_shard_artifacts_feed_the_report_and_the_flake_ledger() -> None:
    jobs = _jobs()
    upload = next(step for step in jobs["pytest"]["steps"] if step.get("name") == "Upload pytest JUnit report")
    # scripts/ci/flake_ledger.py downloads "pytest-junit-shard-*" from merge_group runs.
    assert upload["with"]["name"] == "pytest-junit-shard-${{ matrix.shard }}"
    assert "ci-artifacts/pytest-shard-*.xml" in upload["with"]["path"]
    assert "ci-artifacts/pytest-shard-*-files.txt" in upload["with"]["path"]
    report = jobs["pytest-report"]
    assert report["if"] == "${{ !cancelled() && needs.pytest.result == 'success' }}"
    steps = report["steps"]
    assert any(step.get("with", {}).get("pattern") == "pytest-junit-shard-*" for step in steps)
    assert any("scripts.ci.pytest_report" in str(step.get("run", "")) for step in steps)
    assert any(step.get("with", {}).get("name") == reuse_green_run.ARTIFACT for step in steps)


def test_pytest_is_skipped_only_on_a_recorded_reuse() -> None:
    jobs = _jobs()
    assert jobs["pytest"]["needs"] == ["reuse"]
    assert jobs["pytest"]["if"] == "${{ !cancelled() && needs.reuse.outputs.reuse != 'true' }}"
    assert jobs["reuse"]["if"] == "github.event_name == 'merge_group'"
    assert jobs["reuse"]["permissions"] == {"contents": "read", "actions": "read", "pull-requests": "read"}


def test_every_checkout_drops_credentials_and_every_action_is_sha_pinned() -> None:
    text = _CI.read_text(encoding="utf-8")
    assert "continue-on-error" not in text
    for job_id, job in _jobs().items():
        for step in job.get("steps", []):
            uses = step.get("uses")
            if not uses or uses.startswith("./"):
                continue
            revision = uses.split("@", 1)[1]
            assert re.fullmatch(r"[0-9a-f]{40}", revision), (job_id, uses)
            if uses.startswith("actions/checkout@"):
                assert step["with"]["persist-credentials"] is False, job_id
    assert yaml.safe_load(text)["permissions"] == {"contents": "read"}
