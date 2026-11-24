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
from lu_machinery.ci import pytest_report
from lu_machinery.ci.split_tests import assign, read_list

from tests.conftest import LU_PYTEST_SHARD_FILES_ENV_VAR, _load_shard_allowlist, pytest_ignore_collect

pytestmark = pytest.mark.usefixtures("_clear_allowlist_cache")

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github" / "workflows" / "ci.yml"


# =============================================================================
# scripts/ci/split_tests.py
# =============================================================================

_FILES = [f"tests/test_{name}.py" for name in "abcdefghij"]


def test_committed_history_list_names_tracked_test_files() -> None:
    listed = read_list(_REPO_ROOT / "scripts/ci/history-tests.txt")
    assert listed and len(listed) == len(set(listed))
    for name in listed:
        assert re.fullmatch(r"tests/(?:.+/)?test_[^/]+\.py", name), name
        assert (_REPO_ROOT / name).is_file(), name


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
    owners = [shard for shard in assign(paths, durations, 16, read_list(_REPO_ROOT / "scripts/ci/history-tests.txt")) if target in shard]
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
    nested = "tests/test_secret_redaction.py::test_xdist_redacts_parameter_ids_without_breaking_worker_routing"
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


# =============================================================================
# .github/workflows/ci.yml wiring
# =============================================================================


def _jobs_of_ci() -> dict:
    return yaml.safe_load(_CI.read_text(encoding="utf-8"))["jobs"]


def _run_pytest_script() -> str:
    return next(step["run"] for step in _jobs_of_ci()["pytest"]["steps"] if step.get("name") == "Run pytest")


def test_pytest_job_runs_the_full_non_slow_tier_through_the_split() -> None:
    script = _run_pytest_script()
    assert '.venv/bin/python -m lu_machinery.ci.split_tests split --shard "$SHARD" --of "$SHARDS"' in script
    assert "lu_machinery.ci.split_tests duration-source" in script
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
    assert "lu_machinery.ci.pg_skip_guard" in script
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
    report_step = next(step for step in steps if "lu_machinery.ci.pytest_report" in str(step.get("run", "")))
    # The audit record identifies the exact candidate and run.
    assert report_step["env"] == {"PR_NUMBER": "${{ github.event.pull_request.number }}"}
    assert any(step.get("with", {}).get("name") == "ci-tested-tree" for step in steps)


def test_pytest_is_skipped_only_on_pull_requests() -> None:
    jobs = _jobs_of_ci()
    assert "reuse" not in jobs
    assert jobs["pytest"]["needs"] == ["pr-scope", "refresh-pytest-durations", "hydrate-release-assets"]
    # A PR runs them only when pr-scope reports that it changes pytest infrastructure.
    for name in ("pytest", "refresh-pytest-durations"):
        assert jobs[name]["if"] == "${{ !cancelled() && (github.event_name != 'pull_request' || needs.pr-scope.outputs.full-suite == 'true') }}"
    assert jobs["frontend"]["if"] == "${{ !cancelled() }}"
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
    assert "lu_machinery.ci.gate --record-queue" in record["run"]
    upload = next(step for step in steps if step.get("with", {}).get("name") == "ci-queue-candidate")
    assert upload["with"]["if-no-files-found"] == "error"
    assert steps.index(record) < steps.index(upload) < steps.index(metadata)
    assert checkout["with"] == {
        "persist-credentials": False,
        "fetch-depth": 0,
        "filter": "blob:none",
        "sparse-checkout": "uv.lock\n.github/actions/python-ci-env/action.yml\n.python-version\n",
        "sparse-checkout-cone-mode": False,
    }
    assert metadata["id"] == "metadata"
    assert "python3 -m lu_machinery.ci.metadata_commit --commit HEAD" in metadata["run"]
    full_scan = next(step for step in _jobs_of_ci()["secret-scan"]["steps"] if "trufflehog" in step.get("uses", ""))
    assert scan["uses"] == full_scan["uses"]
    assert scan["with"] == {
        "image": full_scan["with"]["image"],
        "version": full_scan["with"]["version"],
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
    # The one exception is the shard upload's first attempt: the artifact service sometimes
    # never answers, and that hang alone must not eject a green shard. It stays safe only
    # while the very next step repeats the upload without continue-on-error, so a lost
    # artifact still fails the shard; a retry that drifts or goes missing fails here.
    assert [(job_id, step.get("id")) for job_id, step in optional] == [("pytest", "junit-upload")]
    steps = _jobs_of_ci()["pytest"]["steps"]
    first = optional[0][1]
    retry = steps[steps.index(first) + 1]
    assert first["continue-on-error"] is True
    assert retry["name"] == f"{first['name']} (retry)"
    assert "continue-on-error" not in retry
    assert retry["if"] == "${{ always() && steps.junit-upload.outcome == 'failure' }}"
    assert retry["uses"] == first["uses"]
    assert retry["with"] == first["with"]
    assert retry["with"]["overwrite"] is True
    assert retry["with"]["if-no-files-found"] == "error"
    assert first["timeout-minutes"] <= retry["timeout-minutes"]
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


def _count_parses(monkeypatch: pytest.MonkeyPatch) -> list[bytes]:
    import ast

    parsed: list[bytes] = []
    real = ast.parse
    monkeypatch.setattr(ast, 'parse', lambda source, *args, **kwargs: parsed.append(source) or real(source, *args, **kwargs))
    return parsed
