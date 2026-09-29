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


def _action_step(name: str) -> dict:
    steps = yaml.safe_load(_ACTION.read_text(encoding="utf-8"))["runs"]["steps"]
    matches = [step for step in steps if step.get("name") == name]
    assert len(matches) == 1, f"expected one action step named {name!r}"
    return matches[0]


def test_ci_install_blocks_use_the_same_cache_and_integrity_sequence() -> None:
    # #9062: the install/hydrate block is one composite action, and every job
    # that used to carry a copy calls it, so the copies cannot drift apart.
    workflow = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    jobs = workflow["jobs"]
    for job in ("fast-checks", "pytest", "needs-artifact-audit"):
        assert any(
            step.get("uses") == "./.github/actions/python-ci-env"
            for step in jobs[job]["steps"]
        ), job
    script = _action_step("Install Python deps")["run"]
    assert script.index("uv pip install --offline") < script.index(
        "uv pip install --python"
    ) < script.index("uv pip check --python .venv/bin/python") < script.index(
        "scripts/audit/check_ci_dependencies.py"
    )
    assert script.index("scripts/audit/check_ci_dependencies.py") < script.index(
        "build_assets.py"
    )


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


def test_warm_workflow_rejects_dispatch_on_other_refs_before_warming() -> None:
    # #9101: workflow_dispatch runs on any branch, where nothing saves and
    # verify would search main for that branch's key. Reject it first (red,
    # obvious) instead of skipping verify; main runs must pass through.
    warm = yaml.safe_load(_WARM.read_text(encoding="utf-8"))
    triggers = warm.get("on", warm.get(True))
    assert "workflow_dispatch" in triggers
    steps = warm["jobs"]["warm"]["steps"]
    guard = steps[0]
    assert guard["if"] == "github.ref != 'refs/heads/main'"
    assert guard["env"]["REF"] == "${{ github.ref }}"
    assert "exit 1" in guard["run"]
    assert "main" in guard["run"]
    # Nothing that installs or saves runs before the guard, and verify cannot
    # run once warm has failed.
    assert "uses" not in guard
    assert warm["jobs"]["verify"]["needs"] == "warm"
    assert "if" not in warm["jobs"]["verify"]


def test_every_uv_cache_action_is_pinned_to_a_full_sha() -> None:
    action = yaml.safe_load(_ACTION.read_text(encoding="utf-8"))
    warm = yaml.safe_load(_WARM.read_text(encoding="utf-8"))
    steps = action["runs"]["steps"] + [
        step for job in warm["jobs"].values() for step in job["steps"]
    ]
    for step in steps:
        uses = step.get("uses")
        if uses is None or uses.startswith("./"):
            continue
        revision = uses.split("@")[1]
        assert len(revision) == 40 and all(c in "0123456789abcdef" for c in revision), uses


def test_ci_retry_settings_cover_uv_and_pip() -> None:
    workflow = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    assert workflow["env"] | {
        "UV_HTTP_RETRIES": "6",
        "UV_HTTP_TIMEOUT": "60",
        "PIP_RETRIES": "6",
        "PIP_TIMEOUT": "60",
    } == workflow["env"]


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
