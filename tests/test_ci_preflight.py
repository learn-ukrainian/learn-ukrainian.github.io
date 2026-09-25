"""Pin the early PR preflight job (#8750, phase A).

Preflight runs the ``repo_wide`` set (#8707) plus a short registered list of
other invariants on pull_request only, in parallel with the pytest shards.
The shards still run the same tests, so preflight only moves a red signal
earlier; CI Gate requires it exactly when Changes scheduled it (the gate rule
itself is exercised in tests/test_ci_pr_triggers.py).
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github" / "workflows" / "ci.yml"
_REPO_WIDE_FLAGS = (
    "-m 'repo_wide and not slow and not atlas_release' --strict-markers "
    "-n logical --dist=loadfile --max-worker-restart=0 --timeout=120 "
    "--timeout-method=thread --override-ini addopts=-v"
)


def _jobs() -> dict:
    return yaml.safe_load(_CI.read_text(encoding="utf-8"))["jobs"]


def _needs(job: dict) -> list[str]:
    needs = job.get("needs") or []
    return [needs] if isinstance(needs, str) else list(needs)


def _step(job: dict, name: str) -> dict:
    matches = [step for step in job["steps"] if step.get("name") == name]
    assert len(matches) == 1, f"expected one step named {name!r}"
    return matches[0]


def _flat(script: str) -> str:
    """Join shell line continuations and collapse whitespace."""
    return " ".join(script.replace("\\\n", " ").split())


def _preflight_script() -> str:
    return _step(_jobs()["preflight"], "Run preflight pytest")["run"]


def _registered_extras() -> list[str]:
    raw = _jobs()["preflight"]["env"]["PREFLIGHT_EXTRA_TESTS"]
    return [line.strip() for line in raw.splitlines() if line.strip()]


def test_preflight_job_reads_the_single_changes_decision() -> None:
    jobs = _jobs()
    preflight = jobs["preflight"]
    assert _needs(preflight) == ["changes"]
    assert preflight["if"] == "needs.changes.outputs.preflight == 'true'"
    assert jobs["changes"]["outputs"]["preflight"] == "${{ steps.classify.outputs.preflight }}"
    # Nothing else re-derives the decision from event names or other outputs.
    assert "github.event_name" not in str(preflight["if"])
    assert preflight["timeout-minutes"] <= 10


def test_preflight_gates_nothing_but_ci_gate() -> None:
    jobs = _jobs()
    dependants = sorted(job_id for job_id, job in jobs.items() if "preflight" in _needs(job))
    assert dependants == ["ci-gate"]
    assert "preflight" not in _needs(jobs["pytest"])


def test_preflight_skips_postgres_npm_and_native_deps() -> None:
    preflight = _jobs()["preflight"]
    assert "services" not in preflight
    uses = [step.get("uses", "") for step in preflight["steps"]]
    assert not any("setup-node" in action for action in uses)
    text = yaml.safe_dump(preflight)
    for needle in ("npm ", "apt-get", "LEARN_UKRAINIAN_CP_PG_DSN", "postgres"):
        assert needle not in text, needle


def test_preflight_installs_python_like_the_shards() -> None:
    jobs = _jobs()

    def commands(job: dict) -> list[str]:
        script = _step(job, "Install Python deps")["run"]
        return [line.strip() for line in script.splitlines() if line.strip() and not line.strip().startswith("#")]

    assert commands(jobs["preflight"]) == commands(jobs["pytest"])


def test_preflight_uses_the_shard_repo_wide_allowlist_and_flags() -> None:
    shard = _flat(_step(_jobs()["pytest"], "Run pytest")["run"])
    preflight = _flat(_preflight_script())
    allowlist = (
        "git ls-files -- tests | grep -E '/test_[^/]+\\.py$' | xargs -r grep -lE "
        "'pytest\\.mark\\.repo_wide' | sort > \"$repo_wide_list\" || true"
    )
    empty_guard = '[ -s "$repo_wide_list" ] || { echo "no repo_wide tests found'
    for fragment in (allowlist, empty_guard, _REPO_WIDE_FLAGS):
        assert fragment in shard, fragment
        assert fragment in preflight, fragment


def test_registered_extra_tests_exist_and_are_not_repo_wide() -> None:
    extras = _registered_extras()
    assert extras, "PREFLIGHT_EXTRA_TESTS is empty; the step would fail"
    assert len(extras) == len(set(extras))
    for path in extras:
        target = _REPO_ROOT / path
        assert re.fullmatch(r"tests/(?:[^/]+/)*test_[^/]+\.py", path), path
        assert target.is_file(), f"registered preflight test is missing: {path}"
        # A repo_wide file already runs in the first invocation.
        assert "pytest.mark.repo_wide" not in target.read_text(encoding="utf-8"), path


def _run_preflight_script(tmp_path: Path, files: dict[str, str], extras: str, python: str) -> subprocess.CompletedProcess[str]:
    """Run the real step script in a scratch git repo with a stub interpreter."""
    repo = tmp_path / "repo"
    for rel, text in files.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(text, encoding="utf-8")
    stub = repo / ".venv" / "bin" / "python"
    stub.parent.mkdir(parents=True)
    stub.write_text(python, encoding="utf-8")
    stub.chmod(0o755)
    subprocess.run(["git", "init", "-q", str(repo)], check=True, timeout=30)
    subprocess.run(["git", "-C", str(repo), "add", "tests"], check=True, timeout=30)
    runner_temp = tmp_path / "runner"
    runner_temp.mkdir()
    return subprocess.run(
        ["bash", "-c", _preflight_script()],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "RUNNER_TEMP": str(runner_temp), "PREFLIGHT_EXTRA_TESTS": extras},
        timeout=60,
    )


_RECORDING_PYTHON = '#!/usr/bin/env bash\necho "pytest $LU_PYTEST_SHARD_FILES" >> "$RUNNER_TEMP/calls"\nexit 0\n'


def test_preflight_step_fails_loudly_on_an_empty_repo_wide_allowlist(tmp_path: Path) -> None:
    result = _run_preflight_script(
        tmp_path,
        {"tests/test_plain.py": "def test_x():\n    pass\n"},
        "tests/test_plain.py\n",
        _RECORDING_PYTHON,
    )
    assert result.returncode == 1
    assert "no repo_wide tests found" in result.stderr
    assert not (tmp_path / "runner" / "calls").exists(), "pytest must not start on an empty allowlist"


def test_preflight_step_fails_loudly_on_an_empty_extra_list(tmp_path: Path) -> None:
    result = _run_preflight_script(
        tmp_path,
        {"tests/test_scan.py": "import pytest\n\n@pytest.mark.repo_wide\ndef test_x():\n    pass\n"},
        "\n  \n",
        _RECORDING_PYTHON,
    )
    assert result.returncode == 1
    assert "PREFLIGHT_EXTRA_TESTS is empty" in result.stderr


@pytest.mark.parametrize("failing_call", [1, 2])
def test_preflight_step_runs_both_sets_and_fails_if_either_fails(tmp_path: Path, failing_call: int) -> None:
    python = (
        "#!/usr/bin/env bash\n"
        'echo "$LU_PYTEST_SHARD_FILES" >> "$RUNNER_TEMP/calls"\n'
        f'[ "$(wc -l < "$RUNNER_TEMP/calls")" -ne {failing_call} ]\n'
    )
    result = _run_preflight_script(
        tmp_path,
        {
            "tests/test_scan.py": "import pytest\n\n@pytest.mark.repo_wide\ndef test_x():\n    pass\n",
            "tests/test_extra.py": "def test_y():\n    pass\n",
        },
        "tests/test_extra.py\n",
        python,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    calls = (tmp_path / "runner" / "calls").read_text(encoding="utf-8").splitlines()
    runner = tmp_path / "runner"
    assert calls == [
        str(runner / "pytest-repo-wide-files.txt"),
        str(runner / "pytest-preflight-extra-files.txt"),
    ]
    assert (runner / "pytest-repo-wide-files.txt").read_text(encoding="utf-8") == "tests/test_scan.py\n"
    assert (runner / "pytest-preflight-extra-files.txt").read_text(encoding="utf-8") == "tests/test_extra.py\n"
