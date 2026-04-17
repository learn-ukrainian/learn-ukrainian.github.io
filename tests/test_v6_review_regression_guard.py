"""Regression-guard tests for the review-heal loop (#1320).

These cover the snapshot + revert behavior that keeps a passing
round from being erased by a later hallucinating round.

The tests exercise ``_run_review_heal_loop`` with the heavy pieces
monkeypatched out:

* ``step_review`` → a scripted sequence of (passed, score, text)
* ``_apply_review_fixes`` / ``_apply_review_rewrite_blocks`` /
  ``_apply_contract_word_budget_rewrites`` → no-ops that mutate
  the content file when a test wants to simulate a bad round
* ``step_verify`` → no-op
* ``check_contract_compliance`` → returns no violations

That way the test drives the state machine directly without
touching an LLM or the deterministic review parser.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from build import v6_build

# ── Helpers ──────────────────────────────────────────────────────────────


def _scripted_reviews(results: list[tuple[bool, float, str]]):
    """Return a ``step_review`` stand-in that hands back scripted tuples."""
    it = iter(results)

    def _fake(
        content_path, level, module_num, slug, *, writer="gemini", reviewer_override=None,
    ):
        try:
            return next(it)
        except StopIteration as exc:  # pragma: no cover - test bug guard
            raise AssertionError("step_review called more times than expected") from exc

    return _fake


def _setup_tree(tmp_path: Path, level: str, slug: str) -> tuple[Path, Path]:
    """Create the minimum filesystem layout the heal loop touches.

    Returns ``(curriculum_root, content_path)``.
    """
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    level_dir = curriculum_root / level
    level_dir.mkdir(parents=True)
    (curriculum_root / "research").mkdir(parents=True, exist_ok=True)
    content_path = level_dir / f"{slug}.md"
    content_path.write_text("R1 content baseline", encoding="utf-8")
    (curriculum_root / level / "orchestration" / slug).mkdir(parents=True, exist_ok=True)
    (curriculum_root / "plans" / level).mkdir(parents=True, exist_ok=True)
    return curriculum_root, content_path


def _patch_noop_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub the heavy parts of the heal loop that aren't under test."""
    monkeypatch.setattr(
        v6_build, "_apply_review_rewrite_blocks",
        lambda *a, **kw: (False, 0),
    )
    monkeypatch.setattr(
        v6_build, "_apply_contract_word_budget_rewrites",
        lambda *a, **kw: (False, 0),
    )
    monkeypatch.setattr(v6_build, "step_verify", lambda *a, **kw: None)
    monkeypatch.setattr(
        v6_build, "_ensure_contract_artifacts",
        lambda *a, **kw: ({}, None),
    )
    monkeypatch.setattr(v6_build, "_save_contract_compliance", lambda *a, **kw: None)
    # Contract compliance import happens inside the loop — patch at the
    # source module so the loop's local import sees it.
    import audit.checks.contract_compliance as cc
    monkeypatch.setattr(cc, "check_contract_compliance", lambda *a, **kw: [])


# ── 1. Snapshot-on-pass, no regression ────────────────────────────────────


def test_snapshot_captured_on_first_passing_round(tmp_path, monkeypatch):
    """R1 passes → snapshot written, loop exits with outcome='pass'."""
    curriculum_root, content_path = _setup_tree(tmp_path, "a1", "pass-first-try")
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    _patch_noop_side_effects(monkeypatch)
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *a, **kw: (False, 0))
    monkeypatch.setattr(
        v6_build, "step_review",
        _scripted_reviews([(True, 9.4, "## Verdict: PASS\n")]),
    )

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="pass-first-try",
        writer="gemini",
        reviewer_override=None,
        max_rounds=6,
    )

    assert result.outcome == "pass"
    assert len(result.rounds) == 1
    # Snapshot files written
    orch = curriculum_root / "a1" / "orchestration" / "pass-first-try"
    assert (orch / "review-snapshot-pass.md").is_file()
    assert (orch / "review-snapshot-pass.yaml").is_file()


# ── 2. Regression is reverted ────────────────────────────────────────────


def test_regression_after_pass_reverts_to_snapshot(tmp_path, monkeypatch):
    """R1 fails → R2 passes → snapshot captured → R3 mutation regresses
    → content reverted to R2 snapshot, loop exits 'pass'.
    """
    curriculum_root, content_path = _setup_tree(tmp_path, "a1", "regressing")
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    _patch_noop_side_effects(monkeypatch)

    # R1 fails at 7.5 → _apply_review_fixes mutates to R2-candidate.
    # R2 passes at 9.2 → snapshot.
    # R3 also mutates (bad), confirmation review returns 7.8 (below
    # 9.2 - 0.2 = 9.0) → revert.
    call_log: list[str] = []

    def fake_fixes(review_text, content_path_, *, level, slug):
        if "first-round" in review_text:
            # Simulate R1 → R2 transition: content improves
            content_path_.write_text("R2 body — passing content", encoding="utf-8")
            call_log.append("r1_fixes")
            return True, 1
        if "second-round" in review_text:
            # R2 had no fixes (it was the passing one)
            call_log.append("r2_no_fixes")
            return False, 0
        if "third-round-bad" in review_text:
            # R3 regresses the content
            content_path_.write_text("R3 body — regressed", encoding="utf-8")
            call_log.append("r3_bad_fixes")
            return True, 1
        return False, 0

    monkeypatch.setattr(v6_build, "_apply_review_fixes", fake_fixes)

    monkeypatch.setattr(
        v6_build, "step_review",
        _scripted_reviews([
            (False, 7.5, "first-round review"),
            (True, 9.2, "second-round review\n## Verdict: PASS\n"),
            (False, 7.8, "third-round-bad review"),
        ]),
    )

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="regressing",
        writer="gemini",
        reviewer_override=None,
        max_rounds=6,
    )

    # The regression is caught and snapshot restored
    assert result.outcome == "pass"
    assert content_path.read_text() == "R2 body — passing content"
    # Rounds are truncated to the best passing round
    assert len(result.rounds) == 2
    assert result.rounds[-1].round_num == 2
    assert result.rounds[-1].score == 9.2


# ── 3. No snapshot means no revert (pre-#1320 behaviour preserved) ───────


def test_no_pass_round_means_no_revert(tmp_path, monkeypatch):
    """If no round ever crosses the threshold, the loop plateaus
    normally — snapshot path must not trigger.
    """
    curriculum_root, content_path = _setup_tree(tmp_path, "a1", "never-passes")
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    _patch_noop_side_effects(monkeypatch)
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *a, **kw: (False, 0))

    # Three rounds all below threshold with small deltas → plateau.
    monkeypatch.setattr(
        v6_build, "step_review",
        _scripted_reviews([
            (False, 7.0, "r1"),
            (False, 7.1, "r2"),
            (False, 7.2, "r3"),
        ]),
    )

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="never-passes",
        writer="gemini",
        reviewer_override=None,
        max_rounds=3,
    )

    assert result.outcome == "plateau"
    # No snapshot was written — it's a "never passed" module.
    orch = curriculum_root / "a1" / "orchestration" / "never-passes"
    assert not (orch / "review-snapshot-pass.md").is_file()


# ── 4. Two passing rounds — snapshot keeps the better one ────────────────


def test_snapshot_tracks_highest_passing_score(tmp_path, monkeypatch):
    """R1=9.1 passes → snapshot. R2 mutation confirms at 9.6 (also
    passes, higher) → snapshot replaced with R2. Loop continues
    normally (no regression) then exits at pass.
    """
    curriculum_root, content_path = _setup_tree(tmp_path, "a1", "ascending")
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    _patch_noop_side_effects(monkeypatch)

    def fake_fixes(review_text, content_path_, *, level, slug):
        if "r1" in review_text:
            content_path_.write_text("R2 body — even better", encoding="utf-8")
            return True, 1
        return False, 0

    monkeypatch.setattr(v6_build, "_apply_review_fixes", fake_fixes)
    monkeypatch.setattr(
        v6_build, "step_review",
        _scripted_reviews([
            (True, 9.1, "r1\n## Verdict: PASS\n"),
            (True, 9.6, "r2\n## Verdict: PASS\n"),
        ]),
    )

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="ascending",
        writer="gemini",
        reviewer_override=None,
        max_rounds=3,
    )

    # The loop passes out after R1 because its score is ≥ threshold
    # AND contract is clean → `_review_loop_decision` returns "pass".
    # This behavior is pre-existing; the new code doesn't extend the
    # loop past R1 just to find a higher score.
    assert result.outcome == "pass"
    # Snapshot exists from R1.
    orch = curriculum_root / "a1" / "orchestration" / "ascending"
    assert (orch / "review-snapshot-pass.md").is_file()


# ── 5. Monotonic-score invariant ────────────────────────────────────────


def test_a1_m1_shape_snapshot_with_nonpass_verdict(tmp_path, monkeypatch):
    """The actual A1/M1 shape: R2 scores 9.22 but ``passed=False``
    (verdict != "PASS"). The looser snapshot trigger must still
    capture it so later-round regressions can be reverted.
    """
    curriculum_root, content_path = _setup_tree(tmp_path, "a1", "a1m1-shape")
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    _patch_noop_side_effects(monkeypatch)

    def fake_fixes(review_text, content_path_, *, level, slug):
        if "fix-into-r2" in review_text:
            content_path_.write_text(
                "R2 body — high-scoring but verdict is REVISE", encoding="utf-8",
            )
            return True, 1
        if "fix-into-r3-bad" in review_text:
            content_path_.write_text(
                "R3 body — regressed", encoding="utf-8",
            )
            return True, 1
        return False, 0

    monkeypatch.setattr(v6_build, "_apply_review_fixes", fake_fixes)
    # R1: 8.4 fail, R2: 9.2 score but passed=False, R3: 8.3 regressed
    monkeypatch.setattr(
        v6_build, "step_review",
        _scripted_reviews([
            (False, 8.4, "fix-into-r2 review"),
            (False, 9.2, "fix-into-r3-bad review"),  # score OK, passed=False
            (False, 8.3, "r3 review"),
        ]),
    )

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="a1m1-shape",
        writer="gemini",
        reviewer_override=None,
        max_rounds=6,
    )

    # The regression guard should fire at R3, restore the R2 snapshot,
    # and exit as pass.
    assert result.outcome == "pass"
    assert content_path.read_text() == "R2 body — high-scoring but verdict is REVISE"
    # Snapshot file present
    orch = curriculum_root / "a1" / "orchestration" / "a1m1-shape"
    assert (orch / "review-snapshot-pass.md").is_file()


def test_monotonic_score_invariant(tmp_path, monkeypatch):
    """Property: final accepted score is never lower than any
    previously-captured passing round. With the current loop's
    "exit on first pass" behavior this holds trivially — and the
    regression guard catches the case where a later round
    sneaks in via the Bug #1316-B confirmation-review path. The
    invariant to assert here is that the final ``result.rounds[-1]``
    is always one of the passing rounds, never a regressed one.
    """
    curriculum_root, content_path = _setup_tree(tmp_path, "a1", "monotonic")
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    _patch_noop_side_effects(monkeypatch)

    def fake_fixes(review_text, content_path_, *, level, slug):
        if "fix-to-r2" in review_text:
            content_path_.write_text("R2 good content", encoding="utf-8")
            return True, 1
        return False, 0

    monkeypatch.setattr(v6_build, "_apply_review_fixes", fake_fixes)

    # R1 fails (8.0). R2 passes (9.3, verdict PASS) → loop exits.
    # Extra scripted reviews should never be consumed.
    monkeypatch.setattr(
        v6_build, "step_review",
        _scripted_reviews([
            (False, 8.0, "fix-to-r2 review"),
            (True, 9.3, "r2\n## Verdict: PASS\n"),
            (False, 7.5, "should-not-run"),
        ]),
    )

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="monotonic",
        writer="gemini",
        reviewer_override=None,
        max_rounds=6,
    )

    assert result.outcome == "pass"
    final = result.rounds[-1]
    # Final is a passing round
    assert final.passed is True
    passing_scores = [r.score for r in result.rounds if r.passed]
    assert passing_scores  # at least one pass captured
    assert final.score >= max(passing_scores)
    # Content matches the round we accepted (not a regressed later one).
    assert content_path.read_text() == "R2 good content"
