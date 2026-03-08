"""Review parsing and quality gate helpers for pipeline/parsing.py.

Contains D.1/factual review parsing, D.3 context building,
calibration loading, and quick review quality gate.
Extracted from parsing_helpers.py to improve maintainability index.
"""

from __future__ import annotations

import contextlib
import json
import re
from pathlib import Path

from pipeline_lib import ModuleContext


# ---------------------------------------------------------------------------
# D.1 review parsing — sub-parsers for scores + issues
# ---------------------------------------------------------------------------

def _parse_d1_verdict_and_score(review_text: str) -> tuple[str, float]:
    """Extract verdict (PASS/FAIL) and overall score from D.1 review text."""
    verdict = ""
    status_m = re.search(r'\*\*Status:\*\*\s*(FAIL|PASS)', review_text)
    if status_m:
        verdict = status_m.group(1)

    score = 0.0
    score_m = re.search(r'\*\*Overall Score:\*\*\s*([\d.]+)/10', review_text)
    if score_m:
        score = float(score_m.group(1))

    return verdict, score


def _parse_d1_dimension_scores(review_text: str) -> dict[str, float]:
    """Extract per-dimension scores from the Scores section of a D.1 review."""
    scores: dict[str, float] = {}

    scores_section = re.search(
        r'## Scores\s*\n(.*?)(?=\n## |\Z)',
        review_text,
        re.DOTALL,
    )
    if not scores_section:
        return scores

    dim_rows = re.findall(
        r'\|\s*\d+\s*\|\s*(.+?)\s*\|\s*([\d.]+)/10\s*\|',
        scores_section.group(1),
    )
    for dim_name, dim_score in dim_rows:
        key = dim_name.strip().lower().replace(" ", "_")
        with contextlib.suppress(ValueError):
            scores[key] = float(dim_score)

    weighted_m = re.search(
        r'\*\*Weighted Overall:\*\*.*?=\s*\*\*([\d.]+)/10\*\*',
        scores_section.group(1),
    )
    if weighted_m:
        with contextlib.suppress(ValueError):
            scores["weighted_overall"] = float(weighted_m.group(1))

    return scores


def _parse_d1_issues(review_text: str) -> list[dict]:
    """Extract issues from the Critical Issues Found section of a D.1 review."""
    issues: list[dict] = []
    issues_section = re.search(
        r'## Critical Issues Found\s*\n(.*?)(?=\n## |\Z)',
        review_text,
        re.DOTALL,
    )
    if not issues_section:
        return issues

    issue_blocks = re.findall(
        r'### Issue \d+:\s*(.+?)(?=### Issue|\Z)',
        issues_section.group(1),
        re.DOTALL,
    )
    for block in issue_blocks:
        issue: dict[str, str] = {"type": "REVIEW_ISSUE", "severity": "HIGH"}
        loc_m = re.search(r'\*\*Location\*\*:\s*(.+)', block)
        if loc_m:
            issue["location"] = loc_m.group(1).strip()
        prob_m = re.search(r'\*\*Problem\*\*:\s*(.+)', block)
        if prob_m:
            issue["text"] = prob_m.group(1).strip()
        fix_m = re.search(r'\*\*Fix\*\*:\s*(.+)', block)
        if fix_m:
            issue["fix"] = fix_m.group(1).strip()
        issues.append(issue)

    return issues


def _parse_d1_review(raw_output: str, extract_delimiter_fn, extract_delimiter_tolerant_fn) -> "D1Result":
    """Parse D.1 Markdown review from delimiters."""
    from pipeline.parsing import D1Result

    review_text = extract_delimiter_fn(raw_output, "===REVIEW_START===", "===REVIEW_END===")
    if not review_text:
        review_text = extract_delimiter_tolerant_fn(
            raw_output, "===REVIEW_START===", "===REVIEW_END===",
            content_type="markdown",
        )

    if not review_text:
        return D1Result(ok=False, raw_review="", verdict="")

    verdict, score = _parse_d1_verdict_and_score(review_text)
    scores = _parse_d1_dimension_scores(review_text)
    if score > 0:
        scores["overall"] = score
    issues = _parse_d1_issues(review_text)

    if not verdict and score > 0:
        verdict = "PASS" if score >= 9.0 else "FAIL"

    return D1Result(
        ok=True,
        issues=issues,
        scores=scores,
        verdict=verdict,
        raw_review=review_text,
    )


# ---------------------------------------------------------------------------
# Factual review parsing — sub-parsers
# ---------------------------------------------------------------------------

def _parse_factual_scores(review_text: str) -> dict[str, float]:
    """Extract factual accuracy and plan adherence scores."""
    scores: dict[str, float] = {}
    score_m = re.search(r'\*\*Factual Alignment Score:\*\*\s*([\d.]+)/10', review_text)
    if score_m:
        scores["factual_accuracy"] = float(score_m.group(1))

    plan_m = re.search(r'\*\*Plan Adherence Score:\*\*\s*([\d.]+)/10', review_text)
    if plan_m:
        scores["plan_adherence"] = float(plan_m.group(1))

    return scores


def _parse_factual_issues(review_text: str) -> tuple[list[dict], int, int]:
    """Extract missing plan points and discrepancies. Returns (issues, discrepancy_count, missing_count)."""
    issues: list[dict] = []

    plan_missing_m = re.search(r'(\d+)\s+missing', review_text[:500])
    plan_missing_count = int(plan_missing_m.group(1)) if plan_missing_m else 0

    disc_m = re.search(r'\*\*Discrepancies \[Tier 1\]:\*\*\s*(\d+)', review_text)
    discrepancy_count = int(disc_m.group(1)) if disc_m else 0

    re.search(r'\*\*Unverified:\*\*\s*(\d+)', review_text)

    missing_points = re.findall(
        r'- \[ \]\s+(?:Point \d+:\s*)?(.+?)(?:\s*\u2014\s*MISSING)',
        review_text,
    )
    for pt_text in missing_points:
        issues.append({
            "type": "MISSING_PLAN_POINT",
            "severity": "MEDIUM",
            "text": pt_text.strip(),
        })

    disc_blocks = re.findall(
        r'### Discrepancy \d+:\s*(.+?)(?=### Discrepancy|\Z)',
        review_text,
        re.DOTALL,
    )
    for block in disc_blocks:
        issue: dict[str, str] = {"type": "FACTUAL_DISCREPANCY", "severity": "HIGH"}
        mod_m = re.search(r'\*\*Module says:\*\*\s*"(.+?)"', block)
        if mod_m:
            issue["text"] = mod_m.group(1).strip()
        ref_m = re.search(r'\*\*Reference says:\*\*\s*"(.+?)"', block)
        if ref_m:
            issue["reference"] = ref_m.group(1).strip()
        src_m = re.search(r'\*\*Source:\*\*\s*(.+)', block)
        if src_m:
            issue["source"] = src_m.group(1).strip()
        fix_m = re.search(r'\*\*Suggested fix:\*\*\s*(.+)', block)
        if fix_m:
            issue["fix"] = fix_m.group(1).strip()
        issues.append(issue)

    return issues, discrepancy_count, plan_missing_count


def _parse_factual_review(raw_output: str, extract_delimiter_fn, extract_delimiter_tolerant_fn) -> "D1Result":
    """Parse Gemini Fact Checker output."""
    from pipeline.parsing import D1Result

    review_text = extract_delimiter_fn(raw_output, "===FACTUAL_REVIEW_START===", "===FACTUAL_REVIEW_END===")
    if not review_text:
        review_text = extract_delimiter_tolerant_fn(
            raw_output, "===FACTUAL_REVIEW_START===", "===FACTUAL_REVIEW_END===",
            content_type="markdown",
        )

    if not review_text:
        return D1Result(ok=False, raw_review="", verdict="")

    verdict = ""
    status_m = re.search(r'\*\*Status:\*\*\s*(FAIL|PASS)', review_text)
    if status_m:
        verdict = status_m.group(1)

    scores = _parse_factual_scores(review_text)
    issues, discrepancy_count, plan_missing_count = _parse_factual_issues(review_text)

    if not verdict:
        verdict = "FAIL" if discrepancy_count > 0 or plan_missing_count >= 3 else "PASS"

    return D1Result(
        ok=True,
        issues=issues,
        scores=scores,
        verdict=verdict,
        raw_review=review_text,
    )


# ---------------------------------------------------------------------------
# Track calibration
# ---------------------------------------------------------------------------

_CALIBRATION_DIR = Path(__file__).resolve().parent.parent.parent / "claude_extensions" / "phases" / "calibration"


def _get_track_calibration(level: str, module_num: int) -> str:
    """Read the appropriate calibration file for a track/level + module number."""
    level_lower = level.lower()

    if level_lower == "b1" and module_num <= 5:
        cal_name = "b1-bridge.md"
    elif level_lower == "b1":
        cal_name = "b1-immersed.md"
    elif level_lower.startswith("lit"):
        cal_name = "lit.md"
    else:
        cal_name = f"{level_lower}.md"

    cal_path = _CALIBRATION_DIR / cal_name
    if cal_path.exists():
        return cal_path.read_text("utf-8")

    base = level_lower.split("-")[0]
    fallback = _CALIBRATION_DIR / f"{base}.md"
    if fallback.exists():
        return fallback.read_text("utf-8")

    return ""


def _get_russicism_table(level: str) -> str:
    """Extract the Russicism Lookup section from a calibration file."""
    cal_text = _get_track_calibration(level, 1)
    if not cal_text:
        return ""

    m = re.search(
        r'## Russicism Lookup.*?\n(.*?)(?=\n## |\Z)',
        cal_text,
        re.DOTALL,
    )
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# D.3 context builder
# ---------------------------------------------------------------------------

def _build_d3_context(d1_review: str, repair_cycle: int) -> str:
    """Build D.3 context injection with D.1 findings and D.2 repair info."""
    review_lines = d1_review.strip().split('\n')
    truncated = '\n'.join(review_lines[:80])
    if len(review_lines) > 80:
        truncated += f"\n\n... ({len(review_lines) - 80} more lines truncated)"

    return f"""## D.3 Re-Review Context (Repair Cycle {repair_cycle})

> **You are re-reviewing content that was already reviewed and repaired.**
> A previous D.1 review found issues. D.2 applied targeted FIND/REPLACE fixes.
> Your job: **verify the fixes landed correctly AND check for regressions** introduced by the repair.

### What D.1 Found (previous review summary)

<details>
<summary>D.1 Review (click to expand)</summary>

{truncated}

</details>

### Your D.3 Re-Review Focus

1. **Verify each D.1 issue was fixed** -- check that the specific problems from D.1 no longer exist in the current content
2. **Check for D.2 regressions** -- D.2 rewrites may have introduced new errors (broken sentences, orphaned references, formatting damage)
3. **Score the current state** -- your scores reflect the content AS IT IS NOW, not the D.1 review's scores
4. **Do NOT auto-pass** -- if D.2 fixes created new problems, flag them even though the originals are fixed

---"""


# ---------------------------------------------------------------------------
# Quick review quality gate — sub-helpers
# ---------------------------------------------------------------------------

def _check_citation_coverage(review_text: str, content_path: Path) -> tuple[bool, str]:
    """Check if review has enough Ukrainian citations for the content size."""
    from audit.checks.review_validation import _extract_ukrainian_citations

    citations = _extract_ukrainian_citations(review_text)
    content_text = content_path.read_text("utf-8") if content_path.exists() else ""
    word_count = len(content_text.split())

    min_citations = max(2, word_count // 600) if word_count > 500 else 2
    if len(citations) < min_citations:
        return False, (
            f"Shallow review: {len(citations)} citation(s), need \u2265{min_citations} "
            f"for {word_count}-word content"
        )
    return True, content_text


def _check_section_coverage(review_text: str, content_text: str) -> tuple[bool, str]:
    """Check if review mentions enough H2 sections from the content."""
    from audit.checks.review_gaming import _extract_h2_headers

    if not content_text:
        return True, "OK"

    h2s = _extract_h2_headers(content_text)
    skip = {'\u0441\u043b\u043e\u0432\u043d\u0438\u043a', 'vocabulary',
            '\u043b\u0435\u043a\u0441\u0438\u043a\u0430',
            '\u0431\u0456\u0431\u043b\u0456\u043e\u0433\u0440\u0430\u0444\u0456\u044f',
            '\u0434\u0436\u0435\u0440\u0435\u043b\u0430',
            '\u043b\u0456\u0442\u0435\u0440\u0430\u0442\u0443\u0440\u0430',
            '\u0432\u0438\u043a\u043e\u0440\u0438\u0441\u0442\u0430\u043d\u0456 \u0434\u0436\u0435\u0440\u0435\u043b\u0430',
            '\u0441\u0430\u043c\u043e\u043e\u0446\u0456\u043d\u044e\u0432\u0430\u043d\u043d\u044f',
            'self-assessment',
            '\u0441\u0430\u043c\u043e\u043f\u0435\u0440\u0435\u0432\u0456\u0440\u043a\u0430'}
    h2s = [h for h in h2s if h.strip().lower() not in skip]

    if len(h2s) >= 3:
        review_lower = review_text.lower()
        mentioned = sum(
            1 for h in h2s
            if h.strip().lower() in review_lower
            or (len(h.split(':')[0].strip()) > 3
                and h.split(':')[0].strip().lower() in review_lower)
        )
        coverage = mentioned / len(h2s)
        if coverage < 0.15:
            return False, (
                f"Shallow review: covers {mentioned}/{len(h2s)} "
                f"({coverage:.0%}) content sections"
            )

    return True, "OK"


def _quick_review_quality_gate(review_text: str, content_path: Path) -> tuple[bool, str]:
    """Fast pre-save check: reject obviously shallow/fake reviews."""
    ok, result = _check_citation_coverage(review_text, content_path)
    if not ok:
        return False, result
    content_text = result  # _check_citation_coverage returns content_text on success

    ok, msg = _check_section_coverage(review_text, content_text)
    if not ok:
        return False, msg

    if len(review_text.split()) < 150:
        return False, f"Shallow review: only {len(review_text.split())} words"

    return True, "OK"
