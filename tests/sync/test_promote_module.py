from __future__ import annotations

import os
import subprocess
from pathlib import Path

from scripts.sync import promote_module


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    # Strip any inherited GIT_* / pre-commit env vars so the inner test repo
    # isn't confused by the outer repo's GIT_DIR / GIT_INDEX_FILE / etc. when
    # the suite runs under pre-commit's pytest hook.
    merged_env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PRE_COMMIT"))}
    if env:
        merged_env.update(env)
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=merged_env,
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


def _rel_module(level: str, slug: str, filename: str) -> Path:
    return Path("curriculum") / "l2-uk-en" / level / slug / filename


def _rel_mdx_build(level: str, slug: str) -> Path:
    """Where `assemble_mdx` writes the freshly-built MDX inside the build branch."""
    return Path("curriculum") / "l2-uk-en" / level / slug / f"{slug}.mdx"


def _rel_mdx(level: str, slug: str) -> Path:
    """Deploy target Starlight reads from."""
    return Path("starlight") / "src" / "content" / "docs" / level / f"{slug}.mdx"


def _seed_build_branch(
    repo: Path,
    branch: str,
    *,
    level: str = "a1",
    slug: str = "foo",
    omit: set[str] | None = None,
    module_text: str = "# Module\n",
    stamp: str = "2026-05-20T01:01:01 +0000",
) -> None:
    omit = omit or set()
    _git(repo, "switch", "-c", branch)
    files = {
        "module.md": module_text,
        "activities.yaml": "- kind: quiz\n",
        "vocabulary.yaml": "- word: тест\n",
        "resources.yaml": "resources: []\n",
        "writer_prompt.md": "prompt\n",
        "writer_output.raw.md": "raw\n",
        "hermes.write.jsonl": "{}\n",
        "writer_tool_calls.json": "[]\n",
        "python_qg.json": "{}\n",
        "llm_qg.json": "{}\n",
        "knowledge_packet.md": "packet\n",
        "implementation_map.json": "{}\n",
    }
    for filename, content in files.items():
        if filename in omit:
            continue
        path = repo / _rel_module(level, slug, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    if "mdx" not in omit:
        # The build's assemble_mdx step writes here (curriculum tree), not into
        # starlight/. Promote reads from this path and writes the deploy copy
        # into starlight/src/content/docs/.
        mdx = repo / _rel_mdx_build(level, slug)
        mdx.parent.mkdir(parents=True, exist_ok=True)
        mdx.write_text("mdx content\n", encoding="utf-8")
    _git(repo, "add", ".")
    env = {"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp}
    _git(repo, "commit", "-m", f"build {branch}", env=env)
    _git(repo, "switch", "main")


def test_promote_copies_lesson_source_and_forensics(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    branch = "build/a1/foo-20260520-010101"
    _seed_build_branch(repo, branch)

    rc = promote_module.main(["--build-branch", branch, "--no-commit"], repo_root=repo)

    assert rc == 0
    assert (repo / _rel_module("a1", "foo", "module.md")).read_text(encoding="utf-8") == "# Module\n"
    assert (repo / _rel_module("a1", "foo", "writer_prompt.md")).read_text(encoding="utf-8") == "prompt\n"
    assert (repo / _rel_mdx("a1", "foo")).read_text(encoding="utf-8") == "mdx content\n"


def test_promote_fails_if_lesson_source_incomplete(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    branch = "build/a1/foo-20260520-010101"
    _seed_build_branch(repo, branch, omit={"module.md"})

    rc = promote_module.main(["--build-branch", branch, "--no-commit"], repo_root=repo)

    assert rc == 2
    assert not (repo / _rel_module("a1", "foo", "activities.yaml")).exists()
    assert not (repo / _rel_mdx("a1", "foo")).exists()


def test_promote_idempotent_on_matching_content(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    branch = "build/a1/foo-20260520-010101"
    _seed_build_branch(repo, branch)
    assert promote_module.main(["--build-branch", branch], repo_root=repo) == 0
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()

    rc = promote_module.main(["--build-branch", branch], repo_root=repo)

    assert rc == 0
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == head


def test_promote_aborts_on_partial_match_without_force(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    branch = "build/a1/foo-20260520-010101"
    _seed_build_branch(repo, branch)
    dest = repo / _rel_module("a1", "foo", "module.md")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("# Hand edited\n", encoding="utf-8")

    rc = promote_module.main(["--build-branch", branch, "--no-commit"], repo_root=repo)

    assert rc == 1
    assert dest.read_text(encoding="utf-8") == "# Hand edited\n"


def test_promote_dry_run_writes_nothing(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    branch = "build/a1/foo-20260520-010101"
    _seed_build_branch(repo, branch)

    rc = promote_module.main(["--build-branch", branch, "--dry-run"], repo_root=repo)

    assert rc == 0
    assert not (repo / _rel_module("a1", "foo", "module.md")).exists()
    assert _git(repo, "status", "--short").stdout == ""


def test_promote_reads_mdx_from_build_curriculum_tree_not_stale_starlight(tmp_path: Path) -> None:
    """Regression: promote must read MDX from the build's curriculum/ tree
    (where assemble_mdx writes), not from the build branch's DOCS_ROOT.

    The m20 (a1/my-morning) revert on 2026-05-23 shipped a broken module
    because promote_module read DOCS_ROOT, found a stale Phase 4 exemplar
    that happened to be there, and the diff against main was empty (since
    main also had the same stale file). The freshly-built MDX written by
    assemble_mdx to `curriculum/.../{slug}.mdx` never reached Starlight.

    This test seeds a build branch with a FRESH curriculum-tree MDX AND a
    STALE starlight-tree MDX, then asserts the FRESH content lands on main.
    """
    repo = _init_repo(tmp_path)
    branch = "build/a1/foo-20260520-010101"
    # Use the standard seed (writes fresh MDX to the curriculum tree path
    # via the updated helper) and then pollute the build branch's
    # DOCS_ROOT with a stale, divergent MDX as the regression bait.
    _seed_build_branch(repo, branch)
    _git(repo, "switch", branch)
    stale = repo / _rel_mdx("a1", "foo")
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text("stale exemplar — must NOT be promoted\n", encoding="utf-8")
    _git(repo, "add", str(_rel_mdx("a1", "foo")))
    env = {
        "GIT_AUTHOR_DATE": "2026-05-20T01:01:02 +0000",
        "GIT_COMMITTER_DATE": "2026-05-20T01:01:02 +0000",
    }
    _git(repo, "commit", "-m", "seed stale starlight mdx", env=env)
    _git(repo, "switch", "main")

    rc = promote_module.main(["--build-branch", branch, "--no-commit"], repo_root=repo)

    assert rc == 0
    promoted = (repo / _rel_mdx("a1", "foo")).read_text(encoding="utf-8")
    assert promoted == "mdx content\n", (
        f"Expected fresh build-tree MDX content on main; got stale starlight content: {promoted!r}"
    )


def test_promote_resolves_latest_branch(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    older = "build/a1/foo-20260520-010101"
    newer = "build/a1/foo-20260520-020202"
    _seed_build_branch(repo, newer, module_text="# Newer\n", stamp="2026-05-20T02:02:02 +0000")
    _seed_build_branch(repo, older, module_text="# Older\n", stamp="2026-05-20T01:01:01 +0000")

    rc = promote_module.main(["--latest", "--level", "a1", "--slug", "foo", "--no-commit"], repo_root=repo)

    assert rc == 0
    assert (repo / _rel_module("a1", "foo", "module.md")).read_text(encoding="utf-8") == "# Newer\n"
