"""Extract structured review findings and build targeted fix prompts.

Parses review-result.md files to extract individual issues with location,
problem, and fix information. Builds constrained fix prompts that prevent
blind module rewrites by specifying exactly which sections to modify.

Issue #937: Fix loops were retrying blindly instead of targeting the specific
issues identified in the review.
"""

from __future__ import annotations

import re
from pathlib import Path


def extract_review_findings(review_text: str) -> list[dict]:
    """Extract structured findings from a review-result.md file.

    Parses both:
    - Claude D.1 format: "### Issue N: ..." with **Location**, **Problem**, **Fix**
    - Gemini review format: "### Issue N: ..." with same structure

    Returns list of dicts with keys: title, location, problem, fix, severity.
    """
    findings: list[dict] = []

    # Find all issue blocks
    issue_blocks = re.findall(
        r'### Issue \d+:\s*(.+?)(?=### Issue \d+:|\n## |\Z)',
        review_text,
        re.DOTALL,
    )

    for block in issue_blocks:
        finding: dict[str, str] = {"severity": "HIGH"}

        # Extract title (first line of the block)
        title_line = block.strip().split('\n')[0].strip()
        finding["title"] = title_line

        # Extract structured fields
        loc_m = re.search(r'\*\*Location\*\*:\s*(.+)', block)
        if loc_m:
            finding["location"] = loc_m.group(1).strip()

        prob_m = re.search(r'\*\*Problem\*\*:\s*(.+)', block)
        if prob_m:
            finding["problem"] = prob_m.group(1).strip()

        fix_m = re.search(r'\*\*(?:Fix|Suggested Fix|Recommendation)\*\*:\s*(.+)', block)
        if fix_m:
            finding["fix"] = fix_m.group(1).strip()

        sev_m = re.search(r'\*\*Severity\*\*:\s*(\w+)', block)
        if sev_m:
            finding["severity"] = sev_m.group(1).strip().upper()

        findings.append(finding)

    return findings


def extract_sections_to_modify(findings: list[dict]) -> list[str]:
    """Extract unique section names from finding locations.

    Looks for markdown header references like "Section: Xyz" or "### Xyz"
    in the location fields.
    """
    sections: set[str] = set()
    for f in findings:
        loc = f.get("location", "")
        # Match "Section N: Title" or "### Title" patterns
        m = re.search(r'(?:Section \d+:\s*|###?\s+)(.+?)(?:\s*\(|$)', loc)
        if m:
            sections.add(m.group(1).strip())
        elif loc:
            # Use the raw location as-is
            sections.add(loc.strip())
    return sorted(sections)


def build_targeted_fix_prompt(
    findings: list[dict],
    fix_plan_base: str = "",
) -> str:
    """Build a constrained fix prompt from review findings.

    The prompt:
    - Lists specific sections to modify (from location fields)
    - Explicitly forbids touching other sections
    - Includes a "preserve these gates" reminder

    Args:
        findings: Structured review findings from extract_review_findings.
        fix_plan_base: Existing fix plan text to prepend.

    Returns:
        Fix prompt text with targeted constraints.
    """
    if not findings:
        return fix_plan_base

    sections = extract_sections_to_modify(findings)

    lines = ["## Review Findings (targeted fix required)\n"]
    lines.append("**CONSTRAINTS:**")
    lines.append("- Fix ONLY the issues listed below")
    lines.append("- Do NOT rewrite surrounding text")
    lines.append("- Preserve word count and structure")
    if sections:
        lines.append(f"- Only modify these sections: {', '.join(sections)}")
    lines.append("")

    for i, finding in enumerate(findings, 1):
        lines.append(f"### Finding {i}: {finding.get('title', 'Untitled')}")
        if "location" in finding:
            lines.append(f"**Location**: {finding['location']}")
        if "problem" in finding:
            lines.append(f"**Problem**: {finding['problem']}")
        if "fix" in finding:
            lines.append(f"**Required Fix**: {finding['fix']}")
        lines.append(f"**Severity**: {finding.get('severity', 'HIGH')}")
        lines.append("")

    targeted_text = "\n".join(lines)

    if fix_plan_base:
        return targeted_text + "\n---\n\n" + fix_plan_base
    return targeted_text


def inject_findings_into_fix_plan(
    orch_dir: Path, fix_plan: str, label: str = "review",
) -> str:
    """Load review findings and inject into fix_plan. Returns updated fix_plan.

    Logs the injection count. Silently returns the original fix_plan if
    no findings are found or if loading fails.
    """
    import logging

    from pipeline.core import log

    try:
        findings = load_review_findings(orch_dir)
        if findings:
            fix_plan = build_targeted_fix_prompt(findings, fix_plan)
            log(f"  {label}: Injected {len(findings)} structured finding(s) into fix prompt")
    except (FileNotFoundError, OSError) as e:
        logging.getLogger(__name__).debug("%s: Could not load review findings: %s", label, e)
    except Exception as e:
        logging.getLogger(__name__).warning("%s: Unexpected error injecting review findings: %s", label, e)
    return fix_plan


def load_review_findings(orch_dir: Path) -> list[dict]:
    """Load review findings from the orchestration directory.

    Tries review-result.md first, then falls back to review-pass1-raw.md
    and review-pass2-raw.md.
    """
    review_path = orch_dir / "review-result.md"
    if review_path.exists():
        return extract_review_findings(review_path.read_text("utf-8"))

    # Fallback: try individual review passes
    findings: list[dict] = []
    for name in ("review-pass1-raw.md", "review-pass2-raw.md"):
        p = orch_dir / name
        if p.exists():
            findings.extend(extract_review_findings(p.read_text("utf-8")))

    return findings
