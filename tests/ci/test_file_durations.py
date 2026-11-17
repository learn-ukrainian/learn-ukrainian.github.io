"""Timing refresh changes weights, while preserving the full file partition."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from lu_machinery.ci import split_tests as split

from tests.test_ci_pr_triggers import _EVENTS, _run_gate, _simulate


def _workflow_jobs() -> dict:
    workflow = Path(__file__).resolve().parents[2] / ".github/workflows/ci.yml"
    return yaml.safe_load(workflow.read_text())["jobs"]


def _run_script(
    script: str, cwd: Path, *, extra_env: dict[str, str] | None = None, path_prefix: Path | None = None
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(extra_env or {})
    if path_prefix is not None:
        env["PATH"] = str(path_prefix) + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        ["bash", "-euo", "pipefail", "-c", script],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=env,
    )


def test_workflow_refreshes_one_snapshot_and_publishes_after_partition_proof() -> None:
    jobs = _workflow_jobs()
    assert "freeze-durations" not in jobs
    refresh = jobs["refresh-pytest-durations"]
    assert "reuse" not in jobs
    assert refresh["needs"] == ["pr-scope"]
    full = "${{ !cancelled() && (github.event_name != 'pull_request' || needs.pr-scope.outputs.full-suite == 'true') }}"
    assert refresh["if"] == full
    assert refresh["timeout-minutes"] == 10
    assert refresh["permissions"] == {"contents": "read", "actions": "read"}
    refresh_steps = [step.get("run", "") for step in refresh["steps"]]
    assert sum("split_tests refresh" in step for step in refresh_steps) == 1
    assert sum(
        "split_tests refresh" in step.get("run", "") for job in jobs.values() for step in job.get("steps", [])
    ) == 1
    upload = next(step for step in refresh["steps"] if str(step.get("uses", "")).startswith("actions/upload-artifact@"))
    assert upload["with"]["name"] == "pytest-duration-input"
    assert upload["with"]["path"] == "ci-artifacts/pytest-file-durations.json"
    pytest_job = jobs["pytest"]
    assert pytest_job["needs"] == ["pr-scope", "refresh-pytest-durations", "hydrate-release-assets"]
    assert pytest_job["if"] == full
    assert pytest_job["timeout-minutes"] == 15
    assert pytest_job["strategy"]["matrix"]["shard"] == list(range(1, 25))
    # The same-run snapshot comes through actions/download-artifact, which needs no token scope.
    assert pytest_job["permissions"] == {"contents": "read"}
    steps = pytest_job["steps"]
    decide = next(step for step in steps if step.get("name") == "Decide pytest duration source")
    download = next(step for step in steps if step.get("name") == "Download pytest duration snapshot")
    validate = next(step for step in steps if step.get("name") == "Validate pytest duration snapshot")
    run_pytest = next(step for step in steps if step.get("name") == "Run pytest")
    assert "matrix" not in decide["run"] + validate["run"]
    assert "::notice::" in decide["run"]
    assert "committed) echo" in decide["run"] and f"{split.SOURCE_SNAPSHOT})" in decide["run"]
    assert "duration-source --refresh-result" in decide["run"]
    assert "--decide" in decide["run"]
    only_snapshot = f"steps.duration-source.outputs.decision == '{split.SOURCE_SNAPSHOT}'"
    assert decide["id"] == "duration-source"
    assert download["if"] == only_snapshot
    assert validate["if"] == only_snapshot
    # REST-free: a same-run artifact through the action, never `gh run download` (a 403 rate limit
    # on 24 shards x 3 attempts failed CI). The action pin matches the report job's.
    assert str(download["uses"]).startswith("actions/download-artifact@")
    assert download["uses"] == next(
        step["uses"] for step in jobs["pytest-report"]["steps"] if str(step.get("uses", "")).startswith("actions/download-artifact@")
    )
    assert download["with"] == {"name": "pytest-duration-input", "path": "ci-artifacts/pytest-duration-input"}
    assert not {"github-token", "run-id", "repository"} & set(download["with"])
    # The shards take the run's one hydrated manifest as an artifact; no step holds a token.
    for step in steps:
        assert "gh run download" not in step.get("run", "")
        assert "GH_TOKEN" not in step.get("env", {})
    for step in (decide, download, validate):
        assert "continue-on-error" not in step
    assert validate["env"]["REFRESH_RESULT"] == "${{ needs.refresh-pytest-durations.result }}"
    assert decide["env"]["REFRESH_RESULT"] == "${{ needs.refresh-pytest-durations.result }}"
    old_fallback = "duration snapshot unavailable or invalid; using committed weights"
    assert old_fallback not in decide["run"] + validate["run"]
    assert old_fallback not in run_pytest["run"]
    assert "duration-source" in run_pytest["run"]
    assert 'validate "$snapshot"' not in run_pytest["run"]
    assert "GH_TOKEN" not in run_pytest["env"]
    assert steps.index(decide) < steps.index(download) < steps.index(validate) < steps.index(run_pytest)
    report = jobs["pytest-report"]
    assert report["needs"] == ["pytest"]
    assert report["if"] == "${{ !cancelled() && needs.pytest.result == 'success' }}"
    report_steps = report["steps"]
    proof = next(i for i, step in enumerate(report_steps) if "lu_machinery.ci.pytest_report" in step.get("run", ""))
    record = next(i for i, step in enumerate(report_steps) if step.get("name") == "Record pytest durations")
    assert proof < record
    assert "split_tests durations --shards ci-artifacts/shards" in report_steps[record]["run"]
    assert '--weights-out "ci-artifacts/pytest-shard-${SHARD}-weights.json"' in run_pytest["run"]
    shard_upload = next(step for step in pytest_job["steps"] if step.get("name") == "Upload pytest JUnit report")
    assert "ci-artifacts/pytest-shard-*-weights.json" in shard_upload["with"]["path"]
    report_upload = next(
        step for step in report_steps if step.get("with", {}).get("name") == "pytest-file-durations"
    )
    assert report_upload["with"]["name"] != upload["with"]["name"]
    gate = jobs["ci-gate"]
    assert gate["name"] == "CI Gate"
    assert gate["if"] == "always()"
    assert gate["timeout-minutes"] == 5
    assert "refresh-pytest-durations" in gate["needs"]
    verdict = next(step["run"] for step in gate["steps"] if step.get("name") == "Require every job")
    assert verdict.splitlines()[-1] == '"$PYTHON_BIN" -m lu_machinery.ci.gate'
    aggregation = next(step for step in gate["steps"] if step.get("name") == "Require every job")
    assert aggregation["env"]["NEEDS_JSON"] == "${{ toJSON(needs) }}"
    for event in ("merge_group", "schedule", "workflow_dispatch"):
        results, _ = _simulate(_EVENTS[event])
        assert all(results[name] == "success" for name in ("refresh-pytest-durations", "pytest", "pytest-report"))
    results, _ = _simulate(_EVENTS["merge_group"], failures={"pytest"})
    assert results["pytest-report"] == "skipped", "failed partition must not publish timing weights"
    result = _run_gate("merge_group", REFRESH="failure")
    assert result.returncode != 0, result.stdout
    assert "refresh-pytest-durations: failure, expected success" in result.stdout


def _selected_test_files() -> list[str]:
    files = split.tracked_test_files()
    assert files and len(files) == len(set(files))
    assert "tests/ci/test_file_durations.py" in files
    assert set(split.read_list(Path("scripts/ci/history-tests.txt"))) <= set(files)
    return files


def _assert_exact_partition(files: list[str], snapshot: Path) -> None:
    """Every shard reads these exact bytes, and the 16 shards cover files once."""
    payload = snapshot.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    durations = json.loads(payload)
    pinned = split.read_list(Path("scripts/ci/history-tests.txt"))
    text = "\n".join(files) + "\n"
    shards: list[list[str]] = []
    for number in range(1, 17):
        assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == digest
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lu_machinery.ci.split_tests",
                "split",
                "--shard",
                str(number),
                "--of",
                "16",
                "--durations",
                str(snapshot),
                "--history",
                "scripts/ci/history-tests.txt",
            ],
            input=text,
            text=True,
            capture_output=True,
            check=True,
            timeout=60,
        )
        shards.append([line for line in result.stdout.splitlines() if line])
    flat = [name for shard in shards for name in shard]
    assert sorted(flat) == sorted(files)
    assert len(flat) == len(set(flat)) == len(files)
    assert all(name in shards[0] for name in pinned)
    # Same bytes, same assignment, including files the snapshot does not name.
    assert shards == split.assign(files, durations, 16, pinned)


def test_tracked_test_files_match_the_workflow_selection() -> None:
    script = next(
        step["run"]
        for step in _workflow_jobs()["pytest"]["steps"]
        if step.get("name") == "Run pytest"
    )
    command = script[script.index("git ls-files") : script.index("| .venv/bin/python")]
    command = command.replace("\\\n", "\n").strip()
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["bash", "-c", command], cwd=root, capture_output=True, text=True, check=True, timeout=30
    )
    listed = [line for line in result.stdout.splitlines() if line]
    assert listed == split.tracked_test_files(root)


def test_lookup_fallback_snapshot_is_shared_and_covers_every_file_once(tmp_path: Path, monkeypatch) -> None:
    def unavailable(endpoint: str) -> bytes:
        raise subprocess.CalledProcessError(1, ["gh", "api", endpoint], stderr="private response")

    monkeypatch.setattr(split, "github_api", unavailable)
    snapshot = tmp_path / "fallback.json"
    assert split.refresh_durations("owner/repo", Path("scripts/ci/pytest-file-durations.json"), snapshot) == 0
    committed = json.loads(Path("scripts/ci/pytest-file-durations.json").read_text(encoding="utf-8"))
    assert json.loads(snapshot.read_text(encoding="utf-8")) == committed
    _assert_exact_partition(_selected_test_files(), snapshot)


def test_committed_weights_partition_every_selected_file_once() -> None:
    _assert_exact_partition(_selected_test_files(), Path("scripts/ci/pytest-file-durations.json"))


def test_refresh_job_shell_retains_committed_weights_when_refresh_fails(tmp_path: Path) -> None:
    script = next(
        step["run"]
        for step in _workflow_jobs()["refresh-pytest-durations"]["steps"]
        if "split_tests refresh" in step.get("run", "")
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "python3"
    fake.write_text(f"#!{sys.executable}\nimport sys\nraise SystemExit(1)\n")
    fake.chmod(0o755)
    root = Path(__file__).resolve().parents[2]
    work = tmp_path / "work"
    destination = work / "scripts" / "ci"
    destination.mkdir(parents=True)
    shutil.copyfile(root / "scripts/ci/pytest-file-durations.json", destination / "pytest-file-durations.json")
    result = _run_script(script, work, extra_env={"REPO": "owner/repo"}, path_prefix=bin_dir)
    produced = work / "ci-artifacts" / "pytest-file-durations.json"
    assert result.returncode == 0, result.stderr
    assert "::notice::duration refresh failed; retaining committed weights" in result.stdout
    assert produced.read_bytes() == (destination / "pytest-file-durations.json").read_bytes()


def test_refresh_job_shell_notices_a_lookup_fallback(tmp_path: Path) -> None:
    script = next(
        step["run"]
        for step in _workflow_jobs()["refresh-pytest-durations"]["steps"]
        if "split_tests refresh" in step.get("run", "")
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "python3"
    fake.write_text(
        f"#!{sys.executable}\n"
        "import sys\n"
        "from pathlib import Path\n"
        "args = sys.argv[1:]\n"
        "if 'validate' in args:\n"
        "    raise SystemExit(0)\n"
        "out = Path(args[args.index('--output') + 1])\n"
        "out.parent.mkdir(parents=True, exist_ok=True)\n"
        "out.write_text('{\"tests/test_a.py\": 1}\\n')\n"
        "print('duration lookup unavailable; retaining committed fallback', file=sys.stderr)\n"
        "raise SystemExit(0)\n"
    )
    fake.chmod(0o755)
    work = tmp_path / "work"
    work.mkdir()
    result = _run_script(script, work, extra_env={"REPO": "owner/repo"}, path_prefix=bin_dir)
    assert result.returncode == 0, result.stderr
    assert "::notice::duration lookup unavailable; retaining committed weights" in result.stdout
    assert json.loads((work / "ci-artifacts/pytest-file-durations.json").read_text()) == {"tests/test_a.py": 1}


def _pytest_step_script(name: str) -> str:
    script = next(step["run"] for step in _workflow_jobs()["pytest"]["steps"] if step.get("name") == name)
    return script.replace(".venv/bin/python", shlex.quote(sys.executable)).replace("python3", shlex.quote(sys.executable))


def _duration_env(refresh_result: str, output: Path) -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    return {"REFRESH_RESULT": refresh_result, "PYTHONPATH": str(root), "GITHUB_OUTPUT": str(output)}


def _shard_snapshot(work: Path, refresh_result: str, artifact: str | None) -> tuple[subprocess.CompletedProcess[str], ...]:
    """Run the three workflow steps in order, standing in for the action by writing its artifact.

    The download action extracts the one-file artifact into its ``path``; a real action failure
    stops the job before validation, which the caller models by passing ``artifact=None``.
    """
    output = work / "github-output"
    env = _duration_env(refresh_result, output)
    decided = _run_script(_pytest_step_script("Decide pytest duration source"), work, extra_env=env)
    results = [decided]
    if decided.returncode != 0 or "decision=snapshot" not in output.read_text():
        return tuple(results)
    if artifact is not None:
        target = work / "ci-artifacts/pytest-duration-input"
        target.mkdir(parents=True)
        (target / "pytest-file-durations.json").write_text(artifact)
    results.append(_run_script(_pytest_step_script("Validate pytest duration snapshot"), work, extra_env=env))
    return tuple(results)


def test_snapshot_steps_share_one_snapshot_across_shards(tmp_path: Path) -> None:
    """A successful refresh plus a successful download gives every shard the same bytes."""
    body = '{"tests/test_a.py": 4}\n'
    digests = []
    for number in range(1, 25):
        work = tmp_path / f"shard-{number}"
        work.mkdir()
        decided, validated = _shard_snapshot(work, "success", body)
        assert decided.returncode == 0, decided.stderr
        assert validated.returncode == 0, validated.stderr
        produced = work / "ci-artifacts/pytest-file-durations.json"
        assert produced.read_text() == body
        digests.append(hashlib.sha256(produced.read_bytes()).hexdigest())
    assert len(set(digests)) == 1


@pytest.mark.parametrize("result", ["failure", "skipped", "cancelled"])
def test_unsuccessful_refresh_uses_committed_weights_without_a_download(tmp_path: Path, result: str) -> None:
    (decided,) = _shard_snapshot(tmp_path, result, None)
    assert decided.returncode == 0, decided.stderr
    assert "::notice::duration refresh did not succeed; using committed weights" in decided.stdout
    assert (tmp_path / "github-output").read_text().strip() == f"decision={split.SOURCE_COMMITTED}"
    assert not (tmp_path / "ci-artifacts/pytest-file-durations.json").exists()


def test_unexpected_decision_fails_closed(tmp_path: Path) -> None:
    (decided,) = _shard_snapshot(tmp_path, "success\ncommitted", None)
    assert decided.returncode != 0
    assert not (tmp_path / "github-output").exists() or "decision=" not in (tmp_path / "github-output").read_text()


def test_refresh_success_fails_the_shard_whose_snapshot_is_missing(tmp_path: Path) -> None:
    """Old behaviour exited 0 and let this shard split on the committed weights."""
    results = _shard_snapshot(tmp_path, "success", None)
    assert results[0].returncode == 0
    # The action step fails when the artifact is missing, so the job stops before validation.
    # A validation that does run without a file must also fail rather than fall back.
    missing = _run_script(
        _pytest_step_script("Validate pytest duration snapshot"),
        tmp_path,
        extra_env=_duration_env("success", tmp_path / "github-output"),
    )
    assert missing.returncode != 0, missing.stdout
    assert "using committed weights" not in missing.stdout
    assert not (tmp_path / "ci-artifacts/pytest-file-durations.json").exists()
    # The shard stops here. It does not assign files from the committed weights.
    with pytest.raises(split.DurationSnapshotRequired):
        split.resolve_duration_path("success", tmp_path / "missing.json")


@pytest.mark.parametrize("body", ["{", '{"tests/test_a.py": true}', "[]"])
def test_invalid_snapshot_fails_the_shard(tmp_path: Path, body: str) -> None:
    decided, validated = _shard_snapshot(tmp_path, "success", body)
    assert decided.returncode == 0
    assert validated.returncode != 0
    assert "using committed weights" not in validated.stdout


def _run_pytest_duration_selection(snapshot: Path, refresh_result: str) -> subprocess.CompletedProcess[str]:
    """The Run pytest lines that choose weights, with this interpreter."""
    script = next(step["run"] for step in _workflow_jobs()["pytest"]["steps"] if step.get("name") == "Run pytest")
    selection = script[script.index("snapshot=") : script.index("git ls-files")]
    selection = selection.replace("ci-artifacts/pytest-file-durations.json", str(snapshot))
    selection = selection.replace(".venv/bin/python", shlex.quote(sys.executable)).replace("python3", shlex.quote(sys.executable))
    env = os.environ.copy()
    env["REFRESH_RESULT"] = refresh_result
    return subprocess.run(
        ["bash", "-e", "-c", selection + '\nprintf "%s" "$durations"'],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=env,
    )


@pytest.mark.parametrize("snapshot_data", [None, "{", "{}", "", '{"tests/test_x.py": false}'])
def test_run_pytest_fails_a_bad_snapshot_when_refresh_succeeded(tmp_path: Path, snapshot_data: str | None) -> None:
    snapshot = tmp_path / "snapshot.json"
    if snapshot_data is not None:
        snapshot.write_text(snapshot_data)
    result = _run_pytest_duration_selection(snapshot, "success")
    assert result.returncode != 0, result.stdout
    assert "scripts/ci/pytest-file-durations.json" not in result.stdout


def test_run_pytest_uses_one_valid_snapshot_when_refresh_succeeded(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text('{"tests/test_x.py": 5}')
    result = _run_pytest_duration_selection(snapshot, "success")
    assert result.returncode == 0, result.stderr
    assert result.stdout == str(snapshot)


@pytest.mark.parametrize("refresh_result", ["failure", "cancelled", "skipped"])
def test_refresh_did_not_succeed_uses_committed_weights_on_every_shard(
    tmp_path: Path, refresh_result: str
) -> None:
    """A present, different snapshot must not leak into any shard."""
    snapshot = tmp_path / "other.json"
    snapshot.write_text(json.dumps({"tests/test_a.py": 999999}) + "\n")
    chosen = [split.resolve_duration_path(refresh_result, snapshot) for _shard in range(16)]
    assert chosen == [Path("scripts/ci/pytest-file-durations.json")] * 16
    # The decision step announces the committed weights; the download and validate steps are skipped.
    work = tmp_path / "shard"
    work.mkdir()
    (decided,) = _shard_snapshot(work, refresh_result, None)
    assert decided.returncode == 0, decided.stderr
    assert "duration refresh did not succeed; using committed weights" in decided.stdout
    result = _run_pytest_duration_selection(snapshot, refresh_result)
    assert result.returncode == 0, result.stderr
    assert result.stdout == Path("scripts/ci/pytest-file-durations.json").as_posix()


def test_mixed_snapshot_and_committed_weights_cannot_be_selected(tmp_path: Path) -> None:
    """The reviewer's reproducer: shard 7 falls back, the other 15 use the snapshot.

    One changed weight makes those two assignments disagree, so mixing them
    skips files and runs others twice. The shared decision does not build that mix.
    """
    files = _selected_test_files()
    pinned = split.read_list(Path("scripts/ci/history-tests.txt"))
    committed = json.loads(Path("scripts/ci/pytest-file-durations.json").read_text(encoding="utf-8"))
    changed = dict(committed)
    name = min((name for name in files if name in changed and name not in pinned), key=changed.get)
    # The reviewer's reproducer moved one file by 1%. If rounding leaves the
    # assignment unchanged, a larger gap still makes the two maps disagree.
    changed[name] = round(float(committed[name]) * 1.01, 3)
    with_committed = split.assign(files, committed, 16, pinned)
    with_snapshot = split.assign(files, changed, 16, pinned)
    if with_snapshot == with_committed:
        changed[name] = float(committed[name]) + 100_000
        with_snapshot = split.assign(files, changed, 16, pinned)
    assert with_snapshot != with_committed
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps(changed) + "\n")
    missing = tmp_path / "missing.json"
    mixed = [with_committed[index] if index == 6 else with_snapshot[index] for index in range(16)]
    flat = [item for shard in mixed for item in shard]
    assert len(flat) != len(set(flat)) or set(flat) != set(files)

    selected: list[Path] = []
    for shard in range(1, 17):
        path = missing if shard == 7 else snapshot
        if shard == 7:
            with pytest.raises(split.DurationSnapshotRequired):
                split.resolve_duration_path("success", path)
            continue
        selected.append(split.resolve_duration_path("success", path))
    assert selected == [snapshot] * 15
    assert Path("scripts/ci/pytest-file-durations.json") not in selected
    # Fifteen shards of the snapshot are one assignment. The fallen shard adds nothing.
    assert [with_snapshot[index] for index in range(16) if index != 6] != mixed
