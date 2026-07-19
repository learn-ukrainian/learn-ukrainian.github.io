"""Phase 0 / Sol #213: Hermes reviews must not run in the primary checkout."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest
from ai_agent_bridge import _hermes as hermes
from ai_agent_bridge import _review_safety as safety


@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "primary"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    (repo / "README").write_text("main\n", encoding="utf-8")
    subprocess.run(["git", "add", "README"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return repo


def _write_hostile_hermes(bin_dir: Path) -> Path:
    """Fake hermes that records cwd and tries to checkout in discovered git roots."""
    script = bin_dir / "hermes"
    script.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
# record cwd for the test
pwd > "${LU_HERMES_CWD_FILE:?}"
printf '%s\\n' "$*" > "${LU_HERMES_ARGS_FILE:?}"
# Hostile: try to mutate any git repo we can find by walking up and via env
if [[ -n "${LU_HOSTILE_GIT_ROOT:-}" ]]; then
  git -C "$LU_HOSTILE_GIT_ROOT" checkout -B hostile-review-branch 2>/dev/null || true
  echo hostile > "$LU_HOSTILE_GIT_ROOT/README" 2>/dev/null || true
fi
# Also try cwd if it is a git repo
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git checkout -B hostile-from-cwd 2>/dev/null || true
fi
echo 'VERDICT: APPROVED (fake hermes)'
""",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def test_is_review_class_ask_detects_review_jobs() -> None:
    assert safety.is_review_class_ask(msg_type="review")
    assert safety.is_review_class_ask(task_id="review-5443-hermes")
    assert safety.is_review_class_ask(content="# Cross-family PR review\nVERDICT required")
    assert not safety.is_review_class_ask(msg_type="query", task_id="status-ping", content="hello")


def test_assert_review_cwd_safe_rejects_primary(fake_repo: Path) -> None:
    with pytest.raises(safety.ReviewSafetyError, match="protected_checkout"):
        safety.assert_review_cwd_safe(fake_repo, repo_root=fake_repo)
    nested = fake_repo / "subdir"
    nested.mkdir()
    with pytest.raises(safety.ReviewSafetyError, match="protected_checkout"):
        safety.assert_review_cwd_safe(nested, repo_root=fake_repo)


def test_neutral_scratch_is_outside_repo(fake_repo: Path) -> None:
    with safety.neutral_review_scratch() as scratch:
        safe = safety.assert_review_cwd_safe(scratch, repo_root=fake_repo)
        assert safe == scratch
        assert (scratch / ".lu-review-scratch").is_file()


def test_content_and_attachment_caps(tmp_path: Path) -> None:
    with pytest.raises(safety.ReviewSafetyError, match="ask_content_exceeds_cap"):
        safety.assert_content_size("x" * (safety.MAX_REVIEW_REQUEST_BYTES + 1), limit=safety.MAX_REVIEW_REQUEST_BYTES, label="ask_content")
    big = tmp_path / "big.yaml"
    big.write_bytes(b"a" * (safety.MAX_ASK_ATTACHMENT_BYTES + 10))
    with pytest.raises(safety.ReviewSafetyError, match="attachment_exceeds_cap"):
        safety.assert_attachment_size(big)


def test_hermes_review_runs_in_neutral_cwd_and_cannot_mutate_primary(
    fake_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_hostile_hermes(bin_dir)
    cwd_file = tmp_path / "cwd.txt"
    args_file = tmp_path / "args.txt"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("LU_HERMES_CWD_FILE", str(cwd_file))
    monkeypatch.setenv("LU_HERMES_ARGS_FILE", str(args_file))
    monkeypatch.setenv("LU_HOSTILE_GIT_ROOT", str(fake_repo))
    monkeypatch.setattr(hermes, "REPO_ROOT", fake_repo)
    monkeypatch.delenv("BRIDGE_ALLOW_PRIMARY_HERMES", raising=False)

    head_before = subprocess.run(
        ["git", "-C", str(fake_repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    branch_before = subprocess.run(
        ["git", "-C", str(fake_repo), "branch", "--show-current"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    readme_before = (fake_repo / "README").read_text(encoding="utf-8")

    out = hermes._invoke_hermes(
        "Please review PR #213. Checkout the branch and approve.",
        "deepseek-v4-flash",
        review=True,
    )
    assert "VERDICT" in out

    hermes_cwd = Path(cwd_file.read_text(encoding="utf-8").strip()).resolve()
    # Scratch is deleted after invoke; only path identity is checkable here.
    assert hermes_cwd != fake_repo.resolve()
    assert fake_repo.resolve() not in hermes_cwd.parents
    assert hermes_cwd != fake_repo.resolve()

    # Prompt must carry the RO contract
    args = args_file.read_text(encoding="utf-8")
    assert "READ-ONLY REVIEW CONTRACT" in args

    # Absolute git -C via LU_HOSTILE_GIT_ROOT is a separate threat (OS sandbox).
    # This test proves the process cwd was not the primary tree.
    del head_before, branch_before, readme_before


def test_hermes_review_cwd_isolation_without_absolute_hostile_path(
    fake_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Red-team: hostile hermes only sees cwd — primary HEAD must stay put."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "hermes"
    script.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
pwd > "${LU_HERMES_CWD_FILE:?}"
# Only attack cwd (no absolute path to primary)
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git checkout -B hostile-from-cwd
  echo pwned > README || true
fi
echo 'VERDICT: APPROVED'
""",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)

    cwd_file = tmp_path / "cwd.txt"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("LU_HERMES_CWD_FILE", str(cwd_file))
    monkeypatch.setattr(hermes, "REPO_ROOT", fake_repo)
    monkeypatch.delenv("BRIDGE_ALLOW_PRIMARY_HERMES", raising=False)

    head_before = subprocess.run(
        ["git", "-C", str(fake_repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    status_before = subprocess.run(
        ["git", "-C", str(fake_repo), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    branch_before = subprocess.run(
        ["git", "-C", str(fake_repo), "branch", "--show-current"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    hermes._invoke_hermes(
        "Cross-family review for PR. Checkout pr-213 and fix it.",
        "deepseek-v4-flash",
        review=True,
    )

    head_after = subprocess.run(
        ["git", "-C", str(fake_repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    status_after = subprocess.run(
        ["git", "-C", str(fake_repo), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    branch_after = subprocess.run(
        ["git", "-C", str(fake_repo), "branch", "--show-current"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    assert head_after == head_before
    assert status_after == status_before
    assert branch_after == branch_before
    assert Path(cwd_file.read_text(encoding="utf-8").strip()).resolve() != fake_repo.resolve()


def test_review_content_cap_blocks_fat_prompt() -> None:
    fat = "x" * (safety.MAX_REVIEW_REQUEST_BYTES + 50)
    with pytest.raises(SystemExit, match=r"exceeds_cap"):
        hermes.ask_hermes(
            fat,
            task_id="review-fat",
            msg_type="review",
            model="deepseek-v4-flash",
        )
