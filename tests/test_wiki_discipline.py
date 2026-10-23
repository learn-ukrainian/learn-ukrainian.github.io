"""Tests for scripts/wiki/discipline.py — citation bound + canonical anchors."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from wiki.discipline import (
    flag_anchor_violations,
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

    def test_ignores_malformed_citations(self):
        # [Sabc], [S], [S1a] are NOT matches (regex requires pure digits)
        text = "Malformed [Sabc] [S] [S1a] fine [S1]"
        violations = validate_citation_bound(text, source_count=5)
        assert violations == []


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

    def test_case_insensitive(self, fake_anchors_path: Path):
        text = "БЛАКИТНО-ЖОВТИЙ прапор."
        violations = validate_canonical_anchors(text, fake_anchors_path)
        assert len(violations) == 1

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
    def test_production_flag_anchor_catches_blakytnyi(self):
        # The real failure case from a1/colors R2 — must be caught by
        # the live production registry, not just a test fixture.
        text = "«жовтий» і «блакитний» — це кольори нашого прапора."
        violations = validate_canonical_anchors(text)
        assert any(v.anchor_id == "flag_ukraine" for v in violations)


# ═══════════════════════════════════════════════════════════════════
# Repairs
# ═══════════════════════════════════════════════════════════════════


class TestStripInventedCitations:
    def test_strips_invented_preserves_valid(self):
        text = "Valid [S1]. Invented [S6]. Valid [S2]."
        out, stripped = strip_invented_citations(text, source_count=5)
        assert "[S6]" not in out
        assert "[S1]" in out
        assert "[S2]" in out
        assert stripped == ["S6"]


class TestRegistryMembershipCitations:
    """#3083: citation validity is REGISTRY MEMBERSHIP, not a numeric bound.

    Root-cause regression: dossier-only compiles passed source_count=1 (the
    dense-retrieval chunk count) while the dossier-seeded registry held ~26 ids,
    so the numeric bound stripped every valid [S2]..[S26]. With valid_ids
    supplied, the strip keys off membership and the seeded citations survive.
    """

    def test_seeded_citations_survive_low_source_count_regression(self):
        valid_ids = {f"S{n}" for n in range(1, 27)}  # S1..S26 (kobzarstvo shape)
        text = "Lead [S1]. Body [S2] and [S26]. Bogus [S99]."
        out, stripped = strip_invented_citations(
            text, source_count=1, valid_ids=valid_ids
        )
        assert "[S1]" in out
        assert "[S2]" in out
        assert "[S26]" in out
        assert "[S99]" not in out
        assert stripped == ["S99"]

    def test_run_discipline_checks_threads_valid_ids(self):
        valid_ids = {"S1", "S2"}
        report = run_discipline_checks(
            "ok [S2] bad [S5]", source_count=99, valid_ids=valid_ids
        )
        # source_count=99 would PASS [S5] under the numeric bound; membership
        # correctly flags it because S5 is not in the registry.
        assert [v.cited_id for v in report.citations] == ["S5"]


class TestFlagAnchorViolations:
    def test_inserts_verify_marker(self, fake_anchors_path: Path):
        text = "Прапор блакитно-жовтий стяг."
        violations = validate_canonical_anchors(text, fake_anchors_path)
        out = flag_anchor_violations(text, violations)
        assert "<!-- VERIFY" in out
        assert "test_flag" in out
        # Original text intact
        assert "блакитно-жовтий" in out


# ═══════════════════════════════════════════════════════════════════
# run_discipline_checks integration
# ═══════════════════════════════════════════════════════════════════


class TestRunDisciplineChecks:
    def test_mixed_violations_both_reported(self, fake_anchors_path: Path):
        text = "Bad [S99] and блакитно-жовтий flag."
        report = run_discipline_checks(text, source_count=5, anchors_path=fake_anchors_path)
        assert not report.clean
        assert len(report.citations) == 1
        assert len(report.anchors) == 1


# ═══════════════════════════════════════════════════════════════════
# Prompt rendering
# ═══════════════════════════════════════════════════════════════════
