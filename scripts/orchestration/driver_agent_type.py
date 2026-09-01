"""Resolve the driver agent type for a launcher lane from ``area_assignments.yaml``.

Claude Code selects its system prompt from ``--agent``. The project default
(``.claude/settings.json`` → ``"agent"``) is the main orchestrator, which is the
wrong prompt for every non-curriculum driver lane. The driver launcher calls this
module to inject ``--agent <driver_agent_type>`` for the epic's area.

Lookup order: the lane is an area key → that area's ``driver_agent_type``; else the
area whose ``slots`` list contains ``<provider>-<lane>`` (e.g. ``claude-folk`` lives
under ``seminars``); else nothing (the caller keeps the settings default).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ASSIGNMENTS_PATH = PROJECT_ROOT / "scripts" / "config" / "area_assignments.yaml"


def resolve_driver_agent_type(
    lane: str,
    *,
    assignments_path: Path = DEFAULT_ASSIGNMENTS_PATH,
    provider: str = "claude",
) -> str | None:
    lane = (lane or "").strip()
    if not lane:
        return None
    try:
        data = yaml.safe_load(assignments_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return None
    assignments = data.get("assignments") if isinstance(data, dict) else None
    if not isinstance(assignments, dict):
        return None

    direct = assignments.get(lane)
    if isinstance(direct, dict) and direct.get("driver_agent_type"):
        return str(direct["driver_agent_type"]).strip() or None

    slot = f"{provider}-{lane}"
    for entry in assignments.values():
        if not isinstance(entry, dict):
            continue
        slots = entry.get("slots") or []
        if isinstance(slots, list) and slot in slots and entry.get("driver_agent_type"):
            return str(entry["driver_agent_type"]).strip() or None
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lane", required=True, help="launcher lane after selector normalisation, e.g. infra")
    parser.add_argument("--provider", default="claude", help="slot prefix used for the slots fallback (default claude)")
    parser.add_argument("--assignments", type=Path, default=DEFAULT_ASSIGNMENTS_PATH, help="area_assignments.yaml path")
    args = parser.parse_args(argv)
    agent_type = resolve_driver_agent_type(args.lane, assignments_path=args.assignments, provider=args.provider)
    if not agent_type:
        print(f"no driver_agent_type for lane {args.lane!r} in {args.assignments}", file=sys.stderr)
        return 1
    print(agent_type)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
