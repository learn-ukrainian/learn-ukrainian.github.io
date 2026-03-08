#!/usr/bin/env python3
"""Batch Phase 0 research: generate lightweight Core A research for all modules.

Usage:
    .venv/bin/python scripts/batch_research.py a1 --from 14 --to 44
    .venv/bin/python scripts/batch_research.py a1 --module 14
    .venv/bin/python scripts/batch_research.py a1 --from 14 --to 44 --dry-run
"""
import argparse
import subprocess
import sys
from pathlib import Path

from slug_utils import to_bare_slug

REPO = Path(__file__).parent.parent.parent


def find_module_files(level: str, num: int) -> dict | None:
    """Find all files for a module by number."""
    level_dir = REPO / f"curriculum/l2-uk-en/{level}"

    # Primary: resolve via manifest (slug-based)
    try:
        sys.path.insert(0, str(REPO / "scripts"))
        from manifest_utils import get_module_by_number
        mod = get_module_by_number(level, num)
        if mod:
            content_path = level_dir / f"{mod.slug}.md"
            if content_path.exists():
                slug = mod.slug
                return {
                    "num": num,
                    "slug": slug,
                    "content": content_path,
                    "meta": level_dir / f"meta/{slug}.yaml",
                    "research": level_dir / f"research/{slug}-research.md",
                }
    except Exception:
        pass

    # Fallback: glob for numbered prefix
    content_files = sorted(level_dir.glob(f"{num:02d}-*.md"))
    if not content_files:
        return None

    content_path = content_files[0]
    slug = to_bare_slug(content_path.stem)

    return {
        "num": num,
        "slug": slug,
        "content": content_path,
        "meta": level_dir / f"meta/{slug}.yaml",
        "research": level_dir / f"research/{slug}-research.md",
    }


def get_module_info(files: dict) -> dict:
    """Extract title and topic from content/meta."""
    info = {"title": files["slug"].replace("-", " ").title(), "subtitle": "", "grammar": ""}

    # Get title from content H1
    if files["content"].exists():
        for line in files["content"].read_text().split('\n'):
            if line.startswith('# '):
                info["title"] = line[2:].strip()
                break

    # Get subtitle and grammar focus from meta
    if files["meta"].exists():
        meta_text = files["meta"].read_text()
        for line in meta_text.split('\n'):
            if line.startswith('subtitle:'):
                info["subtitle"] = line.split(':', 1)[1].strip().strip("'\"")
            if line.startswith('title:'):
                info["title"] = line.split(':', 1)[1].strip().strip("'\"")

    return info


# Grammar milestones per level: list of (min_module_num, description)
_A1_MILESTONES: list[tuple[int, str]] = [
    (3, "Gender recognition (masculine/feminine/neuter)"),
    (4, "Це (this is), я є (I am), basic sentences"),
    (6, "Present tense conjugation (Group 1)"),
    (7, "Questions (хто, що, де, куди) and negation (не)"),
    (8, "Present tense conjugation (Group 2)"),
    (9, "Reflexive verbs (-ся)"),
    (11, "Accusative case (inanimate)"),
    (12, "Accusative case (animate)"),
    (13, "Locative case (в/на + location)"),
    (14, "Possessive pronouns (мій/твій/наш/ваш/його/її)"),
    (16, "Genitive case (absence, possession)"),
    (17, "Numbers and counting"),
    (21, "Past tense"),
    (22, "Future tense"),
    (24, "Modal verbs (можу, мушу, хочу)"),
    (26, "Adjectives (agreement)"),
    (30, "Prepositions (expanded)"),
    (34, "All core A1 grammar (checkpoint passed)"),
]

_A2_BASE_KNOWLEDGE: list[str] = [
    "ALL A1 grammar: Nominative, Accusative, Locative, Genitive cases",
    "Present/Past/Future tenses, reflexive verbs, modals, adjectives",
    "Possessive pronouns, prepositions, numbers, basic communication",
]

_A2_MILESTONES: list[tuple[int, str]] = [
    (2, "Dative case (pronouns)"),
    (3, "Dative case (nouns)"),
    (4, "Dative verbs (подобатися, допомагати, etc.)"),
    (5, "Instrumental case (з + accompaniment)"),
    (6, "Instrumental case (means/tools)"),
    (7, "Бути/ставати (being and becoming)"),
    (8, "Spatial prepositions (expanded)"),
    (9, "Logical prepositions"),
    (11, "All cases practice (checkpoint passed)"),
    (13, "Verbal aspect introduction (imperfective/perfective)"),
    (14, "Completed past (perfective past tense)"),
    (15, "Future plans (perfective future)"),
    (16, "Aspect morphology (prefix/suffix patterns)"),
    (17, "Aspect mastery (common pairs)"),
    (18, "Свій (reflexive possessive)"),
    (19, "Comparative adjectives (більший, кращий)"),
    (20, "Superlative adjectives (найкращий)"),
    (22, "Numerals with noun agreement"),
    (23, "Conditional (якби + past tense)"),
    (24, "Imperative mood (full paradigm)"),
    (25, "Aspect + comparison checkpoint passed"),
    (27, "Narrative past tense usage"),
    (28, "Causal/concessive conjunctions (бо, хоча)"),
    (29, "Reported speech (що-clauses)"),
    (32, "Purpose clauses (щоб + infinitive)"),
    (33, "Relative clauses (який/яка/яке)"),
    (34, "Time clauses (коли, після того як)"),
    (35, "Complex sentences checkpoint passed"),
    (37, "Basic motion verb prefixes"),
    (38, "Advanced motion verb prefixes"),
    (39, "Action verb prefixes"),
    (44, "Word formation mastery (suffixes, roots)"),
    (56, "Full A2 grammar checkpoint passed"),
]


def _collect_milestones(milestones: list[tuple[int, str]], num: int) -> list[str]:
    """Return all milestone descriptions where num >= milestone threshold."""
    return [desc for threshold, desc in milestones if num >= threshold]


def build_prior_knowledge(level: str, num: int) -> str:
    """Build a summary of what grammar/cases students know at this module number."""
    knowledge: list[str] = []

    if level == "a1":
        knowledge = _collect_milestones(_A1_MILESTONES, num)
    elif level == "a2":
        knowledge = list(_A2_BASE_KNOWLEDGE)
        knowledge.extend(_collect_milestones(_A2_MILESTONES, num))

    return "\n".join(f"- {k}" for k in knowledge) if knowledge else "- Basic alphabet and pronunciation only"


def build_research_prompt(files: dict, info: dict, level: str) -> str:
    """Build the research prompt for Gemini."""
    prior = build_prior_knowledge(level, files["num"])
    output_path = str(files["research"])

    return f"""You are doing lightweight Core A research for a Ukrainian language learning module.

MODULE: {level.upper()} M{files['num']:02d} "{info['title']}"
SUBTITLE: {info['subtitle']}
LEVEL: A1 (beginner)

STUDENT'S PRIOR KNOWLEDGE AT THIS POINT:
{prior}

YOUR TASK: Write a research document covering:

1. **Grammar: State Standard 2024 reference** — Find the relevant §section in Державний стандарт української мови (ДСТУ 2024) for the grammar/topic taught in this module. Quote the specific section.

2. **Vocabulary frequency** — Key vocabulary items for this topic. Common collocations at A1 level. Note which words are high-frequency vs. lower.

3. **Cultural hook** — 1-2 verified facts about how this topic relates to Ukrainian culture or daily life. NOT from memory — use real cultural references.

4. **Pedagogical notes** — Key differences from English. Common learner errors. Teaching sequence recommendations.

5. **Scope boundaries** — Based on prior knowledge listed above, what grammar/vocabulary is IN scope and what is OUT of scope. Be specific about which cases, tenses, or structures students do NOT know yet.

IMPORTANT CONSTRAINTS:
- This is A1 (absolute beginner). Keep it simple.
- Only reference grammar the student already knows (see prior knowledge above).
- Do NOT use cases/tenses the student hasn't learned yet in examples.
- Write in English (this is a research document, not student-facing content).

Write your COMPLETE output to: {output_path}

Use markdown format with clear headers for each section."""


def research_module(level: str, num: int, model: str, dry_run: bool = False) -> dict:
    """Run research for a single module."""
    files = find_module_files(level, num)
    if not files:
        return {"num": num, "status": "SKIP", "reason": "no content file"}

    # Skip if research already exists
    if files["research"].exists() and files["research"].stat().st_size > 500:
        return {"num": num, "slug": files["slug"], "status": "EXISTS",
                "size": files["research"].stat().st_size}

    info = get_module_info(files)
    prompt = build_research_prompt(files, info, level)
    output_path = str(files["research"])

    if dry_run:
        return {"num": num, "slug": files["slug"], "status": "DRY_RUN", "title": info["title"]}

    # Ensure research directory exists
    files["research"].parent.mkdir(parents=True, exist_ok=True)

    task_id = f"batch-research-{level}-{num:02d}"

    try:
        result = subprocess.run(
            [
                sys.executable, str(REPO / "scripts/ai_agent_bridge/__main__.py"),
                "ask-gemini", "-",
                "--task-id", task_id,
                "--output-path", output_path,
                "--model", model,
            ],
            capture_output=True, text=True, input=prompt,
            timeout=600, cwd=str(REPO),
        )

        if result.returncode != 0:
            return {"num": num, "slug": files["slug"], "status": "ERROR", "reason": result.stderr[:200]}

        if Path(output_path).exists():
            size = Path(output_path).stat().st_size
            return {"num": num, "slug": files["slug"], "status": "OK", "size": size, "output": output_path}
        else:
            return {"num": num, "slug": files["slug"], "status": "ERROR", "reason": "no output file"}

    except subprocess.TimeoutExpired:
        return {"num": num, "slug": files["slug"], "status": "TIMEOUT"}
    except Exception as e:
        return {"num": num, "slug": files["slug"], "status": "ERROR", "reason": str(e)[:200]}


def main():
    parser = argparse.ArgumentParser(description="Batch research for a level")
    parser.add_argument("level", help="Level (e.g., a1)")
    parser.add_argument("--from", dest="from_num", type=int, default=1)
    parser.add_argument("--to", dest="to_num", type=int, default=None)
    parser.add_argument("--module", type=int)
    parser.add_argument("--model", default="gemini-3-flash-preview")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.module:
        modules = [args.module]
    else:
        to_num = args.to_num or 99
        modules = list(range(args.from_num, to_num + 1))

    print(f"{'='*60}")
    print(f"Batch Research: {args.level.upper()} M{modules[0]:02d}-M{modules[-1]:02d}")
    print(f"Model: {args.model}")
    print(f"{'='*60}\n")

    results = []
    for num in modules:
        print(f"--- M{num:02d} ---")
        result = research_module(args.level, num, args.model, args.dry_run)
        results.append(result)

        if result["status"] == "EXISTS":
            print(f"  EXISTS ({result['size']} bytes)")
        elif result["status"] == "OK":
            print(f"  OK ({result['size']} bytes) → {result.get('output', '')}")
        elif result["status"] == "SKIP":
            print(f"  SKIP: {result.get('reason', '')}")
        elif result["status"] == "DRY_RUN":
            print(f"  DRY_RUN: {result.get('title', '')}")
        else:
            print(f"  {result['status']}: {result.get('reason', '')}")

    # Summary
    print(f"\n{'='*60}")
    ok = sum(1 for r in results if r["status"] == "OK")
    exists = sum(1 for r in results if r["status"] == "EXISTS")
    fail = sum(1 for r in results if r["status"] in ("ERROR", "TIMEOUT"))
    skip = sum(1 for r in results if r["status"] == "SKIP")
    print(f"Done: {ok} new, {exists} existing, {fail} failed, {skip} skipped")


if __name__ == "__main__":
    main()
