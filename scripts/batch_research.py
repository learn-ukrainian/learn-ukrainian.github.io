#!/usr/bin/env python3
"""Batch Phase 0 research: generate lightweight Core A research for all modules.

Usage:
    .venv/bin/python scripts/batch_research.py a1 --from 14 --to 44
    .venv/bin/python scripts/batch_research.py a1 --module 14
    .venv/bin/python scripts/batch_research.py a1 --from 14 --to 44 --dry-run
"""
import argparse
import json
import re
import subprocess
import sys
import multiprocessing
from pathlib import Path
from functools import partial

REPO = Path(__file__).parent.parent


def find_module_files(level: str, num: int) -> dict | None:
    """Find all files for a module by number."""
    level_dir = REPO / f"curriculum/l2-uk-en/{level}"
    content_files = sorted(level_dir.glob(f"{num:02d}-*.md"))
    if not content_files:
        return None

    content_path = content_files[0]
    slug = content_path.stem[3:]
    full_stem = content_path.stem

    meta_path = level_dir / f"meta/{full_stem}.yaml"
    if not meta_path.exists():
        meta_path = level_dir / f"meta/{slug}.yaml"
    research_path = level_dir / f"research/{slug}-research.md"

    return {
        "num": num,
        "slug": slug,
        "content": content_path,
        "meta": meta_path,
        "research": research_path,
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


def build_prior_knowledge(level: str, num: int) -> str:
    """Build a summary of what grammar/cases students know at this module number."""
    knowledge = []

    if level == "a1":
        if num >= 3:
            knowledge.append("Gender recognition (masculine/feminine/neuter)")
        if num >= 4:
            knowledge.append("Це (this is), я є (I am), basic sentences")
        if num >= 6:
            knowledge.append("Present tense conjugation (Group 1)")
        if num >= 7:
            knowledge.append("Questions (хто, що, де, куди) and negation (не)")
        if num >= 8:
            knowledge.append("Present tense conjugation (Group 2)")
        if num >= 9:
            knowledge.append("Reflexive verbs (-ся)")
        if num >= 11:
            knowledge.append("Accusative case (inanimate)")
        if num >= 12:
            knowledge.append("Accusative case (animate)")
        if num >= 13:
            knowledge.append("Locative case (в/на + location)")
        if num >= 14:
            knowledge.append("Possessive pronouns (мій/твій/наш/ваш/його/її)")
        if num >= 16:
            knowledge.append("Genitive case (absence, possession)")
        if num >= 17:
            knowledge.append("Numbers and counting")
        if num >= 21:
            knowledge.append("Past tense")
        if num >= 22:
            knowledge.append("Future tense")
        if num >= 24:
            knowledge.append("Modal verbs (можу, мушу, хочу)")
        if num >= 26:
            knowledge.append("Adjectives (agreement)")
        if num >= 30:
            knowledge.append("Prepositions (expanded)")
        if num >= 34:
            knowledge.append("All core A1 grammar (checkpoint passed)")

    elif level == "a2":
        # A2 students have ALL of A1
        knowledge.append("ALL A1 grammar: Nominative, Accusative, Locative, Genitive cases")
        knowledge.append("Present/Past/Future tenses, reflexive verbs, modals, adjectives")
        knowledge.append("Possessive pronouns, prepositions, numbers, basic communication")
        # A2 progression
        if num >= 2:
            knowledge.append("Dative case (pronouns)")
        if num >= 3:
            knowledge.append("Dative case (nouns)")
        if num >= 4:
            knowledge.append("Dative verbs (подобатися, допомагати, etc.)")
        if num >= 5:
            knowledge.append("Instrumental case (з + accompaniment)")
        if num >= 6:
            knowledge.append("Instrumental case (means/tools)")
        if num >= 7:
            knowledge.append("Бути/ставати (being and becoming)")
        if num >= 8:
            knowledge.append("Spatial prepositions (expanded)")
        if num >= 9:
            knowledge.append("Logical prepositions")
        if num >= 11:
            knowledge.append("All cases practice (checkpoint passed)")
        if num >= 13:
            knowledge.append("Verbal aspect introduction (imperfective/perfective)")
        if num >= 14:
            knowledge.append("Completed past (perfective past tense)")
        if num >= 15:
            knowledge.append("Future plans (perfective future)")
        if num >= 16:
            knowledge.append("Aspect morphology (prefix/suffix patterns)")
        if num >= 17:
            knowledge.append("Aspect mastery (common pairs)")
        if num >= 18:
            knowledge.append("Свій (reflexive possessive)")
        if num >= 19:
            knowledge.append("Comparative adjectives (більший, кращий)")
        if num >= 20:
            knowledge.append("Superlative adjectives (найкращий)")
        if num >= 22:
            knowledge.append("Numerals with noun agreement")
        if num >= 23:
            knowledge.append("Conditional (якби + past tense)")
        if num >= 24:
            knowledge.append("Imperative mood (full paradigm)")
        if num >= 25:
            knowledge.append("Aspect + comparison checkpoint passed")
        if num >= 27:
            knowledge.append("Narrative past tense usage")
        if num >= 28:
            knowledge.append("Causal/concessive conjunctions (бо, хоча)")
        if num >= 29:
            knowledge.append("Reported speech (що-clauses)")
        if num >= 32:
            knowledge.append("Purpose clauses (щоб + infinitive)")
        if num >= 33:
            knowledge.append("Relative clauses (який/яка/яке)")
        if num >= 34:
            knowledge.append("Time clauses (коли, після того як)")
        if num >= 35:
            knowledge.append("Complex sentences checkpoint passed")
        if num >= 37:
            knowledge.append("Basic motion verb prefixes")
        if num >= 38:
            knowledge.append("Advanced motion verb prefixes")
        if num >= 39:
            knowledge.append("Action verb prefixes")
        if num >= 44:
            knowledge.append("Word formation mastery (suffixes, roots)")
        if num >= 56:
            knowledge.append("Full A2 grammar checkpoint passed")

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

    return prompt


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
    msg = f"{prompt}"

    try:
        result = subprocess.run(
            [
                sys.executable, str(REPO / "scripts/ai_agent_bridge.py"),
                "ask-gemini", msg,
                "--task-id", task_id,
                "--output-path", output_path,
                "--model", model,
            ],
            capture_output=True, text=True, timeout=600,
            cwd=str(REPO),
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
    parser.add_argument("--jobs", "-j", type=int, default=1,
                        help="Number of parallel jobs (default: 1, recommendation: 4-8)")
    args = parser.parse_args()

    if args.module:
        modules = [args.module]
    else:
        to_num = args.to_num or 99
        modules = list(range(args.from_num, to_num + 1))

    print(f"{'='*60}")
    print(f"Batch Research: {args.level.upper()} M{modules[0]:02d}-M{modules[-1]:02d}")
    print(f"Model: {args.model}")
    if args.jobs > 1:
        print(f"Parallel Jobs: {args.jobs}")
    print(f"{'='*60}\n")

    results = []
    if args.jobs > 1 and len(modules) > 1:
        print(f"Running parallel research with {args.jobs} jobs...")
        with multiprocessing.Pool(processes=args.jobs) as pool:
            worker_func = partial(research_module, args.level, model=args.model, dry_run=args.dry_run)
            results = pool.map(worker_func, modules)

        for result in results:
            num = result["num"]
            print(f"--- M{num:02d} ---")
            if result["status"] == "EXISTS":
                print(f"  EXISTS ({result['size']} bytes)")
            elif result["status"] == "OK":
                print(f"  OK ({result['size']} bytes) → {result.get('output', '')}")
            elif result["status"] == "SKIP":
                print(f"  SKIP: {result.get('reason', '')}")
            else:
                print(f"  {result['status']}: {result.get('reason', '')}")
    else:
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
