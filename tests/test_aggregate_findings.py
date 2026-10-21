"""Tests for scripts/aggregate_review_findings.py."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from scripts.aggregate_review_findings import (
    collect_findings,
    parse_findings_from_markdown,
    parse_findings_from_yaml,
)

pytestmark = pytest.mark.reads_content
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

    def test_malformed_yaml(self, tmp_path: Path):
        p = tmp_path / "bad.yaml"
        p.write_text("{{invalid yaml", "utf-8")
        assert parse_findings_from_yaml(p, "bad") == []


class TestCollectFindings:
    def test_round_suffix_glob(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """Bug #2102: aggregate_review_findings glob drops round-suffixed reviews."""
        # Mock CURRICULUM_ROOT
        import scripts.aggregate_review_findings
        monkeypatch.setattr(scripts.aggregate_review_findings, "CURRICULUM_ROOT", tmp_path)

        # Setup mock file structure
        level_dir = tmp_path / "a1"
        review_dir = level_dir / "review"
        review_dir.mkdir(parents=True)

        # 1. No round suffix
        f1 = review_dir / "mod1-review.md"
        f1.write_text(dedent("""\
            ## Findings

            [PLAN ADHERENCE] [MINOR]
            Location: here
            Issue: issue1
            Fix: fix1

            ## Verdict: PASS
        """))

        # 2. Round suffix
        f2 = review_dir / "mod2-review-r1.md"
        f2.write_text(dedent("""\
            ## Findings

            [ENGAGEMENT & TONE] [MAJOR]
            Location: there
            Issue: issue2
            Fix: fix2

            ## Verdict: REVISE
        """))

        findings = collect_findings("a1")

        # Verify both files were parsed
        issues = {f["issue"] for f in findings}
        assert "issue1" in issues
        assert "issue2" in issues
        assert len(findings) == 2
