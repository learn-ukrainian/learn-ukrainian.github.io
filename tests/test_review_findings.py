"""Tests for the review findings extraction and targeted fix prompt builder."""

import os
import sys
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from pipeline.review_findings import (
    build_targeted_fix_prompt,
    extract_review_findings,
    extract_sections_to_modify,
    load_review_findings,
)


class TestExtractReviewFindings:
    def test_extracts_issues_with_all_fields(self):
        review = textwrap.dedent("""\
            ## Critical Issues Found

            ### Issue 1: Incorrect verb form
            **Location**: Section 2: Verb Conjugation
            **Problem**: The verb "ходити" is conjugated incorrectly in 3rd person
            **Fix**: Change "ходе" to "ходить"
            **Severity**: HIGH

            ### Issue 2: Missing vocabulary
            **Location**: Section 4: Practice
            **Problem**: Vocabulary item "книга" not introduced before use
            **Fix**: Add "книга" definition in Section 3
            **Severity**: MEDIUM
        """)
        findings = extract_review_findings(review)
        assert len(findings) == 2
        assert findings[0]["title"] == "Incorrect verb form"
        assert findings[0]["location"] == "Section 2: Verb Conjugation"
        assert findings[0]["problem"] == 'The verb "ходити" is conjugated incorrectly in 3rd person'
        assert findings[0]["fix"] == 'Change "ходе" to "ходить"'
        assert findings[0]["severity"] == "HIGH"
        assert findings[1]["severity"] == "MEDIUM"

    def test_handles_missing_fields(self):
        review = textwrap.dedent("""\
            ## Critical Issues Found

            ### Issue 1: Some problem
            **Problem**: A vague issue
        """)
        findings = extract_review_findings(review)
        assert len(findings) == 1
        assert "location" not in findings[0]
        assert findings[0]["problem"] == "A vague issue"

    def test_no_issues(self):
        review = "## Review Summary\nEverything looks good.\n"
        findings = extract_review_findings(review)
        assert findings == []

    def test_suggested_fix_variant(self):
        review = textwrap.dedent("""\
            ### Issue 1: Typo
            **Suggested Fix**: Fix the typo
        """)
        findings = extract_review_findings(review)
        assert findings[0]["fix"] == "Fix the typo"


class TestExtractSectionsToModify:
    def test_extracts_section_names(self):
        findings = [
            {"location": "Section 2: Verb Conjugation"},
            {"location": "### Practice Exercises"},
            {"location": "Section 4: Summary (final part)"},
        ]
        sections = extract_sections_to_modify(findings)
        assert "Verb Conjugation" in sections
        assert "Practice Exercises" in sections
        assert "Summary" in sections

    def test_handles_missing_location(self):
        findings = [{"problem": "something", "severity": "HIGH"}]
        sections = extract_sections_to_modify(findings)
        assert sections == []

    def test_raw_location_fallback(self):
        findings = [{"location": "near the beginning of the module"}]
        sections = extract_sections_to_modify(findings)
        assert "near the beginning of the module" in sections


class TestBuildTargetedFixPrompt:
    def test_builds_constrained_prompt(self):
        findings = [
            {
                "title": "Bad verb form",
                "location": "Section 2: Verbs",
                "problem": "Incorrect conjugation",
                "fix": "Fix the form",
                "severity": "HIGH",
            },
        ]
        prompt = build_targeted_fix_prompt(findings)
        assert "Review Findings" in prompt
        assert "Fix ONLY" in prompt
        assert "Do NOT rewrite" in prompt
        assert "Bad verb form" in prompt
        assert "Verbs" in prompt

    def test_preserves_base_fix_plan(self):
        findings = [{"title": "Issue", "severity": "HIGH"}]
        prompt = build_targeted_fix_prompt(findings, fix_plan_base="Original fix plan here")
        assert "Review Findings" in prompt
        assert "Original fix plan here" in prompt

    def test_empty_findings_returns_base(self):
        prompt = build_targeted_fix_prompt([], fix_plan_base="base plan")
        assert prompt == "base plan"

    def test_section_constraints_listed(self):
        findings = [
            {"title": "Issue A", "location": "Section 1: Intro", "severity": "HIGH"},
            {"title": "Issue B", "location": "Section 3: Practice", "severity": "HIGH"},
        ]
        prompt = build_targeted_fix_prompt(findings)
        assert "Only modify these sections" in prompt
        assert "Intro" in prompt
        assert "Practice" in prompt


class TestLoadReviewFindings:
    def test_loads_from_review_result(self, tmp_path):
        review_text = textwrap.dedent("""\
            ## Critical Issues Found

            ### Issue 1: Test issue
            **Location**: Section 1
            **Problem**: Test problem
            **Fix**: Test fix
        """)
        (tmp_path / "review-result.md").write_text(review_text)
        findings = load_review_findings(tmp_path)
        assert len(findings) == 1
        assert findings[0]["title"] == "Test issue"

    def test_falls_back_to_pass_files(self, tmp_path):
        pass1 = textwrap.dedent("""\
            ### Issue 1: Pass 1 issue
            **Problem**: From pass 1
        """)
        (tmp_path / "review-pass1-raw.md").write_text(pass1)
        findings = load_review_findings(tmp_path)
        assert len(findings) == 1

    def test_empty_when_no_files(self, tmp_path):
        findings = load_review_findings(tmp_path)
        assert findings == []
