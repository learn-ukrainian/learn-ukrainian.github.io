"""Tests for scripts/aggregate_review_findings.py."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from scripts.aggregate_review_findings import (
    Finding,
    collect_findings,
    format_report,
    normalize_dimension,
    normalize_severity,
    parse_findings_from_markdown,
    parse_findings_from_yaml,
)


class TestNormalizeDimension:
    def test_canonical(self):
        assert normalize_dimension("engagement") == "ENGAGEMENT & TONE"
        assert normalize_dimension("EXERCISE QUALITY") == "EXERCISE QUALITY"

    def test_numbered_prefix(self):
        assert normalize_dimension("1. Plan adherence") == "PLAN ADHERENCE"
        assert normalize_dimension("5. Exercise quality") == "EXERCISE QUALITY"

    def test_dim_prefix(self):
        assert normalize_dimension("DIM 2: Linguistic accuracy") == "LINGUISTIC ACCURACY"
        assert normalize_dimension("DIMENSION 6: ENGAGEMENT") == "ENGAGEMENT & TONE"

    def test_slash_compound(self):
        result = normalize_dimension("plan adherence / structural integrity")
        assert result == "PLAN ADHERENCE / STRUCTURAL INTEGRITY"

    def test_unknown_passthrough(self):
        assert normalize_dimension("ENRICH ISSUES") == "ENRICH ISSUES"

    def test_whitespace(self):
        assert normalize_dimension("  engagement  ") == "ENGAGEMENT & TONE"


class TestNormalizeSeverity:
    def test_cases(self):
        assert normalize_severity("minor") == "MINOR"
        assert normalize_severity("MAJOR") == "MAJOR"
        assert normalize_severity("Critical") == "CRITICAL"


SAMPLE_REVIEW_FENCED = dedent("""\
    ## Findings

    ```
    [PLAN ADHERENCE] [MINOR]
    Location: Dialogue 1
    Issue: Plan scripts opening differently.
    Fix: Accept as creative choice.
    ```

    ```
    [ENGAGEMENT] [MINOR]
    Location: Final paragraph
    Issue: Generic LLM closing.
    Fix: Remove or tone down.
    ```

    ## Verdict: PASS
""")

SAMPLE_REVIEW_BOLD = dedent("""\
    ## Findings

    **[EXERCISE QUALITY] [minor]**
    Location: quiz block
    Issue: All answers at position 0.
    Fix: Frontend concern.

    **[ENGAGEMENT] [MAJOR]**
    Location: Throughout
    Issue: Dry prose.
    Fix: Add cultural hooks.

    ## Verdict: REVISE
""")

SAMPLE_REVIEW_BARE = dedent("""\
    ## Findings

    [PLAN ADHERENCE] [minor]
    Location: Section 2
    Issue: Writer used generic phrase.
    Fix: Replace with specific reference.

    [ENGAGEMENT & TONE] [minor]
    Location: Section 3
    Issue: Slightly literary phrasing.
    Fix: Simplify.

    ## Verdict: PASS
""")

SAMPLE_REVIEW_SEVERITY_COLON = dedent("""\
    ## Findings

    ```
    [PLAN ADHERENCE] [SEVERITY: minor]
    Location: Quiz 2
    Issue: Word not taught in prior modules.
    Fix: Replace with known vocabulary.
    ```

    ## Verdict: PASS
""")


class TestParseFindingsFromMarkdown:
    def test_fenced_format(self):
        findings = parse_findings_from_markdown(SAMPLE_REVIEW_FENCED, "test-mod")
        assert len(findings) == 2
        assert findings[0]["dimension"] == "PLAN ADHERENCE"
        assert findings[0]["severity"] == "MINOR"
        assert findings[0]["module"] == "test-mod"
        assert "creative choice" in findings[0]["fix"]

    def test_bold_format(self):
        findings = parse_findings_from_markdown(SAMPLE_REVIEW_BOLD, "bold-mod")
        assert len(findings) == 2
        assert findings[0]["dimension"] == "EXERCISE QUALITY"
        assert findings[0]["severity"] == "MINOR"
        assert findings[1]["dimension"] == "ENGAGEMENT & TONE"
        assert findings[1]["severity"] == "MAJOR"

    def test_bare_format(self):
        findings = parse_findings_from_markdown(SAMPLE_REVIEW_BARE, "bare-mod")
        assert len(findings) == 2
        assert findings[0]["dimension"] == "PLAN ADHERENCE"
        assert findings[1]["dimension"] == "ENGAGEMENT & TONE"

    def test_severity_colon_variant(self):
        findings = parse_findings_from_markdown(SAMPLE_REVIEW_SEVERITY_COLON, "sev-mod")
        assert len(findings) == 1
        assert findings[0]["severity"] == "MINOR"
        assert "not taught" in findings[0]["issue"]

    def test_no_findings_section(self):
        text = "## Scores\n\nSome scores here.\n\n## Verdict: PASS\n"
        assert parse_findings_from_markdown(text, "empty") == []

    def test_empty_findings_section(self):
        text = "## Findings\n\nNo findings.\n\n## Verdict: PASS\n"
        assert parse_findings_from_markdown(text, "empty") == []


class TestParseFindingsFromYaml:
    def test_valid_yaml(self, tmp_path: Path):
        yaml_content = dedent("""\
            round: 1
            scores:
              - dimension: 1
                name: Plan adherence
                score: 9
                evidence: Good
            findings:
              - dimension: EXERCISE QUALITY
                severity: minor
                location: quiz block
                issue: All answers at position 0
                fix: Shuffle options
        """)
        p = tmp_path / "review-structured-r1.yaml"
        p.write_text(yaml_content, "utf-8")
        findings = parse_findings_from_yaml(p, "yaml-mod")
        assert len(findings) == 1
        assert findings[0]["dimension"] == "EXERCISE QUALITY"
        assert findings[0]["severity"] == "MINOR"

    def test_empty_yaml(self, tmp_path: Path):
        p = tmp_path / "review-structured-r1.yaml"
        p.write_text("round: 1\nscores: []\nfindings: []\n", "utf-8")
        assert parse_findings_from_yaml(p, "empty") == []

    def test_malformed_yaml(self, tmp_path: Path):
        p = tmp_path / "bad.yaml"
        p.write_text("{{invalid yaml", "utf-8")
        assert parse_findings_from_yaml(p, "bad") == []


class TestFormatReport:
    def test_basic_report(self):
        findings: list[Finding] = [
            Finding(module="m1", dimension="ENGAGEMENT & TONE", severity="MINOR",
                    location="p1", issue="LLM filler", fix="remove"),
            Finding(module="m2", dimension="ENGAGEMENT & TONE", severity="MINOR",
                    location="p2", issue="LLM filler", fix="remove"),
            Finding(module="m3", dimension="EXERCISE QUALITY", severity="MAJOR",
                    location="ex1", issue="Bad distractor", fix="fix it"),
        ]
        report = format_report("a1", findings)
        assert "3 findings total" in report
        assert "ENGAGEMENT & TONE (2 findings):" in report
        assert 'x2' in report  # "LLM filler" appears twice
        assert "EXERCISE QUALITY (1 findings):" in report

    def test_severity_filter(self):
        findings: list[Finding] = [
            Finding(module="m1", dimension="EQ", severity="MINOR",
                    location="", issue="minor issue", fix=""),
            Finding(module="m2", dimension="EQ", severity="MAJOR",
                    location="", issue="major issue", fix=""),
        ]
        report = format_report("a1", findings, severity_filter="major")
        assert "1 findings total" in report
        assert "major issue" in report
        assert "minor issue" not in report

    def test_empty_findings(self):
        report = format_report("a1", [])
        assert "0 findings total" in report
        assert "No findings match" in report


class TestCollectFindings:
    def test_with_real_a1_data(self):
        """Integration test — only runs if A1 review data exists."""
        review_dir = Path(__file__).resolve().parent.parent / "curriculum" / "l2-uk-en" / "a1" / "review"
        if not review_dir.is_dir() or not list(review_dir.glob("*-review.md")):
            pytest.skip("No A1 review data available")

        findings = collect_findings("a1")
        assert len(findings) > 0
        # Every finding should have required keys
        for f in findings:
            assert f["module"]
            assert f["dimension"]
            assert f["severity"] in {"CRITICAL", "MAJOR", "MINOR"}
            assert f["issue"]
