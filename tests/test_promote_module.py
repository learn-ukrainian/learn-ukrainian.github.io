from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.build import promote_quality_gate
from scripts.common.thresholds import seminar_promote_floors_for
from scripts.sync import promote_module


def _git(
    repo: Path,
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("GIT_", "PRE_COMMIT"))
    }
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
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "base")
    return repo


def _rel_module(level: str, slug: str, filename: str) -> Path:
    return Path("curriculum") / "l2-uk-en" / level / slug / filename


def _rel_plan(level: str, slug: str) -> Path:
    return Path("curriculum") / "l2-uk-en" / "plans" / level / f"{slug}.yaml"


def _rel_mdx_build(level: str, slug: str) -> Path:
    return Path("curriculum") / "l2-uk-en" / level / slug / f"{slug}.mdx"


def _rel_mdx(level: str, slug: str) -> Path:
    return Path("site") / "src" / "content" / "docs" / level / f"{slug}.mdx"


def _write_plan_on_main(repo: Path, *, level: str, slug: str) -> None:
    plan = repo / _rel_plan(level, slug)
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("title: Promote fixture\n", encoding="utf-8")
    _git(repo, "add", plan.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", f"plan {level}/{slug}")


def _passing_scores(level: str) -> dict[str, float]:
    floors = seminar_promote_floors_for(level)
    assert floors is not None
    return {dim: floor + 0.1 for dim, floor in floors.items()}


def _seed_build_branch(
    repo: Path,
    branch: str,
    *,
    level: str,
    slug: str,
    scores: dict[str, float] | None = None,
) -> None:
    _git(repo, "switch", "-c", branch)
    files = {
        "module.md": "# Module\n",
        "activities.yaml": "- kind: quiz\n",
        "vocabulary.yaml": "- word: test\n",
        "resources.yaml": "resources: []\n",
    }
    for filename, content in files.items():
        path = repo / _rel_module(level, slug, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    mdx = repo / _rel_mdx_build(level, slug)
    mdx.parent.mkdir(parents=True, exist_ok=True)
    mdx.write_text("mdx content\n", encoding="utf-8")
    if scores is not None:
        promote_quality_gate.record(
            level,
            slug,
            module_dir=repo / _rel_module(level, slug, ""),
            repo_root=repo,
            writer_family="anthropic",
            writer_agent="claude",
            writer_model="claude-opus-4.8",
            reviewer_family="openai",
            reviewer_agent="codex",
            reviewer_model="gpt-5",
            scores=scores,
            evidence={"summary": "synthetic promote fixture"},
            scored_at="2026-06-23T00:00:00Z",
        )
    _git(repo, "add", ".")
    _git(
        repo,
        "commit",
        "-m",
        f"build {branch}",
        env={
            "GIT_AUTHOR_DATE": "2026-06-23T00:00:00 +0000",
            "GIT_COMMITTER_DATE": "2026-06-23T00:00:00 +0000",
        },
    )
    _git(repo, "switch", "main")


def _stub_folk_readings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        promote_module,
        "_run_generate_readings",
        lambda _repo_root, _source: (0, []),
    )


def test_promote_fails_closed_for_failing_enrolled_sidecar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _init_repo(tmp_path)
    level = "folk"
    slug = "quality-fixture"
    branch = f"build/{level}/{slug}-20260623-000000"
    _write_plan_on_main(repo, level=level, slug=slug)
    scores = _passing_scores(level)
    scores["beauty"] = 8.4
    _seed_build_branch(repo, branch, level=level, slug=slug, scores=scores)
    _stub_folk_readings(monkeypatch)

    rc = promote_module.main(["--build-branch", branch, "--no-commit"], repo_root=repo)

    assert rc == 1
    captured = capsys.readouterr()
    assert f"ERROR promote_quality failed for {level}/{slug}" in captured.err
    assert "score below floor: beauty" in captured.err


def test_promote_proceeds_for_passing_enrolled_sidecar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _init_repo(tmp_path)
    level = "folk"
    slug = "quality-fixture"
    branch = f"build/{level}/{slug}-20260623-000000"
    _write_plan_on_main(repo, level=level, slug=slug)
    _seed_build_branch(repo, branch, level=level, slug=slug, scores=_passing_scores(level))
    _stub_folk_readings(monkeypatch)

    rc = promote_module.main(["--build-branch", branch, "--no-commit"], repo_root=repo)

    assert rc == 0
    captured = capsys.readouterr()
    assert f"PASS promote_quality {level}/{slug}" in captured.out
    assert (repo / _rel_module(level, slug, "promote_quality.json")).exists()
    assert (repo / _rel_mdx(level, slug)).read_text(encoding="utf-8") == "mdx content\n"


def test_promote_proceeds_for_unenrolled_seminar_without_sidecar(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    level = "bio"
    slug = "quality-fixture"
    branch = f"build/{level}/{slug}-20260623-000000"
    _seed_build_branch(repo, branch, level=level, slug=slug)

    rc = promote_module.main(["--build-branch", branch, "--no-commit"], repo_root=repo)

    assert rc == 0
    assert not (repo / _rel_module(level, slug, "promote_quality.json")).exists()
    assert (repo / _rel_mdx(level, slug)).exists()
