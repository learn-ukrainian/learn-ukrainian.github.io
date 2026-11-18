"""Guard the CI install's uv cache publication (#9095, #9101)."""

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github/workflows/ci.yml"
_WARM = _REPO_ROOT / ".github/workflows/uv-cache-warm.yml"
_ACTION = _REPO_ROOT / ".github/actions/python-ci-env/action.yml"


def test_main_push_publishes_the_uv_cache_merge_group_can_read() -> None:
    # #9095: merge_group restores only a cache saved on the default branch.
    # setup-uv matches the uv.lock key exactly. Since #9101 only
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
    # Only machinery-wheel-only callers (which never install the project) skip the cache.
    assert uv["with"]["enable-cache"] == "${{ inputs.machinery-wheel-only != 'true' }}"
    assert uv["with"]["cache-dependency-glob"] == "uv.lock"
    assert uv["with"].get("prune-cache", False) is False

    warm = yaml.safe_load(_WARM.read_text(encoding="utf-8"))
    triggers = warm.get("on", warm.get(True))
    assert triggers["push"] == {
        "branches": ["main"],
        "paths": [
            "uv.lock",
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
