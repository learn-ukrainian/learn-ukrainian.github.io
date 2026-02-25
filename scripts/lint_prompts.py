#!/usr/bin/env python3
"""
Prompt linter — catches known anti-patterns in Gemini skill/phase files
and (optionally) curriculum research files.

Runs automatically during `npm run claude:deploy` (add to package.json).
Can also be run standalone:
  .venv/bin/python scripts/lint_prompts.py               # Prompts only (deploy gate)
  .venv/bin/python scripts/lint_prompts.py --curriculum   # Also check research files
  .venv/bin/python scripts/lint_prompts.py --fix          # Auto-strip persona lines from research

Exit code 0 = clean, 1 = violations found.
"""

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories to scan for prompt/skill files (deploy gate)
PROMPT_SCAN_DIRS = [
    PROJECT_ROOT / "gemini_extensions" / "skills",
    PROJECT_ROOT / "claude_extensions" / "phases",
]

# Directories to scan for curriculum research files (--curriculum mode)
CURRICULUM_RESEARCH_DIRS = [
    PROJECT_ROOT / "curriculum" / "l2-uk-en",
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

# ---------- CURRICULUM RESEARCH RULES ----------
# These apply to curriculum/l2-uk-en/*/research/*-research.md files.
# Persona references in research files are contamination — persona is defined
# by the skill at content generation time, not baked into research.

# Known persona names across all skills (used for detection + auto-fix)
KNOWN_PERSONA_NAMES = [
    "Ukrainian Teacher",
    "Cultural Guide",
    "Encouraging Cultural Guide",
    "Helpful Neighbor",
    "Friendly Neighbour",
    "Storyteller",
    "Village Storyteller",
    "Government Spokesperson",
    "Investigative Journalist",
    "Olympic Trainer",
    "Fitness Trainer",
    "School Principal",
    "Gossip Columnist",
    "Theater Box Office Manager",
    "Metro Navigator",
    "Real Estate Agent",
    "Bessarabka Market Vendor",
    "Taxi Driver",
    # NOTE: "Safe Harbor" deliberately excluded — it's a pedagogical concept, not a persona
]

# Build a combined pattern from known persona names
_persona_names_pattern = "|".join(
    re.escape(name) for name in KNOWN_PERSONA_NAMES
)

RESEARCH_RULES = [
    (
        "RESEARCH_PERSONA_NAME",
        "warn",
        "Research file references a specific persona name — persona is defined by the skill, not research",
        re.compile(rf"({_persona_names_pattern})", re.IGNORECASE),
        # Exceptions: anti-pattern guards, or cultural facts where the name appears
        # incidentally (e.g., "real estate agents", "Village Storyteller (Казкар)")
        re.compile(r"(Do NOT reference persona|NEVER.*persona|forbid|Казкар|agents?\b|tradition)", re.IGNORECASE),
    ),
    (
        "RESEARCH_PERSONA_KEYWORD",
        "warn",
        "Research file uses 'persona' keyword — persona guidance belongs in skills only",
        re.compile(r"\bpersona\b", re.IGNORECASE),
        re.compile(r"(Do NOT reference persona|NEVER.*persona|forbid)", re.IGNORECASE),
    ),
    (
        "RESEARCH_PERSONA_FLAVOR",
        "warn",
        "Research file references PERSONA_FLAVOR — this is a skill-level variable",
        re.compile(r"PERSONA_FLAVOR", re.IGNORECASE),
        None,
    ),
]


def check_file_level_rule(filepath: Path) -> list[dict]:
    """Check rules that apply to the whole file (like MISSING_NO_IPA_B1PLUS)."""
    violations = []
    content = filepath.read_text(encoding="utf-8")

    # Check: B1+ skills must have "no inline IPA" or "No inline IPA" somewhere
    # Skip calibration files — they're not skill/phase prompts
    if "/calibration/" in str(filepath):
        return violations
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


def scan_prompts() -> list[dict]:
    """Scan prompt/skill files for violations (deploy gate)."""
    all_violations = []

    for scan_dir in PROMPT_SCAN_DIRS:
        if not scan_dir.exists():
            continue
        for filepath in sorted(scan_dir.rglob("*.md")):
            all_violations.extend(check_line_rules(filepath))
            all_violations.extend(check_file_level_rule(filepath))

    return all_violations


def scan_curriculum_research() -> list[dict]:
    """Scan curriculum research files for persona contamination."""
    violations = []

    for base_dir in CURRICULUM_RESEARCH_DIRS:
        if not base_dir.exists():
            continue
        # Find all research directories
        for research_dir in sorted(base_dir.rglob("research")):
            if not research_dir.is_dir():
                continue
            for filepath in sorted(research_dir.glob("*-research.md")):
                content = filepath.read_text(encoding="utf-8")
                lines = content.splitlines()

                for rule_id, severity, description, pattern, exception in RESEARCH_RULES:
                    for i, line in enumerate(lines, 1):
                        if pattern.search(line):
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


def fix_research_persona(dry_run: bool = False) -> int:
    """Strip persona-contaminated lines from research files.

    Conservative: only removes lines that contain the word 'persona' or
    'PERSONA_FLAVOR'. Lines that merely mention a persona name without
    the keyword are flagged by --curriculum but NOT auto-stripped, since
    they may reference cultural concepts (e.g., 'Village Storyteller' as
    a cultural fact rather than a module persona directive).
    """
    fixed_count = 0
    # Conservative: require "persona" or "PERSONA_FLAVOR" keyword on the line
    persona_pattern = re.compile(
        r"\b(?:persona|PERSONA_FLAVOR)\b",
        re.IGNORECASE,
    )
    exception_pattern = re.compile(
        r"(Do NOT reference persona|NEVER.*persona|forbid)", re.IGNORECASE
    )

    for base_dir in CURRICULUM_RESEARCH_DIRS:
        if not base_dir.exists():
            continue
        for research_dir in sorted(base_dir.rglob("research")):
            if not research_dir.is_dir():
                continue
            for filepath in sorted(research_dir.glob("*-research.md")):
                content = filepath.read_text(encoding="utf-8")
                lines = content.splitlines()
                new_lines = []
                removed = []

                for i, line in enumerate(lines, 1):
                    if persona_pattern.search(line) and not exception_pattern.search(line):
                        removed.append((i, line.strip()[:100]))
                    else:
                        new_lines.append(line)

                if removed:
                    rel_path = filepath.relative_to(PROJECT_ROOT)
                    if dry_run:
                        print(f"  Would fix: {rel_path} ({len(removed)} lines)")
                        for line_num, content in removed:
                            print(f"    L{line_num}: {content}")
                    else:
                        filepath.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                        print(f"  Fixed: {rel_path} ({len(removed)} persona lines removed)")
                    fixed_count += 1

    return fixed_count


def print_violations(violations: list[dict], header: str) -> None:
    """Print violations grouped by severity."""
    errors = [v for v in violations if v["severity"] == "error"]
    warns = [v for v in violations if v["severity"] == "warn"]

    if errors:
        print(f"\n❌ {len(errors)} ERROR(s) {header}:\n")
        for v in errors:
            print(f"  {v['rule']}: {v['file']}:{v['line']}")
            print(f"    {v['message']}")
            if v.get("content"):
                print(f"    > {v['content']}")
            print()

    if warns:
        print(f"\n⚠️  {len(warns)} WARNING(s) {header}:\n")
        # Group by file for readability
        by_file: dict[str, list[dict]] = {}
        for v in warns:
            by_file.setdefault(v["file"], []).append(v)

        for filepath, file_violations in by_file.items():
            print(f"  {filepath}:")
            for v in file_violations:
                rule_short = v["rule"].replace("RESEARCH_", "")
                print(f"    L{v['line']}: [{rule_short}] {v.get('content', v.get('message', ''))[:80]}")
            print()


def main():
    parser = argparse.ArgumentParser(description="Prompt & curriculum linter")
    parser.add_argument(
        "--curriculum", action="store_true",
        help="Also scan curriculum research files for persona contamination",
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Auto-strip persona lines from research files",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="With --fix: show what would be changed without modifying files",
    )
    args = parser.parse_args()

    # --- Fix mode ---
    if args.fix:
        print("🔧 Fixing persona contamination in research files...\n")
        fixed = fix_research_persona(dry_run=args.dry_run)
        if fixed:
            action = "would fix" if args.dry_run else "fixed"
            print(f"\n{'🔍' if args.dry_run else '✅'} {action} {fixed} research file(s)")
        else:
            print("✅ No persona contamination found in research files.")
        return 0

    # --- Lint mode ---
    prompt_violations = scan_prompts()

    if not prompt_violations and not args.curriculum:
        print("✅ All prompts clean — no violations found.")
        return 0

    has_errors = False

    if prompt_violations:
        print_violations(prompt_violations, "(blocks deploy)")
        errors = [v for v in prompt_violations if v["severity"] == "error"]
        warns = [v for v in prompt_violations if v["severity"] == "warn"]
        print(f"Prompts: {len(errors)} errors, {len(warns)} warnings")
        if errors:
            has_errors = True

    if args.curriculum:
        research_violations = scan_curriculum_research()
        if research_violations:
            print_violations(research_violations, "in curriculum research")
            by_file = set(v["file"] for v in research_violations)
            print(f"Research: {len(research_violations)} violations in {len(by_file)} files")
            print("  Run with --fix to auto-strip persona lines")
        else:
            print("\n✅ Curriculum research files clean — no persona contamination.")

    if not prompt_violations and args.curriculum and not research_violations:
        print("\n✅ All clean — prompts and research.")

    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
