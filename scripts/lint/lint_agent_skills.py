#!/usr/bin/env python3
"""Validate local agent skill metadata.

The skill loader reads YAML frontmatter before it can show a useful error.
This lint catches malformed metadata at deploy time so broken skills do not
get copied into `.claude/`, `.agent/`, or `.agents/`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = PROJECT_ROOT / "claude_extensions" / "skills"
REQUIRED_KEYS = {"name", "description"}


def _frontmatter(path: Path) -> tuple[dict[str, object] | None, str | None]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, "missing opening frontmatter delimiter"

    end = text.find("\n---\n", 4)
    if end == -1:
        return None, "missing closing frontmatter delimiter"

    raw = text[4:end]
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return None, f"invalid YAML frontmatter: {exc}"

    if not isinstance(data, dict):
        return None, "frontmatter must be a mapping"

    return data, None


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print(f"skills directory not found: {SKILLS_DIR.relative_to(PROJECT_ROOT)}", file=sys.stderr)
        return 1

    errors: list[str] = []
    skill_files = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    skill_dirs = sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())

    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        if skill_file not in skill_files:
            errors.append(f"{skill_dir.relative_to(PROJECT_ROOT)}: missing SKILL.md")

    for skill_file in skill_files:
        rel = skill_file.relative_to(PROJECT_ROOT)
        data, error = _frontmatter(skill_file)
        if error is not None:
            errors.append(f"{rel}: {error}")
            continue

        missing = sorted(REQUIRED_KEYS - set(data))
        if missing:
            errors.append(f"{rel}: missing required key(s): {', '.join(missing)}")

        for key in REQUIRED_KEYS | {"argument-hint", "compatibility", "effort"}:
            value = data.get(key)
            if value is not None and not isinstance(value, str):
                errors.append(f"{rel}: {key} must be a string")

        expected_name = skill_file.parent.name
        actual_name = data.get("name")
        if actual_name != expected_name:
            errors.append(f"{rel}: name {actual_name!r} does not match directory {expected_name!r}")

    if errors:
        print("Skill metadata lint failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"Skill metadata OK ({len(skill_files)} skill(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
