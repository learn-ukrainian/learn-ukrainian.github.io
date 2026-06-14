"""Unit tests for the wiki dimensional review orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from wiki.review import (
    DEFAULT_PRIMARY,
    DIMS,
    MAX_ROUNDS,
    SEMINAR_MAX_ROUNDS,
    DimResult,
    _run_round,
    core_reviewer_overrides,
    max_rounds_for_domain,
    review_article,
    seminar_reviewer_overrides,
)
from wiki.review_merger import Fix


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
        event_sink=None,
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


def test_max_rounds_for_domain_seminar_vs_core() -> None:
    """Seminar domains get extra rounds; core levels keep MAX_ROUNDS."""
    assert SEMINAR_MAX_ROUNDS > MAX_ROUNDS
    # Seminar tracks (no a1–c2 level token in the domain path).
    for seminar_domain in ("folk/genres", "folk/ritual", "hist/topics", "lit/drama"):
        assert max_rounds_for_domain(seminar_domain) == SEMINAR_MAX_ROUNDS
    # Core levels a1–c2 stay at the default budget.
    for core_domain in ("a1/letters", "a2/genitive-intro", "b1/x", "c1/stylistics"):
        assert max_rounds_for_domain(core_domain) == MAX_ROUNDS


def test_seminar_reviewer_overrides_routes_culture_dims_to_claude() -> None:
    """Seminar domains route register+factual+source_grounding to claude;
    core levels untouched."""
    # These are NOT claude by default — the override is what changes them
    # (register/factual default to agy, source_grounding to codex).
    assert DEFAULT_PRIMARY["register"] == "agy"
    assert DEFAULT_PRIMARY["factual_accuracy"] == "agy"
    assert DEFAULT_PRIMARY["source_grounding"] == "codex"
    expected = {
        "register": "claude",
        "factual_accuracy": "claude",
        "source_grounding": "claude",
    }
    for seminar_domain in ("folk/genres", "folk/ritual", "hist/topics", "lit/drama"):
        assert seminar_reviewer_overrides(seminar_domain) == expected
    # ukrainian_perspective is already claude by default — not in the override.
    assert "ukrainian_perspective" not in expected
    # Core levels keep the global default (empty override).
    for core_domain in ("a1/letters", "a2/genitive-intro", "c1/stylistics"):
        assert seminar_reviewer_overrides(core_domain) == {}


def test_core_reviewer_overrides_routes_noisy_core_dims_to_deepseek() -> None:
    """Core review routes factual/register off agy; seminar remains untouched."""
    assert core_reviewer_overrides("grammar/b1/aspect") == {
        "factual_accuracy": "deepseek",
        "register": "deepseek",
    }
    assert core_reviewer_overrides("folk/genres") == {}

    # Keep unrelated CORE dimensions on their global defaults.
    assert "source_grounding" not in core_reviewer_overrides("grammar/b1/aspect")
    assert "ukrainian_perspective" not in core_reviewer_overrides("grammar/b1/aspect")


# ── Seminar review-loop fixes (folk Session-19/20) ─────────────────────
#
# review_article must: (a) give seminar articles enough rounds for the
# reviewer's citation fixes to be confirmed (SEMINAR_MAX_ROUNDS); (b) not
# let an already-passing dim's ±1 wobble break a still-converging run
# (_min_score_regressed); and (c) report the BEST round, never a degraded
# tail round (folk Session-20: bylyny scored MIN 5→6→6→5 across 4 rounds —
# the find/replace loop + noisy reviewers made round 4 WORSE than 2-3).
# These tests pin all three.

_CONV_ARTICLE = (
    "# Билини київського циклу\n\n"
    "Билини виникли в Київській Русі.\n\n"
    "Старини збереглися переважно на Півночі.\n"
)
_CONV_FIX_1 = Fix(
    dim="source_grounding",
    find="Билини виникли в Київській Русі.",
    replace="Билини виникли в Київській Русі [S1].",
)
_CONV_FIX_2 = Fix(
    dim="source_grounding",
    find="Старини збереглися переважно на Півночі.",
    replace="Старини збереглися переважно на Півночі [S2].",
)


def _convergence_fake_run_single_dim(
    *,
    dim: str,
    article_path: Path,
    article_text: str,
    primary: str,
    fallbacks,
    cwd: Path,
    event_sink=None,
) -> DimResult:
    """source_grounding fails (6) until BOTH citations are present, then 9.

    Round state is derived from the article text itself (how many ``[S#]``
    are already applied), so the fake is stateless and round-order-agnostic
    — exactly mirroring how a real reviewer would re-score after a fix lands.
    Every other dim always passes.
    """
    if dim != "source_grounding":
        return DimResult(
            dim=dim, agent=primary, model="fake", score=9, verdict="PASS",
            findings=[], fixes=[], notes="", duration_s=0.0,
        )
    if "[S1]" not in article_text:
        fixes, score = [_CONV_FIX_1], 6
    elif "[S2]" not in article_text:
        fixes, score = [_CONV_FIX_2], 6
    else:
        fixes, score = [], 9
    return DimResult(
        dim=dim, agent=primary, model="fake", score=score,
        verdict="PASS" if score >= 8 else "REVISE",
        findings=[], fixes=fixes, notes="", duration_s=0.0,
    )


def test_seminar_rounds_converge_to_pass(tmp_path: Path, monkeypatch) -> None:
    """Extra rounds let the citation fixes be confirmed → PASS at round 3;
    2 rounds never reach an all-pass round."""
    monkeypatch.setattr(
        "wiki.review._run_single_dim", _convergence_fake_run_single_dim
    )

    # 2 rounds: the article never reaches an all-pass round → reported failure.
    article_2 = tmp_path / "two.md"
    article_2.write_text(_CONV_ARTICLE, encoding="utf-8")
    report_2, _ = review_article(article_2, max_rounds=MAX_ROUNDS)
    assert len(report_2.rounds) == 2
    assert report_2.final_verdict != "PASS"
    assert report_2.min_score == 6
    assert report_2.failing_dim == "source_grounding"

    # 4 rounds (seminar budget): round-3 re-reviews the now-cited text → an
    # all-pass round → PASS. A PASS breaks the loop immediately, so the
    # passing (best) round is the last one and its fully-cited text is returned.
    article_4 = tmp_path / "four.md"
    article_4.write_text(_CONV_ARTICLE, encoding="utf-8")
    report_4, final_4 = review_article(article_4, max_rounds=SEMINAR_MAX_ROUNDS)
    assert report_4.final_verdict == "PASS"
    assert report_4.min_score >= 8
    assert len(report_4.rounds) == 3  # converged at round 3, stopped early
    assert "[S1]" in final_4 and "[S2]" in final_4


# best-round selection: a diverging trajectory must report the BEST round.
_DIV_ARTICLE = "# Билини\n\nПоходження билин сягає Київської Русі.\n"
_DIV_FIX = Fix(
    dim="source_grounding",
    find="Походження билин сягає Київської Русі.",
    replace="Походження билин сягає Київської Русі [S1].",
)


def _divergence_fake_run_single_dim(
    *,
    dim: str,
    article_path: Path,
    article_text: str,
    primary: str,
    fallbacks,
    cwd: Path,
    event_sink=None,
) -> DimResult:
    """register is high (9) on the original but a noisy reviewer tanks it to
    5 once a fix lands; source_grounding holds at 6. So MIN goes 6 (round 1)
    → 5 (round 2): the tail round is WORSE, exactly bylyny's 5→6→6→5 shape.
    """
    has_fix = "[S1]" in article_text
    if dim == "source_grounding":
        return DimResult(
            dim=dim, agent=primary, model="fake", score=6, verdict="REVISE",
            findings=[], fixes=[] if has_fix else [_DIV_FIX], notes="",
            duration_s=0.0,
        )
    if dim == "register":
        score = 5 if has_fix else 9
        return DimResult(
            dim=dim, agent=primary, model="fake", score=score,
            verdict="PASS" if score >= 8 else "REVISE",
            findings=[], fixes=[], notes="", duration_s=0.0,
        )
    return DimResult(
        dim=dim, agent=primary, model="fake", score=9, verdict="PASS",
        findings=[], fixes=[], notes="", duration_s=0.0,
    )


def test_best_round_selected_over_degraded_tail(
    tmp_path: Path, monkeypatch,
) -> None:
    monkeypatch.setattr(
        "wiki.review._run_single_dim", _divergence_fake_run_single_dim
    )
    art = tmp_path / "div.md"
    art.write_text(_DIV_ARTICLE, encoding="utf-8")

    report, _ = review_article(art, max_rounds=SEMINAR_MAX_ROUNDS)

    # Round 1 MIN=6 (register 9, sg 6); round 2 MIN=5 (register tanked to 5).
    # The report MUST reflect the BEST round (6) and its failing set, NOT the
    # degraded tail (5) — returning the last round would ship a worse score
    # AND make a larger max_rounds budget unsafe.
    assert report.min_score == 6
    assert report.final_verdict != "PASS"
    assert report.failing_dims == ["source_grounding"]  # round-1's set, not {sg, register}
    assert len(report.rounds) == 2


# ── Regression guard scoping: ±1 wobble must not kill a converging run ──
#
# Under the OLD guard (``any dim's score dropped``), an already-passing dim
# wobbling 9→8 within reviewer noise broke the loop BEFORE the failing dim's
# round-3 citation fix got its confirming round-4 re-review — a converging
# seminar article reported a stale failure (folk Session-20: register's 7→6
# wobble is exactly what kept bylyny from converging). The MIN-based guard
# tolerates the wobble because the MIN (driven by the still-failing dim) did
# not regress. This test fails under the old per-dim guard.

_GUARD_ARTICLE = (
    "# Билини\n\n"
    "Походження билин сягає Київської Русі.\n\n"
    "Чижевський аналізує тонічний вірш.\n\n"
    "Попович підкреслює втрату старокиївських варіантів.\n"
)
_GUARD_FIXES = {
    "[S1]": Fix(
        dim="source_grounding",
        find="Походження билин сягає Київської Русі.",
        replace="Походження билин сягає Київської Русі [S1].",
    ),
    "[S2]": Fix(
        dim="source_grounding",
        find="Чижевський аналізує тонічний вірш.",
        replace="Чижевський аналізує тонічний вірш [S2].",
    ),
    "[S3]": Fix(
        dim="source_grounding",
        find="Попович підкреслює втрату старокиївських варіантів.",
        replace="Попович підкреслює втрату старокиївських варіантів [S3].",
    ),
}


def _guard_fake_run_single_dim(
    *,
    dim: str,
    article_path: Path,
    article_text: str,
    primary: str,
    fallbacks,
    cwd: Path,
    event_sink=None,
) -> DimResult:
    """source_grounding needs THREE citation fixes (passes only on round 4);
    register wobbles 9→8 (always passing) once ≥2 citations are present.
    """
    present = sum(tok in article_text for tok in ("[S1]", "[S2]", "[S3]"))
    if dim == "source_grounding":
        if present >= 3:
            fixes, score = [], 9
        else:
            missing = next(t for t in ("[S1]", "[S2]", "[S3]") if t not in article_text)
            fixes, score = [_GUARD_FIXES[missing]], 6
        return DimResult(
            dim=dim, agent=primary, model="fake", score=score,
            verdict="PASS" if score >= 8 else "REVISE",
            findings=[], fixes=fixes, notes="", duration_s=0.0,
        )
    if dim == "register":
        # Already-passing, but wobbles DOWN within noise once the article
        # picks up citations — the exact ±1 that broke the old guard.
        score = 8 if present >= 2 else 9
        return DimResult(
            dim=dim, agent=primary, model="fake", score=score, verdict="PASS",
            findings=[], fixes=[], notes="", duration_s=0.0,
        )
    return DimResult(
        dim=dim, agent=primary, model="fake", score=9, verdict="PASS",
        findings=[], fixes=[], notes="", duration_s=0.0,
    )


def test_regression_guard_tolerates_passing_dim_wobble(
    tmp_path: Path, monkeypatch,
) -> None:
    monkeypatch.setattr(
        "wiki.review._run_single_dim", _guard_fake_run_single_dim
    )
    article = tmp_path / "guard.md"
    article.write_text(_GUARD_ARTICLE, encoding="utf-8")

    report, final = review_article(article, max_rounds=SEMINAR_MAX_ROUNDS)

    # The old per-dim guard would break at round 3 (register 9→8) and report
    # a stale source_grounding=6 failure; the MIN-based guard runs round 4
    # and lets source_grounding's third citation be confirmed → PASS.
    assert report.final_verdict == "PASS"
    assert len(report.rounds) == 4
    assert report.min_score == 8  # driven by register's tolerated 9→8 wobble
    # Document that the wobble actually happened (guard tolerated it):
    assert report.rounds[1].dim_results["register"].score == 9
    assert report.rounds[3].dim_results["register"].score == 8
    assert all(tok in final for tok in ("[S1]", "[S2]", "[S3]"))
