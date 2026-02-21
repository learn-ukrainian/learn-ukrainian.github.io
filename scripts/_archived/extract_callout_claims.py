#!/usr/bin/env python3
"""Extract all callout boxes from built modules for factual review.

Produces a single markdown file with every [!did-you-know], [!myth-buster],
[!culture-note], and [!fun-fact] block, grouped by level, with source location
and audit status. Designed for a single-pass human or AI fact-check.

Usage:
    .venv/bin/python scripts/extract_callout_claims.py
    .venv/bin/python scripts/extract_callout_claims.py --output claims.md
    .venv/bin/python scripts/extract_callout_claims.py --level a1
"""

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURRICULUM = ROOT / "curriculum" / "l2-uk-en"

# HIGH RISK: assert facts about the real world — must be verified
HIGH_RISK_TYPES = {
    "myth-buster", "did-you-know", "culture-note", "fun-fact",
    "decolonization", "history-bite", "source", "quote",
    "culture", "cultural", "fact", "biography", "legacy",
    "historiography", "perspective",
}
# MEDIUM RISK: may contain factual claims mixed with pedagogy
MEDIUM_RISK_TYPES = {"context", "insight"}
# LOW RISK / PEDAGOGICAL: grammar tips, observations, summaries (skip by default)
SKIP_CALLOUT_TYPES = {
    "tip", "observe", "note", "summary", "caution", "warning",
    "example", "practice", "remember", "important",
    "dialogue", "model-answer", "analysis", "reflection",
    "essay-response",
}

# Match any callout box
CALLOUT_RE = re.compile(r"^> \[!([\w-]+)\]", re.MULTILINE)


def extract_callouts(md_path: Path, allowed_types: set[str] | None = None) -> list[dict]:
    """Extract callout blocks from a markdown file.

    Args:
        md_path: Path to the markdown file.
        allowed_types: If set, only include callouts of these types.
                       If None, include all callouts.
    """
    content = md_path.read_text("utf-8")
    lines = content.split("\n")
    results = []

    i = 0
    while i < len(lines):
        m = CALLOUT_RE.match(lines[i])
        if m:
            callout_type = m.group(1)
            start_line = i + 1  # 1-indexed
            block_lines = [lines[i]]
            i += 1
            while i < len(lines) and lines[i].startswith(">"):
                block_lines.append(lines[i])
                i += 1
            if allowed_types is None or callout_type in allowed_types:
                results.append({
                    "type": callout_type,
                    "line": start_line,
                    "text": "\n".join(block_lines),
                })
        else:
            i += 1

    return results


def get_audit_status(level: str, slug: str) -> str:
    """Get audit pass/fail status for a module."""
    status_path = CURRICULUM / level / "status" / f"{slug}.json"
    if not status_path.exists():
        return "no-status"
    try:
        data = json.loads(status_path.read_text("utf-8"))
        overall = data.get("overall", {})
        if isinstance(overall, dict):
            return overall.get("status", "unknown")
        return str(overall)
    except Exception:
        return "error"


def main():
    parser = argparse.ArgumentParser(description="Extract callout boxes for fact-checking")
    parser.add_argument("--output", "-o", default="curriculum/l2-uk-en/callout-claims-review.md",
                        help="Output file path (default: curriculum/l2-uk-en/callout-claims-review.md)")
    parser.add_argument("--level", "-l", help="Filter to a specific level (e.g., a1, b1, b2-hist)")
    parser.add_argument("--include-medium", action="store_true",
                        help="Include medium-risk callout types (context, insight)")
    parser.add_argument("--all-types", action="store_true",
                        help="Include ALL callout types (including pedagogical)")
    args = parser.parse_args()

    # Determine which callout types to include
    if args.all_types:
        allowed_types = None  # all
    elif args.include_medium:
        allowed_types = HIGH_RISK_TYPES | MEDIUM_RISK_TYPES
    else:
        allowed_types = HIGH_RISK_TYPES

    if args.level:
        levels = [args.level]
    else:
        levels = sorted(
            d.name for d in CURRICULUM.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

    all_claims = []  # (level, slug, audit_status, callouts)

    for level in levels:
        level_dir = CURRICULUM / level
        md_files = sorted(level_dir.glob("*.md"))
        for md_path in md_files:
            slug = md_path.stem
            if md_path.stat().st_size < 500:
                continue
            callouts = extract_callouts(md_path, allowed_types)
            if callouts:
                audit = get_audit_status(level, slug)
                all_claims.append((level, slug, audit, callouts))

    # Generate output
    out_lines = [
        "# Callout Box Fact-Check Review",
        "",
        f"**Generated:** {__import__('datetime').date.today()}",
        f"**Total modules with callouts:** {len(all_claims)}",
        f"**Total callout boxes:** {sum(len(c) for _, _, _, c in all_claims)}",
        "",
        "## Instructions",
        "",
        "Review each callout box below. For each claim, mark:",
        "- **OK** — claim is accurate",
        "- **EXAGGERATION** — claim overstates (e.g., \"first in Europe\" when it's \"first in Eastern Slavic world\")",
        "- **FABRICATION** — claim is invented (e.g., nonexistent works, fake statistics)",
        "- **UNVERIFIABLE** — claim may be true but cannot be confirmed",
        "- **NEEDS FIX** — with the corrected text",
        "",
        "---",
        "",
    ]

    current_level = None
    claim_num = 0

    for level, slug, audit, callouts in all_claims:
        if level != current_level:
            current_level = level
            level_count = sum(len(c) for l, s, a, c in all_claims if l == level)
            out_lines.append(f"# {level.upper()} ({level_count} callouts)")
            out_lines.append("")

        out_lines.append(f"## {level}/{slug} (audit: {audit})")
        out_lines.append("")

        for callout in callouts:
            claim_num += 1
            out_lines.append(f"### Claim #{claim_num} — `[!{callout['type']}]` at line {callout['line']}")
            out_lines.append(f"**File:** `curriculum/l2-uk-en/{level}/{slug}.md:{callout['line']}`")
            out_lines.append("")
            out_lines.append(callout["text"])
            out_lines.append("")
            out_lines.append("**Verdict:** _________________")
            out_lines.append("")
            out_lines.append("---")
            out_lines.append("")

    output_path = ROOT / args.output if not os.path.isabs(args.output) else Path(args.output)
    output_path.write_text("\n".join(out_lines), "utf-8")

    print(f"Extracted {claim_num} callout boxes from {len(all_claims)} modules")
    print(f"Output: {output_path}")

    # Summary by type
    type_counts = {}
    for _, _, _, callouts in all_claims:
        for c in callouts:
            type_counts[c["type"]] = type_counts.get(c["type"], 0) + 1
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  [{t}]: {count}")


if __name__ == "__main__":
    main()
