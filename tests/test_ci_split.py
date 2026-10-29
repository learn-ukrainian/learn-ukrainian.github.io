"""CI pytest sharding, the whole-run report, and event tiers.

- ``scripts/ci/split_tests.py``: the static duration-balanced file split and
  the history files it pins to shard 1.
- ``tests/conftest.py``: the ``LU_PYTEST_SHARD_FILES`` allowlist hook each
  shard collects through.
- ``scripts/ci/pytest_report.py``: partition, executed-test and
  needs_artifact collected/skip checks over every shard.
- ``tests/conftest.py``: the collected ``needs_artifact`` list pytest report audits.
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

from scripts.ci import metadata_commit, pytest_report
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
    monkeypatch.setattr(sys, "stdin", __import__("io").StringIO("tests/test_a.py\ntests/test_b.py\ntests/test_new.py\n"))
    weights = tmp_path / "weights.json"
    assert split_main(["split", "--shard", "2", "--of", "2", *args, "--weights-out", str(weights)]) == 0
    # b is pinned to shard 1 despite being the shorter file.
    assert capsys.readouterr().out == "tests/test_a.py\n"
    # Only recorded weights are written; an unrecorded file's median stand-in is not.
    assert json.loads(weights.read_text(encoding="utf-8")) == {"tests/test_a.py": 5.0}
    with pytest.raises(SystemExit):
        split_main(["split", "--shard", "3", "--of", "2", *args])


def test_committed_history_list_names_tracked_test_files() -> None:
    listed = read_list(DEFAULT_HISTORY)
    assert listed and len(listed) == len(set(listed))
    for name in listed:
        assert re.fullmatch(r"tests/(?:.+/)?test_[^/]+\.py", name), name
        assert (_REPO_ROOT / name).is_file(), name


def test_durations_sum_testcase_time_per_file(tmp_path: Path, capsys) -> None:
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
    assert split_main(["durations", str(junit)]) == 0
    assert json.loads(capsys.readouterr().out) == {"tests/audit/test_x.py": 3.5, "tests/test_y.py": 0.25}

    # --shards: a fast runner's seconds are divided by its speed (median observed/weight),
    # a listed file that ran no test records 0, and a shard too small to measure keeps its seconds.
    fast = tmp_path / "shards/pytest-junit-shard-1"
    fast.mkdir(parents=True)
    names = [f"tests/test_f{index}.py" for index in range(10)]
    (fast / "pytest-shard-1-files.txt").write_text("\n".join([*names, "tests/test_deselected.py"]) + "\n")
    (fast / "pytest-shard-1-weights.json").write_text(json.dumps({name: 10.0 for name in [*names, "tests/test_deselected.py"]}))
    (fast / "pytest-shard-1.xml").write_text(
        "<testsuite>"
        + "".join(f'<testcase classname="tests.test_f{index}" name="test_a" time="6"/>' for index in range(10))
        + "</testsuite>"
    )
    alone = tmp_path / "shards/pytest-junit-shard-2"
    alone.mkdir()
    (alone / "pytest-shard-2-files.txt").write_text("tests/test_big.py\n")
    (alone / "pytest-shard-2-weights.json").write_text('{"tests/test_big.py": 900}')
    (alone / "pytest-shard-2.xml").write_text('<testsuite><testcase classname="tests.test_big" name="t" time="600"/></testsuite>')
    assert split_main(["durations", "--shards", str(tmp_path / "shards")]) == 0
    recorded = capsys.readouterr()
    assert json.loads(recorded.out) == {
        **{name: 10.0 for name in names},
        "tests/test_deselected.py": 0.0,
        "tests/test_big.py": 600.0,
    }
    assert "pytest-shard-1=0.60 pytest-shard-2=1.00" in recorded.err
    with pytest.raises(SystemExit):
        split_main(["durations", str(junit), "--shards", str(tmp_path / "shards")])


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

    # Exercise the real queue-record entry point against this Git candidate.
    actual = _git(repo, "rev-parse", "HEAD")
    queue_ref = "refs/heads/gh-readonly-queue/main/pr-7-" + "a" * 40
    payload = {"action": "checks_requested", "repository": {"default_branch": "main"}, "merge_group": {"base_sha": parent, "base_ref": "refs/heads/main", "head_sha": actual, "head_ref": queue_ref}}
    event = tmp_path / "event.json"
    event.write_text(json.dumps(payload))
    record = tmp_path / "queue-candidate.json"
    env = {**os.environ, "EVENT_NAME": "merge_group", "GITHUB_EVENT_PATH": str(event), "GITHUB_SHA": actual, "GITHUB_REF": queue_ref, "GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "1", "QUEUE_RECORD": str(record)}
    result = subprocess.run([sys.executable, str(_REPO_ROOT / "scripts/ci/gate.py"), "--record-queue"], cwd=repo, env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(record.read_text()) == {"base_sha": parent, "head_sha": actual, "head_ref": queue_ref, "run_id": 123, "run_attempt": 1}
    for broken in ({"EVENT_NAME": "pull_request"}, {"GITHUB_SHA": parent}, {"GITHUB_REF": "refs/heads/main"}, {"GITHUB_RUN_ID": "missing"}):
        result = subprocess.run([sys.executable, str(_REPO_ROOT / "scripts/ci/gate.py"), "--record-queue"], cwd=repo, env={**env, **broken}, capture_output=True, text=True, timeout=30)
        assert result.returncode != 0


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
    assert "scripts.ci.split_tests duration-source" in script
    assert '--durations "$durations"' in script
    assert 'export LU_PYTEST_SHARD_FILES="ci-artifacts/pytest-shard-${SHARD}-files.txt"' in script
    assert "-m 'not atlas_release and not slow and not site_toolchain' --strict-markers" in script
    assert "not site_toolchain" in script
    # Frontend selection over tests/ is covered by tests/build/test_fresh_page_safety.py::
    # test_ci_runs_site_toolchain_tests_in_required_frontend_job.
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
    assert env == {
        "SHARD": "${{ matrix.shard }}",
        "SHARDS": "${{ strategy.job-total }}",
        "REFRESH_RESULT": "${{ needs.refresh-pytest-durations.result }}",
    }


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
    # The audit record identifies the exact candidate and run.
    assert report_step["env"] == {"PR_NUMBER": "${{ github.event.pull_request.number }}"}
    assert any(step.get("with", {}).get("name") == "ci-tested-tree" for step in steps)


def test_pytest_and_frontend_run_on_every_event() -> None:
    jobs = _jobs_of_ci()
    assert "reuse" not in jobs
    assert jobs["pytest"]["needs"] == ["refresh-pytest-durations"]
    for name in ("pytest", "refresh-pytest-durations", "frontend"):
        assert jobs[name]["if"] == "${{ !cancelled() }}"
    refresh = jobs["refresh-pytest-durations"]
    assert all("if" not in step for step in refresh["steps"])
    collection = next(step for step in jobs["checks"]["steps"] if step.get("name") == "Collect pytest for PR admission")
    assert collection["if"] == "github.event_name == 'pull_request'"
    assert "pytest tests --collect-only --strict-markers" in collection["run"]
    assert "--override-ini addopts=-qq " in collection["run"]
    assert "norecursedirs=.* node_modules" in collection["run"]


def test_queue_commit_metadata_is_scanned_on_every_merge_group_run() -> None:
    job = _jobs_of_ci()["queue-metadata-scan"]
    # Queue metadata scanning is independent of file-content scanning.
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
    record = next(step for step in steps if step.get("name") == "Record original queue candidate")
    assert "scripts.ci.gate --record-queue" in record["run"]
    upload = next(step for step in steps if step.get("with", {}).get("name") == "ci-queue-candidate")
    assert upload["with"]["if-no-files-found"] == "error"
    assert steps.index(record) < steps.index(upload) < steps.index(metadata)
    assert checkout["with"] == {
        "persist-credentials": False,
        "fetch-depth": 0,
        "filter": "blob:none",
        "sparse-checkout": "scripts/\n.python-version\n",
        "sparse-checkout-cone-mode": False,
    }
    assert metadata["id"] == "metadata"
    assert "python3 -m scripts.ci.metadata_commit --commit HEAD" in metadata["run"]
    full_scan = next(step for step in _jobs_of_ci()["secret-scan"]["steps"] if "trufflehog" in step.get("uses", ""))
    assert scan["uses"] == full_scan["uses"]
    assert scan["with"] == {
        "version": "3.99.0",
        "base": "${{ steps.metadata.outputs.parent }}",
        "head": "${{ steps.metadata.outputs.commit }}",
        "extra_args": "--results=verified,unknown --exclude-detectors=Lob --trust-local-git-config --fail-on-scan-errors",
    }


def test_every_checkout_drops_credentials_and_every_action_is_sha_pinned() -> None:
    text = _CI.read_text(encoding="utf-8")
    optional = [
        (job_id, step)
        for job_id, job in _jobs_of_ci().items()
        for step in job.get("steps", [])
        if "continue-on-error" in step
    ]
    assert optional == []
    # No job may tolerate a whole-job failure.
    assert not any("continue-on-error" in job for job in _jobs_of_ci().values())
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

def test_pr_changed_test_files_and_guard_list_are_selected_without_selector(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Use immutable merge parents despite stale metadata; reject wrong heads and dirty sources."""
    from scripts.ci import pr_affected_tests as affected

    guards = [
        'tests/test_delegate_review_admission.py', 'tests/review/test_routing_consumers.py',
        'tests/agent_runtime/test_lane_probe.py',
        'tests/common/test_jsonl_splitlines_guard.py', 'tests/test_review_reviewer_resolver.py',
    ]
    assert (_REPO_ROOT / affected.GUARDS).read_text().splitlines() == guards
    repo = tmp_path / 'candidate'
    repo.mkdir()
    _git(repo, 'init', '-q', '-b', 'fixture-base')
    ident = ['-c', 'user.name=CI fixture', '-c', 'user.email=ci@example.invalid']
    for name in [*guards, 'tests/test_deleted.py', 'tests/test_old.py', 'tests/test_space name.py']:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('def test_exact_candidate():\n    assert 2 + 2 == 4\n')
    (repo / 'scripts/ci').mkdir(parents=True)
    (repo / affected.GUARDS).write_text('\n'.join(guards) + '\n')
    weights = {p: 1 for p in [*guards, 'tests/test_new.py', 'tests/test_space name.py']}
    (repo / affected.DURATIONS).write_text(json.dumps(weights))
    (repo / 'scripts/ci/pr_affected_tests.py').write_bytes(Path(affected.__file__).read_bytes())
    (repo / 'scripts/ci/gate.py').write_bytes((_REPO_ROOT / 'scripts/ci/gate.py').read_bytes())
    (repo / 'pytest.ini').write_text(
        '[pytest]\nmarkers =\n    repo_wide: repository invariant\n    slow: nightly test\n'
        '    atlas_release: release test\n    site_toolchain: frontend test\n'
    )
    (repo / 'tests/build').mkdir()
    (repo / 'tests/build/test_invariant.py').write_text(
        'import pytest\n@pytest.mark.repo_wide\ndef test_invariant():\n    assert True\n'
        'def test_unmarked():\n    assert False, "unmarked tests must not run"\n'
        '@pytest.mark.repo_wide\n@pytest.mark.slow\ndef test_slow():\n    assert False, "nightly test"\n'
        '@pytest.mark.repo_wide\n@pytest.mark.atlas_release\ndef test_release():\n    assert False, "release test"\n'
        '@pytest.mark.repo_wide\n@pytest.mark.site_toolchain\ndef test_frontend():\n    assert False, "frontend test"\n'
    )
    (repo / '.gitignore').write_text('ci-artifacts/\n')
    _git(repo, 'add', '.')
    _git(repo, *ident, 'commit', '-qm', 'base')
    event_base = _git(repo, 'rev-parse', 'HEAD')
    (repo / 'README.md').write_text('Target advances before GitHub creates its test merge.\n')
    _git(repo, 'add', 'README.md')
    _git(repo, *ident, 'commit', '-qm', 'advanced target')
    base = _git(repo, 'rev-parse', 'HEAD')
    _git(repo, 'update-ref', 'refs/remotes/origin/fixture-base', base)
    _git(repo, 'checkout', '-qb', 'pr')
    _git(repo, 'mv', 'tests/test_old.py', 'tests/test_new.py')
    _git(repo, 'rm', '-q', 'tests/test_deleted.py')
    (repo / 'tests/test_space name.py').write_text('def test_exact_candidate():\n    assert "candidate" != "base"\n')
    _git(repo, 'add', '.')
    _git(repo, *ident, 'commit', '-qm', 'PR')
    head = _git(repo, 'rev-parse', 'HEAD')
    _git(repo, 'checkout', '-q', 'fixture-base')
    _git(repo, *ident, 'merge', '--no-ff', '-qm', 'candidate', 'pr')
    candidate = _git(repo, 'rev-parse', 'HEAD')
    advanced_target = _git(repo, *ident, 'commit-tree', f'{base}^{{tree}}', '-p', base, '-m', 'later target')
    _git(repo, 'update-ref', 'refs/remotes/origin/fixture-base', advanced_target)
    monkeypatch.chdir(repo)
    selected = affected.plan(base, candidate)
    assert selected['run_files'] == sorted([*guards, 'tests/test_new.py', 'tests/test_space name.py'])
    assert selected['deferred_files'] == []
    assert selected['deleted_test_files'] == ['tests/test_deleted.py', 'tests/test_old.py']
    assert selected['estimate_seconds'] == 67
    payload = {'action': 'opened', 'repository': {'default_branch': 'fixture-base'},
               'pull_request': {'number': 7, 'base': {'sha': event_base, 'ref': 'fixture-base'}, 'head': {'sha': head}}}
    event = tmp_path / 'event.json'
    event.write_text(json.dumps(payload))
    for key, value in {'EVENT_NAME': 'pull_request', 'GITHUB_EVENT_PATH': str(event),
                       'GITHUB_SHA': candidate, 'GITHUB_REF': 'refs/pull/7/merge',
                       'GITHUB_BASE_REF': 'fixture-base',
                       'GITHUB_STEP_SUMMARY': str(tmp_path / 'summary')}.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(sys, 'argv', ['pr-affected'])
    cli = subprocess.run([sys.executable, '-m', 'scripts.ci.pr_affected_tests'],
                         capture_output=True, text=True, timeout=60)
    assert cli.returncode == 0, cli.stdout + cli.stderr
    print(cli.stdout)
    record = json.loads((repo / 'ci-artifacts/pr-affected.json').read_text())
    assert record['candidate'] == candidate and record['reported_cases'] == 7
    assert record['base'] == base and record['event_base'] == event_base
    assert record['run_files'] == sorted([*guards, 'tests/test_new.py', 'tests/test_space name.py'])
    assert record['execution_status'] == 'completed' and record['exit_code'] == 0
    assert record['skipped_cases'] == 0 and record['failed_cases'] == 0
    assert 'the full pytest shards run in their own jobs' in (tmp_path / 'summary').read_text()
    assert 'deferred test-case count: UNKNOWN' in (tmp_path / 'summary').read_text()
    # Duration deferral cannot suppress a marker, including under pytest's
    # normally excluded build/ directory, or execute its unmarked neighbour.
    with monkeypatch.context() as context:
        context.setattr(affected, 'CAP_SECONDS', 1)
        context.setattr(sys, 'argv', ['pr-affected', '--repo-wide'])
        assert affected.main() == 0
    marker = json.loads((repo / 'ci-artifacts/pr-repo-wide.json').read_text())
    assert marker['reason'] == 'recorded estimate exceeds 600 second cap'
    assert marker['reported_cases'] == 1 and marker['failed_cases'] == 0
    (repo / 'ci-artifacts/pr-repo-wide.xml').unlink()
    assert affected.main() == 1  # stale report cannot masquerade as this execution
    monkeypatch.setenv('GITHUB_SHA', base)
    cli = subprocess.run([sys.executable, '-m', 'scripts.ci.pr_affected_tests'],
                         capture_output=True, text=True, timeout=60)
    assert cli.returncode == 1
    assert 'stage=event_identity' in cli.stderr
    assert 'ValueError: checked-out candidate does not match GITHUB_SHA' in cli.stderr
    print(cli.stderr)
    monkeypatch.setenv('GITHUB_SHA', candidate)
    payload['pull_request']['head']['sha'] = base
    event.write_text(json.dumps(payload))
    cli = subprocess.run([sys.executable, '-m', 'scripts.ci.pr_affected_tests'],
                         capture_output=True, text=True, timeout=60)
    assert cli.returncode == 1
    assert 'stage=merge_parents' in cli.stderr
    assert 'ValueError: PR merge candidate must have two parents and match event head' in cli.stderr
    print(cli.stderr)

    payload['pull_request']['head']['sha'] = head
    event.write_text(json.dumps(payload))
    _git(repo, 'checkout', '-q', 'pr')
    (repo / '.github/workflows').mkdir(parents=True)
    (repo / '.github/workflows/ci.yml').write_text('name: changed workflow\n')
    _git(repo, 'add', '.github/workflows/ci.yml')
    _git(repo, *ident, 'commit', '-qm', 'workflow change')
    workflow_head = _git(repo, 'rev-parse', 'HEAD')
    _git(repo, 'checkout', '-qB', 'workflow-candidate', base)
    _git(repo, *ident, 'merge', '--no-ff', '-qm', 'workflow merge', 'pr')
    workflow_candidate = _git(repo, 'rev-parse', 'HEAD')
    payload['pull_request']['head']['sha'] = workflow_head
    event.write_text(json.dumps(payload))
    monkeypatch.setenv('GITHUB_SHA', workflow_candidate)
    # The candidate needs no mutable local target ref or untracked-file gate.
    _git(repo, 'update-ref', '-d', 'refs/remotes/origin/fixture-base')
    (repo / 'untracked-note.txt').write_text('unrelated runner output\n')
    (repo / 'ci-artifacts/pr-affected.xml').unlink()
    cli = subprocess.run([sys.executable, '-m', 'scripts.ci.pr_affected_tests'],
                         capture_output=True, text=True, timeout=60)
    assert cli.returncode == 0, cli.stdout + cli.stderr
    print(cli.stdout)
    workflow = json.loads((repo / 'ci-artifacts/pr-affected.json').read_text())
    assert workflow['candidate'] == workflow_candidate and workflow['base'] == base
    assert workflow['event_base'] == event_base
    assert workflow['run_files'] == sorted(guards) and workflow['reported_cases'] == 5
    assert workflow['deferred_files'] == ['tests/test_new.py', 'tests/test_space name.py']
    assert workflow['reason'] == 'pytest infrastructure changed'
    assert workflow['execution_status'] == 'completed' and workflow['exit_code'] == 0
    assert workflow['failed_cases'] == 0 and workflow['skipped_cases'] == 0
    assert workflow['deferred_case_count'] is None
    marker_cli = subprocess.run([sys.executable, '-m', 'scripts.ci.pr_affected_tests', '--repo-wide'],
                                capture_output=True, text=True, timeout=60)
    assert marker_cli.returncode == 0, marker_cli.stdout + marker_cli.stderr
    marker = json.loads((repo / 'ci-artifacts/pr-repo-wide.json').read_text())
    assert marker['reported_cases'] == 1 and marker['failed_cases'] == 0
    assert marker['selection'] == 'repo_wide and not atlas_release and not slow and not site_toolchain'
    assert marker['requested_paths'] == ['tests']
    assert marker['reason'] == 'pytest infrastructure changed'
    assert marker['candidate'] == workflow_candidate and marker['wall_seconds'] > 0
    (repo / 'untracked-note.txt').unlink()
    (repo / guards[0]).write_text('# dirty selected source\n')
    assert affected.main() == 1
    _git(repo, 'restore', guards[0])
    _git(repo, 'checkout', '-q', 'pr')
    (repo / 'tests/conftest.py').write_text('# infrastructure defers changed test files\n')
    (repo / guards[0]).write_text('def test_exact_candidate():\n    assert False, "candidate defect"\n')
    invariant = repo / 'tests/build/test_invariant.py'
    invariant.write_text(invariant.read_text().replace('assert True', 'assert False, "invariant defect"'))
    _git(repo, 'add', 'tests/build/test_invariant.py')
    _git(repo, 'add', 'tests/conftest.py', guards[0])
    _git(repo, *ident, 'commit', '-qm', 'broken PR')
    broken_head = _git(repo, 'rev-parse', 'HEAD')
    _git(repo, 'checkout', '-qB', 'broken-candidate', base)
    _git(repo, *ident, 'merge', '--no-ff', '-qm', 'broken merge candidate', 'pr')
    broken_candidate = _git(repo, 'rev-parse', 'HEAD')
    payload['pull_request']['head']['sha'] = broken_head
    event.write_text(json.dumps(payload))
    monkeypatch.setenv('GITHUB_SHA', broken_candidate)
    (repo / 'ci-artifacts/pr-affected.xml').unlink()
    assert affected.main() == 1
    failed = json.loads((repo / 'ci-artifacts/pr-affected.json').read_text())
    assert failed['failed_cases'] == 1 and failed['exit_code'] == 1
    assert failed['run_files'] == sorted(guards)
    assert failed['deferred_files'] == ['tests/build/test_invariant.py', 'tests/test_new.py', 'tests/test_space name.py']
    assert failed['reason'] == 'pytest infrastructure changed'
    assert failed['deferred_case_count'] is None
    (repo / 'ci-artifacts/pr-repo-wide.xml').unlink()
    marker_cli = subprocess.run([sys.executable, '-m', 'scripts.ci.pr_affected_tests', '--repo-wide'],
                                capture_output=True, text=True, timeout=60)
    assert marker_cli.returncode == 1
    marker = json.loads((repo / 'ci-artifacts/pr-repo-wide.json').read_text())
    assert marker['reported_cases'] == 1 and marker['failed_cases'] == 1
    assert marker['exit_code'] == 1 and marker['candidate'] == broken_candidate
    # Missing JUnit must preserve an incomplete plan with unknown case counts.
    (repo / 'pytest.ini').write_text('[pytest]\naddopts = -p no:junitxml\n')
    (repo / guards[0]).write_text('def test_exact_candidate():\n    assert 2 + 2 == 4\n')
    _git(repo, 'add', 'pytest.ini', guards[0])
    _git(repo, *ident, 'commit', '-qm', 'missing report head')
    missing_head = _git(repo, 'rev-parse', 'HEAD')
    _git(repo, 'checkout', '-qB', 'missing-report-candidate', base)
    _git(repo, *ident, 'merge', '--no-ff', '-qm', 'missing report merge', missing_head)
    payload['pull_request']['head']['sha'] = missing_head
    event.write_text(json.dumps(payload))
    monkeypatch.setenv('GITHUB_SHA', _git(repo, 'rev-parse', 'HEAD'))
    (repo / 'ci-artifacts/pr-affected.xml').unlink()
    assert affected.main() == 1
    partial = json.loads((repo / 'ci-artifacts/pr-affected.json').read_text())
    assert partial['execution_status'] == 'incomplete'
    assert partial['reported_cases'] is None and partial['exit_code'] == 0
    _git(repo, 'checkout', '-q', 'fixture-base')

    weights['tests/test_new.py'] = 600
    (repo / affected.DURATIONS).write_text(json.dumps(weights))
    deferred = affected.plan(base, candidate)
    assert deferred['run_files'] == sorted(guards)
    assert deferred['deferred_files'] == ['tests/test_new.py', 'tests/test_space name.py']
    assert deferred['reason'] == 'recorded estimate exceeds 600 second cap'
    del weights['tests/test_new.py']
    (repo / affected.DURATIONS).write_text(json.dumps(weights))
    # A new test file with no recorded duration is weighted at the median and still runs.
    unrecorded = affected.plan(base, candidate)
    assert unrecorded['unknown_duration_files'] == ['tests/test_new.py']
    assert unrecorded['reason'] is None
    assert unrecorded['run_files'] == sorted([*guards, 'tests/test_new.py', 'tests/test_space name.py'])
    assert unrecorded['deferred_files'] == []
    assert unrecorded['estimate_seconds'] == 67
    weights['tests/test_new.py'] = -1
    (repo / affected.DURATIONS).write_text(json.dumps(weights))
    with pytest.raises(ValueError, match='invalid recorded duration'):
        affected.plan(base, candidate)
    weights['tests/test_new.py'] = 1
    (repo / affected.DURATIONS).write_text(json.dumps(weights))
    (repo / 'tests/conftest.py').write_text('# changed infrastructure\n')
    _git(repo, 'add', 'tests/conftest.py')
    _git(repo, *ident, 'commit', '-qm', 'infrastructure')
    infrastructure = _git(repo, 'rev-parse', 'HEAD')
    assert affected.plan(base, infrastructure)['reason'] == 'pytest infrastructure changed'
    for unsafe in ('../tests/test_bad.py', '/tests/test_bad.py', 'tests/../test_bad.py',
                   'tests//test_bad.py', 'tests/test_\n.py', 'tests/test_\u202e.py', 'tests/test_a::b.py', 'tests/test_a\\b.py'):
        with pytest.raises(ValueError, match='unsafe repository path'):
            affected.safe_path(unsafe)
    (repo / affected.GUARDS).write_text('\n'.join([*guards, guards[0]]) + '\n')
    with pytest.raises(ValueError, match='duplicate guard'):
        affected.plan(base, candidate)
    (repo / affected.GUARDS).write_text('tests/test_absent.py\n')
    with pytest.raises(ValueError, match='tracked regular file'):
        affected.plan(base, candidate)
    (repo / affected.GUARDS).write_text('\n'.join(guards) + '\n')
    (repo / guards[0]).unlink()
    (repo / guards[0]).symlink_to(repo / guards[1])
    with pytest.raises(ValueError, match='symlinked test path'):
        affected.plan(base, candidate)
