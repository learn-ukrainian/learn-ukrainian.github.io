#!/usr/bin/env python3
"""
Alignment Audit — checks plan ↔ content alignment for a given level.

Reuses outline_compliance functions for section extraction and fuzzy matching.
Reports: section match %, word count, and file existence for all module artifacts.

Usage:
    .venv/bin/python scripts/alignment_audit.py a1
    .venv/bin/python scripts/alignment_audit.py hist
    .venv/bin/python scripts/alignment_audit.py a1 --csv
"""

import argparse
import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Setup project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from audit.checks.outline_compliance import (
    extract_markdown_sections,
    fuzzy_match_section,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CURRICULUM = PROJECT_ROOT / "curriculum" / "l2-uk-en"


def load_plan(plan_path: Path) -> dict | None:
    """Load a plan YAML, return None on failure."""
    try:
        with open(plan_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"  WARN: failed to load plan {plan_path.name}: {e}", file=sys.stderr)
        return None


def audit_module(plan_path: Path, level_dir: Path) -> dict:
    """Audit a single module, returning a row dict."""
    plan = load_plan(plan_path)
    slug = plan_path.stem
    seq = plan.get("sequence", "?") if plan else "?"
    outline = plan.get("content_outline", []) if plan else []
    plan_sections = [s["section"] for s in outline if "section" in s]

    md_path = level_dir / f"{slug}.md"
    act_path = level_dir / "activities" / f"{slug}.yaml"
    vocab_path = level_dir / "vocabulary" / f"{slug}.yaml"
    research_path = level_dir / "research" / f"{slug}-research.md"
    discovery_path = level_dir / "orchestration" / slug / "discovery.yaml"

    row = {
        "seq": seq,
        "slug": slug,
        "plan_sections": len(plan_sections),
        "md_sections": 0,
        "section_match": 0.0,
        "word_count": 0,
        "has_activities": act_path.exists(),
        "has_vocab": vocab_path.exists(),
        "has_research": research_path.exists(),
        "has_discovery": discovery_path.exists(),
        "status": "MISSING",
    }

    if not md_path.exists():
        return row

    # Extract markdown sections
    md_sections = extract_markdown_sections(md_path)
    row["md_sections"] = len(md_sections)
    row["word_count"] = sum(s["words"] for s in md_sections.values())

    # Fuzzy-match plan sections against markdown sections
    if plan_sections and md_sections:
        md_names = list(md_sections.keys())
        matched = 0
        for ps in plan_sections:
            is_match, _, _ = fuzzy_match_section(ps, md_names)
            if is_match:
                matched += 1
        row["section_match"] = round(matched / len(plan_sections) * 100, 1)

    # Determine status
    if row["section_match"] >= 80:
        row["status"] = "ALIGNED"
    elif row["section_match"] > 0:
        row["status"] = "DRIFTED"
    else:
        row["status"] = "DRIFTED" if md_path.exists() else "MISSING"

    return row


def main():
    parser = argparse.ArgumentParser(description="Plan↔content alignment audit")
    parser.add_argument("level", help="Level directory name (e.g., a1, hist, b1)")
    parser.add_argument("--csv", action="store_true", help="Output as CSV")
    args = parser.parse_args()

    plans_dir = CURRICULUM / "plans" / args.level
    level_dir = CURRICULUM / args.level

    if not plans_dir.exists():
        print(f"ERROR: Plans directory not found: {plans_dir}", file=sys.stderr)
        sys.exit(1)

    plan_files = sorted(plans_dir.glob("*.yaml"))
    if not plan_files:
        print(f"ERROR: No plan files found in {plans_dir}", file=sys.stderr)
        sys.exit(1)

    if not level_dir.exists():
        print(f"ERROR: Level directory not found: {level_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Auditing {args.level.upper()} ({len(plan_files)} plans)...\n")

    rows = [audit_module(p, level_dir) for p in plan_files]
    rows.sort(key=lambda r: (r["seq"] if isinstance(r["seq"], int) else 999, r["slug"]))

    # --- Summary stats ---
    total = len(rows)
    aligned = sum(1 for r in rows if r["status"] == "ALIGNED")
    drifted = sum(1 for r in rows if r["status"] == "DRIFTED")
    missing = sum(1 for r in rows if r["status"] == "MISSING")
    has_act = sum(1 for r in rows if r["has_activities"])
    has_voc = sum(1 for r in rows if r["has_vocab"])
    has_res = sum(1 for r in rows if r["has_research"])
    has_dis = sum(1 for r in rows if r["has_discovery"])

    if args.csv:
        print("seq,slug,plan_sections,md_sections,section_match,word_count,has_activities,has_vocab,has_research,has_discovery,status")
        for r in rows:
            print(f"{r['seq']},{r['slug']},{r['plan_sections']},{r['md_sections']},"
                  f"{r['section_match']},{r['word_count']},"
                  f"{r['has_activities']},{r['has_vocab']},"
                  f"{r['has_research']},{r['has_discovery']},{r['status']}")
    else:
        # Pretty table
        hdr = f"{'seq':>4} {'slug':<42} {'plan':>4} {'md':>3} {'match%':>6} {'words':>6} {'act':>3} {'voc':>3} {'res':>3} {'dis':>3} {'status':<8}"
        sep = "-" * len(hdr)
        print(sep)
        print(hdr)
        print(sep)
        for r in rows:
            act = "✓" if r["has_activities"] else "✗"
            voc = "✓" if r["has_vocab"] else "✗"
            res = "✓" if r["has_research"] else "✗"
            dis = "✓" if r["has_discovery"] else "✗"
            print(
                f"{r['seq']:>4} {r['slug']:<42} {r['plan_sections']:>4} "
                f"{r['md_sections']:>3} {r['section_match']:>5.1f}% {r['word_count']:>6} "
                f"  {act}   {voc}   {res}   {dis} {r['status']:<8}"
            )
        print(sep)
        print(f"\nSummary: {total} modules | {aligned} ALIGNED | {drifted} DRIFTED | {missing} MISSING")
        print(f"  Activities: {has_act}/{total} | Vocab: {has_voc}/{total} | Research: {has_res}/{total} | Discovery: {has_dis}/{total}")


if __name__ == "__main__":
    main()
