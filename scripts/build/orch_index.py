#!/usr/bin/env python3
"""Generate orchestration/{slug}/index.md — human-readable build summary.

Can be called standalone or from v6_build.py after build completion.

Usage:
    .venv/bin/python scripts/build/orch_index.py a1 ukrainian-alphabet
    .venv/bin/python scripts/build/orch_index.py a1 --all

Issue: #1029
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


def generate_index(level: str, slug: str) -> Path | None:
    """Generate orchestration index.md for a single module."""
    orch_dir = CURRICULUM_ROOT / level / "orchestration" / slug
    if not orch_dir.exists():
        return None

    lines = [f"# Build Summary: {slug} ({level.upper()})\n"]
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # State
    state_path = orch_dir / "state.json"
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text())
            phases = state.get("phases", {})
            if phases:
                lines.append("## Pipeline Phases\n")
                lines.append("| Phase | Status | Timestamp |")
                lines.append("|-------|--------|-----------|")
                for phase, info in phases.items():
                    ts = info.get("ts", "")[:19].replace("T", " ")
                    lines.append(
                        f"| {phase} | {info.get('status', '?')} | {ts} |"
                    )
                lines.append("")
        except (json.JSONDecodeError, TypeError):
            pass

    # Review scores
    review_dir = CURRICULUM_ROOT / level / "review"
    reviews = (
        sorted(review_dir.glob(f"{slug}-review-r*.md"))
        if review_dir.exists()
        else []
    )
    if reviews:
        lines.append("## Reviews\n")
        lines.append("| Round | File |")
        lines.append("|-------|------|")
        for r in reviews:
            round_num = r.stem.split("-r")[-1]
            lines.append(f"| {round_num} | {r.name} |")
        lines.append("")

    # Dispatch logs
    dispatch_dir = orch_dir / "dispatch"
    if dispatch_dir.exists():
        meta_files = sorted(dispatch_dir.glob("*-meta.json"))
        if meta_files:
            lines.append("## Dispatch Log\n")
            lines.append("| Phase | Agent | Duration | OK |")
            lines.append("|-------|-------|----------|----|")
            for mf in meta_files:
                try:
                    d = json.loads(mf.read_text())
                    ok_icon = "✅" if d.get("ok") else "❌"
                    lines.append(
                        f"| {d.get('phase', '?')} | {d.get('agent', '?')} "
                        f"| {d.get('duration_s', 0):.0f}s | {ok_icon} |"
                    )
                except (json.JSONDecodeError, TypeError):
                    pass
            lines.append("")

    # Friction
    friction_path = orch_dir / "friction.yaml"
    if friction_path.exists():
        lines.append("## Friction\n")
        lines.append(f"- `friction.yaml` ({friction_path.stat().st_size} bytes)")
        lines.append("")

    # VERIFY flags
    verify_path = orch_dir / "verify-flags.yaml"
    if verify_path.exists():
        lines.append("## Writer VERIFY Flags\n")
        lines.append(f"- `verify-flags.yaml` ({verify_path.stat().st_size} bytes)")
        lines.append("")

    # Files inventory
    all_files = sorted(
        f.name
        for f in orch_dir.iterdir()
        if f.is_file() and f.name != "index.md"
    )
    if all_files:
        lines.append("## Files\n")
        for f in all_files:
            lines.append(f"- `{f}`")
        lines.append("")

    index_path = orch_dir / "index.md"
    index_path.write_text("\n".join(lines), "utf-8")
    return index_path


def main():
    parser = argparse.ArgumentParser(description="Generate orchestration index files")
    parser.add_argument("level", help="Level (a1, a2, b1, etc.)")
    parser.add_argument("slug", nargs="?", help="Module slug (omit with --all)")
    parser.add_argument("--all", action="store_true", help="Generate for all modules")
    args = parser.parse_args()

    if args.all:
        orch_dir = CURRICULUM_ROOT / args.level / "orchestration"
        if not orch_dir.exists():
            print(f"No orchestration dir for {args.level}")
            return
        count = 0
        for d in sorted(orch_dir.iterdir()):
            if d.is_dir():
                result = generate_index(args.level, d.name)
                if result:
                    count += 1
        print(f"Generated {count} index files for {args.level}")
    elif args.slug:
        result = generate_index(args.level, args.slug)
        if result:
            print(f"✅ Generated: {result}")
        else:
            print(f"No orchestration dir for {args.level}/{args.slug}")
    else:
        parser.error("Provide slug or --all")


if __name__ == "__main__":
    main()
