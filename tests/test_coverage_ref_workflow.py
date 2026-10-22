"""Prevent diagnostic coverage from changing the CI denominator or accepting moving refs."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = yaml.safe_load((ROOT / ".github/workflows/coverage-ref.yml").read_text())
CI = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())


def step(job, name):
    return next(item for item in job["steps"] if item.get("name") == name)


@pytest.mark.parametrize(
    "sha,valid",
    [
        ("a" * 40, True),
        ("B" * 40, True),
        ("main", False),
        ("a" * 39, False),
        ("g" * 40, False),
        ("a" * 40 + "\n", False),
        ("$(touch injected)", False),
    ],
)
def test_validation_rejects_moving_refs_and_shell_input(tmp_path, sha, valid):
    validate = step(WORKFLOW["jobs"]["prepare"], "Validate an exact repository commit")
    gh = tmp_path / "gh"
    gh.write_text(
        '#!/bin/bash\ncase "$*" in\n  *compare*) echo identical ;;\n  *) printf "%s\\n" "${SHA,,}" ;;\nesac\n'
    )
    gh.chmod(0o755)
    output = tmp_path / "output"
    env = os.environ | {
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "SHA": sha,
        "REPO": "test/repo",
        "GITHUB_OUTPUT": str(output),
    }
    result = subprocess.run(
        ["bash", "-c", validate["run"]], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10
    )
    assert (result.returncode == 0) is valid, result.stdout + result.stderr
    assert output.read_text() == f"validated_revision={sha.lower()}\n" if valid else not output.exists()
    assert not (tmp_path / "injected").exists()


def test_nonrepository_commit_fails_even_when_syntax_is_valid(tmp_path):
    gh = tmp_path / "gh"
    gh.write_text("#!/bin/bash\nexit 1\n")
    gh.chmod(0o755)
    env = os.environ | {
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "SHA": "a" * 40,
        "REPO": "test/repo",
        "GITHUB_OUTPUT": str(tmp_path / "output"),
    }
    result = subprocess.run(
        ["bash", "-c", WORKFLOW["jobs"]["prepare"]["steps"][0]["run"]],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert not (tmp_path / "output").exists()


def test_ci_partition_and_pytest_denominator_are_unchanged():
    """Detect marker/option/file-split drift that would silently measure a smaller suite."""
    baseline = CI["jobs"]["pytest"]
    measured = WORKFLOW["jobs"]["pytest"]
    assert measured["strategy"] == baseline["strategy"]
    before = step(baseline, "Run pytest")["run"]
    after = step(measured, "Run CI pytest suite with branch coverage")["run"]
    assert (
        before[before.index("git ls-files") : before.index(".venv/bin/python -m pytest")]
        == after[after.index("git ls-files") : after.index('.venv/bin/python "$RUNNER_TEMP')]
    )
    original = shlex.split(
        before[before.index(".venv/bin/python -m pytest") : before.index("# Postgres")].replace("\\\n", "")
    )
    instrumented = shlex.split(
        after[after.index('.venv/bin/python "$RUNNER_TEMP') : after.index("# Postgres")].replace("\\\n", "")
    )
    instrumented = instrumented[instrumented.index("--") + 1 :]
    # Coverage needs 5x the wall-clock budget (#11226); selection and all other
    # pytest options must still match CI. Pin both budgets before normalizing.
    assert original.count("--timeout=120") == 1
    assert instrumented.count("--timeout=600") == 1
    # A signal timeout reports a test failure and lets coverage save. The thread
    # method calls os._exit(), losing that worker and its remaining tests.
    assert original.count("--timeout-method=thread") == 1
    assert instrumented.count("--timeout-method=signal") == 1
    normalization = {"--timeout=600": "--timeout=120", "--timeout-method=signal": "--timeout-method=thread"}
    assert [normalization.get(arg, arg) for arg in instrumented if not arg.startswith("--cov")] == original[3:]
    assert (
        step(measured, "Download pytest duration snapshot")["run"]
        == step(baseline, "Download pytest duration snapshot")["run"]
    )
    assert measured["timeout-minutes"] > baseline["timeout-minutes"]
    assert measured["env"]["PYTEST_XDIST_AUTO_NUM_WORKERS"] == "2"
    assert "PYTEST_XDIST_AUTO_NUM_WORKERS" not in baseline.get("env", {})
    startup = step(measured, "Isolate coverage storage from import-smoke guards")
    assert startup["run"] == '.venv/bin/python "$RUNNER_TEMP/coverage-ref/coverage_ref_environment.py"'


@pytest.mark.parametrize(
    "comparison,allowed", [("ahead", True), ("identical", True), ("behind", False), ("diverged", False), ("", False)]
)
def test_pull_only_commits_are_rejected_unless_reachable_from_own_branch(tmp_path, comparison, allowed):
    """The commit API resolving a fork PR head must not authorize its execution."""
    gh = tmp_path / "gh"
    gh.write_text(
        '#!/bin/bash\ncase "$*" in\n'
        '  *branches*) printf "%040d\\n" 1 ;;\n'
        '  *compare*) printf "%s\\n" "$COMPARISON" ;;\n'
        '  *) printf "%s\\n" "$SHA" ;;\nesac\n'
    )
    gh.chmod(0o755)
    output = tmp_path / "output"
    env = os.environ | {
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "SHA": "a" * 40,
        "REPO": "test/repo",
        "GITHUB_OUTPUT": str(output),
        "COMPARISON": comparison,
    }
    result = subprocess.run(
        ["bash", "-c", step(WORKFLOW["jobs"]["prepare"], "Validate an exact repository commit")["run"]],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert (result.returncode == 0) is allowed, result.stderr
    assert output.exists() is allowed


def test_diagnostic_workflow_cannot_save_uv_or_npm_caches_even_for_old_commits():
    """A main dispatch must never save caches modified by measured code."""
    job = WORKFLOW["jobs"]["pytest"]
    tooling = step(job, "Check out measurement tooling")
    assert tooling["with"]["ref"] == "${{ github.workflow_sha }}"
    assert tooling["with"]["path"] == "coverage-tooling"
    action = step(job, "Python CI environment")
    assert action["uses"] == "./coverage-tooling/.github/actions/python-ci-env"
    assert action["with"]["save-cache"] is False
    for job in WORKFLOW["jobs"].values():
        for item in job["steps"]:
            assert not str(item.get("uses", "")).startswith("actions/cache@")
            if str(item.get("uses", "")).startswith("actions/setup-node@"):
                assert "cache" not in item.get("with", {})
                assert item["with"]["package-manager-cache"] is False


def test_workflow_is_manual_and_uploads_hidden_data_even_after_failure():
    assert WORKFLOW["on"] == {
        "workflow_dispatch": {
            "inputs": {
                "sha": {
                    "description": "Repository commit SHA to measure (40 hexadecimal characters)",
                    "required": True,
                    "type": "string",
                }
            }
        }
    }
    raw = step(WORKFLOW["jobs"]["pytest"], "Upload raw branch coverage and receipt")
    assert raw["if"] == "${{ always() }}"
    assert raw["with"]["include-hidden-files"] is True
    assert raw["with"]["if-no-files-found"] == "error"
    merge = WORKFLOW["jobs"]["combine"]
    assert merge["if"] == "${{ always() }}"
    assert set(merge["needs"]) == {"prepare", "pytest"}
    assert "continue-on-error" not in step(merge, "Validate receipts, combine and report")


def test_prepare_failure_keeps_tooling_and_dependency_lock_available_for_manifest():
    """A skipped target checkout must not remove the interpreter pin or coverage installer."""
    job = WORKFLOW["jobs"]["combine"]
    sources = step(job, "Check out measured sources for JSON reporting")
    assert "if" not in sources
    assert sources["with"]["ref"] == "${{ needs.prepare.outputs.validated_revision || github.workflow_sha }}"
    for name in ("pytest", "combine"):
        job = WORKFLOW["jobs"][name]
        tooling = step(job, "Check out measurement tooling")
        assert tooling["with"]["path"] == "coverage-tooling"
        assert tooling["with"]["ref"] == "${{ github.workflow_sha }}"
        if name == "pytest":
            assert {".python-version", "scripts/__init__.py"} <= set(tooling["with"]["sparse-checkout"].splitlines())
            assert tooling["with"]["sparse-checkout-cone-mode"] is False
        else:
            assert "sparse-checkout" not in tooling["with"]
        assert job["steps"].index(tooling) > next(
            i
            for i, item in enumerate(job["steps"])
            if item.get("with", {}).get("ref") != "${{ github.workflow_sha }}"
            and str(item.get("uses", "")).startswith("actions/checkout@")
        )
