"""Guard the CI install's cache fallback and fail-closed dependency check."""

import os
import subprocess
import sys
from pathlib import Path
from subprocess import CompletedProcess

import pytest
import yaml

from scripts.audit import check_ci_dependencies
from scripts.audit.check_ci_dependencies import unexpected_diagnostics

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github/workflows/ci.yml"
_WARM = _REPO_ROOT / ".github/workflows/uv-cache-warm.yml"
_ACTION = _REPO_ROOT / ".github/actions/python-ci-env/action.yml"


def test_main_push_publishes_the_uv_cache_merge_group_can_read() -> None:
    # #9095: merge_group restores only a cache saved on the default branch.
    # setup-uv matches the requirements-lock.txt key exactly. Since #9101 only
    # refs/heads/main saves, so PR runs stop writing ~447 MiB private entries.
    # The warm workflow is the writer.
    workflow = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    pytest_steps = workflow["jobs"]["pytest"]["steps"]
    action = yaml.safe_load(_ACTION.read_text(encoding="utf-8"))
    uv = next(step for step in action["runs"]["steps"] if step.get("name") == "Set up uv")
    assert action["inputs"]["save-cache"]["default"] == "${{ github.ref == 'refs/heads/main' && 'true' || 'false' }}"
    assert uv["with"]["save-cache"] == "${{ inputs.save-cache }}"
    assert uv["id"] == "setup-uv"
    assert action["outputs"]["uv-cache-key"]["value"] == "${{ steps.setup-uv.outputs.cache-key }}"
    assert uv["with"]["enable-cache"] is True
    assert uv["with"]["cache-dependency-glob"] == "requirements-lock.txt\nrequirements-machinery.lock\n"
    assert uv["with"].get("prune-cache", False) is False

    warm = yaml.safe_load(_WARM.read_text(encoding="utf-8"))
    triggers = warm.get("on", warm.get(True))
    assert triggers["push"] == {
        "branches": ["main"],
        "paths": [
            "requirements-lock.txt",
            "requirements-machinery.lock",
            ".python-version",
            ".github/actions/python-ci-env/**",
            ".github/workflows/uv-cache-warm.yml",
        ],
    }
    assert "pull_request" not in triggers
    assert "merge_group" not in triggers
    assert triggers["schedule"] == [{"cron": "30 4 * * *"}]
    assert warm["permissions"] == {"contents": "read"}
    assert warm["concurrency"]["cancel-in-progress"] is False
    assert warm["env"]["UV_HTTP_RETRIES"] == workflow["env"]["UV_HTTP_RETRIES"]
    assert warm["env"]["PIP_RETRIES"] == workflow["env"]["PIP_RETRIES"]

    job = warm["jobs"]["warm"]
    assert job["runs-on"] == workflow["jobs"]["pytest"]["runs-on"]
    assert job["timeout-minutes"] == 15
    checkout = next(
        step for step in job["steps"] if str(step.get("uses", "")).startswith("actions/checkout@")
    )
    ci_checkout = next(
        step for step in pytest_steps if str(step.get("uses", "")).startswith("actions/checkout@")
    )
    assert checkout["uses"] == ci_checkout["uses"]
    assert checkout["with"]["persist-credentials"] is False
    setup = next(
        step for step in job["steps"] if str(step.get("uses", "")).startswith("actions/setup-python@")
    )
    ci_setup = next(
        step for step in pytest_steps if str(step.get("uses", "")).startswith("actions/setup-python@")
    )
    assert setup["uses"] == ci_setup["uses"]
    assert setup["with"] == {"python-version-file": ".python-version"}
    ci_env = next(step for step in job["steps"] if step.get("uses") == "./.github/actions/python-ci-env")
    assert job["outputs"]["uv-cache-key"] == f"${{{{ steps.{ci_env['id']}.outputs.uv-cache-key }}}}"


def test_warm_workflow_fails_loudly_when_main_has_no_uv_entry() -> None:
    # #9101: after the save (setup-uv's post step, so a later job) main must
    # hold the exact key for the current lock, or the run goes red.
    warm = yaml.safe_load(_WARM.read_text(encoding="utf-8"))
    verify = warm["jobs"]["verify"]
    assert verify["needs"] == "warm"
    assert verify["permissions"] == {"actions": "read"}
    assert verify["env"]["UV_CACHE_KEY"] == "${{ needs.warm.outputs.uv-cache-key }}"
    script = verify["steps"][0]["run"]
    assert "gh cache list --ref refs/heads/main --key" in script
    assert "grep -Fx" in script
    assert "exit 1" in script
    assert "gh cache delete" not in script


def test_only_exact_filtered_ml_omission_is_allowed() -> None:
    known = "accelerate 1.14.0 requires torch, which is not installed."
    skew = (
        "pydantic 2.13.5 has requirement pydantic-core==2.46.5, "
        "but you have pydantic-core 2.46.4."
    )
    assert unexpected_diagnostics(known) == []
    assert unexpected_diagnostics(known + "\n" + skew) == [skew]
    # A routine version bump of an allowed requiring package still passes.
    assert unexpected_diagnostics(known.replace("accelerate 1.14.0", "accelerate 1.14.1")) == []
    # A new missing dependency of an allowed package, or a new package, fails.
    new_dependency = "accelerate 1.14.0 requires narwhals, which is not installed."
    assert unexpected_diagnostics(new_dependency) == [new_dependency]
    new_package = "scikit-learn 1.9.1 requires torch, which is not installed."
    assert unexpected_diagnostics(new_package) == [new_package]
    # A version conflict on an allowed pair is never an intentional omission.
    allowed_pair_conflict = "accelerate 1.14.0 has requirement torch>=2, but you have torch 1.0."
    assert unexpected_diagnostics(allowed_pair_conflict) == [allowed_pair_conflict]
    stale_conflict = "httpx2 2.12.0 has requirement httpcore2==2.12.0, but you have httpcore2 2.10.0."
    assert unexpected_diagnostics(stale_conflict) == [stale_conflict]
    assert unexpected_diagnostics("unrecognized pip diagnostic") == [
        "unrecognized pip diagnostic"
    ]


def test_dependency_check_fails_on_pydantic_skew(monkeypatch, capsys) -> None:
    skew = (
        "pydantic 2.13.5 has requirement pydantic-core==2.46.5, "
        "but you have pydantic-core 2.46.4."
    )
    monkeypatch.setattr(
        check_ci_dependencies.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcess(args, 1, skew, ""),
    )
    assert check_ci_dependencies.main() == 1
    assert skew in capsys.readouterr().err


def test_dependency_check_fails_on_empty_pip_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        check_ci_dependencies.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcess(args, 1, "", ""),
    )
    assert check_ci_dependencies.main() == 1


def _shared_pin_step() -> str:
    """The run script of the dependency-audit job's shared-pin step."""
    workflow = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    step = next(
        step
        for step in workflow["jobs"]["dependency-audit"]["steps"]
        if step.get("name") == "Check shared pins with the machinery lock"
    )
    assert "if" not in step  # runs on every event, before the scope cheap-exit
    return step["run"]


def _shared_pin_check() -> str:
    """The step's inline Python."""
    return _shared_pin_step().split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]


def _run_shared_pin_check(product: Path, machinery: Path, dependabot: Path):
    return subprocess.run(
        [sys.executable, "-I", "-", str(product), str(machinery), str(dependabot)],
        input=_shared_pin_check(),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def test_shared_pin_check_accepts_the_repository_locks() -> None:
    result = _run_shared_pin_check(
        _REPO_ROOT / "requirements-lock.txt",
        _REPO_ROOT / "requirements-machinery.lock",
        _REPO_ROOT / ".github/dependabot.yml",
    )
    assert result.returncode == 0, result.stdout + result.stderr


_MACHINERY_LOCK = (
    "lu-machinery==0.1.25 \\\n    --hash=sha256:" + "a" * 64 + "\n"
    "pluggy==1.6.0 \\\n    --hash=sha256:" + "b" * 64 + "\n"
    "PyJWT==2.15.0 \\\n    --hash=sha256:" + "c" * 64 + "\n"
)
_IGNORE_BOTH = (
    'version: 2\nupdates:\n  - package-ecosystem: "pip"\n    directory: "/"\n'
    '    ignore:\n      - dependency-name: "pluggy"\n      - dependency-name: "pyjwt"\n'
)


@pytest.mark.parametrize(
    ("product_lock", "dependabot", "expected"),
    [
        # Dependabot #13086/#13088 class: a shared package pinned differently.
        ("pluggy==1.7.0\npyjwt==2.15.0\n", _IGNORE_BOTH, "pluggy: "),
        # A shared package Dependabot may still bump: missing, version-filtered,
        # or spelled other than the canonical name.
        ("pluggy==1.6.0\nPyJWT==2.15.0\n", _IGNORE_BOTH.replace('"pyjwt"', '"PyJWT"'), '"pyjwt"'),
        (
            "pluggy==1.6.0\npyjwt==2.15.0\n",
            _IGNORE_BOTH.replace('"pluggy"\n', '"pluggy"\n        versions: [">=1.7.0"]\n'),
            '"pluggy"',
        ),
        # A requirement form the parser does not know is never skipped silently:
        # extras, a wildcard or compound specifier, a decorated local path.
        ("pluggy[extra]==1.6.0\npyjwt==2.15.0\n", _IGNORE_BOTH, "unrecognized requirement line"),
        ("pluggy==1.*\npyjwt==2.15.0\n", _IGNORE_BOTH, "unrecognized requirement line"),
        ("pluggy==1.6.0,!=1.7.0\npyjwt==2.15.0\n", _IGNORE_BOTH, "unrecognized requirement line"),
        (
            "pluggy==1.6.0\npyjwt==2.15.0\n./packages/v4-runtime[dev]\n",
            _IGNORE_BOTH,
            "unrecognized requirement line",
        ),
        (
            "pluggy==1.6.0\npyjwt==2.15.0\n./packages/v4-runtime --config-settings=k=v\n",
            _IGNORE_BOTH,
            "unrecognized requirement line",
        ),
    ],
)
def test_shared_pin_check_fails_on_lock_disagreement_or_unignored_shared_package(
    tmp_path: Path, product_lock: str, dependabot: str, expected: str
) -> None:
    product = tmp_path / "requirements-lock.txt"
    machinery = tmp_path / "requirements-machinery.lock"
    config = tmp_path / "dependabot.yml"
    product.write_text("# comment\n" + product_lock + "./packages/v4-runtime\n", encoding="utf-8")
    machinery.write_text(_MACHINERY_LOCK, encoding="utf-8")
    config.write_text(dependabot, encoding="utf-8")
    result = _run_shared_pin_check(product, machinery, config)
    assert result.returncode == 1
    assert expected in result.stdout
    # The same fixture with only the defect removed passes.
    config.write_text(_IGNORE_BOTH, encoding="utf-8")
    product.write_text("pluggy==1.6.0\npyjwt==2.15.0\n./packages/v4-runtime\n", encoding="utf-8")
    assert _run_shared_pin_check(product, machinery, config).returncode == 0


@pytest.mark.parametrize(
    ("pyyaml_line", "installed"),
    [
        ("PyYAML==6.0.3\n", "PyYAML==6.0.3"),
        ("pyyaml==6.0.3 \\\n    --hash=sha256:" + "d" * 64 + "\n", "PyYAML==6.0.3"),
        ("", None),
        ("PyYAML==6.0.3\npyyaml==6.0.2\n", None),
    ],
)
def test_shared_pin_step_bootstraps_pyyaml_from_any_valid_lock_spelling(
    tmp_path: Path, pyyaml_line: str, installed: str | None
) -> None:
    # The bootstrap reads the same lock the script validates: a hash
    # continuation or canonical spelling must not keep the check from running.
    stub = tmp_path / "bin"
    stub.mkdir()
    log = tmp_path / "python3.log"
    (stub / "python3").write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$STUB_LOG"\ncat > /dev/null\n')
    (stub / "python3").chmod(0o755)
    (tmp_path / "requirements-lock.txt").write_text("pluggy==1.6.0\n" + pyyaml_line, encoding="utf-8")
    result = subprocess.run(
        ["bash", "-c", _shared_pin_step()],
        cwd=tmp_path,
        env={**os.environ, "PATH": f"{stub}{os.pathsep}{os.environ['PATH']}", "STUB_LOG": str(log)},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if installed is None:
        assert result.returncode == 1
        assert "must pin PyYAML exactly once" in result.stdout
        assert not log.exists()
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        calls = log.read_text().splitlines()
        assert calls[0] == f"-m pip install --disable-pip-version-check --quiet {installed}"
        assert calls[1].startswith("-I - requirements-lock.txt requirements-machinery.lock")
