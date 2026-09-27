"""#8890 round 2: ``v7_build --dry-run --worktree`` creates no worktree and no
branch at all.

The create-then-discard design (round 1) could leak on any exit path between
``git worktree add`` and cleanup. Instead, ``main()`` never dispatches a dry
run to ``_run_in_worktree`` — it runs the dry-run pipeline in place, the same
way a bare ``--dry-run`` (no ``--worktree``) already does. Unit-level coverage
against a throwaway git repository (never the shared repo) lives here; the
end-to-end "invoked from a primary checkout" contract lives in
``test_v7_build_e2e.py``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.build import linear_pipeline, v7_build

LEVEL = "a1"
SLUG = "my-morning"
GATE_PASS = {"verdict": "PASS", "checks": {}}

pytestmark = pytest.mark.reads_content


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, timeout=30)
    (repo / "README.md").write_text("temp repo for v7_build --dry-run --worktree tests\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True, timeout=30)
    (repo / "curriculum/l2-uk-en/a1").mkdir(parents=True)
    return repo


def _repo_state(repo: Path) -> tuple[str, str, str]:
    refs = subprocess.run(
        ["git", "for-each-ref", "refs/heads"], cwd=repo, text=True, capture_output=True, check=True, timeout=30
    ).stdout
    worktrees = subprocess.run(
        ["git", "worktree", "list", "--porcelain"], cwd=repo, text=True, capture_output=True, check=True, timeout=30
    ).stdout
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, text=True, capture_output=True, check=True, timeout=30
    ).stdout
    return refs, worktrees, status


@pytest.fixture
def dry_run_pipeline(temp_repo: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point ``v7_build`` at ``temp_repo`` and stub the paid phases.

    Mirrors ``test_v7_dry_run_no_writes.py``'s ``content_root`` fixture: the
    plan itself is read from this real repo (``linear_pipeline.PROJECT_ROOT``
    is not monkeypatched), everything the build would otherwise write goes
    under ``temp_repo``.
    """
    monkeypatch.chdir(temp_repo)
    monkeypatch.setattr(v7_build, "PROJECT_ROOT", temp_repo)
    monkeypatch.setattr(linear_pipeline, "build_knowledge_packet", lambda **_: "packet\n")
    monkeypatch.setattr(linear_pipeline, "build_wiki_manifest_data", lambda **_: {"articles": []})
    monkeypatch.setattr(linear_pipeline, "run_wiki_completeness_gate", lambda **_: dict(GATE_PASS))

    def paid_writer(*_args: Any, **_kwargs: Any) -> str:
        raise AssertionError("a dry run must never reach the paid writer")

    monkeypatch.setattr(linear_pipeline, "invoke_writer", paid_writer)
    monkeypatch.setattr(v7_build, "_enforce_cf_preflight", lambda *_a, **_k: None)
    return temp_repo


def test_dry_run_worktree_leaves_refs_worktrees_and_files_untouched(
    dry_run_pipeline: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    before = _repo_state(dry_run_pipeline)

    rc = v7_build.main([LEVEL, SLUG, "--dry-run", "--worktree"])

    assert rc == 0
    assert _repo_state(dry_run_pipeline) == before
    assert "No build worktree created" in capsys.readouterr().out


def test_dry_run_worktree_does_not_dispatch_to_run_in_worktree(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args: Any, **_kwargs: Any) -> int:
        raise AssertionError("_run_in_worktree must not be called for a dry run (#8890)")

    monkeypatch.setattr(v7_build, "_run_in_worktree", _boom)
    monkeypatch.setattr(v7_build, "_run", lambda _args: 0)

    assert v7_build.main([LEVEL, SLUG, "--dry-run", "--worktree"]) == 0


@pytest.mark.parametrize(
    "argv",
    [
        [LEVEL, SLUG, "--dry-run", "--keep-worktree"],
        [LEVEL, SLUG, "--dry-run", "--worktree", "--keep-worktree"],
    ],
)
def test_keep_worktree_with_dry_run_is_a_usage_error(
    argv: list[str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def _boom(*_args: Any, **_kwargs: Any) -> int:
        raise AssertionError("a usage error must be caught before any build runs")

    monkeypatch.setattr(v7_build, "_run_in_worktree", _boom)
    monkeypatch.setattr(v7_build, "_run", _boom)

    rc = v7_build.main(argv)

    assert rc == 2
    assert "--keep-worktree" in capsys.readouterr().err


def test_setup_worktree_real_build_branch_name(temp_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Real (non-dry) builds keep the exact ``build/<level>/<slug>-<stamp>``
    shape ``scripts/sync/promote_module.py`` parses."""
    monkeypatch.chdir(temp_repo)
    monkeypatch.setattr(v7_build, "PROJECT_ROOT", temp_repo)
    monkeypatch.setattr(v7_build, "_fetch_origin_main", lambda repo_root: False)
    monkeypatch.setattr(v7_build, "_utc_timestamp", lambda: "20260927-120000")

    worktree = v7_build._setup_worktree("a1", "my-morning", None)

    assert worktree.branch == "build/a1/my-morning-20260927-120000"
    subprocess.run(["git", "worktree", "remove", "--force", str(worktree.path)], cwd=temp_repo, check=True, timeout=30)
    subprocess.run(["git", "branch", "-D", worktree.branch], cwd=temp_repo, check=True, timeout=30)
