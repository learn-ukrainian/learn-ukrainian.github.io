#!/usr/bin/env python3
"""Generate A2 plan YAML files from the A2 curriculum design doc.

Parses the markdown tables in docs/l2-uk-en/A2-CURRICULUM-V3.md and generates
plan YAML files at curriculum/l2-uk-en/plans/a2/{slug}.yaml.

Usage:
    .venv/bin/python scripts/generate_a2_plans.py --dry-run          # preview 3 samples
    .venv/bin/python scripts/generate_a2_plans.py --dry-run --all    # preview all
    .venv/bin/python scripts/generate_a2_plans.py                    # write all files
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DESIGN_DOC = PROJECT_ROOT / "docs" / "l2-uk-en" / "A2-CURRICULUM-V3.md"
PLANS_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans" / "a2"
CURRICULUM_YAML = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"

# Read from config.py at runtime
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from audit.config import LEVEL_CONFIG

WORD_TARGET_REGULAR = LEVEL_CONFIG["A2"]["target_words"]  # 2000
WORD_TARGET_CHECKPOINT = LEVEL_CONFIG["A2-checkpoint"]["target_words"]  # 1500

# Activity hints by focus type
ACTIVITY_HINTS = {
    "grammar": [
        {"type": "quiz", "focus": "Test understanding of key grammar concepts from this module", "items": 6},
        {"type": "fill-in", "focus": "Complete sentences using the grammar patterns taught", "items": 6},
        {"type": "match-up", "focus": "Match forms to their functions or translations", "items": 6},
    ],
    "communication": [
        {"type": "quiz", "focus": "Comprehension questions about practical situations", "items": 6},
        {"type": "fill-in", "focus": "Complete dialogues in practical contexts", "items": 6},
        {"type": "group-sort", "focus": "Categorize expressions by situation or function", "items": 8},
    ],
    "review": [
        {"type": "quiz", "focus": "Self-check questions covering reviewed modules", "items": 8},
        {"type": "true-false", "focus": "Verify understanding of key grammar rules", "items": 6},
        {"type": "match-up", "focus": "Match grammar concepts to examples", "items": 6},
    ],
    "bridge": [
        {"type": "quiz", "focus": "Identify Ukrainian metalanguage terms for grammar concepts", "items": 6},
        {"type": "match-up", "focus": "Match Ukrainian grammar terms to their meanings", "items": 8},
        {"type": "fill-in", "focus": "Complete grammar explanations using Ukrainian terminology", "items": 6},
    ],
}

# Phase titles from the design doc
PHASE_TITLES = {
    "A2.1": "Foundation and Aspect Introduction",
    "A2.2": "Genitive Case Complete",
    "A2.3": "Dative Case",
    "A2.4": "Instrumental Case",
    "A2.5": "Case Synthesis and Plurals",
    "A2.6": "Aspect, Tenses, and Motion",
    "A2.7": "Complex Sentences and Conditionals",
    "A2.8": "Refinement and Graduation",
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ModuleRow:
    """A parsed row from the design doc markdown table."""

    seq: int
    slug: str
    title: str
    focus: str  # grammar, communication, review, bridge
    core_content: str
    phase: str  # e.g. "A2.1"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_design_doc(path: Path) -> list[ModuleRow]:
    """Parse the A2 design doc markdown and extract module rows."""
    text = path.read_text(encoding="utf-8")
    modules: list[ModuleRow] = []
    current_phase = ""

    # Match phase headers like "### A2.1: Foundation and Aspect Introduction (7 modules)"
    phase_re = re.compile(r"^### (A2\.\d+):")
    # Match table rows: | 01 | slug | Title | focus | Core Content |
    row_re = re.compile(
        r"^\|\s*(\d+)\s*\|"  # sequence number
        r"\s*([a-z0-9-]+)\s*\|"  # slug
        r"\s*(.+?)\s*\|"  # title
        r"\s*(\w+)\s*\|"  # focus
        r"\s*(.+?)\s*\|$"  # core content
    )

    for line in text.splitlines():
        phase_match = phase_re.match(line)
        if phase_match:
            current_phase = phase_match.group(1)
            continue

        row_match = row_re.match(line)
        if row_match:
            seq = int(row_match.group(1))
            slug = row_match.group(2).strip()
            title = row_match.group(3).strip()
            focus = row_match.group(4).strip()
            core_content = row_match.group(5).strip()
            modules.append(
                ModuleRow(
                    seq=seq,
                    slug=slug,
                    title=title,
                    focus=focus,
                    core_content=core_content,
                    phase=current_phase,
                )
            )

    return modules


def load_curriculum_slugs() -> list[str]:
    """Load A2 slug list from curriculum.yaml for validation."""
    with open(CURRICULUM_YAML, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["levels"]["a2"]["modules"]


# ---------------------------------------------------------------------------
# Content outline generation
# ---------------------------------------------------------------------------


def extract_ukrainian_words(text: str) -> list[str]:
    """Extract Ukrainian words (Cyrillic) from core content text.

    Returns words that look like vocabulary items — filters out grammar
    labels and very short items.
    """
    # Find Cyrillic words, including those with apostrophes
    cyrillic_re = re.compile(r"[А-ЯІЇЄҐа-яіїєґ''][а-яіїєґ'']+")
    raw = cyrillic_re.findall(text)

    # Filter: skip very common grammar labels and short words
    skip = {
        "або", "та", "це", "не", "як", "що",
        "він", "вона", "воно", "вони",
        "де", "до", "за", "на", "по", "із", "зі",
    }
    seen: set[str] = set()
    result: list[str] = []
    for w in raw:
        lower = w.lower()
        if len(w) >= 3 and lower not in skip and lower not in seen:
            seen.add(lower)
            result.append(w)
    return result


def split_content_to_points(core_content: str) -> list[str]:
    """Split core content into section points.

    Splits on sentence boundaries, semicolons, and bold markers.
    Groups related content together.
    """
    parts: list[str] = []
    clean = core_content

    # Split on semicolons first (explicit separators in the design doc)
    segments = re.split(r";\s*", clean)

    for seg in segments:
        seg = seg.strip()
        if seg:
            # If a segment has multiple sentences, keep as one point
            parts.append(seg)

    return parts if parts else [core_content]


def generate_content_outline(module: ModuleRow) -> list[dict]:
    """Generate content_outline sections from module data."""
    points = split_content_to_points(module.core_content)
    word_target = (
        WORD_TARGET_CHECKPOINT
        if module.focus == "review" and "checkpoint" in module.slug
        else WORD_TARGET_REGULAR
    )

    if module.focus == "review" and "checkpoint" in module.slug:
        return _outline_checkpoint(module, points, word_target)
    if module.focus == "bridge":
        return _outline_bridge(module, points, word_target)
    if module.focus == "communication":
        return _outline_communication(module, points, word_target)
    return _outline_grammar(module, points, word_target)


def _distribute_words(total: int, n_sections: int) -> list[int]:
    """Distribute word target across sections roughly evenly."""
    base = total // n_sections
    remainder = total % n_sections
    result = [base] * n_sections
    for i in range(remainder):
        result[i] += 1
    return result


def _outline_grammar(module: ModuleRow, points: list[str], word_target: int) -> list[dict]:
    """Grammar module: intro + core grammar sections + practice + summary."""
    # Distribute points across grammar sections
    n_grammar_sections = max(1, len(points))

    sections = []
    # Words: ~15% intro, ~55% grammar, ~20% practice, ~10% summary
    intro_words = int(word_target * 0.15)
    grammar_words = int(word_target * 0.55)
    practice_words = int(word_target * 0.20)
    summary_words = word_target - intro_words - grammar_words - practice_words

    sections.append({
        "section": "Вступ (Introduction)",
        "words": intro_words,
        "points": [
            f"Context and motivation: why this topic matters at A2. Connect to prior knowledge from {module.phase}.",
        ],
    })

    grammar_per_section = _distribute_words(grammar_words, n_grammar_sections)
    for i, (point, words) in enumerate(zip(points, grammar_per_section, strict=False)):
        section_title = f"Граматика {i + 1} (Grammar {i + 1})" if n_grammar_sections > 1 else "Граматика (Grammar)"
        sections.append({
            "section": section_title,
            "words": words,
            "points": [point],
        })

    sections.append({
        "section": "Практика (Practice)",
        "words": practice_words,
        "points": [
            "Reading Practice: 8-10 Ukrainian sentences using the grammar taught in this module.",
            "Mini-dialogues applying the grammar in real situations.",
        ],
    })

    sections.append({
        "section": "Підсумок (Summary)",
        "words": summary_words,
        "points": [
            "Key patterns summary. Self-check questions.",
        ],
    })

    return sections


def _outline_communication(module: ModuleRow, points: list[str], word_target: int) -> list[dict]:
    """Communication module: situation + dialogues + vocabulary + practice."""
    sections = []
    # ~15% intro, ~35% situation, ~30% dialogues, ~20% practice
    intro_words = int(word_target * 0.15)
    situation_words = int(word_target * 0.35)
    dialogue_words = int(word_target * 0.30)
    practice_words = word_target - intro_words - situation_words - dialogue_words

    sections.append({
        "section": "Вступ (Introduction)",
        "words": intro_words,
        "points": [
            f"Setting the scene: practical context for {module.title}.",
        ],
    })

    sections.append({
        "section": "Ситуація (Situation)",
        "words": situation_words,
        "points": points,
    })

    sections.append({
        "section": "Діалоги (Dialogues)",
        "words": dialogue_words,
        "points": [
            "4-6 practical dialogues applying grammar from this phase in real situations.",
            "Each dialogue 6-8 turns, using vocabulary from this and previous modules.",
        ],
    })

    sections.append({
        "section": "Практика (Practice)",
        "words": practice_words,
        "points": [
            "Reading Practice: connected Ukrainian text using all patterns from this phase.",
            "Self-check: can you handle these situations in Ukrainian?",
        ],
    })

    return sections


def _outline_checkpoint(module: ModuleRow, points: list[str], word_target: int) -> list[dict]:
    """Checkpoint module: review + reading + grammar summary + practice."""
    sections = []
    # ~15% self-check, ~25% reading, ~25% grammar summary, ~20% practice, ~15% next steps
    words_list = _distribute_words(word_target, 5)

    sections.append({
        "section": "Що ми знаємо? (What Do We Know?)",
        "words": words_list[0],
        "points": [points[0] if points else f"Self-check covering modules in {module.phase}."],
    })

    sections.append({
        "section": "Читання (Reading Practice)",
        "words": words_list[1],
        "points": [
            "A short Ukrainian text (10-12 sentences) using ONLY vocabulary from reviewed modules. No new words.",
        ],
    })

    sections.append({
        "section": "Граматика (Grammar Summary)",
        "words": words_list[2],
        "points": [
            f"Key grammar patterns from {module.phase}. Tables and examples for quick reference.",
        ],
    })

    sections.append({
        "section": "Практика (Practice)",
        "words": words_list[3],
        "points": [
            "Extended practice combining all grammar from this phase.",
        ],
    })

    sections.append({
        "section": "Далі (What's Next)",
        "words": words_list[4],
        "points": [
            "Preview of the next phase. What new grammar will build on what we learned.",
        ],
    })

    return sections


def _outline_bridge(module: ModuleRow, points: list[str], word_target: int) -> list[dict]:
    """Bridge (metalanguage) module: concept mapping + Ukrainian terms + practice."""
    sections = []
    # ~15% intro, ~40% terms, ~25% practice with terms, ~20% dictionary skills
    intro_words = int(word_target * 0.15)
    terms_words = int(word_target * 0.40)
    practice_words = int(word_target * 0.25)
    dict_words = word_target - intro_words - terms_words - practice_words

    sections.append({
        "section": "Вступ (Introduction)",
        "words": intro_words,
        "points": [
            "Why Ukrainian grammar terms matter: B1 uses 100% Ukrainian instruction.",
        ],
    })

    sections.append({
        "section": "Терміни (Terms)",
        "words": terms_words,
        "points": points,
    })

    sections.append({
        "section": "Практика (Practice)",
        "words": practice_words,
        "points": [
            "Exercises using Ukrainian metalanguage: identify parts of speech, name cases, describe verb forms.",
        ],
    })

    sections.append({
        "section": "Словник (Dictionary Skills)",
        "words": dict_words,
        "points": [
            "How to read dictionary entries using Ukrainian abbreviations and terms.",
        ],
    })

    return sections


# ---------------------------------------------------------------------------
# Vocabulary hints
# ---------------------------------------------------------------------------


def generate_vocabulary_hints(module: ModuleRow) -> dict:
    """Generate vocabulary_hints from Ukrainian words in core content."""
    words = extract_ukrainian_words(module.core_content)
    required = [f"{w} (<!-- VERIFY meaning -->)" for w in words[:12]]
    return {
        "required": required if required else ["<!-- TODO: extract vocabulary from content -->"],
        "recommended": [],
    }


# ---------------------------------------------------------------------------
# Plan generation
# ---------------------------------------------------------------------------


def generate_plan(module: ModuleRow, curriculum_slugs: list[str]) -> dict:
    """Generate a complete plan dict for a module."""
    # Determine module ID
    module_id = f"a2-{module.seq:03d}"

    # Determine word target
    is_checkpoint = module.focus == "review" and "checkpoint" in module.slug
    word_target = WORD_TARGET_CHECKPOINT if is_checkpoint else WORD_TARGET_REGULAR

    # Determine pedagogy
    if module.focus == "review":
        pedagogy = "review"
    elif module.focus == "bridge":
        pedagogy = "PPP"
    else:
        pedagogy = "PPP"

    # Phase with title
    phase_title = PHASE_TITLES.get(module.phase, "")
    phase_str = f"{module.phase} [{phase_title}]" if phase_title else module.phase

    # Objectives from core content
    objectives = _generate_objectives(module)

    # Content outline
    content_outline = generate_content_outline(module)

    # Vocabulary hints
    vocabulary_hints = generate_vocabulary_hints(module)

    # Activity hints
    focus_key = module.focus if module.focus in ACTIVITY_HINTS else "grammar"
    activity_hints = ACTIVITY_HINTS[focus_key]

    # Connects to next module
    next_seq = module.seq + 1
    connects_to = []
    if next_seq <= 60:
        # Find the next slug in curriculum order
        idx = module.seq - 1  # 0-based
        if idx + 1 < len(curriculum_slugs):
            connects_to.append(curriculum_slugs[idx + 1])

    # Prerequisites: previous module
    prerequisites = []
    if module.seq > 1:
        idx = module.seq - 2  # 0-based index of previous
        if 0 <= idx < len(curriculum_slugs):
            prerequisites.append(curriculum_slugs[idx])

    plan = {
        "module": module_id,
        "level": "A2",
        "sequence": module.seq,
        "slug": module.slug,
        "version": "1.0",
        "title": module.title,
        "subtitle": "<!-- TODO: add Ukrainian subtitle -->",
        "focus": module.focus,
        "pedagogy": pedagogy,
        "phase": phase_str,
        "word_target": word_target,
        "objectives": objectives,
        "content_outline": content_outline,
        "vocabulary_hints": vocabulary_hints,
        "activity_hints": activity_hints,
        "connects_to": connects_to,
        "prerequisites": prerequisites,
        "grammar": _extract_grammar_tags(module),
        "register": "розмовний",
        "references": [],
    }

    return plan


def _generate_objectives(module: ModuleRow) -> list[str]:
    """Generate 3-5 learning objectives from the module data."""
    objectives = []
    points = split_content_to_points(module.core_content)

    for point in points[:4]:
        # Clean up bold markers and shorten
        clean = re.sub(r"\*\*(.+?)\*\*", r"\1", point)
        # Truncate long points
        if len(clean) > 120:
            clean = clean[:117] + "..."
        objectives.append(f"Understand and apply: {clean}")

    if not objectives:
        objectives.append(f"Master the concepts in {module.title}")

    return objectives


def _extract_grammar_tags(module: ModuleRow) -> list[str]:
    """Extract grammar topic tags from core content."""
    tags = []
    content = module.core_content

    # Look for key grammar patterns
    grammar_patterns = [
        (r"[Гг]енітив|Gen\.|Род\.", "Genitive case"),
        (r"[Дд]атив|Dat\.|Дав\.", "Dative case"),
        (r"[Іі]нструментал|Instr\.|Ор\.", "Instrumental case"),
        (r"[Аа]спект|доконаний|недоконаний", "Verb aspect"),
        (r"[Іі]мператив|наказов", "Imperative mood"),
        (r"[Пп]орівняльн|[Кк]омпаратив|comparative", "Comparison"),
        (r"підрядн|складн|тому що|щоб|який", "Complex sentences"),
        (r"[Чч]ислівник|numeral", "Numerals"),
        (r"[Зз]айменник|pronoun", "Pronouns"),
        (r"[Пп]рийменник|preposition", "Prepositions"),
        (r"множин|plural", "Plural forms"),
        (r"рух|motion|іти/ходити", "Motion verbs"),
    ]

    for pattern, tag in grammar_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            tags.append(tag)

    if not tags:
        tags.append(module.title)

    return tags


# ---------------------------------------------------------------------------
# YAML output
# ---------------------------------------------------------------------------


class PlanDumper(yaml.Dumper):
    """Custom YAML dumper that produces clean, readable output."""
    pass


def str_representer(dumper: yaml.Dumper, data: str) -> yaml.Node:
    """Use literal block style for long strings, plain style for short ones."""
    if "\n" in data or len(data) > 100:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    if ":" in data or "#" in data or data.startswith("{") or data.startswith("["):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


PlanDumper.add_representer(str, str_representer)


def plan_to_yaml(plan: dict) -> str:
    """Convert a plan dict to YAML string with proper formatting."""
    return yaml.dump(
        plan,
        Dumper=PlanDumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate A2 plan YAML files from design doc")
    parser.add_argument("--dry-run", action="store_true", help="Preview plans without writing files")
    parser.add_argument("--all", action="store_true", help="In dry-run mode, show all plans (not just 3 samples)")
    parser.add_argument("--module", type=int, help="Generate only this module number")
    args = parser.parse_args()

    if not DESIGN_DOC.exists():
        print(f"ERROR: Design doc not found: {DESIGN_DOC}", file=sys.stderr)
        sys.exit(1)

    # Parse design doc
    modules = parse_design_doc(DESIGN_DOC)
    print(f"Parsed {len(modules)} modules from design doc")

    # Load curriculum.yaml for validation
    curriculum_slugs = load_curriculum_slugs()
    print(f"Found {len(curriculum_slugs)} A2 slugs in curriculum.yaml")

    # Validate: every parsed slug must be in curriculum.yaml
    parsed_slugs = {m.slug for m in modules}
    curriculum_set = set(curriculum_slugs)
    missing_from_curriculum = parsed_slugs - curriculum_set
    missing_from_design = curriculum_set - parsed_slugs

    if missing_from_curriculum:
        print(f"WARNING: Slugs in design doc but NOT in curriculum.yaml: {missing_from_curriculum}")
    if missing_from_design:
        print(f"WARNING: Slugs in curriculum.yaml but NOT in design doc: {missing_from_design}")

    # Filter if --module specified
    if args.module:
        modules = [m for m in modules if m.seq == args.module]
        if not modules:
            print(f"ERROR: Module {args.module} not found", file=sys.stderr)
            sys.exit(1)

    # Generate plans
    plans: list[tuple[ModuleRow, dict]] = []
    for module in modules:
        plan = generate_plan(module, curriculum_slugs)
        plans.append((module, plan))

    if args.dry_run:
        # Show sample plans
        show_count = len(plans) if args.all else min(3, len(plans))
        # Pick samples: first, a middle grammar module, a checkpoint
        samples = (
            [plans[0], plans[3], plans[6]]
            if not args.all and len(plans) > 3
            else plans[:show_count]
        )

        for module, plan in samples:
            print(f"\n{'=' * 80}")
            print(f"  M{module.seq:02d} | {module.slug} | {module.focus} | {module.phase}")
            print(f"  Would write to: {PLANS_DIR / f'{module.slug}.yaml'}")
            print(f"{'=' * 80}")
            print(plan_to_yaml(plan))

        print(f"\n--- DRY RUN: {len(plans)} plans would be written to {PLANS_DIR}/")
        print("    Run without --dry-run to write files.")
    else:
        # Write files
        PLANS_DIR.mkdir(parents=True, exist_ok=True)
        written = 0
        for module, plan in plans:
            path = PLANS_DIR / f"{module.slug}.yaml"
            path.write_text(plan_to_yaml(plan), encoding="utf-8")
            written += 1
            print(f"  Wrote {path.name}")

        print(f"\nWrote {written} plan files to {PLANS_DIR}/")


if __name__ == "__main__":
    main()
