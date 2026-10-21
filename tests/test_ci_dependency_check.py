"""Guard the CI install's cache fallback and fail-closed dependency check."""

from pathlib import Path
from subprocess import CompletedProcess

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
    assert uv["with"]["save-cache"] == "${{ github.ref == 'refs/heads/main' && 'true' || 'false' }}"
    assert uv["id"] == "setup-uv"
    assert action["outputs"]["uv-cache-key"]["value"] == "${{ steps.setup-uv.outputs.cache-key }}"
    assert uv["with"]["enable-cache"] is True
    assert uv["with"]["cache-dependency-glob"] == "requirements-lock.txt"
    assert uv["with"].get("prune-cache", False) is False

    warm = yaml.safe_load(_WARM.read_text(encoding="utf-8"))
    triggers = warm.get("on", warm.get(True))
    assert triggers["push"] == {
        "branches": ["main"],
        "paths": [
            "requirements-lock.txt",
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
    changed_known_pair = known.replace("accelerate 1.14.0", "accelerate 1.14.1")
    assert unexpected_diagnostics(changed_known_pair) == [changed_known_pair]
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
