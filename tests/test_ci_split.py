"""CI pytest sharding, the whole-run report, and merge-queue reuse.

- ``scripts/ci/split_tests.py``: the static duration-balanced file split and
  the history files it pins to shard 1.
- ``tests/conftest.py``: the ``LU_PYTEST_SHARD_FILES`` allowlist hook each
  shard collects through.
- ``scripts/ci/pytest_report.py``: partition, executed-test and
  needs_artifact collected/skip checks over every shard.
- ``tests/conftest.py``: the collected ``needs_artifact`` list pytest report audits.
- ``scripts/ci/reuse_green_run.py``: the merge-queue reuse decision.
- ``scripts/ci/metadata_commit.py``: the queue commit's metadata-only secret scan.
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

from scripts.ci import metadata_commit, pytest_report, reuse_green_run
from scripts.ci.split_tests import DEFAULT_HISTORY, HISTORY_SHARD, assign, junit_file_seconds, read_list
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


def test_split_pins_history_files_to_the_history_shard() -> None:
    durations = {"tests/test_a.py": 10.0, "tests/test_b.py": 6.0, "tests/test_c.py": 5.0, "tests/test_d.py": 1.0}
    shards = assign(list(durations), durations, 2, pinned=["tests/test_d.py", "tests/test_c.py"])
    assert HISTORY_SHARD == 1
    # d and c (6) start shard 1; a(10) goes to the empty shard 2; b(6) joins shard 1 (6 < 10).
    assert shards == [["tests/test_b.py", "tests/test_c.py", "tests/test_d.py"], ["tests/test_a.py"]]
    with pytest.raises(ValueError, match=re.escape("pinned files are not in the input: tests/test_gone.py")):
        assign(list(durations), durations, 2, pinned=["tests/test_gone.py"])


def test_split_cli_prints_one_shard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    durations = tmp_path / "durations.json"
    durations.write_text(json.dumps({"tests/test_a.py": 5.0, "tests/test_b.py": 1.0}), encoding="utf-8")
    history = tmp_path / "history.txt"
    history.write_text("# comment\ntests/test_b.py  # reads old commits\n\n", encoding="utf-8")
    args = ["--durations", str(durations), "--history", str(history)]
    monkeypatch.setattr(sys, "stdin", __import__("io").StringIO("tests/test_a.py\ntests/test_b.py\n"))
    assert split_main(["split", "--shard", "2", "--of", "2", *args]) == 0
    # b is pinned to shard 1 despite being the shorter file.
    assert capsys.readouterr().out == "tests/test_a.py\n"
    with pytest.raises(SystemExit):
        split_main(["split", "--shard", "3", "--of", "2", *args])


def test_committed_history_list_names_tracked_test_files() -> None:
    listed = read_list(DEFAULT_HISTORY)
    assert listed and len(listed) == len(set(listed))
    for name in listed:
        assert re.fullmatch(r"tests/(?:.+/)?test_[^/]+\.py", name), name
        assert (_REPO_ROOT / name).is_file(), name


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
    owners = [shard for shard in assign(paths, durations, 16, read_list(DEFAULT_HISTORY)) if target in shard]
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


def _shard(results: Path, number: int, files: list[str], cases: str, collected: tuple[str, ...] = ()) -> None:
    """One shard's artifact: file list, JUnit report, and the collected needs_artifact node ids."""
    directory = results / f"pytest-junit-shard-{number}"
    directory.mkdir(parents=True)
    (directory / f"pytest-shard-{number}-files.txt").write_text(
        "".join(f"{name}\n" for name in files), encoding="utf-8"
    )
    (directory / f"pytest-shard-{number}.xml").write_text(
        f"<testsuites><testsuite>{cases}</testsuite></testsuites>", encoding="utf-8"
    )
    (directory / f"pytest-shard-{number}-needs-artifact.txt").write_text(
        "".join(f"{node_id}\n" for node_id in collected), encoding="utf-8"
    )


_PASS_A = '<testcase classname="tests.test_a" name="test_ok" time="1"/>'
_SKIP_B = (
    '<testcase classname="tests.sub.test_b" name="test_artifact" time="0">'
    '<skipped message="needs_artifact: data/x.json missing"/></testcase>'
)
_OTHER_SKIP_B = (
    '<testcase classname="tests.sub.test_b" name="test_artifact" time="0">'
    '<skipped message="needs_sparse_tree: data/projects absent"/></testcase>'
)
_B = "tests/sub/test_b.py::test_artifact"
_B_ID = "tests.sub.test_b::test_artifact\n"


def _report(tmp_path: Path, repo: Path, results: Path) -> tuple[int, Path]:
    record = tmp_path / "out" / "tested-tree.json"
    return pytest_report.main(["--results", str(results), "--root", str(repo), "--record", str(record)]), record


def test_report_passes_a_complete_run_and_records_the_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in {
        "GITHUB_EVENT_NAME": "pull_request",
        "PR_NUMBER": "7",
        "GITHUB_RUN_ID": "11",
        "GITHUB_RUN_ATTEMPT": "1",
    }.items():
        monkeypatch.setenv(name, value)
    repo = _report_repo(tmp_path, _B_ID)
    results = tmp_path / "results"
    _shard(results, 1, ["tests/test_a.py"], _PASS_A)
    _shard(results, 2, ["tests/sub/test_b.py"], _SKIP_B, collected=(_B,))

    status, record = _report(tmp_path, repo, results)

    assert status == 0
    assert json.loads(record.read_text(encoding="utf-8")) == {
        "tier": "full",
        "tree": _git(repo, "rev-parse", "HEAD^{tree}"),
        "sha": _git(repo, "rev-parse", "HEAD"),
        "tests": 2,
        "event": "pull_request",
        "pr": 7,
        "run_id": 11,
        "run_attempt": 1,
    }


@pytest.mark.parametrize(
    ("shards", "expected_skips", "problem"),
    [
        ([(1, ["tests/test_a.py"], _PASS_A, ())], "", "ran on no shard"),
        (
            [
                (1, ["tests/test_a.py", "tests/sub/test_b.py"], _PASS_A, ()),
                (2, ["tests/sub/test_b.py"], _SKIP_B, (_B,)),
            ],
            _B_ID,
            "more than one shard",
        ),
        (
            [(1, ["tests/test_a.py", "tests/sub/test_b.py", "tests/test_gone.py"], _PASS_A, ())],
            "",
            "not tracked test files",
        ),
        ([(1, ["tests/test_a.py", "tests/sub/test_b.py"], "", ())], "", "no test results"),
        (
            [(1, ["tests/test_a.py", "tests/sub/test_b.py"], _PASS_A + _SKIP_B, (_B,))],
            "",
            "unexpected needs_artifact skips",
        ),
        # A new marked test the tier deselects (slow): nothing skipped, so only
        # the collected set shows it.
        (
            [(1, ["tests/test_a.py", "tests/sub/test_b.py"], _PASS_A, (_B,))],
            "",
            "collected needs_artifact tests that are not expected",
        ),
        # Listed as expected, but deselected (slow) instead of skipping.
        (
            [(1, ["tests/test_a.py", "tests/sub/test_b.py"], _PASS_A, (_B,))],
            _B_ID,
            "did not skip for a missing artifact",
        ),
        # Marked and expected, but skipped for another reason.
        (
            [(1, ["tests/test_a.py", "tests/sub/test_b.py"], _PASS_A + _OTHER_SKIP_B, (_B,))],
            _B_ID,
            "did not skip for a missing artifact",
        ),
        # Skipped for a missing artifact, but no longer marked.
        (
            [(1, ["tests/test_a.py", "tests/sub/test_b.py"], _PASS_A + _SKIP_B, ())],
            _B_ID,
            "expected needs_artifact tests that were not collected",
        ),
    ],
)
def test_report_fails_closed(tmp_path: Path, capsys, shards, expected_skips: str, problem: str) -> None:
    repo = _report_repo(tmp_path, expected_skips)
    results = tmp_path / "results"
    for number, files, cases, collected in shards:
        _shard(results, number, files, cases, collected)

    status, record = _report(tmp_path, repo, results)

    assert status == 1
    assert problem in capsys.readouterr().err
    assert not record.exists()


@pytest.mark.parametrize(
    ("missing", "problem"),
    [("pytest-shard-1.xml", "no JUnit report"), ("pytest-shard-1-needs-artifact.txt", "no collected")],
)
def test_report_fails_when_a_shard_uploaded_no_junit_or_collection(
    tmp_path: Path, capsys, missing: str, problem: str
) -> None:
    repo = _report_repo(tmp_path, "")
    results = tmp_path / "results"
    _shard(results, 1, ["tests/test_a.py", "tests/sub/test_b.py"], _PASS_A)
    (results / "pytest-junit-shard-1" / missing).unlink()

    assert _report(tmp_path, repo, results)[0] == 1
    assert problem in capsys.readouterr().err


def _collected_under_xdist(tmp_path: Path, *args: str) -> tuple[set[str], set[str]]:
    """Run pytest under xdist on the first expected module plus ``args``; return (collected, expected) ids."""
    expected = pytest_report.read_expected_skips(_REPO_ROOT / pytest_report.EXPECTED_ARTIFACT_SKIPS)
    module = sorted(expected)[0].split("::", 1)[0]
    collected = tmp_path / "collected.txt"
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest", module.replace(".", "/") + ".py", *args,
            "-n", "2", "-p", "no:cacheprovider", "--override-ini", "addopts=-q",
        ],
        cwd=_REPO_ROOT,
        env={**os.environ, "LU_PYTEST_NEEDS_ARTIFACT_COLLECTED": str(collected)},
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )  # fmt: skip
    assert result.returncode in (0, 5), result.stdout + result.stderr
    ids = {
        pytest_report.nodeid_to_junit_id(line) for line in collected.read_text(encoding="utf-8").splitlines() if line
    }
    return ids, {test_id for test_id in expected if test_id.startswith(f"{module}::")}


def test_conftest_records_marked_tests_before_deselection(tmp_path: Path) -> None:
    """A real pytest run under xdist: ``-m 'not needs_artifact'`` deselects every marked test,
    yet the collected list still names them (so a ``slow`` marked test cannot drop out)."""
    collected, expected = _collected_under_xdist(tmp_path, "-m", "not needs_artifact")
    assert collected == expected


def test_nested_pytest_leaves_the_collected_list_intact(tmp_path: Path) -> None:
    """A test that runs a child pytest (here with the inherited environment) must not
    replace the shard's collected list with the child's (CI run 36658788394 lost 77 ids)."""
    nested = "tests/test_conftest_worktree_guard.py::test_acp_redirect_is_active_when_module_was_not_preimported"
    collected, expected = _collected_under_xdist(tmp_path, nested)
    assert collected == expected


# =============================================================================
# scripts/ci/reuse_green_run.py
# =============================================================================

_TREE = "1" * 40
_PR_HEAD = "a" * 40
_MERGE = "c" * 40
_QUEUED = reuse_green_run.Queued(pr=7, pr_head=_PR_HEAD, tree=_TREE, jobs=reuse_green_run.expected_jobs((1, 2, 3)))


def _run(**overrides) -> dict:
    return {
        "id": 11,
        "event": "pull_request",
        "path": ".github/workflows/ci.yml",
        "status": "completed",
        "conclusion": "success",
        "run_attempt": 1,
        "head_sha": _PR_HEAD,
    } | overrides


def _record(**overrides) -> dict:
    return {
        "tier": "full",
        "tree": _TREE,
        "sha": _MERGE,
        "tests": 250,
        "event": "pull_request",
        "pr": 7,
        "run_id": 11,
        "run_attempt": 1,
    } | overrides


def _jobs(edit=None) -> dict:
    """A pull_request run's attempt-1 jobs: the full inventory green, the queue-only jobs skipped."""
    jobs = [
        {"name": name, "status": "completed", "conclusion": "success", "id": 100 + index, "run_attempt": 1}
        for index, name in enumerate(_QUEUED.jobs)
    ] + [
        {"name": name, "status": "completed", "conclusion": "skipped", "id": 90 + index, "run_attempt": 1}
        for index, name in enumerate(reuse_green_run.SKIPPED_ON_PULL_REQUEST)
    ]
    if edit:
        jobs = edit(jobs)
    return {"total_count": len(jobs), "jobs": jobs}


def _candidate(run=None, record="default", commits=None, jobs=None) -> reuse_green_run.Candidate:
    """A candidate whose GitHub commit objects are ``commits`` (default: the PR merge commit)."""
    commits = commits or {_MERGE: {"sha": _MERGE, "tree": _TREE, "parents": ["b" * 40, _PR_HEAD]}}
    return reuse_green_run.Candidate(
        run=run or _run(),
        load_record=lambda: _record() if record == "default" else record,
        load_commit=commits.__getitem__,
        load_jobs=lambda: jobs or _jobs(),
    )


def _set(name: str, **fields):
    return lambda jobs: [job | fields if job["name"] == name else job for job in jobs]


def test_reuse_when_one_green_attempt_tested_the_identical_tree() -> None:
    decision = reuse_green_run.decide(_QUEUED, [_candidate()])
    assert decision.reuse and decision.run_id == "11", decision.reason
    # Every job of the inventory is logged with its job id in the reused run.
    assert [name for name, _job in decision.jobs] == list(_QUEUED.jobs)
    assert {"pytest (1)", "pytest (2)", "pytest (3)", "Secret scan", "Checks", "Frontend", "pytest report"} <= {
        name for name, _job in decision.jobs
    }
    assert "PR #7" in decision.reason and _MERGE in decision.reason


_OTHER_TREE_COMMIT = {"d" * 40: {"sha": "d" * 40, "tree": "2" * 40, "parents": ["b" * 40, _PR_HEAD]}}


@pytest.mark.parametrize(
    ("candidate", "reason"),
    [
        # The job inventory.
        (
            _candidate(jobs=_jobs(lambda jobs: [j for j in jobs if j["name"] != "pytest (2)"])),
            "0 jobs named 'pytest (2)'",
        ),
        (_candidate(jobs=_jobs(_set("pytest (2)", conclusion="cancelled"))), "'pytest (2)' is 'completed'/'cancelled'"),
        (_candidate(jobs=_jobs(lambda jobs: [*jobs, dict(jobs[5], id=7)])), "2 jobs named 'pytest (1)'"),
        (_candidate(jobs=_jobs(_set("Checks", conclusion="failure"))), "'Checks' is 'completed'/'failure'"),
        (_candidate(jobs=_jobs(_set("Secret scan", conclusion="skipped"))), "'Secret scan' is 'completed'/'skipped'"),
        (_candidate(jobs=_jobs(lambda jobs: [j for j in jobs if j["name"] != "Frontend"])), "0 jobs named 'Frontend'"),
        (_candidate(jobs=_jobs(lambda jobs: [j for j in jobs if j["name"] != "pytest report"])), "'pytest report'"),
        (_candidate(jobs=_jobs(lambda jobs: [*jobs, dict(jobs[0], name="pytest (4)")])), "unexpected job 'pytest (4)'"),
        (_candidate(jobs=_jobs(_set("Reuse check", conclusion="success"))), "'Reuse check' concluded 'success'"),
        (_candidate(jobs={"total_count": 30, "jobs": _jobs()["jobs"]}), "of 30 jobs listed"),
        # The run: one attempt, the right PR head, event and workflow.
        (_candidate(run=_run(run_attempt=2)), "run_attempt is 2"),
        (_candidate(jobs=_jobs(_set("pytest (3)", run_attempt=2))), "jobs from run attempt [2]"),
        (_candidate(run=_run(head_sha="e" * 40)), "head_sha is"),
        (_candidate(run=_run(event="push")), "event is 'push'"),
        (_candidate(run=_run(conclusion="failure")), "conclusion is 'failure'"),
        (_candidate(run=_run(path=".github/workflows/other.yml")), "path is"),
        # The record.
        (_candidate(record=None), "no ci-tested-tree record"),
        (_candidate(record=_record(tier="fast")), "record tier is 'fast'"),
        (_candidate(record=_record(tests=0)), "record claims 0 tests"),
        (_candidate(record=_record(tests=True)), "record claims True tests"),
        (_candidate(record=_record(pr=8)), "record pr is 8"),
        (_candidate(record=_record(run_id=12)), "record run_id is 12"),
        (_candidate(record=_record(run_attempt=2)), "record run_attempt is 2"),
        (_candidate(record=_record(sha="not-a-sha")), "is not a commit SHA"),
        # The tested commit, read from GitHub: the record's tree claim is not trusted.
        (
            _candidate(record=_record(sha="d" * 40), commits=_OTHER_TREE_COMMIT),
            f"has tree {'2' * 40}, the queue commit {_TREE}",
        ),
        (
            _candidate(commits={_MERGE: {"sha": _MERGE, "tree": _TREE, "parents": ["b" * 40, "e" * 40]}}),
            f"is not a merge of PR head {_PR_HEAD}",
        ),
        (_candidate(record=_record(tree="3" * 40)), "record tree"),
    ],
)
def test_no_reuse_without_complete_proof(candidate: reuse_green_run.Candidate, reason: str) -> None:
    decision = reuse_green_run.decide(_QUEUED, [candidate])
    assert not decision.reuse and not decision.jobs and decision.run_id == ""
    assert reason in decision.reason


def test_reuse_takes_the_first_matching_candidate() -> None:
    decision = reuse_green_run.decide(
        _QUEUED,
        [
            _candidate(run=_run(id=13), record=None),
            _candidate(run=_run(id=12), record=_record(run_id=12), jobs=_jobs(_set("Checks", conclusion="failure"))),
            _candidate(run=_run(id=10), record=_record(run_id=10)),
        ],
    )
    assert decision.run_id == "10"


def test_pytest_shards_match_the_ci_matrix() -> None:
    matrix = _jobs_of_ci()["pytest"]["strategy"]["matrix"]["shard"]
    assert reuse_green_run.pytest_shards(_CI.read_text(encoding="utf-8")) == tuple(matrix)
    # Every other ci.yml job name is either required in the reused run or queue-only.
    names = {job.get("name") for job in _jobs_of_ci().values()}
    assert set(reuse_green_run.EXPECTED_JOBS) | set(reuse_green_run.SKIPPED_ON_PULL_REQUEST) == names - {
        "pytest (${{ matrix.shard }})"
    }


@pytest.mark.parametrize("text", ["", "        shard: [1, 2]\n        shard: [1]\n", "        shard: [2, 3]\n"])
def test_pytest_shards_refuse_an_unreadable_matrix(text: str) -> None:
    with pytest.raises(ValueError):
        reuse_green_run.pytest_shards(text)


def _main_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    output = tmp_path / "output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    for name in ("REPO", "HEAD_SHA", "HEAD_REF"):
        monkeypatch.setenv(name, "x")
    return output


def test_reuse_logs_the_run_and_job_ids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setattr(reuse_green_run, "lookup", lambda *_args: reuse_green_run.decide(_QUEUED, [_candidate()]))
    output = _main_env(monkeypatch, tmp_path)
    summary = tmp_path / "summary"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    assert reuse_green_run.main() == 0
    assert output.read_text(encoding="utf-8") == "reuse=true\nrun_id=11\n"
    logged = capsys.readouterr().out
    for name in _QUEUED.jobs:
        assert f"{name}: reused from run 11, job " in logged
        assert f"{name}: reused from run 11, job " in summary.read_text(encoding="utf-8")


def test_lookup_failure_runs_every_job(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(*_args, **_kwargs):
        raise subprocess.CalledProcessError(1, ["gh"], stderr="HTTP 502")

    monkeypatch.setattr(reuse_green_run, "lookup", broken)
    output = _main_env(monkeypatch, tmp_path)
    assert reuse_green_run.main() == 0
    assert output.read_text(encoding="utf-8") == "reuse=false\nrun_id=\n"


@pytest.mark.parametrize(
    "candidate",
    [
        reuse_green_run.Candidate(
            run=_run(), load_record=lambda: json.loads("{"), load_commit=dict, load_jobs=lambda: _jobs()
        ),
        # GitHub does not know the recorded commit.
        _candidate(record=_record(sha="f" * 40)),
    ],
)
def test_a_record_or_commit_that_fails_to_load_runs_every_job(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, candidate
) -> None:
    monkeypatch.setattr(reuse_green_run, "lookup", lambda *_args: reuse_green_run.decide(_QUEUED, [candidate]))
    output = _main_env(monkeypatch, tmp_path)
    assert reuse_green_run.main() == 0
    assert output.read_text(encoding="utf-8") == "reuse=false\nrun_id=\n"


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
# scripts/ci/metadata_commit.py
# =============================================================================

_RAW = (
    "tree " + "1" * 40 + "\n"
    "parent " + "2" * 40 + "\n"
    "parent " + "3" * 40 + "\n"
    "author A <a@example.invalid> 1 +0000\n"
    "committer GitHub <noreply@github.com> 2 +0000\n"
    "gpgsig -----BEGIN PGP SIGNATURE-----\n"
    " \n"
    " abc\n"
    " -----END PGP SIGNATURE-----\n"
    "\n"
    "Merge pull request #7: title\n\nbody\n"
)


def test_metadata_only_object_keeps_people_and_message_and_drops_the_diff() -> None:
    obj = metadata_commit.metadata_only_object(_RAW, "2" * 40, "4" * 40)
    assert obj == (
        "tree " + "4" * 40 + "\n"
        "parent " + "2" * 40 + "\n"
        "author A <a@example.invalid> 1 +0000\n"
        "committer GitHub <noreply@github.com> 2 +0000\n"
        "\n"
        "Merge pull request #7: title\n\nbody\n"
    )


def test_metadata_commit_writes_an_empty_diff_commit_on_a_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    ident = ["-c", "user.name=Queue", "-c", "user.email=q@example.invalid"]
    _git(repo, "init", "-q", "-b", "main")
    (repo / "f").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "f")
    _git(repo, *ident, "commit", "-qm", "base")
    _git(repo, "checkout", "-qb", "pr")
    (repo / "f").write_text("changed\n", encoding="utf-8")
    _git(repo, *ident, "commit", "-qam", "pr")
    _git(repo, "checkout", "-q", "main")
    _git(repo, *ident, "merge", "-q", "--no-ff", "pr", "-m", "Merge pull request #7\n\nPR-derived text")
    monkeypatch.chdir(repo)

    assert metadata_commit.main([]) == 0

    outputs = dict(line.split("=", 1) for line in capsys.readouterr().out.splitlines())
    new, parent = outputs["commit"], outputs["parent"]
    assert parent == _git(repo, "rev-parse", "HEAD^1")
    assert _git(repo, "rev-parse", "ci-queue-metadata") == new
    assert _git(repo, "rev-list", "--parents", "-n", "1", new).split() == [new, parent]
    assert _git(repo, "diff", "--name-only", parent, new) == ""
    fields = "%an%n%ae%n%ad%n%cn%n%ce%n%cd%n%B"
    assert _git(repo, "log", "-1", f"--format={fields}", new) == _git(repo, "log", "-1", f"--format={fields}", "HEAD")


# =============================================================================
# .github/workflows/ci.yml wiring
# =============================================================================


def _jobs_of_ci() -> dict:
    return yaml.safe_load(_CI.read_text(encoding="utf-8"))["jobs"]


def _run_pytest_script() -> str:
    return next(step["run"] for step in _jobs_of_ci()["pytest"]["steps"] if step.get("name") == "Run pytest")


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
    assert (
        'export LU_PYTEST_NEEDS_ARTIFACT_COLLECTED="ci-artifacts/pytest-shard-${SHARD}'
        + pytest_report.COLLECTED_SUFFIX
        + '"'
    ) in script


def test_pytest_matrix_is_contiguous_and_counted_by_the_job() -> None:
    pytest_job = _jobs_of_ci()["pytest"]
    shards = pytest_job["strategy"]["matrix"]["shard"]
    assert shards == list(range(1, len(shards) + 1))
    env = next(step["env"] for step in pytest_job["steps"] if step.get("name") == "Run pytest")
    assert env == {"SHARD": "${{ matrix.shard }}", "SHARDS": "${{ strategy.job-total }}"}


def test_shard_artifacts_feed_the_report_and_the_flake_ledger() -> None:
    jobs = _jobs_of_ci()
    upload = next(step for step in jobs["pytest"]["steps"] if step.get("name") == "Upload pytest JUnit report")
    # scripts/ci/flake_ledger.py downloads "pytest-junit-shard-*" from merge_group runs.
    assert upload["with"]["name"] == "pytest-junit-shard-${{ matrix.shard }}"
    assert "ci-artifacts/pytest-shard-*.xml" in upload["with"]["path"]
    assert "ci-artifacts/pytest-shard-*-files.txt" in upload["with"]["path"]
    assert f"ci-artifacts/pytest-shard-*{pytest_report.COLLECTED_SUFFIX}" in upload["with"]["path"]
    report = jobs["pytest-report"]
    assert report["if"] == "${{ !cancelled() && needs.pytest.result == 'success' }}"
    steps = report["steps"]
    assert any(step.get("with", {}).get("pattern") == "pytest-junit-shard-*" for step in steps)
    report_step = next(step for step in steps if "scripts.ci.pytest_report" in str(step.get("run", "")))
    # The record names the PR it tested; reuse_green_run binds the queued PR to it.
    assert report_step["env"] == {"PR_NUMBER": "${{ github.event.pull_request.number }}"}
    assert any(step.get("with", {}).get("name") == reuse_green_run.ARTIFACT for step in steps)


def test_pytest_is_skipped_only_on_a_recorded_reuse() -> None:
    jobs = _jobs_of_ci()
    assert jobs["pytest"]["needs"] == ["reuse"]
    assert jobs["pytest"]["if"] == "${{ !cancelled() && needs.reuse.outputs.reuse != 'true' }}"
    assert jobs["reuse"]["if"] == "github.event_name == 'merge_group'"
    assert jobs["reuse"]["permissions"] == {"contents": "read", "actions": "read", "pull-requests": "read"}
    # reuse_green_run reads the shard matrix from the queue commit's ci.yml.
    assert reuse_green_run.WORKFLOW in jobs["reuse"]["steps"][0]["with"]["sparse-checkout"].split()


def test_queue_commit_metadata_is_scanned_on_every_merge_group_run() -> None:
    job = _jobs_of_ci()["queue-metadata-scan"]
    # Not gated on the reuse decision: the reused secret scan covered files, not this commit's metadata.
    assert job["if"] == "github.event_name == 'merge_group'" and "needs" not in job
    steps = job["steps"]
    checkout, setup, metadata, scan = (
        next(step for step in steps if str(step.get("uses", "")).startswith("actions/checkout@")),
        next(step for step in steps if str(step.get("uses", "")).startswith("actions/setup-python@")),
        next(step for step in steps if step.get("id") == "metadata"),
        next(step for step in steps if "trufflehog" in step.get("uses", "")),
    )
    assert steps.index(checkout) < steps.index(setup) < steps.index(metadata) < steps.index(scan)
    assert setup["with"] == {"python-version-file": ".python-version"}
    assert checkout["with"] == {"persist-credentials": False, "fetch-depth": 2}
    assert metadata["id"] == "metadata"
    assert "python3 -m scripts.ci.metadata_commit --commit HEAD" in metadata["run"]
    full_scan = next(step for step in _jobs_of_ci()["secret-scan"]["steps"] if "trufflehog" in step.get("uses", ""))
    assert scan["uses"] == full_scan["uses"]
    assert scan["with"] == {
        "base": "${{ steps.metadata.outputs.parent }}",
        "head": "${{ steps.metadata.outputs.commit }}",
        "extra_args": "--results=verified,unknown --exclude-detectors=Lob",
    }


def test_every_checkout_drops_credentials_and_every_action_is_sha_pinned() -> None:
    text = _CI.read_text(encoding="utf-8")
    assert "continue-on-error" not in text
    for job_id, job in _jobs_of_ci().items():
        for step in job.get("steps", []):
            uses = step.get("uses")
            if not uses or uses.startswith("./"):
                continue
            revision = uses.split("@", 1)[1]
            assert re.fullmatch(r"[0-9a-f]{40}", revision), (job_id, uses)
            if uses.startswith("actions/checkout@"):
                assert step["with"]["persist-credentials"] is False, job_id
    assert yaml.safe_load(text)["permissions"] == {"contents": "read"}
