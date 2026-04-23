"""Tests for scripts/wiki/discipline.py — citation bound + canonical anchors."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from wiki.discipline import (
    AnchorViolation,
    CitationViolation,
    DisciplineReport,
    flag_anchor_violations,
    load_canonical_anchors,
    render_canonical_anchors_for_reviewer,
    render_canonical_anchors_for_writer,
    render_citation_discipline_block,
    run_discipline_checks,
    strip_invented_citations,
    validate_canonical_anchors,
    validate_citation_bound,
)


# ═══════════════════════════════════════════════════════════════════
# Citation bound
# ═══════════════════════════════════════════════════════════════════


class TestValidateCitationBound:
    def test_all_within_bound_clean(self):
        text = "Claim [S1]. Another [S2]. End [S5]."
        assert validate_citation_bound(text, source_count=5) == []

    def test_invented_citation_flagged(self):
        text = "Fine [S1]. Invented [S6]."
        violations = validate_citation_bound(text, source_count=5)
        assert len(violations) == 1
        assert violations[0].cited_id == "S6"
        assert violations[0].cited_number == 6
        assert violations[0].max_legal == 5

    def test_multiple_inventions_all_flagged(self):
        text = "One [S1]. Two [S7]. Three [S8]. Four [S2]."
        violations = validate_citation_bound(text, source_count=5)
        assert [v.cited_id for v in violations] == ["S7", "S8"]

    def test_context_window_captured(self):
        text = "a" * 100 + " [S99] " + "b" * 100
        violations = validate_citation_bound(text, source_count=5)
        assert violations[0].context.count("a") > 0
        assert violations[0].context.count("b") > 0
        assert "[S99]" in violations[0].context

    def test_same_invented_id_multiple_times(self):
        # Gemini often repeats the same invented ID. Flag each occurrence.
        text = "First [S6]. Second [S6]. Third [S6]."
        violations = validate_citation_bound(text, source_count=5)
        assert len(violations) == 3
        assert all(v.cited_id == "S6" for v in violations)

    def test_zero_source_count_flags_everything(self):
        text = "Any citation [S1] is invented when source_count=0."
        violations = validate_citation_bound(text, source_count=0)
        assert len(violations) == 1

    def test_negative_source_count_rejected(self):
        with pytest.raises(ValueError, match="source_count must be ≥0"):
            validate_citation_bound("[S1]", source_count=-1)

    def test_ignores_malformed_citations(self):
        # [Sabc], [S], [S1a] are NOT matches (regex requires pure digits)
        text = "Malformed [Sabc] [S] [S1a] fine [S1]"
        violations = validate_citation_bound(text, source_count=5)
        assert violations == []

    def test_handles_cyrillic_article_body(self):
        text = "Претензія [S1]. Вигадана [S99]. Ще одна [S2]."
        violations = validate_citation_bound(text, source_count=5)
        assert len(violations) == 1
        assert violations[0].cited_id == "S99"

    def test_large_numbers_still_flagged(self):
        text = "[S1234]"
        violations = validate_citation_bound(text, source_count=5)
        assert violations[0].cited_number == 1234


# ═══════════════════════════════════════════════════════════════════
# Canonical anchors
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def fake_anchors_path(tmp_path: Path) -> Path:
    """Minimal test-fixture registry with 2 anchors for focused regex tests."""
    path = tmp_path / "anchors.yaml"
    path.write_text(
        yaml.dump(
            {
                "version": "test",
                "anchors": [
                    {
                        "id": "test_flag",
                        "topic_uk": "Прапор (test)",
                        "correct": "синьо-жовтий",
                        "forbidden": [
                            {
                                "pattern": "блакитно-жовт",
                                "reason": "Soviet diminishing framing",
                            }
                        ],
                    },
                    {
                        "id": "test_calque",
                        "topic_uk": "Калька (test)",
                        "correct": "Мене звати Іван",
                        "forbidden": [
                            {
                                "pattern": r"Моє ім'я є\s",
                                "reason": "English calque via copula",
                            }
                        ],
                    },
                ],
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return path


class TestValidateCanonicalAnchors:
    def test_clean_article_no_violations(self, fake_anchors_path: Path):
        text = "Прапор України — синьо-жовтий. Мене звати Іван."
        assert validate_canonical_anchors(text, fake_anchors_path) == []

    def test_flag_violation_caught(self, fake_anchors_path: Path):
        text = "Прапор — блакитно-жовтий стяг."
        violations = validate_canonical_anchors(text, fake_anchors_path)
        assert len(violations) == 1
        assert violations[0].anchor_id == "test_flag"
        assert "блакитно-жовт" in violations[0].matched_text.lower()

    def test_calque_violation_caught(self, fake_anchors_path: Path):
        text = "Моє ім'я є Іван."
        violations = validate_canonical_anchors(text, fake_anchors_path)
        assert len(violations) == 1
        assert violations[0].anchor_id == "test_calque"

    def test_multiple_anchors_multiple_hits(self, fake_anchors_path: Path):
        text = "Прапор блакитно-жовтий. Моє ім'я є Іван."
        violations = validate_canonical_anchors(text, fake_anchors_path)
        assert len(violations) == 2
        assert {v.anchor_id for v in violations} == {"test_flag", "test_calque"}

    def test_case_insensitive(self, fake_anchors_path: Path):
        text = "БЛАКИТНО-ЖОВТИЙ прапор."
        violations = validate_canonical_anchors(text, fake_anchors_path)
        assert len(violations) == 1

    def test_context_surrounds_match(self, fake_anchors_path: Path):
        text = "x" * 100 + " блакитно-жовтий " + "y" * 100
        violations = validate_canonical_anchors(text, fake_anchors_path)
        assert "x" in violations[0].context
        assert "y" in violations[0].context

    def test_invalid_regex_surfaces_as_registry_error(self, tmp_path: Path):
        path = tmp_path / "bad.yaml"
        path.write_text(
            yaml.dump(
                {
                    "anchors": [
                        {
                            "id": "bad",
                            "topic_uk": "Bad",
                            "correct": "x",
                            "forbidden": [
                                {"pattern": "[unclosed", "reason": "broken"}
                            ],
                        }
                    ]
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        violations = validate_canonical_anchors("any text", path)
        assert len(violations) == 1
        assert violations[0].kind == "registry_error"


# ═══════════════════════════════════════════════════════════════════
# Real production registry sanity
# ═══════════════════════════════════════════════════════════════════


class TestProductionRegistry:
    def test_production_registry_loads_cleanly(self):
        data = load_canonical_anchors()
        assert "anchors" in data
        assert len(data["anchors"]) > 0
        assert data.get("version")

    def test_production_flag_anchor_catches_blakytnyi(self):
        # The real failure case from a1/colors R2 — must be caught by
        # the live production registry, not just a test fixture.
        text = "«жовтий» і «блакитний» — це кольори нашого прапора."
        violations = validate_canonical_anchors(text)
        assert any(v.anchor_id == "flag_ukraine" for v in violations)

    def test_production_flag_anchor_passes_correct_form(self):
        text = "Прапор України — синьо-жовтий, це державний символ."
        violations = validate_canonical_anchors(text)
        assert not any(v.anchor_id == "flag_ukraine" for v in violations)

    def test_production_kiev_vs_kyiv(self):
        text = "The capital of Ukraine is Kiev."
        violations = validate_canonical_anchors(text)
        assert any(v.anchor_id == "capital" for v in violations)

    def test_production_kyiv_passes(self):
        text = "The capital of Ukraine is Kyiv."
        violations = validate_canonical_anchors(text)
        assert not any(v.anchor_id == "capital" for v in violations)


# ═══════════════════════════════════════════════════════════════════
# Repairs
# ═══════════════════════════════════════════════════════════════════


class TestStripInventedCitations:
    def test_leaves_valid_alone(self):
        text = "First [S1]. Second [S2]."
        out, stripped = strip_invented_citations(text, source_count=5)
        assert out == text
        assert stripped == []

    def test_strips_invented_preserves_valid(self):
        text = "Valid [S1]. Invented [S6]. Valid [S2]."
        out, stripped = strip_invented_citations(text, source_count=5)
        assert "[S6]" not in out
        assert "[S1]" in out
        assert "[S2]" in out
        assert stripped == ["S6"]

    def test_collapses_double_spaces(self):
        text = "a [S6] b"
        out, _ = strip_invented_citations(text, source_count=5)
        assert "  " not in out

    def test_preserves_order_in_stripped_list(self):
        text = "[S9] [S1] [S7] [S3] [S5] [S8]"
        _, stripped = strip_invented_citations(text, source_count=5)
        assert stripped == ["S9", "S7", "S8"]

    def test_idempotent_on_second_pass(self):
        text = "a [S1] b [S99] c"
        out1, _ = strip_invented_citations(text, source_count=5)
        out2, stripped2 = strip_invented_citations(out1, source_count=5)
        assert out1 == out2
        assert stripped2 == []


class TestFlagAnchorViolations:
    def test_noop_when_no_violations(self):
        text = "clean article"
        assert flag_anchor_violations(text, []) == text

    def test_inserts_verify_marker(self, fake_anchors_path: Path):
        text = "Прапор блакитно-жовтий стяг."
        violations = validate_canonical_anchors(text, fake_anchors_path)
        out = flag_anchor_violations(text, violations)
        assert "<!-- VERIFY" in out
        assert "test_flag" in out
        # Original text intact
        assert "блакитно-жовтий" in out

    def test_original_preserved_in_body(self, fake_anchors_path: Path):
        text = "Прапор блакитно-жовтий."
        violations = validate_canonical_anchors(text, fake_anchors_path)
        out = flag_anchor_violations(text, violations)
        assert out.startswith("Прапор блакитно-жовтий")

    def test_does_not_double_mark_same_position(self, fake_anchors_path: Path):
        # Only one marker per matched span, even if called twice.
        text = "Прапор блакитно-жовтий."
        violations = validate_canonical_anchors(text, fake_anchors_path)
        out = flag_anchor_violations(text, violations)
        assert out.count("<!-- VERIFY") == 1


# ═══════════════════════════════════════════════════════════════════
# run_discipline_checks integration
# ═══════════════════════════════════════════════════════════════════


class TestRunDisciplineChecks:
    def test_clean_article_returns_clean_report(self, fake_anchors_path: Path):
        text = "Clean [S1] and [S2] citations. Прапор синьо-жовтий."
        report = run_discipline_checks(text, source_count=5, anchors_path=fake_anchors_path)
        assert report.clean
        assert report.to_dict()["clean"] is True

    def test_mixed_violations_both_reported(self, fake_anchors_path: Path):
        text = "Bad [S99] and блакитно-жовтий flag."
        report = run_discipline_checks(text, source_count=5, anchors_path=fake_anchors_path)
        assert not report.clean
        assert len(report.citations) == 1
        assert len(report.anchors) == 1

    def test_to_dict_structure(self, fake_anchors_path: Path):
        text = "Bad [S99]."
        report = run_discipline_checks(text, source_count=5, anchors_path=fake_anchors_path)
        d = report.to_dict()
        assert d["clean"] is False
        assert d["counts"]["citations"] == 1
        assert d["counts"]["anchors"] == 0
        assert d["citation_violations"][0]["cited_id"] == "S99"


# ═══════════════════════════════════════════════════════════════════
# Prompt rendering
# ═══════════════════════════════════════════════════════════════════


class TestPromptRendering:
    def test_writer_block_has_numeric_bound(self):
        block = render_citation_discipline_block(7)
        assert "[S1]..[S7]" in block
        assert "7" in block

    def test_writer_block_zero_sources(self):
        # Degenerate but valid — wiki with no retrieved sources.
        block = render_citation_discipline_block(0)
        assert "0" in block

    def test_writer_anchors_block_is_ukrainian(self):
        block = render_canonical_anchors_for_writer()
        assert "Канонічні" in block or "канонічні" in block
        assert "ОБОВ'ЯЗКОВО" in block or "обов'язково" in block.lower()

    def test_writer_anchors_block_contains_known_pattern(self):
        # Production registry's flag anchor should render into the block.
        block = render_canonical_anchors_for_writer()
        assert "блакитно-жовт" in block

    def test_reviewer_block_is_english(self):
        # Reviewer prompts run in mixed lang — block is English per design
        block = render_canonical_anchors_for_reviewer()
        assert "REJECT" in block
        assert "canonical" in block.lower()

    def test_reviewer_block_names_anchor_ids(self):
        block = render_canonical_anchors_for_reviewer()
        assert "Прапор" in block  # topic_uk rendered
