"""Tests for deterministic-dimension review overrides (#1321).

Covers the four recognized override shapes, the tolerance boundary,
and the exact A1/M1 R4 hallucination that motivated the feature.

The tests call :func:`v6_build._apply_deterministic_overrides`
directly rather than running ``step_review`` end-to-end — this keeps
the fixtures small (a content file + a parsed review struct) and
avoids any live-LLM dependency.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from build import v6_build

# ── Helpers ──────────────────────────────────────────────────────────────


def _make_parsed(
    *,
    score: float,
    verdict: str = "REVISE",
    dims: list[dict],
    findings_count: int = 1,
) -> v6_build.ReviewParseResult:
    """Build a ReviewParseResult matching the real parser's shape."""
    raw_scores = [int(d["score"]) for d in dims]
    dim_floor_fail = any(
        d["score"] < v6_build.REVIEW_TARGET_SCORE
        and v6_build._evidence_has_error_keyword(d.get("evidence", ""))
        for d in dims
    )
    passed = score >= v6_build.REVIEW_TARGET_SCORE and verdict == "PASS" and not dim_floor_fail
    return v6_build.ReviewParseResult(
        score=score,
        verdict=verdict,
        raw_scores=raw_scores,
        parsed_scores=dims,
        findings_count=findings_count,
        dim_floor_fail=dim_floor_fail,
        reviewer_contract_invalid=False,
        passed=passed,
    )


def _write_content(tmp_path: Path, body: str) -> Path:
    """Write a test module with at-least the shape ``extract_core_content`` expects."""
    path = tmp_path / "sounds-letters-and-hello.md"
    path.write_text(body, encoding="utf-8")
    return path


# ── 1. Word-count hallucination: the A1/M1 R4 case ───────────────────────


def test_word_count_hallucination_overrides_structural_integrity(tmp_path):
    """Reviewer claims 'word count 1163 below 1200 target' but the file has 1300.

    Expected: Structural Integrity (dim 7) is overridden from 7 → 9,
    the weighted score rises, and the override event fires.
    """
    # 1300 Ukrainian-word body (core content well above 1200 target)
    body = "## Section\n\n" + ("слово " * 1300)
    content_path = _write_content(tmp_path, body)

    dims = [
        {"dimension": 1, "name": "Plan adherence", "score": 9, "evidence": "good"},
        {"dimension": 2, "name": "Linguistic accuracy", "score": 9, "evidence": "clean"},
        {"dimension": 3, "name": "Pedagogical quality", "score": 9, "evidence": "ok"},
        {"dimension": 4, "name": "Vocabulary coverage", "score": 9, "evidence": "ok"},
        {"dimension": 5, "name": "Exercise quality", "score": 9, "evidence": "ok"},
        {"dimension": 6, "name": "Engagement & tone", "score": 9, "evidence": "ok"},
        {
            "dimension": 7,
            "name": "Structural integrity",
            "score": 7,
            # Exact phrasing from A1/M1 R4
            "evidence": "the pipeline word count is 1163, below the 1200 target",
        },
        {"dimension": 8, "name": "Cultural accuracy", "score": 10, "evidence": "ok"},
        {"dimension": 9, "name": "Dialogue & conversation quality", "score": 9, "evidence": "ok"},
    ]
    parsed = _make_parsed(score=8.8, dims=dims)

    new_parsed, overrides = v6_build._apply_deterministic_overrides(
        parsed,
        content_path=content_path,
        level="a1",
        slug="sounds-letters-and-hello",
        word_target=1200,
    )

    assert len(overrides) == 1
    assert overrides[0]["dim"] == 7
    assert overrides[0]["claim"] == "word_count_below_target"
    assert overrides[0]["reviewer_value"] == 1163
    assert overrides[0]["deterministic_value"] >= 1200
    # Dim 7 score lifted out of the floor
    dim7 = next(d for d in new_parsed.parsed_scores if d["dimension"] == 7)
    assert dim7["score"] >= 9
    assert dim7["evidence"].startswith("[OVERRIDE:")
    # Weighted score moves up
    assert new_parsed.score > parsed.score
    # dim_floor_fail clears on that dimension
    assert new_parsed.dim_floor_fail is False


def test_override_flips_outcome_to_pass_when_verdict_pass(tmp_path):
    """The exact save-the-module case: R4 says REVISE because of the
    hallucinated word count; with the override + a PASS verdict, the
    result passes. (Under the current pipeline the reviewer's verdict
    drives the final gate; this test asserts the gate respects
    overrides when the verdict cooperates.)
    """
    body = "## Section\n\n" + ("слово " * 1400)
    content_path = _write_content(tmp_path, body)

    dims = [
        {"dimension": i, "name": f"Dim{i}", "score": 10, "evidence": "ok"}
        for i in range(1, 10)
    ]
    # Dim 7 is the only low one and it's a false claim
    dims[6] = {
        "dimension": 7,
        "name": "Structural integrity",
        "score": 7,
        "evidence": "word count is 1163 below the 1200 target",
    }
    parsed = _make_parsed(score=8.85, verdict="PASS", dims=dims)

    new_parsed, overrides = v6_build._apply_deterministic_overrides(
        parsed,
        content_path=content_path,
        level="a1",
        slug="x",
        word_target=1200,
    )

    assert overrides  # at least one override applied
    assert new_parsed.passed is True
    assert new_parsed.score >= v6_build.REVIEW_TARGET_SCORE


# ── 2. Correct reviewer claims must NOT trigger an override ───────────────


def test_truthful_low_word_count_is_not_overridden(tmp_path):
    """When the reviewer's claim is CORRECT (content really is under
    target), leave the dim score alone.
    """
    body = "## Short\n\n" + ("слово " * 800)  # genuinely ~800 < 1200
    content_path = _write_content(tmp_path, body)

    dims = [
        {"dimension": i, "name": f"Dim{i}", "score": 10, "evidence": "ok"}
        for i in range(1, 10)
    ]
    dims[6] = {
        "dimension": 7,
        "name": "Structural integrity",
        "score": 7,
        "evidence": "word count is 800, below the 1200 target",
    }
    parsed = _make_parsed(score=8.85, dims=dims)

    new_parsed, overrides = v6_build._apply_deterministic_overrides(
        parsed,
        content_path=content_path,
        level="a1",
        slug="x",
        word_target=1200,
    )

    assert overrides == []
    assert new_parsed.parsed_scores[6]["score"] == 7
    assert new_parsed.score == parsed.score


def test_tolerance_edge_case(tmp_path):
    """A count that's within the 5 % tolerance below target still
    qualifies for override — the reviewer is technically right but
    the production gate treats 1160 ≈ 1200 as acceptable slack.
    """
    body = "## Section\n\n" + ("слово " * 1160)  # 1160 core words
    content_path = _write_content(tmp_path, body)

    dims = [
        {"dimension": i, "name": f"Dim{i}", "score": 10, "evidence": "ok"}
        for i in range(1, 10)
    ]
    dims[6] = {
        "dimension": 7,
        "name": "Structural integrity",
        "score": 7,
        "evidence": "word count is 1160 below 1200 target",
    }
    parsed = _make_parsed(score=8.85, dims=dims)

    _, overrides = v6_build._apply_deterministic_overrides(
        parsed,
        content_path=content_path,
        level="a1",
        slug="x",
        word_target=1200,
    )

    # 1160 / 1200 = 96.67 % — within the 5 % tolerance band → override.
    assert len(overrides) == 1


def test_tolerance_outside_band_no_override(tmp_path):
    """A genuine ~10 % shortfall stays un-overridden."""
    body = "## Section\n\n" + ("слово " * 1050)  # 1050 core words ≈ 12.5 % below
    content_path = _write_content(tmp_path, body)

    dims = [
        {"dimension": i, "name": f"Dim{i}", "score": 10, "evidence": "ok"}
        for i in range(1, 10)
    ]
    dims[6] = {
        "dimension": 7,
        "name": "Structural integrity",
        "score": 7,
        "evidence": "word count is 1050 below 1200 target",
    }
    parsed = _make_parsed(score=8.85, dims=dims)

    _, overrides = v6_build._apply_deterministic_overrides(
        parsed,
        content_path=content_path,
        level="a1",
        slug="x",
        word_target=1200,
    )

    assert overrides == []


# ── 3. Activity-count hallucination ──────────────────────────────────────


def test_activity_undercount_overrides_exercise_quality(tmp_path):
    """Reviewer claims 'only 3 markers present' but the file has 4."""
    body = (
        "## A\nIntro.\n<!-- INJECT_ACTIVITY: a1 -->\n"
        "## B\n<!-- INJECT_ACTIVITY: a2 -->\n"
        "## C\n<!-- INJECT_ACTIVITY: a3 -->\n"
        "## D\n<!-- INJECT_ACTIVITY: a4 -->\n"
    )
    content_path = _write_content(tmp_path, body)

    dims = [
        {"dimension": i, "name": f"Dim{i}", "score": 10, "evidence": "ok"}
        for i in range(1, 10)
    ]
    dims[4] = {
        "dimension": 5,
        "name": "Exercise quality",
        "score": 7,
        "evidence": "only 3 markers present instead of 4",
    }
    parsed = _make_parsed(score=8.85, dims=dims)

    _, overrides = v6_build._apply_deterministic_overrides(
        parsed,
        content_path=content_path,
        level="a1",
        slug="x",
        word_target=1200,
    )

    assert len(overrides) == 1
    assert overrides[0]["claim"] == "activity_count_undercounted"
    assert overrides[0]["deterministic_value"] == 4


# ── 4. Defensive: never crash on malformed inputs ────────────────────────


def test_empty_dims_returns_parsed_unchanged(tmp_path):
    content_path = _write_content(tmp_path, "## S\n" + ("слово " * 1300))
    parsed = _make_parsed(score=0.0, dims=[], findings_count=0)
    new_parsed, overrides = v6_build._apply_deterministic_overrides(
        parsed,
        content_path=content_path,
        level="a1",
        slug="x",
        word_target=1200,
    )
    assert overrides == []
    assert new_parsed is parsed


def test_word_target_zero_is_noop(tmp_path):
    content_path = _write_content(tmp_path, "body")
    dims = [{"dimension": 7, "name": "Structural integrity", "score": 7, "evidence": "word count is 100 below 200 target"}]
    parsed = _make_parsed(score=7.0, dims=dims)
    new_parsed, overrides = v6_build._apply_deterministic_overrides(
        parsed,
        content_path=content_path,
        level="a1",
        slug="x",
        word_target=0,
    )
    assert overrides == []
    assert new_parsed is parsed


# ── 5. Regex coverage for real-world reviewer phrasings ──────────────────


@pytest.mark.parametrize(
    "evidence",
    [
        # sounds-letters-and-hello R3 — backticks around numbers + "floor"
        "All H2 headings are present and ordered correctly, but the pipeline word count is `1165`, below the `1200` floor.",
        # checkpoint-time-nature R2 — "required 1200"
        "All planned H2 headings are present and ordered correctly, but the pipeline word count is 1095, below the required 1200.",
        # where-is-it R1 — "1200-word target" hyphenated
        "Section order is clean, but the pipeline word count is 1124, below the 1200-word target.",
        # my-family — "deterministic pipeline count"
        "The H2 structure is clean and ordered correctly, but the deterministic pipeline count is 1112 words, below the 1200 target.",
        # i-want-i-can R8 — "pipeline note gives a total"
        "Headings are clean and ordered, but the pipeline note gives a total of 1186 words, below target.",
        # many-things R5 — "Word count: N words ... below the required N"
        "The H2 structure is clean and complete, but the pipeline note states `Word count: 1012 words`, which is below the required `1200`.",
    ],
)
def test_real_review_phrasings_trigger_override(tmp_path, evidence):
    """Every phrasing observed in real A1 reviewer output must match."""
    body = "## Section\n\n" + ("слово " * 1400)
    content_path = _write_content(tmp_path, body)

    dims = [
        {"dimension": i, "name": f"Dim{i}", "score": 10, "evidence": "ok"}
        for i in range(1, 10)
    ]
    dims[6] = {
        "dimension": 7,
        "name": "Structural integrity",
        "score": 7,
        "evidence": evidence,
    }
    parsed = _make_parsed(score=8.85, dims=dims)

    _, overrides = v6_build._apply_deterministic_overrides(
        parsed,
        content_path=content_path,
        level="a1",
        slug="x",
        word_target=1200,
    )

    assert len(overrides) == 1, f"Regex failed to match: {evidence!r}"
    assert overrides[0]["claim"] == "word_count_below_target"


def test_activity_phrasing_there_are_only(tmp_path):
    """"There are only 3 inject markers" — a real phrasing from
    ``checkpoint-food-shopping-review.md`` — must match.
    """
    # File needs > 3 markers for the override to trigger, and NO
    # secondary-defect keyword so the mixed-evidence guard doesn't
    # fire.
    body = (
        "## A\n<!-- INJECT_ACTIVITY: a1 -->\n## B\n<!-- INJECT_ACTIVITY: a2 -->\n"
        "## C\n<!-- INJECT_ACTIVITY: a3 -->\n## D\n<!-- INJECT_ACTIVITY: a4 -->\n"
    )
    content_path = _write_content(tmp_path, body)

    dims = [
        {"dimension": i, "name": f"Dim{i}", "score": 10, "evidence": "ok"}
        for i in range(1, 10)
    ]
    dims[4] = {
        "dimension": 5,
        "name": "Exercise quality",
        "score": 7,
        # Real phrasing, MINUS the "pre-solved" clause (that would
        # correctly trigger the secondary-defect skip — see the next
        # test).
        "evidence": "There are only 3 inject markers in the module body.",
    }
    parsed = _make_parsed(score=8.85, dims=dims)

    _, overrides = v6_build._apply_deterministic_overrides(
        parsed,
        content_path=content_path,
        level="a1",
        slug="x",
        word_target=1200,
    )

    assert len(overrides) == 1
    assert overrides[0]["claim"] == "activity_count_undercounted"


# ── 6. Mixed-evidence guard: don't wipe a second defect ──────────────────


def test_mixed_evidence_with_second_defect_skips_override(tmp_path):
    """Codex-review pushback: the real
    ``checkpoint-food-shopping-review.md`` cell reads:
    "There are only 3 inject markers, and the inline `Швидке
    сортування` block is pre-solved...". Auto-lifting the dim would
    erase the "pre-solved" finding, which is an independent defect.
    The mixed-evidence guard must skip override in this case.
    """
    body = (
        "## A\n<!-- INJECT_ACTIVITY: a1 -->\n## B\n<!-- INJECT_ACTIVITY: a2 -->\n"
        "## C\n<!-- INJECT_ACTIVITY: a3 -->\n## D\n<!-- INJECT_ACTIVITY: a4 -->\n"
    )
    content_path = _write_content(tmp_path, body)

    dims = [
        {"dimension": i, "name": f"Dim{i}", "score": 10, "evidence": "ok"}
        for i in range(1, 10)
    ]
    dims[4] = {
        "dimension": 5,
        "name": "Exercise quality",
        "score": 7,
        "evidence": (
            "There are only 3 inject markers, and the inline sorting block "
            "is pre-solved, so one of the four planned activities is not "
            "functioning as an exercise."
        ),
    }
    parsed = _make_parsed(score=8.85, dims=dims)

    _, overrides = v6_build._apply_deterministic_overrides(
        parsed,
        content_path=content_path,
        level="a1",
        slug="x",
        word_target=1200,
    )

    # Secondary defect ("pre-solved", "not functioning") must suppress
    # the override even though the count claim is technically wrong.
    assert overrides == []


def test_word_count_with_secondary_defect_skips_override(tmp_path):
    """Same mixed-evidence rule applied to dim 7 word-count claims."""
    body = "## Section\n\n" + ("слово " * 1400)
    content_path = _write_content(tmp_path, body)

    dims = [
        {"dimension": i, "name": f"Dim{i}", "score": 10, "evidence": "ok"}
        for i in range(1, 10)
    ]
    dims[6] = {
        "dimension": 7,
        "name": "Structural integrity",
        "score": 7,
        "evidence": (
            "Word count is 1163, below the 1200 target, AND the "
            "consonant section is missing its closing paragraph."
        ),
    }
    parsed = _make_parsed(score=8.85, dims=dims)

    _, overrides = v6_build._apply_deterministic_overrides(
        parsed,
        content_path=content_path,
        level="a1",
        slug="x",
        word_target=1200,
    )

    assert overrides == []


# ── 7. Override promotes passed=True when all dims clear ─────────────────


def test_override_promotes_passed_even_when_verdict_revise(tmp_path):
    """The actual A1/M1 R2 case: verdict REVISE + all dims ≥9 except
    the hallucinated dim 7. After override, every dim ≥9, score ≥9,
    no floor fail — the review's dim-level signal now agrees with
    PASS. ``passed`` must flip to True so the snapshot trigger can
    fire and the pipeline can ship the content.
    """
    body = "## Section\n\n" + ("слово " * 1400)
    content_path = _write_content(tmp_path, body)

    dims = [
        {"dimension": i, "name": f"Dim{i}", "score": 9, "evidence": "ok"}
        for i in range(1, 10)
    ]
    dims[6] = {
        "dimension": 7,
        "name": "Structural integrity",
        "score": 7,
        "evidence": "pipeline word count is 1163, below the 1200 target",
    }
    # Verdict REVISE, passed=False before override.
    parsed = _make_parsed(score=8.7, verdict="REVISE", dims=dims)
    assert parsed.passed is False

    new_parsed, overrides = v6_build._apply_deterministic_overrides(
        parsed,
        content_path=content_path,
        level="a1",
        slug="x",
        word_target=1200,
    )

    assert overrides  # override applied
    # All dims now ≥9 → passed promoted regardless of verdict string.
    assert new_parsed.passed is True


def test_override_does_not_promote_when_another_dim_below_target(tmp_path):
    """Guard on the promotion: if ANY dim is still <9 after override
    (because it had an unrelated legitimate defect), ``passed`` stays
    False. The hallucination fix does not erase genuine concerns.
    """
    body = "## Section\n\n" + ("слово " * 1400)
    content_path = _write_content(tmp_path, body)

    dims = [
        {"dimension": i, "name": f"Dim{i}", "score": 9, "evidence": "ok"}
        for i in range(1, 10)
    ]
    dims[2] = {  # dim 3 Pedagogical quality — genuinely weak
        "dimension": 3,
        "name": "Pedagogical quality",
        "score": 6,
        "evidence": "learner never performs the transformation themselves",
    }
    dims[6] = {
        "dimension": 7,
        "name": "Structural integrity",
        "score": 7,
        "evidence": "word count is 1163, below the 1200 target",
    }
    parsed = _make_parsed(score=8.4, verdict="REVISE", dims=dims)

    new_parsed, overrides = v6_build._apply_deterministic_overrides(
        parsed,
        content_path=content_path,
        level="a1",
        slug="x",
        word_target=1200,
    )

    assert overrides  # dim 7 still overridden
    # dim 3 still at 6 → passed stays False.
    assert new_parsed.passed is False


# ── 8. Counting-basis alignment (reviewer prompt vs override) ───────────


def test_override_counting_basis_matches_audit_cleaner(tmp_path):
    """The override and the reviewer-prompt injection must use the
    same counting basis. Concrete check: calling the shared helper
    on the SAME string produces the SAME number the override uses
    internally.
    """
    body = "## Section\n\nслово " * 1300
    content_path = _write_content(tmp_path, body)

    via_path = v6_build._deterministic_core_word_count(content_path)
    via_text = v6_build._compute_core_word_count_for_text(body)

    assert via_path == via_text
    # Both routes return a positive count on real content.
    assert via_path > 0
