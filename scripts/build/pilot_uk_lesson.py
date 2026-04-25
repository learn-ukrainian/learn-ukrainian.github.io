"""Dry-run: Ukrainian-canonical lesson generation for one slug.

Minimal assembly script for the A.12 pilot. Not a production pipeline.
- Loads plan YAML for the given slug
- Retrieves top-K context from sources.db (ukrainian_wiki + textbooks)
- Fills v6-write-uk.md template placeholders
- Calls Gemini via one-shot CLI
- Saves assembled prompt + generated output for inspection
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
PHASES_DIR = REPO / "scripts" / "build" / "phases"
PLANS_DIR = REPO / "curriculum" / "l2-uk-en" / "plans"
OUT_DIR = REPO / "data" / "native-reviewer-lessons" / "pilot-output"


def load_plan(level: str, slug: str) -> dict:
    p = PLANS_DIR / level / f"{slug}.yaml"
    return yaml.safe_load(p.read_text("utf-8"))


def retrieval_context(plan: dict, level: str, limit: int = 12) -> str:
    """Build a simple retrieval context from plan → search_sources queries."""
    sys.path.insert(0, str(REPO / "scripts"))
    from wiki.sources_db import search_sources  # type: ignore

    # Build query from title + objectives + section names
    query_parts = [plan.get("title", ""), plan.get("subtitle", "")]
    query_parts.extend(plan.get("objectives", []))
    for sec in plan.get("content_outline", []):
        query_parts.append(sec.get("section", ""))
    # search_sources' _prepare_query does Path(query).exists() which raises
    # OSError on strings longer than the filesystem filename limit (~255 bytes).
    # Bug filed separately. Workaround: cap to 120 chars.
    query = " ".join(p.strip() for p in query_parts if p)
    query = " ".join(query.split())  # collapse whitespace
    query = query[:120]

    # Prefer the discovery YAML (that's what build_query_buckets actually parses)
    discovery_path = REPO / "curriculum" / "l2-uk-en" / level / "discovery" / f"{plan.get('slug')}.yaml"
    if discovery_path.exists():
        hits = search_sources(discovery_path, track=level, limit=limit)
    else:
        hits = search_sources(query, track=level, limit=limit)
    if not hits:
        return "(No retrieval results — proceeding with plan only.)"

    blocks = []
    for i, hit in enumerate(hits, 1):
        src = hit.get("source", hit.get("corpus", "?"))
        title = hit.get("title", hit.get("article", hit.get("unit_key", "?")))
        text = (hit.get("text") or hit.get("content") or "").strip()
        if not text:
            continue
        blocks.append(f"### [S{i}] {src} — {title}\n{text}\n")
    return "\n---\n".join(blocks) if blocks else "(No retrieval text content.)"


def assemble_prompt(plan: dict, level: str) -> str:
    tpl_path = PHASES_DIR / "v6-write-uk.md"
    template = tpl_path.read_text("utf-8")

    # Section titles — exactly as plan says
    sections = plan.get("content_outline", [])
    section_lines = []
    for s in sections:
        name = s.get("section", "")
        words = s.get("words", 0)
        section_lines.append(f"- `## {name}` (~{words} слів)")
    section_titles = "\n".join(section_lines)

    # Summary heading — last section in plan
    last_section = sections[-1].get("section", "Підсумок") if sections else "Підсумок"

    # Dialogue situations — render as bullet list
    dialogue_situations = plan.get("dialogue_situations", [])
    if dialogue_situations:
        ds_lines = []
        for ds in dialogue_situations:
            setting = ds.get("setting", "")
            speakers = ", ".join(ds.get("speakers", []))
            motivation = ds.get("motivation", "")
            ds_lines.append(f"- **Ситуація:** {setting}  **Мовці:** {speakers}  **Мотивація:** {motivation}")
        dialogue_sit_block = "**Допустимі діалогові ситуації для цього уроку:**\n\n" + "\n".join(ds_lines)
    else:
        dialogue_sit_block = ""

    # Retrieval context
    wiki_excerpts = retrieval_context(plan, level)

    # Contract YAML — just dump the plan for now
    contract_yaml = yaml.safe_dump(plan, allow_unicode=True, sort_keys=False)

    # Word ceiling = target * 1.5 per overshoot rule
    target = plan.get("word_target", 1200)
    ceiling = int(target * 1.5)

    # Use explicit replace() — .format() would misinterpret literal {foo} in
    # code examples inside the prompt. Each replacement targets exactly its
    # placeholder and nothing else.
    substitutions = {
        "{MODULE_NUM}": str(plan.get("module", f"{level}-001")),
        "{TOPIC_TITLE}": str(plan.get("title", "")),
        "{LEVEL}": str(plan.get("level", level.upper())),
        "{WORD_TARGET}": str(target),
        "{WORD_CEILING}": str(ceiling),
        "{CONTRACT_YAML}": contract_yaml,
        "{PRE_VERIFIED_FACTS}": "",
        "{SECTION_WIKI_EXCERPTS}": wiki_excerpts,
        "{GOLDEN_DIALOGUE_ANCHORS}": "",
        "{EXACT_SECTION_TITLES}": section_titles,
        "{SUMMARY_HEADING}": last_section,
        "{DIALOGUE_SITUATIONS}": dialogue_sit_block,
    }
    filled = template
    for key, val in substitutions.items():
        filled = filled.replace(key, val)
    return filled


def call_gemini(prompt: str, model: str = "gemini-3.1-pro-preview") -> str:
    """Call Gemini through the shared fallback ladder (#1384).

    The ladder honors ``GEMINI_AUTH_MODE`` and the sticky API cooldown,
    so a 429 on the API key automatically flips subsequent calls to
    the subscription/OAuth path for ~1h without user intervention.
    Using the shared ladder — instead of a bespoke ``subprocess.run`` —
    is what makes that auto-fallover reach this script.
    """
    # Local import keeps the ``--no-call`` path zero-cost.
    from ai_llm.fallback import call_gemini_with_fallback

    result = call_gemini_with_fallback(
        prompt,
        task_name=f"pilot_uk_lesson (model={model})",
        preferred_model=model,
        cwd=REPO,
        logger=lambda msg: print(msg, flush=True),
    )
    if not result.ok or not result.response_text:
        sys.stderr.write(
            f"Gemini ladder exhausted: {result.error_message or 'no response'}\n"
        )
        sys.exit(1)
    return result.response_text


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Generate ONE Ukrainian-canonical lesson for the A.12 pilot (EPIC #1365). "
            "Use this to test the v6-write-uk.md prompt on a single slug before batching. "
            "NOT a production pipeline — it skips audit, activities, review, and publish."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Assemble + call Gemini, save both prompt and output\n"
            "  .venv/bin/python scripts/build/pilot_uk_lesson.py a1 sounds-letters-and-hello\n\n"
            "  # Assemble only (cheap dry-run, no Gemini call, saves prompt for inspection)\n"
            "  .venv/bin/python scripts/build/pilot_uk_lesson.py a1 sounds-letters-and-hello --no-call\n\n"
            "  # A2 slug (word_target 2000 instead of 1200)\n"
            "  .venv/bin/python scripts/build/pilot_uk_lesson.py a2 aspect-concept\n\n"
            "Outputs (per run):\n"
            "  data/native-reviewer-lessons/pilot-output/<level>/<slug>.prompt.md  (assembled prompt)\n"
            "  data/native-reviewer-lessons/pilot-output/<level>/<slug>.md         (Gemini output)\n\n"
            "Exit codes: 0 on success, 1 on Gemini failure or plan not found.\n\n"
            "Related:\n"
            "  scripts/build/phases/v6-write-uk.md  — the prompt template this uses\n"
            "  scripts/build/v6_build.py            — full production pipeline (English)\n"
            "  EPIC #1365 step A.12                 — why this exists"
        ),
    )
    ap.add_argument(
        "level",
        choices=["a1", "a2"],
        help="CEFR level. Determines plan location (curriculum/l2-uk-en/plans/<level>/) "
             "and default word target (a1=1200, a2=2000).",
    )
    ap.add_argument(
        "slug",
        help='Module slug, e.g. "sounds-letters-and-hello". Must have a plan file at '
             'curriculum/l2-uk-en/plans/<level>/<slug>.yaml. Discovery file optional but '
             'improves retrieval.',
    )
    ap.add_argument(
        "--no-call",
        action="store_true",
        help="Assemble the prompt but do not call Gemini. Saves only the assembled "
             ".prompt.md file for inspection. Default: call Gemini and save both prompt "
             "and output.",
    )
    args = ap.parse_args()

    plan = load_plan(args.level, args.slug)
    print(f"Loaded plan: {plan.get('title', args.slug)}")
    print(f"  Level: {plan.get('level')}")
    print(f"  Word target: {plan.get('word_target')}")
    print(f"  Sections: {len(plan.get('content_outline', []))}")

    prompt = assemble_prompt(plan, args.level)
    print(f"\nAssembled prompt: {len(prompt):,} chars, approx {len(prompt.split()):,} words")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = OUT_DIR / args.level
    out_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = out_dir / f"{args.slug}.prompt.md"
    prompt_path.write_text(prompt, "utf-8")
    print(f"Prompt saved: {prompt_path}")

    if args.no_call:
        print("[--no-call] skipping Gemini call")
        return

    print("\nCalling Gemini...")
    output = call_gemini(prompt)

    out_path = out_dir / f"{args.slug}.md"
    out_path.write_text(output, "utf-8")
    print(f"Output saved: {out_path} ({len(output):,} chars, ~{len(output.split()):,} words)")


if __name__ == "__main__":
    main()
