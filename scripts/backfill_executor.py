#!/usr/bin/env python3
"""Backfill executor provenance for existing state.json files.

Infers executor info from artifacts:
- *-gemini-session.json files → gemini LLM executor (reads model from session)
- review files → claude LLM executor
- discover → script (discover_passthrough)
- validate → deterministic (morphological_validator)
- mdx phase → not tracked in state

Usage:
    .venv/bin/python scripts/backfill_executor.py [--dry-run]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"


def _infer_gemini_model(orch_dir: Path, phase_prefix: str) -> str:
    """Try to read model from a Gemini session JSON file."""
    for f in sorted(orch_dir.glob(f"{phase_prefix}*-gemini-session.json")):
        try:
            data = json.loads(f.read_text("utf-8"))
            if isinstance(data, dict) and data.get("model"):
                return data["model"]
        except Exception:
            continue
    # Fallback: check content-attempt files
    for f in sorted(orch_dir.glob("content-attempt-*-gemini-session.json")):
        try:
            data = json.loads(f.read_text("utf-8"))
            if isinstance(data, dict) and data.get("model"):
                return data["model"]
        except Exception:
            continue
    return "unknown"


def _infer_executor(phase_name: str, phase_data: dict, orch_dir: Path) -> dict | None:
    """Infer executor from artifacts and phase data."""
    # Already has executor
    if phase_data.get("executor"):
        return None

    # Legacy ad-hoc agent/model → migrate
    if phase_data.get("agent") or phase_data.get("model"):
        return {
            "type": "llm",
            "agent": phase_data.get("agent", "unknown"),
            "model": phase_data.get("model", "unknown"),
        }

    # Infer from phase name + artifacts
    if phase_name == "discover":
        return {"type": "script", "name": "discover_passthrough"}

    if phase_name == "validate":
        return {"type": "deterministic", "name": "morphological_validator"}

    if phase_name == "research":
        model = _infer_gemini_model(orch_dir, "research")
        if model != "unknown":
            return {"type": "llm", "agent": "gemini", "model": model}
        # Check for Claude research
        if any(orch_dir.glob("research-claude-*")):
            return {"type": "llm", "agent": "claude", "model": "unknown"}
        return {"type": "llm", "agent": "gemini", "model": model}

    if phase_name == "content":
        model = _infer_gemini_model(orch_dir, "content")
        return {"type": "llm", "agent": "gemini", "model": model}

    if phase_name == "activities":
        note = phase_data.get("note", "")
        if "adopted" in note or "extracted" in note:
            return {"type": "script", "name": note.replace("-", "_")}
        model = _infer_gemini_model(orch_dir, "activit")
        return {"type": "llm", "agent": "gemini", "model": model}

    if phase_name == "review":
        # Check for Claude review files
        review_files = list(orch_dir.glob("review-*.md"))
        for rf in review_files:
            try:
                text = rf.read_text("utf-8")[:500]
                if "claude" in text.lower():
                    return {"type": "llm", "agent": "claude", "model": "unknown"}
            except Exception:
                continue
        # Default to gemini for review
        model = _infer_gemini_model(orch_dir, "review")
        if model != "unknown":
            return {"type": "llm", "agent": "gemini", "model": model}
        return {"type": "llm", "agent": "unknown", "model": "unknown"}

    return None


def backfill(dry_run: bool = False) -> tuple[int, int]:
    """Backfill all state.json files. Returns (files_updated, phases_updated)."""
    files_updated = 0
    phases_updated = 0

    for state_file in sorted(CURRICULUM_DIR.rglob("orchestration/*/state.json")):
        try:
            data = json.loads(state_file.read_text("utf-8"))
        except Exception:
            continue

        if data.get("mode") != "v5":
            continue

        orch_dir = state_file.parent
        modified = False
        phases = data.get("phases", {})

        for phase_name, phase_data in phases.items():
            if not isinstance(phase_data, dict):
                continue
            executor = _infer_executor(phase_name, phase_data, orch_dir)
            if executor is not None:
                phase_data["executor"] = executor
                # Clean up legacy fields
                phase_data.pop("agent", None)
                phase_data.pop("model", None)
                modified = True
                phases_updated += 1

        if modified:
            files_updated += 1
            if not dry_run:
                state_file.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False), "utf-8"
                )
            slug = data.get("slug", orch_dir.name)
            print(f"  {'[DRY-RUN] ' if dry_run else ''}Updated {slug}")

    return files_updated, phases_updated


def main():
    dry_run = "--dry-run" in sys.argv
    print(f"Backfilling executor provenance {'(DRY-RUN)' if dry_run else ''}...")
    files, phases = backfill(dry_run)
    print(f"\nDone: {files} files, {phases} phases updated")


if __name__ == "__main__":
    main()
