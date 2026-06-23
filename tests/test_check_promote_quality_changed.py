from __future__ import annotations

from pathlib import Path

import pytest

from scripts.audit import check_promote_quality_changed as check_changed
from scripts.build import promote_quality_gate
from scripts.common.thresholds import seminar_promote_floors_for

SLUG = "koliadky-shchedrivky"


def _write_module(repo_root: Path, *, track: str = "folk", slug: str = SLUG) -> Path:
    module_dir = repo_root / "curriculum" / "l2-uk-en" / track / slug
    plan_dir = repo_root / "curriculum" / "l2-uk-en" / "plans" / track
    mdx_dir = repo_root / "site" / "src" / "content" / "docs" / track
    module_dir.mkdir(parents=True)
    plan_dir.mkdir(parents=True)
    mdx_dir.mkdir(parents=True)
    (plan_dir / f"{slug}.yaml").write_text("title: Stub plan\n", encoding="utf-8")
    (module_dir / "module.md").write_text("# Stub module\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text("- prompt: Stub\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("- term: Stub\n", encoding="utf-8")
    (module_dir / "resources.yaml").write_text(
        "- url: https://example.com\n",
        encoding="utf-8",
    )
    (mdx_dir / f"{slug}.mdx").write_text("lesson\n", encoding="utf-8")
    return module_dir


def _passing_scores(track: str = "folk") -> dict[str, float]:
    floors = seminar_promote_floors_for(track)
    assert floors is not None
    return {dim: floor + 0.1 for dim, floor in floors.items()}


def _record_sidecar(
    repo_root: Path,
    module_dir: Path,
    *,
    scores: dict[str, float] | None = None,
) -> None:
    promote_quality_gate.record(
        "folk",
        SLUG,
        module_dir=module_dir,
        repo_root=repo_root,
        writer_family="anthropic",
        writer_agent="claude",
        writer_model="claude-opus-4.8",
        reviewer_family="openai",
        reviewer_agent="codex",
        reviewer_model="gpt-5",
        scores=scores or _passing_scores(),
        evidence={"summary": "synthetic test fixture"},
        scored_at="2026-06-23T00:00:00Z",
    )


def test_enrolled_below_floor_sidecar_exits_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root = tmp_path / "repo"
    module_dir = _write_module(repo_root)
    scores = _passing_scores()
    scores["beauty"] = 8.4
    _record_sidecar(repo_root, module_dir, scores=scores)

    rc = check_changed.main(
        [
            "--repo-root",
            str(repo_root),
            "--changed-file",
            f"curriculum/l2-uk-en/folk/{SLUG}/module.md",
        ]
    )

    assert rc == 1
    out = capsys.readouterr().out
    assert f"FAIL: folk/{SLUG}" in out
    assert "score below floor: beauty" in out
    assert "enrolled_failures=1" in out


@pytest.mark.parametrize(
    "changed_path",
    [
        f"site/src/content/docs/folk/{SLUG}.mdx",
        f"curriculum/l2-uk-en/folk/{SLUG}/module.md",
        f"curriculum/l2-uk-en/folk/{SLUG}/promote_quality.json",
    ],
)
def test_enrolled_passing_sidecar_exits_zero_from_each_trigger_shape(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    changed_path: str,
) -> None:
    repo_root = tmp_path / "repo"
    module_dir = _write_module(repo_root)
    _record_sidecar(repo_root, module_dir)

    rc = check_changed.main(
        ["--repo-root", str(repo_root), "--changed-file", changed_path]
    )

    assert rc == 0
    out = capsys.readouterr().out
    assert f"PASS: folk/{SLUG}" in out
    assert "enrolled_failures=0" in out


def test_unenrolled_seminar_deployed_mdx_changed_is_notice_only(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root = tmp_path / "repo"

    rc = check_changed.main(
        [
            "--repo-root",
            str(repo_root),
            "--changed-file",
            "site/src/content/docs/bio/lesia-ukrainka.mdx",
        ]
    )

    assert rc == 0
    out = capsys.readouterr().out
    assert "NOTICE: bio/lesia-ukrainka not enrolled" in out
    assert "enrolled_failures=0" in out


def test_no_seminar_change_exits_zero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root = tmp_path / "repo"

    rc = check_changed.main(
        [
            "--repo-root",
            str(repo_root),
            "--changed-file",
            "README.md",
            "--changed-file",
            "curriculum/l2-uk-en/a1/hello/module.md",
        ]
    )

    assert rc == 0
    out = capsys.readouterr().out
    assert "checked 0 gated seminar module(s)" in out


def test_enrolled_source_without_deployed_mdx_is_not_gated(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root = tmp_path / "repo"
    _write_module(repo_root, slug="unbuilt-folk")
    (repo_root / "site" / "src" / "content" / "docs" / "folk" / "unbuilt-folk.mdx").unlink()

    rc = check_changed.main(
        [
            "--repo-root",
            str(repo_root),
            "--changed-file",
            "curriculum/l2-uk-en/folk/unbuilt-folk/module.md",
        ]
    )

    assert rc == 0
    out = capsys.readouterr().out
    assert "checked 0 gated seminar module(s)" in out
