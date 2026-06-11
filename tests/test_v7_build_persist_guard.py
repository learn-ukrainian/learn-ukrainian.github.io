from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.build import run_archive, v7_build

_REAL_RUN = subprocess.run
_RUN_ID = "20260611-120000"


def git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and not key.startswith("PRE_COMMIT")
    }


def git(cwd: Path, *args: str) -> str:
    proc = _REAL_RUN(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=git_env(),
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return (proc.stdout or "").strip()


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    git(tmp_path, "init", "--initial-branch=main", str(repo))
    git(repo, "config", "user.email", "tester@example.com")
    git(repo, "config", "user.name", "Test User")
    (repo / ".gitignore").write_text(
        ".worktrees/\ncurriculum/l2-uk-en/_orchestration/\n",
        encoding="utf-8",
    )
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    git(repo, "add", ".gitignore", "README.md")
    git(repo, "commit", "-m", "base")
    return repo


def add_build_worktree(repo: Path, branch: str = "build/a1/foo") -> Path:
    worktree = repo / ".worktrees" / "builds" / branch.replace("/", "-")
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", "-b", branch, str(worktree), "main")
    git(worktree, "config", "user.email", "tester@example.com")
    git(worktree, "config", "user.name", "Test User")
    return worktree


def build_worktree(repo: Path, path: Path, branch: str = "build/a1/foo") -> v7_build.BuildWorktree:
    return v7_build.BuildWorktree(
        path=path,
        branch=branch,
        base_sha=git(path, "rev-parse", "--short", "HEAD"),
        repo_root=repo,
        run_id=_RUN_ID,
    )


def seed_artifacts(root: Path, *, level: str = "a1", slug: str = "foo") -> None:
    module_dir = root / "curriculum" / "l2-uk-en" / level / slug
    module_dir.mkdir(parents=True, exist_ok=True)
    for name, content in {
        "writer_prompt.md": "prompt\n",
        "writer_output.raw.md": "raw\n",
        "hermes.write.jsonl": "{}\n",
        "writer_tool_calls.json": "[]\n",
        "knowledge_packet.md": "packet\n",
        "implementation_map.json": "{}\n",
        "module.md": "# Module\n",
        "activities.yaml": "[]\n",
        "vocabulary.yaml": "[]\n",
        "resources.yaml": "[]\n",
    }.items():
        (module_dir / name).write_text(content, encoding="utf-8")

    mdx_path = root / "starlight" / "src" / "content" / "docs" / level / f"{slug}.mdx"
    mdx_path.parent.mkdir(parents=True, exist_ok=True)
    mdx_path.write_text("---\ntitle: Foo\n---\n", encoding="utf-8")

    archive_dir = run_archive.archive_dir_for(
        root,
        level=level,
        slug=slug,
        run_id=_RUN_ID,
    )
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / "state.json").write_text('{"status": "complete"}\n', encoding="utf-8")


def test_persist_refuses_primary_checkout_and_creates_no_commit(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    seed_artifacts(repo)
    worktree = build_worktree(repo, repo, branch="main")
    before = git(repo, "rev-parse", "HEAD")

    with pytest.raises(v7_build.PrimaryCheckoutPersistError):
        v7_build._persist_build_artifacts(
            worktree,
            level="a1",
            slug="foo",
            result="failed",
        )

    assert git(repo, "rev-parse", "HEAD") == before
    assert git(repo, "rev-list", "--count", "HEAD") == "1"


def test_persist_allows_real_worktree_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    child = add_build_worktree(repo)
    seed_artifacts(child)
    worktree = build_worktree(repo, child)
    monkeypatch.setenv("GIT_DIR", str(repo / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(repo))

    assert (
        v7_build._persist_build_artifacts(
            worktree,
            level="a1",
            slug="foo",
            result="success",
        )
        is True
    )

    assert git(child, "log", "-1", "--format=%s") == "build(a1/foo): artifacts (success)"
    committed = git(child, "show", "--name-only", "--format=", "HEAD")
    assert "curriculum/l2-uk-en/a1/foo/writer_prompt.md" in committed
    assert "curriculum/l2-uk-en/_orchestration/a1/foo/runs/" in committed
    assert "starlight/src/content/docs/a1/foo.mdx" in committed


def test_persist_scoped_add_leaves_unrelated_untracked_file_out(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    child = add_build_worktree(repo)
    seed_artifacts(child)
    (child / "scratch-notes.txt").write_text("do not commit\n", encoding="utf-8")
    worktree = build_worktree(repo, child)

    assert (
        v7_build._persist_build_artifacts(
            worktree,
            level="a1",
            slug="foo",
            result="failed",
        )
        is True
    )

    stat = git(child, "show", "--stat", "--oneline", "HEAD")
    assert "writer_prompt.md" in stat
    assert "scratch-notes.txt" not in stat
    assert "?? scratch-notes.txt" in git(child, "status", "--short")


def test_main_guard_refuses_primary_checkout_but_allows_archive_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = init_repo(tmp_path)
    monkeypatch.chdir(repo)
    monkeypatch.delenv(run_archive.ENV_KEY, raising=False)
    calls: list[Any] = []
    monkeypatch.setattr(v7_build, "_run", lambda args: calls.append(args) or 0)

    exit_code = v7_build.main(["a1", "foo", "--dry-run"])

    captured = capsys.readouterr()
    assert exit_code == v7_build.PrimaryCheckoutSafetyError.exit_code
    assert calls == []
    assert "Refusing to run v7_build in the primary checkout" in captured.err
    assert "See #2884" in captured.err

    monkeypatch.setenv(run_archive.ENV_KEY, "test-child")
    assert v7_build.main(["a1", "foo", "--dry-run"]) == 0
    assert len(calls) == 1
