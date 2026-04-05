#!/usr/bin/env python3
"""Convert seminar plans from v3 to v4 design using track-specific templates.

Reads section templates from docs/l2-uk-en/v4-seminar-section-templates.yaml
and uses Gemini to enrich each plan with v4 structure (Розминка, Конфліктна
карта, pedagogical annotations, etc.).

Supports ALL seminar tracks: hist, bio, istorio, lit, lit-*, folk, oes, ruth.

Usage:
    # Dry run one plan:
    .venv/bin/python scripts/tools/convert_plans_v4.py hist --slug trypillian-civilization --dry-run

    # Convert all HIST plans:
    .venv/bin/python scripts/tools/convert_plans_v4.py hist --all

    # Convert multiple tracks:
    .venv/bin/python scripts/tools/convert_plans_v4.py hist bio --all

    # All seminar tracks:
    .venv/bin/python scripts/tools/convert_plans_v4.py --all-tracks

    # Resume (skips v4.0):
    .venv/bin/python scripts/tools/convert_plans_v4.py hist --all --skip-done

    # Limit batch:
    .venv/bin/python scripts/tools/convert_plans_v4.py hist --all --limit 10

Issue: #1139
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLANS_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans"
TEMPLATES_PATH = PROJECT_ROOT / "docs" / "l2-uk-en" / "v4-seminar-section-templates.yaml"

# Gemini config
GEMINI_CLI = shutil.which("gemini") or "gemini"
GEMINI_MODEL = "gemini-2.5-pro"
_ENV = os.environ.copy()
_ENV["GEMINI_SESSION"] = "1"

# All seminar tracks
ALL_SEMINAR_TRACKS = [
    "folk", "hist", "bio", "istorio",
    "lit", "lit-essay", "lit-war", "lit-hist-fic", "lit-youth",
    "lit-fantastika", "lit-humor", "lit-drama", "lit-doc", "lit-crimea",
    "oes", "ruth",
]


def load_templates() -> dict:
    """Load track-specific v4 section templates."""
    with open(TEMPLATES_PATH) as f:
        return yaml.safe_load(f)


def get_template_for_track(templates: dict, track: str) -> dict:
    """Get the effective template for a track, handling inheritance."""
    if track in templates:
        tmpl = templates[track]
        if "inherits" in tmpl:
            base = dict(templates[tmpl["inherits"]])
            # Apply overrides
            if "section_overrides" in tmpl:
                sections = list(base.get("sections", []))
                for override in tmpl["section_overrides"]:
                    for i, sec in enumerate(sections):
                        if sec["section"].startswith(override["original"].split(":")[0]):
                            sections[i] = {
                                "section": override["replace_with"],
                                "words": override["words"],
                                "content": override.get("content", sec.get("content", "")),
                                "annotations": override.get("annotations", []),
                            }
                            break
                base["sections"] = sections
            # Merge other fields
            for key in ["cefr_min", "differentiator"]:
                if key in tmpl:
                    base[key] = tmpl[key]
            return base
        return tmpl
    # Fallback: if track not found, use lit base for lit-* tracks
    if track.startswith("lit-") and "lit" in templates:
        return templates["lit"]
    return templates.get("folk", {})


def format_template_for_prompt(tmpl: dict) -> str:
    """Format a template into a readable section spec for the Gemini prompt."""
    lines = []
    lines.append(f"cefr_min: {tmpl.get('cefr_min', 'C1')}")
    lines.append(f"pedagogy: {tmpl.get('pedagogy', 'CBI')}")
    lines.append(f"word_target: {tmpl.get('word_target', 5000)}")
    lines.append(f"\nDifferentiator: {tmpl.get('differentiator', '').strip()}")
    lines.append(f"\nPrimary annotations: {tmpl.get('primary_annotations', [])}")
    lines.append("\nSection structure:")

    for sec in tmpl.get("sections", []):
        section_name = sec.get("section", "?")
        words = sec.get("words", 0)
        content_desc = sec.get("content", "").strip()
        annotations = sec.get("annotations", [])
        lines.append(f"\n  ## {section_name} ({words}w)")
        lines.append(f"  {content_desc}")
        if annotations:
            lines.append(f"  Annotations: {', '.join(annotations)}")

    total = sum(s.get("words", 0) for s in tmpl.get("sections", []))
    lines.append(f"\n  TOTAL: {total}w (minimum)")
    return "\n".join(lines)


def build_v4_prompt(plan: dict, track: str, tmpl: dict, reference_plan: str) -> str:
    """Build the Gemini prompt for v3→v4 conversion."""
    plan_yaml = yaml.dump(plan, allow_unicode=True, default_flow_style=False, width=120)
    template_spec = format_template_for_prompt(tmpl)
    cefr = tmpl.get("cefr_min", "C1")

    return f"""You are converting a seminar plan from v3 to v4 format for the Ukrainian language curriculum.

## Track: {track.upper()}

## V4 Section Template for {track.upper()}
This is the MANDATORY section structure. Follow it exactly.

{template_spec}

## V4 Design Rules (universal)
1. **Розминка** (first section) — provocative question or mystery. NOT a summary.
2. **Конфліктна карта** (second section) — at least 2 debates (Дебат 1, Дебат 2).
3. **Pedagogical annotations** in content_outline points:
   - `[!epistemic-humility]` — contested claims, multiple positions
   - `[!decolonization]` — challenging imperial/Soviet narratives
   - `[!anti-hagiography]` — de-romanticizing, showing dark side
   - `[!myth-buster]` — correcting common misconceptions
   - `[!biography]` — introducing key figures
4. **Дискусія та підсумок** (last section) — return to opening question.
5. vocabulary_hints: list of {{word: ..., pos: ..., definition: ...}} (Ukrainian definitions)
6. objectives: IN UKRAINIAN (not English)
7. activity_hints: type/focus/description format, 2 quiz/fill-in + 1-2 essay/analysis
8. SET: cefr_min: {cefr}, pedagogy: CBI, version: '4.0'
9. ADD: persona (voice + role), connects_to, references fields
10. word_target: 5000 (MINIMUM — section budgets can exceed this)

## Reference Plan (FOLK v4 — for format/style reference only, NOT section structure)
```yaml
{reference_plan}
```

## Current Plan (v3 — CONVERT THIS)
```yaml
{plan_yaml}
```

## Critical Rules
1. PRESERVE all existing content facts — do NOT delete information from the v3 plan
2. USE the section template above — section names and order MUST match
3. Fill {{placeholders}} in section names with topic-appropriate titles from the plan content
4. The points under each section should be SPECIFIC to this module's topic, not generic
5. Every section MUST have a `words:` budget matching or exceeding the template minimum
6. Section word budgets MUST sum to ≥ 5000
7. YAML must be parseable by Python yaml.safe_load()
8. Use single quotes for strings containing colons

## Output
Return ONLY valid YAML. No markdown fences, no preamble. Start with `module:` line.
"""


def call_gemini(prompt: str, *, max_retries: int = 3) -> str | None:
    """Call Gemini CLI and return response."""
    for attempt in range(max_retries):
        try:
            proc = subprocess.Popen(
                [GEMINI_CLI, "-m", GEMINI_MODEL, "--approval-mode=yolo"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(PROJECT_ROOT),
                env=_ENV,
            )

            try:
                stdout, stderr = proc.communicate(input=prompt, timeout=300)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                print(f"    ⏱️  Timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(30)
                continue

            if proc.returncode != 0:
                if "429" in stderr or "quota" in stderr.lower() or "rate" in stderr.lower():
                    delay = 60 * (attempt + 1)
                    print(f"    ⏳ Rate limited, waiting {delay}s")
                    time.sleep(delay)
                    continue
                print(f"    ⚠️  Exit code {proc.returncode}: {stderr[:200]}")
                if not stdout.strip():
                    if attempt < max_retries - 1:
                        time.sleep(10)
                    continue

            response = stdout.strip()
            if len(response) < 200:
                print(f"    ⚠️  Short response ({len(response)} chars), retrying...")
                if attempt < max_retries - 1:
                    time.sleep(10)
                continue

            return response

        except FileNotFoundError:
            print("    ❌ gemini CLI not found")
            return None
        except Exception as e:
            print(f"    ❌ Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(10)

    return None


def extract_yaml_from_response(response: str) -> str:
    """Extract YAML from Gemini response, stripping markdown fences."""
    response = re.sub(r"^```(?:yaml)?\s*\n", "", response, flags=re.MULTILINE)
    response = re.sub(r"\n```\s*$", "", response, flags=re.MULTILINE)
    lines = response.split("\n")
    yaml_start = 0
    for i, line in enumerate(lines):
        if line.startswith("module:") or line.startswith("level:"):
            yaml_start = i
            break
    return "\n".join(lines[yaml_start:])


def validate_v4_plan(plan: dict, tmpl: dict) -> list[str]:
    """Validate a v4 plan against its track template."""
    issues = []

    for field in ["module", "level", "cefr_min", "slug", "version", "title",
                  "word_target", "pedagogy", "content_outline", "vocabulary_hints"]:
        if field not in plan:
            issues.append(f"Missing field: {field}")

    if str(plan.get("version", "")) != "4.0":
        issues.append(f"Version is {plan.get('version')}, expected 4.0")

    if plan.get("pedagogy") != "CBI":
        issues.append(f"Pedagogy is {plan.get('pedagogy')}, expected CBI")

    outline = plan.get("content_outline", [])
    if not outline:
        issues.append("Empty content_outline")
    else:
        first = outline[0].get("section", "")
        if "Розминка" not in first and "розминка" not in first.lower():
            issues.append(f"First section is '{first}', expected Розминка")

        has_conflict = any(
            "Конфліктна" in s.get("section", "") or "конфліктна" in s.get("section", "").lower()
            for s in outline
        )
        if not has_conflict:
            issues.append("Missing Конфліктна карта section")

        total_words = sum(s.get("words", 0) for s in outline)
        if total_words < 5000:
            issues.append(f"Word budget sum is {total_words}, expected ≥ 5000")

        # Check section count matches template
        expected_count = len(tmpl.get("sections", []))
        if len(outline) < expected_count:
            issues.append(f"Only {len(outline)} sections, template has {expected_count}")

    # Vocabulary hints format
    vocab = plan.get("vocabulary_hints", [])
    if isinstance(vocab, list) and vocab:
        if isinstance(vocab[0], dict):
            if "word" not in vocab[0]:
                issues.append("vocabulary_hints items missing 'word' field")
        elif isinstance(vocab[0], str):
            issues.append("vocabulary_hints should be list of dicts, not strings")
    elif isinstance(vocab, dict):
        issues.append("vocabulary_hints should be list of dicts, not dict")

    # Objectives in Ukrainian
    for obj in plan.get("objectives", []):
        if not any("\u0400" <= c <= "\u04FF" for c in str(obj)):
            issues.append(f"Objective not in Ukrainian: {str(obj)[:60]}...")
            break

    return issues


def convert_one(track: str, slug: str, tmpl: dict, reference_plan: str,
                *, dry_run: bool = False, force: bool = False) -> bool:
    """Convert a single plan from v3 to v4."""
    plan_path = PLANS_ROOT / track / f"{slug}.yaml"
    if not plan_path.exists():
        print(f"  ❌ Plan not found: {plan_path}")
        return False

    with open(plan_path) as f:
        plan = yaml.safe_load(f)

    if not plan or not isinstance(plan, dict):
        print(f"  ❌ Invalid plan: {slug}")
        return False

    if str(plan.get("version", "")) == "4.0" and not force:
        print(f"  ⏭️  Already v4: {slug}")
        return True

    print(f"  🔄 Converting: {slug} (v{plan.get('version', '?')} → v4.0)")

    prompt = build_v4_prompt(plan, track, tmpl, reference_plan)

    if dry_run:
        print(f"    Prompt length: {len(prompt)} chars")
        print(f"    Current sections: {[s.get('section', '?') for s in plan.get('content_outline', [])]}")
        tmpl_sections = [s.get("section", "?") for s in tmpl.get("sections", [])]
        print(f"    Target sections:  {tmpl_sections}")
        return True

    response = call_gemini(prompt)
    if not response:
        print(f"  ❌ Gemini failed for {slug}")
        return False

    yaml_text = extract_yaml_from_response(response)
    try:
        new_plan = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        print(f"  ❌ YAML parse error for {slug}: {e}")
        err_path = PLANS_ROOT / track / f".{slug}.v4-error.txt"
        err_path.write_text(response, encoding="utf-8")
        print(f"    Saved raw response to {err_path.name}")
        return False

    if not new_plan or not isinstance(new_plan, dict):
        print(f"  ❌ Empty or invalid YAML for {slug}")
        return False

    issues = validate_v4_plan(new_plan, tmpl)
    if issues:
        print(f"  ⚠️  Validation issues for {slug}:")
        for issue in issues:
            print(f"    - {issue}")
        serious = [i for i in issues if "Missing field" in i or "Empty content" in i]
        if serious:
            print(f"  ❌ Serious issues, skipping {slug}")
            return False

    # Backup original
    bak_path = PLANS_ROOT / track / f"{slug}.v3.bak"
    if not bak_path.exists():
        shutil.copy2(plan_path, bak_path)

    with open(plan_path, "w") as f:
        yaml.dump(new_plan, f, allow_unicode=True, default_flow_style=False, width=120)

    print(f"  ✅ Converted: {slug} (v4.0)")
    return True


def load_reference_plan() -> str:
    """Load a FOLK v4 plan as reference."""
    ref_path = PLANS_ROOT / "folk" / "dumy-lytsarski.yaml"
    if not ref_path.exists():
        folk_plans = list((PLANS_ROOT / "folk").glob("*.yaml"))
        if folk_plans:
            ref_path = folk_plans[0]
        else:
            return "(No reference plan available)"
    return ref_path.read_text(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Convert seminar plans to v4 design")
    parser.add_argument("tracks", nargs="*",
                        help="Tracks to convert (e.g., hist bio lit)")
    parser.add_argument("--all-tracks", action="store_true",
                        help="Convert ALL seminar tracks")
    parser.add_argument("--slug", help="Convert a specific slug")
    parser.add_argument("--all", action="store_true", help="Convert all plans in track(s)")
    parser.add_argument("--limit", type=int, help="Max plans to convert per track")
    parser.add_argument("--skip-done", action="store_true",
                        help="Skip plans already at v4.0")
    parser.add_argument("--force", action="store_true",
                        help="Reconvert even if already v4")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be converted")

    args = parser.parse_args()

    if args.all_tracks:
        tracks = ALL_SEMINAR_TRACKS
    elif args.tracks:
        tracks = args.tracks
    else:
        parser.error("Specify track name(s) or --all-tracks")

    if not args.slug and not args.all:
        parser.error("Specify --slug or --all")

    # Validate track names
    for t in tracks:
        if t not in ALL_SEMINAR_TRACKS:
            parser.error(f"Unknown track: {t}. Available: {', '.join(ALL_SEMINAR_TRACKS)}")

    # Load templates and reference
    templates = load_templates()
    reference = load_reference_plan()
    print(f"📋 Templates loaded ({len(templates)} tracks)")
    print(f"📋 Reference plan loaded ({len(reference)} chars)")

    total_success = 0
    total_failed = 0
    total_skipped = 0

    for track in tracks:
        track_dir = PLANS_ROOT / track
        if not track_dir.is_dir():
            print(f"⏭️  No plans dir for {track}, skipping")
            continue

        tmpl = get_template_for_track(templates, track)
        if not tmpl:
            print(f"⚠️  No template for {track}, skipping")
            continue

        if args.slug:
            slugs = [args.slug]
        else:
            slugs = sorted(
                p.stem for p in track_dir.glob("*.yaml")
                if not p.stem.startswith(".") and not p.name.endswith(".bak")
            )

        if args.skip_done:
            filtered = []
            for slug in slugs:
                plan_path = track_dir / f"{slug}.yaml"
                with open(plan_path) as f:
                    plan = yaml.safe_load(f)
                if plan and str(plan.get("version", "")) == "4.0" and not args.force:
                    total_skipped += 1
                    continue
                filtered.append(slug)
            slugs = filtered

        if args.limit:
            slugs = slugs[:args.limit]

        tmpl_sections = [s.get("section", "?") for s in tmpl.get("sections", [])]
        print(f"\n{'═' * 60}")
        print(f"  {track.upper()}: {len(slugs)} plans to convert")
        print(f"  Template: {tmpl_sections}")
        print(f"{'═' * 60}")

        for i, slug in enumerate(slugs, 1):
            print(f"\n[{i}/{len(slugs)}] {track}/{slug}")
            success = convert_one(
                track, slug, tmpl, reference,
                dry_run=args.dry_run, force=args.force,
            )
            if success:
                total_success += 1
            else:
                total_failed += 1

            if not args.dry_run and i < len(slugs):
                time.sleep(2)

    print(f"\n{'═' * 60}")
    print(f"  TOTAL: ✅ {total_success} | ❌ {total_failed} | ⏭️  {total_skipped}")
    if args.dry_run:
        print("  (DRY RUN — no files were modified)")
    print(f"{'═' * 60}")


if __name__ == "__main__":
    main()
