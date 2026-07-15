#!/usr/bin/env python3
"""
Prompt linter — catches known anti-patterns in Gemini skill/phase files
and (optionally) curriculum research files.

Runs automatically during `npm run agents:deploy` (add to package.json).
Can also be run standalone:
  .venv/bin/python scripts/lint_prompts.py               # Prompts only (deploy gate)
  .venv/bin/python scripts/lint_prompts.py --curriculum   # Also check research files
  .venv/bin/python scripts/lint_prompts.py --fix          # Auto-strip persona lines from research

Exit code 0 = clean, 1 = violations found.
"""

import argparse
import importlib.util
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Directories to scan for prompt/skill files (deploy gate)
PROMPT_SCAN_DIRS = [
    PROJECT_ROOT / "gemini_extensions" / "skills",
    PROJECT_ROOT / "agents_extensions/shared" / "phases",
]

ORCHESTRATOR_PROMPT_ROOT = PROJECT_ROOT / "docs" / "prompts" / "orchestrators"
CURRICULUM_MANIFEST = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
LEGACY_PROMPT_MIGRATION = (
    PROJECT_ROOT
    / "agents_extensions/shared/curriculum-lifecycle/config/legacy-prompt-migration.v1.yaml"
)

# Directories to scan for curriculum research files (--curriculum mode)
CURRICULUM_RESEARCH_DIRS = [
    PROJECT_ROOT / "curriculum" / "l2-uk-en",
]

LEGACY_NON_SUITE_PROMPT_TRACKS = {"a1", "a2", "b1", "b2", "folk"}
SEMINAR_SUITE_TRACKS = {
    "hist",
    "bio",
    "lit",
    "lit-drama",
    "lit-essay",
    "lit-fantastika",
    "lit-hist-fic",
    "lit-humor",
    "lit-war",
    "lit-youth",
    "istorio",
    "oes",
    "ruth",
}

SUITE_REQUIRED_MARKERS = [
    "Prompt version:",
    "## Source Assumptions",
    "## Goal",
    "## WORKTREE_ROOT Setup",
    "## Read First",
    "## Allowed Writes",
    "## Forbidden Writes",
    "## Helpers",
    "## Validation Commands",
    "## Expected Final Response",
]

SUITE_SHARED_REFERENCES = [
    "docs/prompts/orchestrators/shared/repo-rules.md",
    "docs/prompts/orchestrators/shared/validation-checklist.md",
    "docs/prompts/orchestrators/shared/telemetry-and-pr.md",
    "docs/prompts/orchestrators/shared/review-output-schema.md",
]

SEMINAR_SHARED_REFERENCES = [
    "docs/prompts/orchestrators/shared/seminar-source-rules.md",
    "docs/prompts/orchestrators/shared/reading-section-rules.md",
]

WORKTREE_SANITY_MARKERS = [
    ".worktrees/dispatch/codex/",
    "pwd",
    "git status --short --branch",
    "git rev-parse --show-toplevel",
]

FORBIDDEN_WRITE_MARKERS = [
    "docs/prompts/orchestrators/b2/**",
    ".python-version",
    ".yamllint",
    ".markdownlint.json",
    "status/",
    "audit/",
    "review/",
    "data/telemetry/**",
]

# ---------- RULES ----------
# Each rule: (id, severity, description, file_glob, pattern, exception_pattern)
# severity: "error" = blocks deploy, "warn" = advisory
# exception_pattern: if this also matches the same line, it's a false positive (anti-pattern guards)

RULES = [
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
    # Colleague/колего tone
    (
        "COLLEAGUE_TONE",
        "warn",
        "Addresses learner as 'колего' (colleague) — should use teacher-student framing",
        "*.md",
        re.compile(r"колего!|Вітаю.*колег[иі]!", re.IGNORECASE),
        None,
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
    """Check rules that apply to the whole file."""
    violations = []
    # No file-level rules currently active
    return violations


def check_line_rules(filepath: Path) -> list[dict]:
    """Check per-line rules against a file."""
    violations = []
    content = filepath.read_text(encoding="utf-8")
    lines = content.splitlines()

    for rule_id, severity, description, file_glob, pattern, exception in RULES:
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

    all_violations.extend(scan_orchestrator_suites())
    all_violations.extend(scan_seminar_prompt_suite_refs())
    return all_violations


def make_violation(
    rule: str,
    message: str,
    filepath: Path,
    *,
    severity: str = "error",
    line: int = 1,
    content: str = "",
) -> dict:
    """Return a linter violation in the existing prompt-lint shape."""
    try:
        rel_file = str(filepath.relative_to(PROJECT_ROOT))
    except ValueError:
        rel_file = str(filepath)
    return {
        "rule": rule,
        "severity": severity,
        "file": rel_file,
        "line": line,
        "message": message,
        "content": content[:120],
    }


def scan_seminar_prompt_suite_refs() -> list[dict]:
    """Run the retired seminar template guard through prompt lint."""
    validator_path = PROJECT_ROOT / "scripts" / "validate" / "seminar_prompt_suite_refs.py"
    if not validator_path.is_file():
        return []

    spec = importlib.util.spec_from_file_location(
        "_seminar_prompt_suite_refs",
        validator_path,
    )
    if spec is None or spec.loader is None:
        return [
            make_violation(
                "SEMINAR_PROMPT_SUITE_REFS",
                "Unable to load seminar prompt-suite reference validator",
                validator_path,
            )
        ]

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return [
        make_violation(
            "SEMINAR_PROMPT_SUITE_REFS",
            error,
            validator_path,
            content=error,
        )
        for error in module.validate()
    ]


def line_number_for(text: str, needle: str) -> int:
    """Return the 1-based line number for a substring, or 1 if absent."""
    index = text.find(needle)
    if index == -1:
        return 1
    return text[:index].count("\n") + 1


def extract_section(text: str, heading: str) -> str:
    """Extract a markdown H2 section body."""
    start = text.find(heading)
    if start == -1:
        return ""
    next_heading = text.find("\n## ", start + len(heading))
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def extract_curriculum_level_keys(manifest_path: Path = CURRICULUM_MANIFEST) -> set[str]:
    """Extract active level/track keys from curriculum.yaml without PyYAML."""
    return set(extract_curriculum_level_types(manifest_path))


def extract_curriculum_level_types(manifest_path: Path = CURRICULUM_MANIFEST) -> dict[str, str]:
    """Extract active level/track types from curriculum.yaml without PyYAML."""
    if not manifest_path.exists():
        return {}

    level_types: dict[str, str] = {}
    current_level: str | None = None
    in_levels = False
    for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
        if raw_line.strip() == "levels:":
            in_levels = True
            continue
        if not in_levels:
            continue
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" "):
            break
        level_match = re.match(r"^  ([a-z0-9][a-z0-9-]*):\s*$", raw_line)
        if level_match:
            current_level = level_match.group(1)
            level_types.setdefault(current_level, "")
            continue
        type_match = re.match(r"^    type:\s*([a-z0-9_-]+)\s*(?:#.*)?$", raw_line)
        if current_level and type_match:
            level_types[current_level] = type_match.group(1)
    return level_types


def require_markers(
    text: str,
    filepath: Path,
    markers: list[str],
    rule: str,
    message_prefix: str,
    *,
    line_anchor: str | None = None,
) -> list[dict]:
    """Return violations for missing text markers."""
    line = line_number_for(text, line_anchor) if line_anchor else 1
    return [
        make_violation(
            rule,
            f"{message_prefix}: {marker}",
            filepath,
            line=line,
        )
        for marker in markers
        if marker not in text
    ]


def check_suite_final_response(
    filepath: Path,
    text: str,
    track: str,
    seminar_tracks: set[str],
) -> list[dict]:
    """Validate the Expected Final Response contract."""
    final_section = extract_section(text, "## Expected Final Response")
    violations = require_markers(
        final_section,
        filepath,
        [
            "Files changed: <paths>",
            "Validation run: <commands and outcomes>",
            "Telemetry: <posted | not module-build | unavailable with reason>",
            "Independent review: <status>",
            "Forbidden artifacts included: no",
            "swarm_used: true/false",
            "swarm_label: <none | helper | swarm>",
            "swarm_note: <helpers used, or solo run; no swarm used>",
        ],
        "ORCH_SUITE_FINAL_RESPONSE",
        "Expected Final Response missing field",
        line_anchor="## Expected Final Response",
    )
    reading_field = "Reading coverage: <hosted/link-only/excerpt-only/omit/needed counts>"
    if track in seminar_tracks and reading_field not in final_section:
        violations.append(make_violation(
            "ORCH_SUITE_READING_COVERAGE",
            f"Seminar suite final response missing field: {reading_field}",
            filepath,
            line=line_number_for(text, "## Expected Final Response"),
        ))
    return violations


def check_suite_seminar_references(
    filepath: Path,
    text: str,
    track: str,
    seminar_tracks: set[str],
) -> list[dict]:
    """Validate seminar-only shared references."""
    if track not in seminar_tracks:
        return []
    return require_markers(
        text,
        filepath,
        SEMINAR_SHARED_REFERENCES,
        "ORCH_SUITE_SEMINAR_REFERENCE",
        "Seminar suite missing shared reference",
    )


def check_orchestrator_suite_file(
    filepath: Path,
    seminar_tracks: set[str] | None = None,
) -> list[dict]:
    """Validate one suite-orchestrator prompt contract."""
    violations: list[dict] = []
    text = filepath.read_text(encoding="utf-8")
    track = filepath.parent.name
    seminar_tracks = seminar_tracks or SEMINAR_SUITE_TRACKS

    violations.extend(require_markers(
        text,
        filepath,
        SUITE_REQUIRED_MARKERS,
        "ORCH_SUITE_REQUIRED_SECTION",
        "Missing required suite marker",
    ))
    violations.extend(require_markers(
        text,
        filepath,
        SUITE_SHARED_REFERENCES,
        "ORCH_SUITE_SHARED_REFERENCE",
        "Missing shared prompt reference",
    ))

    worktree_section = extract_section(text, "## WORKTREE_ROOT Setup")
    violations.extend(require_markers(
        worktree_section,
        filepath,
        WORKTREE_SANITY_MARKERS,
        "ORCH_SUITE_WORKTREE_SANITY",
        "WORKTREE_ROOT setup missing",
        line_anchor="## WORKTREE_ROOT Setup",
    ))

    forbidden_section = extract_section(text, "## Forbidden Writes")
    violations.extend(require_markers(
        forbidden_section,
        filepath,
        FORBIDDEN_WRITE_MARKERS,
        "ORCH_SUITE_FORBIDDEN_WRITE",
        "Forbidden Writes missing protected marker",
        line_anchor="## Forbidden Writes",
    ))
    violations.extend(check_suite_final_response(filepath, text, track, seminar_tracks))
    violations.extend(check_suite_seminar_references(filepath, text, track, seminar_tracks))
    return violations


def check_b2_prompt_contracts(root: Path) -> list[dict]:
    """Validate B2 legacy prompts still carry executable review/swarm gates."""
    marker_sets = {
        root / "b2" / "preflight-readiness-audit-orchestrator.md": [
            "## Helper Swarm Policy",
            "gpt-5.4-mini",
            "gpt-5.3-codex-spark",
            "Do not let helpers read secrets",
            "## Independent-Family Review Gate",
            "Claude Opus 4.8",
            "Gemini 3.1 Pro High",
            "unresolved findings are blockers",
            "## PR Body Requirements",
            "reviewer identity",
            "review scope",
            "final disposition",
        ],
        root / "b2" / "production-build-orchestrator.md": [
            "## Helper Swarm Policy",
            "gpt-5.4-mini",
            "gpt-5.3-codex-spark",
            "Do not let helpers read secrets",
            "## Independent-Family Review Gate",
            "Claude Opus 4.8",
            "Gemini 3.1 Pro High",
            "unresolved findings are blockers",
            "POST /api/telemetry/module-builds",
            "pr_number",
            "pr_url",
            "reviewer identity",
        ],
        root / "b2" / "quality-audit-orchestrator.md": [
            "## Helper Swarm Policy",
            "gpt-5.4-mini",
            "gpt-5.3-codex-spark",
            "Do not let helpers read secrets",
            "## Independent-Family Review Gate",
            "Claude Opus 4.8",
            "Gemini 3.1 Pro High",
            "unresolved findings are blockers",
            "## PR Body Requirements",
            "reviewer identity",
            "review scope",
            "final disposition",
        ],
    }

    violations: list[dict] = []
    for filepath, markers in marker_sets.items():
        if not filepath.exists():
            continue
        text = filepath.read_text(encoding="utf-8")
        violations.extend(require_markers(
            text,
            filepath,
            markers,
            "ORCH_B2_REVIEW_SWARM_CONTRACT",
            "B2 prompt missing executable review/swarm marker",
        ))
    return violations


def check_orchestrator_track_coverage(
    root: Path,
    manifest_path: Path,
    prompt_track_dirs: set[str],
    suite_tracks: set[str],
    *,
    legacy_frozen: bool = False,
) -> list[dict]:
    """Validate prompt dirs and suites against active curriculum tracks."""
    violations: list[dict] = []
    active_tracks = set(extract_curriculum_level_types(manifest_path))
    manifest_display = manifest_path if manifest_path.exists() else root

    for track in sorted(prompt_track_dirs - active_tracks):
        violations.append(make_violation(
            "ORCH_TRACK_NOT_ACTIVE",
            f"Prompt directory has no active curriculum.yaml level: {track}",
            root / track,
        ))

    if not legacy_frozen:
        for track in sorted(active_tracks - prompt_track_dirs):
            violations.append(make_violation(
                "ORCH_ACTIVE_TRACK_MISSING_PROMPT",
                f"Active curriculum.yaml level has no orchestrator prompt dir: {track}",
                manifest_display,
            ))

        for track in sorted((active_tracks - LEGACY_NON_SUITE_PROMPT_TRACKS) - suite_tracks):
            violations.append(make_violation(
                "ORCH_ACTIVE_TRACK_MISSING_SUITE",
                f"Active non-legacy track has no suite-orchestrator.md: {track}",
                root / track,
            ))

    for stale_track in ["lit-crimea", "lit-doc"]:
        if stale_track in prompt_track_dirs:
            violations.append(make_violation(
                "ORCH_STALE_LIT_TRACK",
                f"Stale plan-only LIT track must not have prompt suite: {stale_track}",
                root / stale_track,
            ))
    return violations


def scan_orchestrator_suites(
    root: Path = ORCHESTRATOR_PROMPT_ROOT,
    manifest_path: Path = CURRICULUM_MANIFEST,
    migration_path: Path | None = None,
) -> list[dict]:
    """Validate orchestrator prompt suite coverage and contracts."""
    if not root.exists():
        return []

    if migration_path is None and root.resolve() == ORCHESTRATOR_PROMPT_ROOT.resolve():
        migration_path = LEGACY_PROMPT_MIGRATION
    legacy_frozen = migration_path is not None and migration_path.is_file()

    violations: list[dict] = []
    prompt_track_dirs = {
        path.name for path in root.iterdir()
        if path.is_dir() and path.name != "shared"
    }
    suite_tracks = {
        path.parent.name for path in root.glob("*/suite-orchestrator.md")
    }
    seminar_tracks = {
        track for track, track_type in extract_curriculum_level_types(manifest_path).items()
        if track_type == "seminar"
    }
    seminar_tracks |= SEMINAR_SUITE_TRACKS
    violations.extend(check_orchestrator_track_coverage(
        root,
        manifest_path,
        prompt_track_dirs,
        suite_tracks,
        legacy_frozen=legacy_frozen,
    ))

    for filepath in sorted(root.glob("*/suite-orchestrator.md")):
        violations.extend(check_orchestrator_suite_file(filepath, seminar_tracks=seminar_tracks))

    violations.extend(check_b2_prompt_contracts(root))
    return violations


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
