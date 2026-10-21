import os
import subprocess
from pathlib import Path

import pytest

from scripts.api import git_hygiene_router

pytestmark = pytest.mark.reads_content


def _git(repo: Path, *args: str) -> str:
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        env.pop(key, None)
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        env=env,
        text=True,
        check=True,
        timeout=30,
    )
    return proc.stdout


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _init_repo(repo: Path) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.email", "codex@example.invalid")
    _git(repo, "config", "user.name", "Codex Test")
    _write(
        repo / "docs" / "best-practices" / "git-hygiene.md",
        """# Git Hygiene

## Exemption paths

- `wiki/**` - wiki builder output
- `registry/corpus_audit/draft_tickets/*.md` - draft tickets

## Other section
""",
    )


def _commit_all(repo: Path, message: str) -> None:
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", message)


def _dirty_repo_with_all_buckets(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)

    _write(repo / "stale.py", "def old_name():\n    return 'old'\n")
    _write(repo / "wip.py", "def stable():\n    return 'stable'\n")
    for name in ("a.txt", "b.txt", "c.txt"):
        _write(repo / "feature" / "remove" / name, f"{name}\n")
    _commit_all(repo, "initial")

    for idx in range(20):
        _write(repo / "fillers" / f"{idx:02d}.txt", f"{idx}\n")
        _commit_all(repo, f"filler {idx}")

    _write(repo / "stale.py", "def new_name():\n    return 'new'\n")
    _commit_all(repo, "update stale file")

    _write(repo / "stale.py", "def old_name():\n    return 'old'\n")
    _write(repo / "wip.py", "def stable():\n    return 'stable'\n\n\ndef local_wip():\n    return 'wip'\n")
    for name in ("a.txt", "b.txt", "c.txt"):
        (repo / "feature" / "remove" / name).unlink()
    _write(repo / "scratch" / "todo.txt", "local note\n")
    _write(repo / "wiki" / "draft.md", "wiki output\n")
    _write(repo / "registry" / "corpus_audit" / "draft_tickets" / "ticket.md", "draft\n")

    return repo


def test_hygiene_classifies_each_dirty_bucket(tmp_path: Path) -> None:
    repo = _dirty_repo_with_all_buckets(tmp_path)

    result = git_hygiene_router.compute_git_hygiene(repo)

    assert result["health"] == "dirty"
    assert result["dirty_total"] == 6
    assert result["exempt"]["wiki"] == 1
    assert result["exempt"]["draft_tickets"] == 1
    assert result["exempt"]["total"] == 2
    assert result["buckets"]["stale_behind_main"]["files"] == ["stale.py"]
    assert result["buckets"]["real_wip"]["files"] == ["wip.py"]
    assert result["buckets"]["untracked_unexempted"]["files"] == ["scratch/todo.txt"]
    assert result["buckets"]["intentional_deletions"]["count"] == 3
    assert result["buckets"]["intentional_deletions"]["pattern"] == "feature/remove/*"
    assert {item["action"] for item in result["suggestions"]} == {
        "restore_to_head",
        "stash_wip",
        "gitignore_pattern",
        "commit_deletions",
    }


def test_hygiene_marks_deleted_python_as_blocked_imports(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _write(repo / "scripts" / "common" / "text_utils.py", "def normalize():\n    return None\n")
    _commit_all(repo, "initial")
    (repo / "scripts" / "common" / "text_utils.py").unlink()

    result = git_hygiene_router.compute_git_hygiene(repo)

    assert result["health"] == "blocked_imports"
    assert result["dirty_total"] == 1
