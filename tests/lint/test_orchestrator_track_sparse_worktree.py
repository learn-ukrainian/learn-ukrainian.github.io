"""Deploy lint sees the same active tracks from a sparse linked worktree."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from scripts.lint.lint_prompts import scan_orchestrator_suites

_MANIFEST = """\
levels:
  a1:
    type: core
  bio:
    type: seminar
"""


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "Lint Fixture"
    env["GIT_AUTHOR_EMAIL"] = "lint-fixture@example.com"
    env["GIT_COMMITTER_NAME"] = "Lint Fixture"
    env["GIT_COMMITTER_EMAIL"] = "lint-fixture@example.com"
    return env


def _git(repo: Path, *args: str, env: dict[str, str]) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )


def _signature(violations: list[dict]) -> list[tuple[str, str]]:
    return sorted((item["rule"], item["message"]) for item in violations)


def test_orchestrator_track_lint_matches_full_checkout_from_a_linked_sparse_worktree(
    tmp_path: Path,
) -> None:
    """A curriculum tree excluded by sparse checkout still counts as active."""
    env = _git_env()
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init", "-b", "main", env=env)
    _git(primary, "config", "--local", "extensions.worktreeConfig", "true", env=env)

    manifest = primary / "curriculum" / "l2-uk-en" / "curriculum.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(_MANIFEST, encoding="utf-8")
    prompts = primary / "docs" / "prompts" / "orchestrators"
    (prompts / "a1").mkdir(parents=True)
    (prompts / "a1" / "keep.txt").write_text("a1\n", encoding="utf-8")
    (prompts / "retired-track").mkdir()
    (prompts / "retired-track" / "keep.txt").write_text("retired\n", encoding="utf-8")
    _git(primary, "add", "--", "curriculum", "docs", env=env)
    _git(primary, "-c", "core.hooksPath=/dev/null", "commit", "-m", "fixture", env=env)

    linked = tmp_path / "linked"
    _git(
        primary,
        "worktree",
        "add",
        "--no-checkout",
        "--no-track",
        "-b",
        "linked-check",
        str(linked),
        "HEAD",
        env=env,
    )
    try:
        _git(linked, "sparse-checkout", "set", "--no-cone", "--", "/*", "!/curriculum/", env=env)
        _git(linked, "reset", "--hard", "HEAD", env=env)

        sparse_manifest = linked / "curriculum" / "l2-uk-en" / "curriculum.yaml"
        sparse_prompts = linked / "docs" / "prompts" / "orchestrators"
        assert manifest.is_file()
        assert not sparse_manifest.exists()
        assert (sparse_prompts / "a1").is_dir()
        assert (sparse_prompts / "retired-track").is_dir()

        full = scan_orchestrator_suites(prompts, manifest)
        sparse = scan_orchestrator_suites(sparse_prompts, sparse_manifest)
        assert _signature(sparse) == _signature(full)

        not_active = [item for item in sparse if item["rule"] == "ORCH_TRACK_NOT_ACTIVE"]
        assert [item["message"] for item in not_active] == [
            "Prompt directory has no active curriculum.yaml level: retired-track"
        ]
        assert Path(not_active[0]["file"]).is_relative_to(linked)
        assert not any(item["rule"] == "ORCH_TRACK_NOT_ACTIVE" and item["message"].endswith(": a1") for item in sparse)
        assert any(
            item["rule"] == "ORCH_ACTIVE_TRACK_MISSING_PROMPT" and item["message"].endswith(": bio") for item in sparse
        )
    finally:
        subprocess.run(
            ["git", "-C", str(primary), "worktree", "remove", "--force", str(linked)],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
