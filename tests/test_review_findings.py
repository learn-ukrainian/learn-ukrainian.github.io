"""Tests for the review findings extraction and targeted fix prompt builder."""

import os
import sys
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from pipeline.review_findings import (
    extract_review_findings,
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

    def test_suggested_fix_variant(self):
        review = textwrap.dedent("""\
            ### Issue 1: Typo
            **Suggested Fix**: Fix the typo
        """)
        findings = extract_review_findings(review)
        assert findings[0]["fix"] == "Fix the typo"


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
