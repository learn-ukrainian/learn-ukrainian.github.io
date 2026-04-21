"""Unit tests for the wiki dimensional review orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from wiki.review import DEFAULT_PRIMARY, DIMS, DimResult, _run_round


def test_run_round_emits_per_dim_progress_lines(tmp_path: Path, monkeypatch) -> None:
    article_path = tmp_path / "article.md"
    article_path.write_text("# Test\n", encoding="utf-8")
    logs: list[str] = []

    def fake_run_single_dim(
        *,
        dim: str,
        article_path: Path,
        article_text: str,
        primary: str,
        fallbacks: tuple[str, ...],
        cwd: Path,
    ) -> DimResult:
        assert article_path.name == "article.md"
        assert article_text == "# Test\n"
        assert cwd == tmp_path
        return DimResult(
            dim=dim,
            agent=primary,
            model="fake-model",
            score=8,
            verdict="PASS",
            findings=[],
            fixes=[],
            notes="",
            duration_s=0.1,
        )

    monkeypatch.setattr("wiki.review._run_single_dim", fake_run_single_dim)

    results = _run_round(
        article_path=article_path,
        article_text="# Test\n",
        agent_overrides={},
        cwd=tmp_path,
        round_num=2,
        progress_logger=logs.append,
    )

    assert set(results) == set(DIMS)
    assert any("Round 2" in line for line in logs)
    assert any("Round 2 complete" in line for line in logs)
    for dim in DIMS:
        assert any(
            f"▶ {dim}" in line and f"agent={DEFAULT_PRIMARY[dim]}" in line
            for line in logs
        )
        assert any(
            f"◀ {dim}" in line and "verdict=PASS, score=8" in line
            for line in logs
        )
