"""Regression tests for descriptor-bound deploy-status breadcrumb updates."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DEPLOY_DIR = REPO_ROOT / "scripts" / "deploy"
MODULE_PATH = DEPLOY_DIR / "update_agent_deploy_status.py"

sys.path.insert(0, str(DEPLOY_DIR))
spec = importlib.util.spec_from_file_location("update_agent_deploy_status_under_test", MODULE_PATH)
assert spec and spec.loader
status_writer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(status_writer)


def test_failure_breadcrumb_stays_in_held_directory_after_root_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The status and log write must ignore a post-open `.agent` path swap."""
    agent_root = tmp_path / "project" / ".agent"
    agent_root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    failure_log = tmp_path / "deploy.log"
    failure_log.write_text("rsync failed\n", encoding="utf-8")
    held_agent = tmp_path / "held-agent"
    swapped = False
    original_open = status_writer.open_agent_directory

    def open_then_swap(root: str) -> int:
        nonlocal swapped
        agent_fd = original_open(root)
        if not swapped:
            agent_root.rename(held_agent)
            agent_root.symlink_to(outside, target_is_directory=True)
            swapped = True
        return agent_fd

    monkeypatch.setattr(status_writer, "open_agent_directory", open_then_swap)
    status_writer.record_failure(str(agent_root), "agents:deploy", 3, failure_log)

    assert not (outside / status_writer.STATUS_FILE).exists()
    assert not (outside / status_writer.FAILURE_LOG).exists()
    assert (held_agent / status_writer.STATUS_FILE).read_text(encoding="utf-8").startswith("FAILED\n")
    assert (held_agent / status_writer.FAILURE_LOG).read_text(encoding="utf-8") == "rsync failed\n"


def test_clear_unlinks_symlink_leaf_without_touching_its_target(tmp_path: Path) -> None:
    """Success cleanup removes only a breadcrumb symlink, never its target."""
    agent_root = tmp_path / "project" / ".agent"
    agent_root.mkdir(parents=True)
    external_status = tmp_path / "external-status"
    external_status.write_text("must survive\n", encoding="utf-8")
    (agent_root / status_writer.STATUS_FILE).symlink_to(external_status)

    status_writer.clear_breadcrumb(str(agent_root))

    assert external_status.read_text(encoding="utf-8") == "must survive\n"
    assert not (agent_root / status_writer.STATUS_FILE).exists()


def test_symlinked_agent_root_is_refused(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A pre-existing root symlink is rejected before a status write can escape."""
    outside = tmp_path / "outside"
    outside.mkdir()
    link_root = tmp_path / "project" / ".agent"
    link_root.parent.mkdir()
    link_root.symlink_to(outside, target_is_directory=True)

    rc = status_writer.main(["clear", "--agent-root", str(link_root)])

    assert rc == 1
    assert "refusing .agent deploy-status update" in capsys.readouterr().err
