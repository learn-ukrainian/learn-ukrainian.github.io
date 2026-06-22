"""Keep the actionlint workflow-structure gate load-bearing.

``.github/workflows/actionlint.yml`` is the root-cause fix for the #3739/#3742
break, where a de-indented ``setup-node`` ``with:`` block was valid YAML but
invalid Actions, passed yamllint + zizmor, and broke the Pages deploy. The gate
runs ``scripts/audit/check_workflows.sh`` (a checksum-pinned actionlint).

These tests assert the wiring statically — no actionlint binary or network is
required — so the gate cannot be silently removed or gutted: the workflow must
trigger on PRs and invoke the shared script, and the shared script must keep its
pinned version + per-platform checksums + checksum verification.
"""

from __future__ import annotations

import stat
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "actionlint.yml"
_SCRIPT = _REPO_ROOT / "scripts" / "audit" / "check_workflows.sh"

# Platforms the shared script must pin a checksum for (CI + common dev machines).
_REQUIRED_PLATFORMS = ("linux_amd64", "linux_arm64", "darwin_amd64", "darwin_arm64")


def _load_workflow() -> dict:
    data = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "actionlint workflow did not parse to a mapping"
    return data


def _triggers(workflow: dict) -> dict:
    # PyYAML (YAML 1.1) parses the bare ``on:`` key as the boolean True.
    raw = workflow.get("on", workflow.get(True))
    assert raw is not None, "actionlint workflow has no `on:` triggers"
    return raw


def test_workflow_file_exists_and_parses() -> None:
    assert _WORKFLOW.is_file(), f"missing workflow: {_WORKFLOW}"
    _load_workflow()


def test_workflow_triggers_on_pull_requests() -> None:
    triggers = _triggers(_load_workflow())
    assert "pull_request" in triggers, (
        "actionlint must run on pull_request so it gates PRs that touch workflows"
    )


def test_workflow_invokes_shared_script() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    assert "scripts/audit/check_workflows.sh" in text, (
        "workflow must call the shared runner (single source of truth)"
    )
    # Reproducible CI: ignore any runner-bundled actionlint, fetch the pin.
    assert "ACTIONLINT_FORCE_DOWNLOAD" in text


def test_workflow_uses_minimal_permissions() -> None:
    workflow = _load_workflow()
    assert workflow.get("permissions") == {"contents": "read"}, (
        "actionlint job needs only contents:read"
    )


def test_workflow_checkout_does_not_persist_credentials() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    assert "persist-credentials: false" in text, (
        "checkout must set persist-credentials: false (zizmor baseline)"
    )


def test_shared_script_exists_and_is_executable() -> None:
    assert _SCRIPT.is_file(), f"missing runner: {_SCRIPT}"
    mode = _SCRIPT.stat().st_mode
    assert mode & stat.S_IXUSR, f"{_SCRIPT} must be executable"


def test_shared_script_pins_version_and_checksums() -> None:
    text = _SCRIPT.read_text(encoding="utf-8")
    assert 'ACTIONLINT_VERSION="' in text, "script must pin an actionlint version"
    # A 64-hex sha256 must be present for every required platform.
    for platform in _REQUIRED_PLATFORMS:
        assert platform in text, f"script missing checksum entry for {platform}"
    # Verification must actually run on the downloaded tarball.
    assert "sha256_verify" in text, "script must verify the download checksum"


def test_checksum_entries_are_well_formed() -> None:
    import re

    text = _SCRIPT.read_text(encoding="utf-8")
    for platform in _REQUIRED_PLATFORMS:
        match = re.search(rf"{platform}\)\s+echo\s+\"([0-9a-f]{{64}})\"", text)
        assert match, f"{platform} checksum is not a 64-char lowercase hex sha256"
