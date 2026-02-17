#!/usr/bin/env python3
"""
Prompt linter — catches known anti-patterns in Gemini skill/phase files.

Runs automatically during `npm run claude:deploy` (add to package.json).
Can also be run standalone: .venv/bin/python scripts/lint_prompts.py

Exit code 0 = clean, 1 = violations found.
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories to scan
SCAN_DIRS = [
    PROJECT_ROOT / "gemini_extensions" / "skills",
    PROJECT_ROOT / "claude_extensions" / "phases",
]

# ---------- RULES ----------
# Each rule: (id, severity, description, file_glob, pattern, exception_pattern)
# severity: "error" = blocks deploy, "warn" = advisory
# exception_pattern: if this also matches the same line, it's a false positive (anti-pattern guards)

RULES = [
    # IPA flooding
    (
        "IPA_EVERY_WORD",
        "error",
        "IPA instruction says 'every word' — should be 'first occurrence only'",
        "*.md",
        re.compile(r"IPA\s+(for\s+)?every\s+new", re.IGNORECASE),
        re.compile(r"(NEVER|NOT|Don't|wrong|incorrect)", re.IGNORECASE),
    ),
    (
        "IPA_MANDATORY_EVERY",
        "error",
        "Mandatory IPA for every word — will cause IPA flooding",
        "*.md",
        re.compile(r"Mandatory\s+IPA\s+stress\s+for\s+EVERY", re.IGNORECASE),
        None,
    ),
    # Persona contamination
    (
        "HELPFUL_NEIGHBOR",
        "error",
        "References 'Helpful Neighbor' persona (should be 'Ukrainian Teacher')",
        "*.md",
        re.compile(r"Helpful\s+Neighbor", re.IGNORECASE),
        re.compile(r"(NEVER|NOT|Don't|do not|anti-pattern|friendly neighbour)", re.IGNORECASE),
    ),
    (
        "FRIENDLY_NEIGHBOUR_PERSONA",
        "error",
        "Uses 'friendly neighbour' as persona framing",
        "*.md",
        re.compile(r"friendly\s+neighbou?r", re.IGNORECASE),
        re.compile(r"(NEVER|NOT|Don't|do not)", re.IGNORECASE),
    ),
    # Persona leaking into research
    (
        "PERSONA_IN_RESEARCH",
        "error",
        "Research template references persona — persona should only come from skill at content time",
        "*research*.md",
        re.compile(r"persona|PERSONA_FLAVOR|voice.*instructor|voice.*teacher", re.IGNORECASE),
        re.compile(r"(Do NOT reference persona|forbid|never.*persona)", re.IGNORECASE),
    ),
    # Missing IPA prohibition for B1+
    (
        "MISSING_NO_IPA_B1PLUS",
        "warn",
        "Skill for B1+ track has no explicit 'no IPA' / 'no inline IPA' statement",
        "*/full-rebuild-core-b/SKILL.md",
        re.compile(r"^(?!.*[Nn]o\s+inline\s+IPA).*$", re.DOTALL),
        None,
    ),
    # Colleague/колего tone
    (
        "COLLEAGUE_TONE",
        "warn",
        "Addresses learner as 'колего' (colleague) — should use teacher-student framing",
        "*.md",
        re.compile(r"колего!|Вітаю.*колег[иі]!", re.IGNORECASE),
        None,
    ),
    # IPA Mandate without level gating
    (
        "IPA_MANDATE_UNGATED",
        "error",
        "IPA Mandate without 'no inline' qualifier — will cause IPA in B1+ prose",
        "*/full-rebuild-*/SKILL.md",
        re.compile(r"IPA\s+Mandate.*MUST\s+use\s+IPA", re.IGNORECASE),
        re.compile(r"no\s+inline|vocabulary\s+YAML|only\s+in", re.IGNORECASE),
    ),
    # Hardcoded activity counts (not level-specific)
    (
        "HARDCODED_ACTIVITY_COUNT",
        "warn",
        "Hardcoded activity count without level differentiation",
        "*/full-rebuild-core-b/SKILL.md",
        re.compile(r"^\s*-\s+\d+\+\s+activities?,\s+\d+\+\s+items", re.IGNORECASE | re.MULTILINE),
        re.compile(r"level|B1|B2|C1|C2|vary", re.IGNORECASE),
    ),
]


def check_file_level_rule(filepath: Path) -> list[dict]:
    """Check rules that apply to the whole file (like MISSING_NO_IPA_B1PLUS)."""
    violations = []
    content = filepath.read_text(encoding="utf-8")

    # Check: B1+ skills must have "no inline IPA" or "No inline IPA" somewhere
    if "full-rebuild-core-b" in str(filepath) or any(
        track in str(filepath)
        for track in ["b2-hist", "c1-bio", "c1-hist", "oes", "ruth", "lit"]
    ):
        if not re.search(r"[Nn]o\s+inline\s+IPA", content):
            violations.append({
                "rule": "MISSING_NO_IPA",
                "severity": "warn",
                "file": str(filepath.relative_to(PROJECT_ROOT)),
                "line": 0,
                "message": "B1+ skill missing explicit 'No inline IPA' statement",
            })

    return violations


def check_line_rules(filepath: Path) -> list[dict]:
    """Check per-line rules against a file."""
    violations = []
    content = filepath.read_text(encoding="utf-8")
    lines = content.splitlines()

    for rule_id, severity, description, file_glob, pattern, exception in RULES:
        # Skip file-level rules (handled separately)
        if rule_id == "MISSING_NO_IPA_B1PLUS":
            continue

        # Check file glob match
        if file_glob != "*.md":
            from fnmatch import fnmatch
            if not fnmatch(str(filepath), f"*{file_glob.lstrip('*')}"):
                continue

        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                # Check exception (anti-pattern guard)
                if exception and exception.search(line):
                    continue
                violations.append({
                    "rule": rule_id,
                    "severity": severity,
                    "file": str(filepath.relative_to(PROJECT_ROOT)),
                    "line": i,
                    "message": description,
                    "content": line.strip()[:120],
                })

    return violations


def scan_all() -> list[dict]:
    """Scan all prompt files for violations."""
    all_violations = []

    for scan_dir in SCAN_DIRS:
        if not scan_dir.exists():
            continue
        for filepath in sorted(scan_dir.rglob("*.md")):
            all_violations.extend(check_line_rules(filepath))
            all_violations.extend(check_file_level_rule(filepath))

    return all_violations


def main():
    violations = scan_all()

    if not violations:
        print("✅ All prompts clean — no violations found.")
        return 0

    errors = [v for v in violations if v["severity"] == "error"]
    warns = [v for v in violations if v["severity"] == "warn"]

    if errors:
        print(f"❌ {len(errors)} ERROR(s) found (blocks deploy):\n")
        for v in errors:
            print(f"  {v['rule']}: {v['file']}:{v['line']}")
            print(f"    {v['message']}")
            if v.get("content"):
                print(f"    > {v['content']}")
            print()

    if warns:
        print(f"⚠️  {len(warns)} WARNING(s):\n")
        for v in warns:
            print(f"  {v['rule']}: {v['file']}:{v['line']}")
            print(f"    {v['message']}")
            if v.get("content"):
                print(f"    > {v['content']}")
            print()

    print(f"Summary: {len(errors)} errors, {len(warns)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
