"""Shared review file parsing utilities.

Used by dashboard_router.py, state_router.py, and batch_fix_review.py
to extract scores, verdicts, and plan review results from markdown review files.
"""

import re

# Pre-compiled patterns
_RE_SCORE_PATTERNS = [
    re.compile(r"\*\*Overall Score:\*\*\s*(\d+\.?\d*)/10"),
    re.compile(r"Overall Score:\s*(\d+\.?\d*)/10"),
    re.compile(r"\*\*(\d+\.?\d*)/10\*\*\s*$", re.MULTILINE),
    re.compile(r"=\s*\*\*(\d+\.?\d*)/10\*\*"),
]
_RE_STATUS = re.compile(r"\*{0,2}Status:?\*{0,2}\s*(PASS|FAIL)\b", re.IGNORECASE)
_RE_PLAN_VERDICT = re.compile(r"\*{0,2}Verdict:?\*{0,2}:?\s*(PASS|NEEDS FIXES|FAIL)\b", re.IGNORECASE)
_RE_ISSUE_HEADER = re.compile(r"^#{1,4}\s+Issue\s*#?\s*\d+", re.MULTILINE | re.IGNORECASE)


def extract_review_score(text: str) -> float | None:
    """Extract overall score (X/10) from a content review file."""
    for pat in _RE_SCORE_PATTERNS:
        match = pat.search(text)
        if match:
            return float(match.group(1))
    return None


def extract_review_verdict(text: str) -> str | None:
    """Extract PASS/FAIL verdict from a content review file."""
    match = _RE_STATUS.search(text)
    return match.group(1).upper() if match else None


def extract_plan_verdict(text: str) -> str | None:
    """Extract PASS/NEEDS FIXES/FAIL verdict from a plan review file."""
    match = _RE_PLAN_VERDICT.search(text)
    return match.group(1).upper() if match else None


def count_review_issues(text: str) -> int:
    """Count issue headers (e.g., '### Issue #1') in a review file."""
    return len(_RE_ISSUE_HEADER.findall(text))
