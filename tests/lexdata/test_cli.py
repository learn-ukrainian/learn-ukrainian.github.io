"""CLI contract: agent-usable --help on every command; worktree builds are refused."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.lexdata import build_store, cli, transforms
from tests.lexdata._support import NO_BUDGET


@pytest.mark.parametrize("argv", [[], ["build"], ["verify"], ["status"], ["digests"]])
def test_help_is_agent_usable(capsys, argv) -> None:
    with pytest.raises(SystemExit) as stop:
        cli.main([*argv, "--help"])
    assert stop.value.code == 0
    text = capsys.readouterr().out
    for needle in ("Example", "Outputs:", "Exit codes:", "Related:"):
        assert needle in text, (argv, needle)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=lexdata-test", "-c", "user.email=lexdata-test@example.com", *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_build_from_a_linked_worktree_is_refused(capsys, tmp_path, monkeypatch) -> None:
    """Refuse ``build`` from a linked worktree this test creates."""
    primary, worker = tmp_path / "primary", tmp_path / "worker"
    primary.mkdir()
    _git(primary, "init", "-q", "-b", "main")
    _git(primary, "commit", "--allow-empty", "-q", "-m", "init")
    _git(primary, "worktree", "add", "--detach", "-q", str(worker))
    (worker / "scripts").mkdir()
    (worker / "data").mkdir()
    monkeypatch.chdir(worker)
    assert cli.main(["build"]) == 2
    assert json.loads(capsys.readouterr().out) == {"reason": "linked_worktree", "status": "refused"}


def test_digests_report_a_closed_registry(capsys) -> None:
    assert cli.main(["digests"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["undeclared_imports"] == {} and len(payload["normalizer_digest"]) == 64


def test_verify_and_status_on_a_published_generation(harness, capsys, monkeypatch) -> None:
    # Built under the production registry, so `status` (which reads with it) can open it.
    result = build_store.build(harness.target, binding=transforms.DEFAULT_BINDING, adapters={}, stores={},
                               repository_root=harness.repository_root, admission=NO_BUDGET)
    assert cli.main(["verify", "--path", str(result.published)]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    monkeypatch.setenv("LU_LEXDATA_DB", str(result.published))
    assert cli.main(["status"]) == 0
    assert json.loads(capsys.readouterr().out)["generation"] == result.generation
    assert cli.main(["verify", "--path", str(result.published.parent / "absent.db")]) == 2
