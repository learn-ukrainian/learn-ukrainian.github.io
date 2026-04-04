"""Curriculum gap analysis against the Ukrainian State Standard 2024.

Compares curriculum module lists against the State Standard requirements
for a given level. Reports theme coverage, grammar wall runs, module
composition, cross-level boundaries, and per-requirement coverage status.

Usage:
    .venv/bin/python scripts/curriculum_gap_analysis.py b2
    .venv/bin/python scripts/curriculum_gap_analysis.py --all
    .venv/bin/python scripts/curriculum_gap_analysis.py b2 --output report.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SS_PATH = ROOT / "docs" / "l2-uk-en" / "state-standard-2024-mapping.yaml"
CURRICULUM_PATH = ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"

# Ukrainian theme → English slug keywords
THEME_SLUG_MAP: dict[str, list[str]] = {
    "людина": ["people", "relationships", "family", "person"],
    "дім": ["housing", "home", "renting", "house"],
    "здоров'я": ["health", "doctor", "zdorovya", "medytsyna"],
    "робота": ["work", "career", "professional", "job"],
    "купівля": ["shopping", "services", "spozhyvannya"],
    "подорожі": ["travel", "ukraine", "podoroz", "traveling"],
    "освіта": ["education", "university", "osvita", "nauka"],
    "дозвілля": ["leisure", "culture", "festival", "free-time", "dozvillya"],
    "природа": ["nature", "environment", "ekolohiya", "klimat"],
    "ресторан": ["restaurant", "food", "cafe", "kharchuvannya"],
    "послуги": ["services", "posluhy"],
    "місця": ["places", "location", "city", "misto", "selo", "prostir"],
    "суспільні відносини": ["society", "media", "debate", "suspilstvo", "hromadyanstvo"],
    "традиції": ["holiday", "festival", "tradition", "identychnist", "tradytsiyi"],
    "щоденне життя": ["daily", "routines", "morning"],
    "побут": ["daily", "routines", "morning", "pobut"],
    "культурне дозвілля": ["leisure", "culture", "kultura", "mystetstvo", "dozvillya"],
    "спорт": ["sport", "liudskyi-potentsial"],
    "середовище": ["environment", "nature"],
    "навчання": ["education", "learning"],
    "їжа": ["food", "drink", "eat", "cafe"],
    "харчування": ["food", "kharchuvannya", "restaurant"],
    "економіка": ["economics", "ekonomika", "business", "dobrobut"],
    "медіа": ["media", "news", "dezinformatsiya", "journalistic"],
    "внутрішня політика": ["political", "politics", "government", "hromadyanstvo"],
    "зовнішня політика": ["diaspora", "zovnishnia", "polityka", "global"],
    "наука і техніка": ["science", "technology", "tekhnolohii", "doslidzhennia", "innovatsiyi"],
}

# Keywords that mark grammar/structural modules (not topic modules)
GRAMMAR_KEYWORDS: set[str] = {
    "checkpoint", "baseline", "bridge", "alternation", "conjugation",
    "declension", "participle", "gerund", "conditional", "imperative",
    "passive", "reflexive", "aspect", "case", "genitive", "dative",
    "instrumental", "accusative", "locative", "vocative", "nominative",
    "plural", "numeral", "pronoun", "adjective", "adverb", "verb",
    "prefix", "suffix", "formation", "comparison", "syntax", "sentence",
    "subordinate", "compound", "asyndetic", "conjunction", "motion",
    "simplification", "noun", "register", "stylistic", "morphology",
    "phonetic", "stress", "euphony", "word-formation", "review",
    "practice", "exam", "finale", "comprehensive", "predicate",
    "detached", "emphasis", "inversion", "ellipsis", "parcelling",
    "connectors", "parenthetical", "homogeneous", "reported", "speech",
    "correlative", "pluperfect", "punctuation", "irregular", "hedging",
    "modality", "citation", "thesis", "counterargument", "abstract",
    "summary", "paraphrase", "essay",
}

# Grammar description → slug keywords for matching SS requirements to modules
GRAMMAR_SLUG_KEYWORDS: dict[str, list[str]] = {
    "noun": ["noun", "declension"],
    "adjective": ["adjective", "possessive-adjective"],
    "numeral": ["numeral"],
    "pronoun": ["pronoun"],
    "nominative": ["nominative"],
    "genitive": ["genitive"],
    "dative": ["dative"],
    "accusative": ["accusative"],
    "instrumental": ["instrumental"],
    "locative": ["locative"],
    "vocative": ["vocative"],
    "indicative": ["verb", "aspect", "conjugation", "tense"],
    "imperative": ["imperative"],
    "conditional": ["conditional"],
    "participle": ["participle"],
    "gerund": ["gerund"],
    "passive": ["passive"],
    "comparison": ["comparison", "comparative", "superlative"],
    "aspect": ["aspect"],
    "motion": ["motion"],
    "agent noun": ["word-formation", "person-suffix"],
    "deverbal": ["verbal-noun", "word-formation"],
    "place noun": ["word-formation", "place"],
    "denominal": ["word-formation", "adjective-formation"],
    "deadjectival": ["word-formation", "adverb"],
    "declarative": ["sentence", "syntax"],
    "interrogative": ["question", "syntax"],
    "complex sentence": ["complex", "subordinate", "compound", "syntax"],
    "complex simple": ["detached", "homogeneous", "participial", "parenthetical"],
    "one-member": ["one-member", "impersonal"],
    "direct": ["direct", "indirect", "speech", "reported"],
    "asyndetic": ["asyndetic"],
    "euphony": ["euphony", "milozvuchnist"],
    "stress": ["stress"],
    "abbreviation": ["compression", "abbreviation"],
    "register": ["register", "formal", "informal"],
    "synonym": ["synonym", "synonymy"],
    "metaphor": ["metaphor", "simile", "stylistic-device"],
    "anaphora": ["anaphora", "parallelism", "syntactic-stylistic"],
    "alliteration": ["phonetic-stylistic", "fonetychni"],
    "style": ["styl", "style", "register"],
    "rhetoric": ["rhetoric", "persuasive"],
    "intonation": ["intonation", "melody"],
}

VALID_LEVELS = ("a1", "a2", "b1", "b2", "c1", "c2")
LEVEL_ORDER = {lvl: i for i, lvl in enumerate(VALID_LEVELS)}


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def get_modules(curriculum: dict, level: str) -> list[str]:
    levels = curriculum.get("levels", {})
    lvl_data = levels.get(level, {})
    return lvl_data.get("modules", [])


def get_ss(ss_data: dict, level: str) -> dict:
    return ss_data.get(level, {})


def is_grammar_module(slug: str) -> bool:
    parts = set(slug.replace("-", " ").split())
    return bool(parts & GRAMMAR_KEYWORDS)


def is_checkpoint(slug: str) -> bool:
    return "checkpoint" in slug or "finale" in slug or "exam" in slug


def find_consecutive_runs(modules: list[str], min_length: int = 4) -> list[tuple[int, int, list[str]]]:
    """Find runs of consecutive grammar modules."""
    runs: list[tuple[int, int, list[str]]] = []
    start = None
    current_run: list[str] = []

    for i, slug in enumerate(modules):
        if is_grammar_module(slug):
            if start is None:
                start = i
                current_run = [slug]
            else:
                current_run.append(slug)
        else:
            if start is not None and len(current_run) >= min_length:
                runs.append((start + 1, start + len(current_run), current_run))
            start = None
            current_run = []

    # trailing run
    if start is not None and len(current_run) >= min_length:
        runs.append((start + 1, start + len(current_run), current_run))

    return runs


def match_theme(topic: str, modules: list[str]) -> list[str]:
    """Find modules whose slug matches a theme keyword."""
    keywords = THEME_SLUG_MAP.get(topic, [])
    # Also try transliterated fragments of the topic itself
    topic_lower = topic.lower()
    matched = []
    for slug in modules:
        slug_lower = slug.lower()
        # Direct keyword match
        for kw in keywords:
            if kw in slug_lower:
                matched.append(slug)
                break
        else:
            # Fallback: check if topic fragment appears in slug
            for frag in topic_lower.split():
                if len(frag) > 3 and frag in slug_lower:
                    matched.append(slug)
                    break
    return matched


def match_ss_requirement(desc: str, _ref: str, modules: list[str]) -> tuple[list[str], str]:
    """Try to match a State Standard requirement to curriculum modules.

    Returns (matched_modules, status) where status is COVERED/LIKELY/MISSING.
    """
    desc_lower = desc.lower()
    matched = []

    # Try grammar keyword matching
    for keyword, slug_keywords in GRAMMAR_SLUG_KEYWORDS.items():
        if keyword in desc_lower:
            for slug in modules:
                slug_lower = slug.lower()
                for sk in slug_keywords:
                    if sk in slug_lower and slug not in matched:
                        matched.append(slug)

    # Also try words from the description directly against slugs
    desc_words = set(desc_lower.replace("—", " ").replace(",", " ").split())
    # Filter short/common words
    desc_words = {w for w in desc_words if len(w) > 4}
    for slug in modules:
        slug_parts = set(slug.lower().replace("-", " ").split())
        if desc_words & slug_parts and slug not in matched:
            matched.append(slug)

    status = ("COVERED" if len(matched) >= 2 else "LIKELY") if matched else "MISSING"

    return matched[:5], status  # cap display at 5


def collect_ss_requirements(ss_level: dict) -> list[dict]:
    """Flatten all SS requirements into a list of dicts."""
    reqs = []
    skip_keys = {"level_lines", "immersion", "themes", "vocabulary_targets"}
    for category, items in ss_level.items():
        if category in skip_keys:
            continue
        if not isinstance(items, dict):
            continue
        for sub_key, sub_val in items.items():
            if not isinstance(sub_val, dict) or "description" not in sub_val:
                continue
            reqs.append({
                "category": category,
                "key": sub_key,
                "reference": sub_val.get("reference", ""),
                "description": sub_val["description"],
                "lines": sub_val.get("lines", []),
            })
    return reqs


def previous_level(level: str) -> str | None:
    idx = LEVEL_ORDER.get(level, 0)
    if idx == 0:
        return None
    return VALID_LEVELS[idx - 1]


def generate_report(level: str, ss_data: dict, curriculum: dict) -> str:
    modules = get_modules(curriculum, level)
    ss_level = get_ss(ss_data, level)

    if not modules:
        return f"# {level.upper()} Gap Analysis\n\nNo modules found for level {level}.\n"
    if not ss_level:
        return f"# {level.upper()} Gap Analysis\n\nNo State Standard data found for level {level}.\n"

    lines: list[str] = []
    lines.append(f"# {level.upper()} Gap Analysis — State Standard 2024\n")

    # --- Module Summary ---
    total = len(modules)
    checkpoints = sum(1 for m in modules if is_checkpoint(m))
    grammar = sum(1 for m in modules if is_grammar_module(m))
    topic = total - grammar

    lines.append("## Module Summary\n")
    lines.append(f"- **Total modules:** {total}")
    lines.append(f"- **Checkpoints/exams:** {checkpoints}")
    lines.append(f"- **Grammar/structural modules:** {grammar}")
    lines.append(f"- **Topic/thematic modules:** {topic}")
    lines.append("")

    # Consecutive runs
    runs = find_consecutive_runs(modules, min_length=4)
    if runs:
        lines.append("### Consecutive Grammar Runs (4+ modules)\n")
        for start, end, slugs in runs:
            lines.append(
                f"- **Run of {len(slugs)}:** M{start:02d}–M{end:02d} "
                f"({slugs[0]} through {slugs[-1]})"
            )
        lines.append("")
    else:
        lines.append("### Consecutive Grammar Runs\n")
        lines.append("No grammar runs of 4+ consecutive modules found.\n")

    # --- State Standard Coverage ---
    reqs = collect_ss_requirements(ss_level)
    lines.append("## State Standard Coverage\n")
    lines.append("| SS Ref | Category | Description | Module(s) | Status |")
    lines.append("|--------|----------|-------------|-----------|--------|")

    stats = {"COVERED": 0, "LIKELY": 0, "MISSING": 0}
    for req in reqs:
        matched, status = match_ss_requirement(req["description"], req["reference"], modules)
        stats[status] += 1
        mod_str = ", ".join(matched) if matched else "—"
        # Truncate long descriptions
        desc = req["description"]
        if len(desc) > 80:
            desc = desc[:77] + "..."
        lines.append(
            f"| {req['reference']} | {req['category']} | {desc} | {mod_str} | {status} |"
        )

    lines.append("")
    lines.append(
        f"**Summary:** {stats['COVERED']} COVERED, {stats['LIKELY']} LIKELY, "
        f"{stats['MISSING']} MISSING out of {len(reqs)} requirements\n"
    )

    # --- Theme Coverage ---
    themes = ss_level.get("themes", {})
    topics = themes.get("topics", [])
    if topics:
        lines.append("## Theme Coverage\n")
        lines.append("| Theme | Module(s) | Status |")
        lines.append("|-------|-----------|--------|")

        theme_stats = {"COVERED": 0, "MISSING": 0}
        for topic in topics:
            matched = match_theme(topic, modules)
            status = "COVERED" if matched else "MISSING"
            theme_stats[status] += 1
            mod_str = ", ".join(matched[:3]) if matched else "—"
            if len(matched) > 3:
                mod_str += f" (+{len(matched) - 3} more)"
            lines.append(f"| {topic} | {mod_str} | {status} |")

        lines.append("")
        lines.append(
            f"**Summary:** {theme_stats['COVERED']} covered, "
            f"{theme_stats['MISSING']} missing out of {len(topics)} themes\n"
        )

    # --- Cross-Level Boundaries ---
    prev = previous_level(level)
    if prev:
        prev_ss = get_ss(ss_data, prev)
        if prev_ss:
            lines.append("## Cross-Level Boundaries\n")
            lines.append("| Category | Previous Level | This Level | Delta |")
            lines.append("|----------|---------------|------------|-------|")

            all_categories = set()
            for d in (prev_ss, ss_level):
                for k, v in d.items():
                    if isinstance(v, dict) and k not in {"level_lines", "immersion", "themes"}:
                        all_categories.add(k)

            for cat in sorted(all_categories):
                prev_items = prev_ss.get(cat, {})
                curr_items = ss_level.get(cat, {})

                if not isinstance(prev_items, dict) or not isinstance(curr_items, dict):
                    continue

                prev_keys = {
                    k for k, v in prev_items.items()
                    if isinstance(v, dict) and "description" in v
                }
                curr_keys = {
                    k for k, v in curr_items.items()
                    if isinstance(v, dict) and "description" in v
                }

                new_keys = curr_keys - prev_keys
                continued = curr_keys & prev_keys

                prev_desc = f"{len(prev_keys)} items"
                curr_desc = f"{len(curr_keys)} items"

                if new_keys:
                    delta = f"+{len(new_keys)} new: {', '.join(sorted(new_keys)[:3])}"
                    if len(new_keys) > 3:
                        delta += f" (+{len(new_keys) - 3} more)"
                elif continued:
                    delta = f"All {len(continued)} expanded from {prev.upper()}"
                else:
                    delta = "New category"

                lines.append(f"| {cat} | {prev_desc} | {curr_desc} | {delta} |")

            lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze curriculum gaps against Ukrainian State Standard 2024"
    )
    parser.add_argument(
        "level",
        nargs="?",
        choices=VALID_LEVELS,
        help="Level to analyze (a1, a2, b1, b2, c1, c2)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Analyze all levels",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Write report to file instead of stdout",
    )
    args = parser.parse_args()

    if not args.level and not args.all:
        parser.error("Provide a level or use --all")

    ss_data = load_yaml(SS_PATH)
    curriculum = load_yaml(CURRICULUM_PATH)

    levels = list(VALID_LEVELS) if args.all else [args.level]
    reports = []
    for level in levels:
        reports.append(generate_report(level, ss_data, curriculum))

    output = "\n---\n\n".join(reports)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
