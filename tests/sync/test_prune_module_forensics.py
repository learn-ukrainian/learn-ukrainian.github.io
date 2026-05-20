from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from scripts.sync import prune_module_forensics
from scripts.sync.promote_module import FORENSICS_FILES, LESSON_SOURCE_FILES


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    # Strip any inherited GIT_* / pre-commit env vars so the inner test repo
    # isn't confused by the outer repo's git context (e.g. when the suite
    # runs under pre-commit's pytest hook).
    sanitized = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PRE_COMMIT"))}
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=sanitized,
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    # Use _git (which strips inherited GIT_*/PRE_COMMIT env vars) for init too —
    # the bare subprocess.run path inherits the parent shell's git context and
    # under pre-commit's pytest hook that confuses init enough to leak into
    # the parent repo's config.
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "base")
    return repo


def _module_dir(repo: Path, level: str, slug: str) -> Path:
    return repo / "curriculum" / "l2-uk-en" / level / slug


def _mdx_path(repo: Path, level: str, slug: str) -> Path:
    return repo / "starlight" / "src" / "content" / "docs" / level / f"{slug}.mdx"


def _seed_module(repo: Path, level: str, slug: str, *, status: str = "locked", forensics: bool = True) -> None:
    module_dir = _module_dir(repo, level, slug)
    module_dir.mkdir(parents=True, exist_ok=True)
    for filename in LESSON_SOURCE_FILES:
        (module_dir / filename).write_text(f"{filename}\n", encoding="utf-8")
    if forensics:
        for filename in FORENSICS_FILES:
            (module_dir / filename).write_text(f"{filename}\n", encoding="utf-8")
    status_dir = module_dir / "status"
    status_dir.mkdir(parents=True, exist_ok=True)
    (status_dir / f"{slug}.json").write_text(json.dumps({"status": status}) + "\n", encoding="utf-8")
    mdx = _mdx_path(repo, level, slug)
    mdx.parent.mkdir(parents=True, exist_ok=True)
    mdx.write_text("mdx\n", encoding="utf-8")


def test_prune_removes_forensics_keeps_lesson_source(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_module(repo, "a1", "foo")

    rc = prune_module_forensics.main(["--level", "a1", "--slug", "foo", "--no-commit"], repo_root=repo)

    assert rc == 0
    module_dir = _module_dir(repo, "a1", "foo")
    for filename in FORENSICS_FILES:
        assert not (module_dir / filename).exists()
    for filename in LESSON_SOURCE_FILES:
        assert (module_dir / filename).exists()
    assert _mdx_path(repo, "a1", "foo").exists()


def test_prune_refuses_when_status_not_locked(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_module(repo, "a1", "foo", status="draft")

    rc = prune_module_forensics.main(["--level", "a1", "--slug", "foo", "--no-commit"], repo_root=repo)

    assert rc == 1
    assert (_module_dir(repo, "a1", "foo") / "writer_prompt.md").exists()


def test_prune_force_bypasses_status_check(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_module(repo, "a1", "foo", status="draft")

    rc = prune_module_forensics.main(["--level", "a1", "--slug", "foo", "--force", "--no-commit"], repo_root=repo)

    assert rc == 0
    assert not (_module_dir(repo, "a1", "foo") / "writer_prompt.md").exists()


def test_prune_idempotent(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_module(repo, "a1", "foo", forensics=False)

    rc = prune_module_forensics.main(["--level", "a1", "--slug", "foo", "--no-commit"], repo_root=repo)

    assert rc == 0
    assert (_module_dir(repo, "a1", "foo") / "module.md").exists()


def test_prune_all_skips_non_locked(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_module(repo, "a1", "locked")
    _seed_module(repo, "a1", "draft", status="draft")
    _seed_module(repo, "a1", "ready", status="ready")

    rc = prune_module_forensics.main(["--all", "--no-commit"], repo_root=repo)

    assert rc == 0
    assert not (_module_dir(repo, "a1", "locked") / "writer_prompt.md").exists()
    assert (_module_dir(repo, "a1", "draft") / "writer_prompt.md").exists()
    assert (_module_dir(repo, "a1", "ready") / "writer_prompt.md").exists()
