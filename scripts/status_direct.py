#!/usr/bin/env python3
"""status_direct.py — Status dashboard for the l2-uk-direct track.

Usage:
  .venv/bin/python scripts/status_direct.py
  .venv/bin/python scripts/status_direct.py --level a1
  .venv/bin/python scripts/status_direct.py --json

Output:
  l2-uk-direct — A1
  ──────────────────────────────────────────────────────────────────────
  #    Module                    Status       Images     Notes
  ──────────────────────────────────────────────────────────────────────
  1    abetka                    🔵 draft     0/33       Needs Pixabay pass
  2    sklad                     ⬜ MISSING   —          Not yet created
  ...
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = REPO_ROOT / "curriculum/l2-uk-direct/manifest.yaml"

STATUS_EMOJI = {
    "published": "🟢",
    "ready":     "🟡",
    "draft":     "🔵",
    "MISSING":   "⬜",
}

STATUS_ORDER = ["published", "ready", "draft", "MISSING"]


def emoji_for(status: str) -> str:
    return STATUS_EMOJI.get(status, "❓")


def load_module_row(lvl_name: str, seq: int, slug: str) -> dict:
    yaml_path   = REPO_ROOT / f"curriculum/l2-uk-direct/{lvl_name}/{slug}.yaml"
    status_path = REPO_ROOT / f"curriculum/l2-uk-direct/{lvl_name}/{slug}.status.json"

    if not yaml_path.exists():
        return {
            "level": lvl_name, "seq": seq, "slug": slug,
            "status": "MISSING", "images": "—",
            "notes": "Not yet created",
        }

    status = "draft"
    images_str = "—"
    notes = ""

    if status_path.exists():
        try:
            with open(status_path, encoding="utf-8") as f:
                sdata = json.load(f)
            status    = sdata.get("status", "draft")
            sourced   = sdata.get("images_sourced", 0)
            total     = sdata.get("images_total", 0)
            images_str = f"{sourced}/{total}" if total else "—"
            notes     = sdata.get("notes", "")
        except Exception as e:
            notes = f"⚠ status.json error: {e}"
    else:
        notes = "No status.json"

    return {
        "level": lvl_name, "seq": seq, "slug": slug,
        "status": status, "images": images_str,
        "notes": notes,
    }


def collect_rows(level_filter: str | None = None) -> list[dict]:
    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(2)

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    rows: list[dict] = []
    for lvl_name, lvl_data in manifest.get("levels", {}).items():
        if level_filter and lvl_name != level_filter:
            continue
        for i, slug in enumerate(lvl_data.get("sequence", []), start=1):
            rows.append(load_module_row(lvl_name, i, slug))
    return rows


def print_table(rows: list[dict], track_name: str) -> None:
    current_level: str | None = None

    for row in rows:
        if row["level"] != current_level:
            current_level = row["level"]
            print(f"\n{track_name} — {current_level.upper()}")
            print("─" * 72)
            print(f"{'#':<5} {'Module':<26} {'Status':<14} {'Images':<10} Notes")
            print("─" * 72)

        em     = emoji_for(row["status"])
        status = f"{em} {row['status']}"
        notes  = (row["notes"] or "")[:34]

        print(
            f"{row['seq']:<5} {row['slug']:<26} {status:<14} "
            f"{row['images']:<10} {notes}"
        )

    # ── Summary ────────────────────────────────────────────────────────────
    by_status: dict[str, int] = {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1

    total = len(rows)
    print("\n" + "─" * 72)
    print("Summary:")
    for s in STATUS_ORDER:
        if s in by_status:
            print(f"  {emoji_for(s)} {s:<12} {by_status[s]}")
    other = {k: v for k, v in by_status.items() if k not in STATUS_ORDER}
    for s, c in other.items():
        print(f"  {emoji_for(s)} {s:<12} {c}")
    print(f"  Total: {total}")

    # ── Missing list (actionable) ──────────────────────────────────────────
    missing = [r for r in rows if r["status"] == "MISSING"]
    if missing:
        print(f"\n{'─' * 72}")
        print(f"Next to build ({len(missing)} modules):")
        for r in missing:
            print(f"  [{r['level']}] {r['slug']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="l2-uk-direct track status dashboard.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--level", metavar="LEVEL", help="Filter by level (e.g. a1)")
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="Output raw JSON instead of table")
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(2)

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    track_name = manifest.get("name", "l2-uk-direct")

    rows = collect_rows(level_filter=args.level)

    if args.as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print_table(rows, track_name)


if __name__ == "__main__":
    main()
