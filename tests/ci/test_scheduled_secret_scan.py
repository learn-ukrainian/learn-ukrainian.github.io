"""Scheduled TruffleHog invocation scans a real range (#10839).

The pinned action treats an empty base and head on ``schedule`` as a full
history scan (``--since-commit '' --branch ''``) and exits 183 when that
history has findings.  The workflow keeps passing the scope step's outputs.
A short history scans the whole branch; the base and head are never the same
value.  Pull-request and push ranges stay on the action's own inputs.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import yaml

from scripts.ci.secret_scan_scope import resolve_scan_scope

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CI = _REPO_ROOT / ".github" / "workflows" / "ci.yml"
_SHA = re.compile(r"[0-9a-f]{40}\Z")


def _workflow() -> dict:
    loaded = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True, timeout=30).strip()


def test_scheduled_scan_uses_a_real_range_and_leaves_pr_and_push_alone(tmp_path: Path) -> None:
    workflow = _workflow()
    triggers = workflow.get("on", workflow.get(True))
    assert triggers["schedule"]
    secret_scan = workflow["jobs"]["secret-scan"]
    scope_step = next(step for step in secret_scan["steps"] if step.get("id") == "secret-scan-scope")
    assert "python3 scripts/ci/secret_scan_scope.py" in scope_step["run"]
    assert scope_step["env"]["EVENT_NAME"] == "${{ github.event_name }}"
    scan = next(step for step in secret_scan["steps"] if "trufflehog" in str(step.get("uses") or ""))
    revision = str(scan["uses"]).split("@", 1)[1]
    assert _SHA.fullmatch(revision)
    base = scan["with"]["base"]
    head = scan["with"]["head"]
    assert base == "${{ steps.secret-scan-scope.outputs.trufflehog_base }}"
    assert head == "${{ steps.secret-scan-scope.outputs.trufflehog_head }}"
    assert base != head
    assert scan["with"]["extra_args"] == (
        "--results=verified,unknown --exclude-paths=.trufflehogignore --exclude-detectors=Lob"
    )
    checkout = next(step for step in secret_scan["steps"] if str(step.get("uses", "")).startswith("actions/checkout@"))
    assert checkout["with"]["fetch-depth"] == 0
    assert "ref" not in checkout["with"]

    _git(tmp_path, "init", "--initial-branch=main")
    _git(tmp_path, "config", "user.email", "ci@example.com")
    _git(tmp_path, "config", "user.name", "ci")
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = "2026-10-01T00:00:00Z"
    env["GIT_COMMITTER_DATE"] = "2026-10-01T00:00:00Z"
    subprocess.check_call(["git", "commit", "-m", "old"], cwd=tmp_path, env=env, timeout=30)
    old = _git(tmp_path, "rev-parse", "HEAD")
    (tmp_path / "README.md").write_text("head\n", encoding="utf-8")
    env["GIT_AUTHOR_DATE"] = "2026-10-16T12:00:00Z"
    env["GIT_COMMITTER_DATE"] = "2026-10-16T12:00:00Z"
    subprocess.check_call(["git", "commit", "-am", "new"], cwd=tmp_path, env=env, timeout=30)
    head_sha = _git(tmp_path, "rev-parse", "HEAD")

    scheduled = resolve_scan_scope("schedule", repo_root=tmp_path)
    assert scheduled.mode == "schedule"
    assert scheduled.reason == "branch-history"
    assert scheduled.trufflehog_base == ""
    assert scheduled.trufflehog_head == head_sha
    assert scheduled.trufflehog_base != scheduled.trufflehog_head
    assert scheduled.trufflehog_base != old

    pull_request = resolve_scan_scope("pull_request", repo_root=tmp_path)
    assert pull_request.trufflehog_base == ""
    assert pull_request.trufflehog_head == ""
    pushed = resolve_scan_scope("push", push_before_sha=old, push_after_sha=head_sha, repo_root=tmp_path)
    assert pushed.trufflehog_base == old
    assert pushed.trufflehog_head == head_sha
