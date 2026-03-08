#!/usr/bin/env python3
"""build_module_direct.py — Build pipeline for l2-uk-direct track.

Enriches existing YAML plans, validates correctness, optionally runs
cross-agent review, and generates MDX.

Pipeline phases:
  enrich   → Gemini fills gaps (activities, teaching notes, sentences)
  validate → Deterministic schema + pedagogical checks
  review   → Claude adversarial review (optional, --review)
  mdx      → Generate MDX via generate_mdx_direct.py

Usage:
  .venv/bin/python scripts/build_module_direct.py a1 tse
  .venv/bin/python scripts/build_module_direct.py a1 tse --validate-only
  .venv/bin/python scripts/build_module_direct.py a1 tse --mdx-only
  .venv/bin/python scripts/build_module_direct.py a1 tse --review
  .venv/bin/python scripts/build_module_direct.py a1 --all
  .venv/bin/python scripts/build_module_direct.py a1 tse --force-phase enrich
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-direct"
MANIFEST_PATH = CURRICULUM_DIR / "manifest.yaml"
PHASES_DIR = PROJECT_ROOT / "claude_extensions" / "phases"
sys.path.insert(0, str(SCRIPTS_DIR))
from batch_gemini_config import PRO_MODEL, VENV_PYTHON
from validate_direct import ValidationResult, validate_file

# ── Constants ─────────────────────────────────────────────────────────────────
PHASES = ["enrich", "validate", "review", "mdx"]
STATUS_FLOW = {
    "enrich": "enriched",
    "validate": "validated",
    "review": "reviewed",
    "mdx": "ready",
}

# ── A1 Vocabulary Targets ─────────────────────────────────────────────────────
# Source: CURRICULUM-PLAN.md "A1 Vocabulary Targets" table
# State Standard A1: 750 words (receptive), ~690 active production
# Distribution: vocab/communicative modules carry most words,
# grammar modules get fewer but still contribute, checkpoints = 0.
#
# Per-module targets: {slug: min_vocab_words}
# Modules not listed default to 0 (script_foundation 1-4, checkpoints).
A1_VOCAB_TARGETS: dict[str, int] = {
    # Phase 0: Script — ~50 total across modules 1-6
    # abetka 1-4: decodable words from available letters (gradually increasing)
    "abetka-1": 5,         # А М Л У Н С → мама, лама, сума, сам, мул...
    "abetka-2": 8,         # + К И Р Б В Д І → банан, вода, рука, книга...
    "abetka-3": 10,        # + П Т Г Ґ Е З Ж Ш Х → most words readable
    "abetka-4": 10,        # full alphabet → any word
    "sklad": 20,           # syllable words — decodable
    "naholos": 10,         # stress examples
    # Phase 1: First Words — ~135 total across 7-12
    "pryvit": 25,          # greetings, farewells, politeness
    "tse": 20,             # Це... naming things
    "ya": 20,              # self-intro: name, nationality, profession
    "shcho-robyt": 15,     # actions, core verbs
    "yakyi": 25,           # adjectives + gender agreement
    "mnozh": 20,           # plurals vocabulary
    # Phase 2: Sentences — ~90 total across 13-19 (no checkpoint)
    "ya-ty-vin": 15,       # pronouns + conjugation
    "rechennia": 10,       # sentence structure
    "spoluchnyky": 10,     # connectors
    "zapytuyu": 15,        # question words
    "chysla": 30,          # numbers 1-100
    "podobayetsya": 15,    # likes, preferences
    "zovnishnist": 20,     # appearance words
    # Phase 3: Accusative — ~40 total across 21-23
    "znavidminnyk-i": 15,  # accusative inanimate
    "znavidminnyk-ii": 10, # accusative animate
    "znavidminnyk-priymennyky": 15,  # accusative + prepositions
    # Phase 4: Location — ~75 total across 24-26
    "mistse": 20,          # locative, months
    "misto": 30,           # city, transport
    "dim": 25,             # home, rooms, possessives
    # Phase 5: Pronoun & Adj Forms — ~25 total across 27-29
    "mene-tobi": 8,        # pronoun forms (existing words)
    "tsej-toj": 8,         # demonstratives
    "prykmetnyk-vidminky": 8,  # adjective case forms
    # Phase 6: Daily Life — ~145 total across 30-36
    "chas": 25,            # time, days, months
    "den": 20,             # daily routine
    "mynule": 10,          # past tense (forms of known verbs)
    "yizha": 35,           # food, café
    "kupuvatysia": 25,     # shopping, hygiene
    "zdorovia": 20,        # health, body
    "dozvillia": 25,       # leisure, hobbies
    # Phase 7: World — ~110 total across 38-41
    "pryroda": 30,         # nature, weather
    "sim-ya": 25,          # family
    "sviatky": 25,         # traditions, holidays
    "podorozhi": 30,       # travel, directions
    # Phase 8: Real-World Skills — ~35 total across 42-45
    "nakazy": 8,           # imperative forms
    "zaborony-dokonane": 8,  # prohibitions, perfective
    "znaky-ta-napysy": 15, # signs, forms
    "lystuvannia": 10,     # writing vocab
    # Phase 9: Polish
    "eufoniia": 5,         # euphony examples
}


# ── Data ──────────────────────────────────────────────────────────────────────
@dataclass
class DirectModuleContext:
    slug: str
    level: str
    yaml_path: Path
    status_path: Path
    orch_dir: Path = field(default=Path("."))
    module_data: dict = field(default_factory=dict)
    status_data: dict = field(default_factory=dict)
    force_phase: str | None = None
    do_review: bool = False
    rebuild: bool = False


# ── Utilities ─────────────────────────────────────────────────────────────────
def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    print(msg, flush=True)


def save_artifact(ctx: DirectModuleContext, phase: str, name: str, content: str) -> Path:
    """Save a prompt/output artifact to the orchestration directory."""
    ctx.orch_dir.mkdir(parents=True, exist_ok=True)
    path = ctx.orch_dir / f"{phase}-{name}"
    path.write_text(content, encoding="utf-8")
    return path


# ── Status I/O ────────────────────────────────────────────────────────────────
def load_status(ctx: DirectModuleContext) -> dict:
    if ctx.status_path.exists():
        with open(ctx.status_path, encoding="utf-8") as f:
            return json.load(f)
    return {
        "module": ctx.slug,
        "track": "l2-uk-direct",
        "level": ctx.level,
        "status": "draft",
    }


def save_status(ctx: DirectModuleContext) -> None:
    ctx.status_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ctx.status_path, "w", encoding="utf-8") as f:
        json.dump(ctx.status_data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def is_phase_complete(ctx: DirectModuleContext, phase: str) -> bool:
    if ctx.force_phase == phase:
        return False
    return ctx.status_data.get("phases", {}).get(phase, {}).get("status") == "complete"


def mark_phase(ctx: DirectModuleContext, phase: str, status: str, **extra: Any) -> None:
    if "phases" not in ctx.status_data:
        ctx.status_data["phases"] = {}
    entry: dict[str, Any] = {"status": status, "ts": _now_iso()}
    entry.update(extra)
    ctx.status_data["phases"][phase] = entry
    ctx.status_data["status"] = STATUS_FLOW.get(phase, ctx.status_data.get("status", "draft"))
    save_status(ctx)


# ── YAML I/O ──────────────────────────────────────────────────────────────────
def load_module_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict at root of {path}")
    return data


def save_module_yaml(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)


# ── Manifest ──────────────────────────────────────────────────────────────────
def load_manifest() -> dict[str, list[str]]:
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    result: dict[str, list[str]] = {}
    for lvl_name, lvl_data in manifest.get("levels", {}).items():
        result[lvl_name] = lvl_data.get("sequence", [])
    return result


def get_available_letters(level: str, target_slug: str) -> set[str]:
    """Compute cumulative letter set from manifest sequence up to (including) target_slug."""
    manifest = load_manifest()
    letters: set[str] = set()
    for slug in manifest.get(level, []):
        yaml_path = CURRICULUM_DIR / level / f"{slug}.yaml"
        if yaml_path.exists():
            data = load_module_yaml(yaml_path)
            if data.get("type") == "script_foundation":
                for letter in data.get("letters", []):
                    letters.add(letter.get("upper", ""))
                    letters.add(letter.get("lower", ""))
        if slug == target_slug:
            break
    letters.discard("")
    return letters


def get_prior_vocab(level: str, target_slug: str) -> list[str]:
    """Collect all vocabulary words from modules before target_slug."""
    manifest = load_manifest()
    words: list[str] = []
    for slug in manifest.get(level, []):
        if slug == target_slug:
            break
        yaml_path = CURRICULUM_DIR / level / f"{slug}.yaml"
        if not yaml_path.exists():
            continue
        data = load_module_yaml(yaml_path)
        vocab = data.get("vocabulary", [])
        if not vocab:
            continue
        if isinstance(vocab[0], dict) and "items" in vocab[0]:
            for group in vocab:
                for item in group.get("items", []):
                    w = item.get("word") or item.get("phrase") or item.get("infinitive", "")
                    if w:
                        words.append(w)
        else:
            for item in vocab:
                w = item.get("word") or item.get("phrase") or item.get("infinitive", "")
                if w:
                    words.append(w)
    return words


def get_vocab_target(slug: str) -> int:
    """Get the minimum vocabulary target for a module."""
    return A1_VOCAB_TARGETS.get(slug, 0)


# ── Phase: Enrich ─────────────────────────────────────────────────────────────
def phase_enrich(ctx: DirectModuleContext) -> bool:
    if is_phase_complete(ctx, "enrich"):
        log("  [enrich] Already complete, skipping.")
        return True

    log("  [enrich] Building prompt...")
    template_path = PHASES_DIR / "gemini" / "direct-enrich.md"
    if not template_path.exists():
        log(f"  [enrich] ERROR: Template not found: {template_path}")
        mark_phase(ctx, "enrich", "failed", error="template_missing")
        return False

    template = template_path.read_text(encoding="utf-8")
    yaml_content = ctx.yaml_path.read_text(encoding="utf-8")

    # Compute available letters for decodability constraint
    letters = get_available_letters(ctx.level, ctx.slug)
    available_letters = " ".join(sorted(letters)) if letters else ""
    all_letters_available = len(letters) >= 66  # full Ukrainian alphabet = 33 upper + 33 lower

    # Compute vocabulary context
    vocab_target = get_vocab_target(ctx.slug)
    prior_words = get_prior_vocab(ctx.level, ctx.slug)
    cumulative_count = len(prior_words)

    # Build position context
    manifest = load_manifest()
    sequence = manifest.get(ctx.level, [])
    position = sequence.index(ctx.slug) + 1 if ctx.slug in sequence else 0
    total = len(sequence)

    prompt = template.replace("{{YAML_CONTENT}}", yaml_content)
    prompt = prompt.replace("{{SLUG}}", ctx.slug)
    prompt = prompt.replace("{{LEVEL}}", ctx.level.upper())
    prompt = prompt.replace("{{MODULE_TYPE}}", ctx.module_data.get("type", ""))
    prompt = prompt.replace("{{POSITION}}", f"{position}/{total}")
    prompt = prompt.replace("{{AVAILABLE_LETTERS}}", available_letters or "Full alphabet available")
    prompt = prompt.replace("{{VOCAB_TARGET}}", str(vocab_target))
    prompt = prompt.replace("{{CUMULATIVE_VOCAB}}", str(cumulative_count))
    prompt = prompt.replace("{{PRIOR_WORDS}}", ", ".join(prior_words[-50:]) if prior_words else "(none — first vocabulary module)")
    prompt = prompt.replace("{{DECODABILITY_NOTE}}",
        f"HARD CONSTRAINT: Only these letters are available: {available_letters}. "
        f"ALL vocabulary words and example sentences must be spelled using ONLY these letters. "
        f"Words requiring other letters CANNOT be used."
        if not all_letters_available and available_letters
        else "Full alphabet available — no letter restrictions."
    )

    save_artifact(ctx, "enrich", "prompt.md", prompt)
    log("  [enrich] Dispatching to Gemini...")
    task_id = f"direct-enrich-{ctx.level}-{ctx.slug}"

    args = [
        VENV_PYTHON,
        str(SCRIPTS_DIR / "ai_agent_bridge/__main__.py"), "ask-gemini",
        "-",
        "--task-id", task_id,
        "--model", PRO_MODEL,
        "--stdout-only",
    ]

    try:
        result = subprocess.run(
            args, input=prompt, capture_output=True, text=True,
            timeout=600, cwd=str(PROJECT_ROOT),
        )
    except subprocess.TimeoutExpired:
        log("  [enrich] TIMEOUT: Gemini dispatch exceeded 600s")
        mark_phase(ctx, "enrich", "failed", error="timeout")
        return False

    if result.returncode != 0:
        log(f"  [enrich] Gemini dispatch failed (rc={result.returncode})")
        if result.stderr:
            log(f"  stderr: {result.stderr[:500]}")
        mark_phase(ctx, "enrich", "failed", error="dispatch_failed")
        return False

    raw_output = result.stdout.strip()
    save_artifact(ctx, "enrich", "output-raw.yaml", raw_output)

    # Strip markdown fences if present
    if raw_output.startswith("```"):
        lines = raw_output.split("\n")
        # Remove first line (```yaml or ```) and last line (```)
        lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        raw_output = "\n".join(lines)

    # Parse YAML
    try:
        enriched = yaml.safe_load(raw_output)
    except yaml.YAMLError as e:
        log(f"  [enrich] YAML parse error in Gemini output: {e}")
        mark_phase(ctx, "enrich", "failed", error="yaml_parse")
        return False

    if not isinstance(enriched, dict):
        log("  [enrich] Gemini output is not a YAML dict")
        mark_phase(ctx, "enrich", "failed", error="not_dict")
        return False

    # Safety checks: critical fields must be preserved
    for field in ("module", "track", "level", "type", "title"):  # noqa: F402
        if enriched.get(field) != ctx.module_data.get(field):
            log(f"  [enrich] REJECTED: '{field}' changed from "
                f"'{ctx.module_data.get(field)}' to '{enriched.get(field)}'")
            mark_phase(ctx, "enrich", "failed", error=f"field_changed:{field}")
            return False

    # Activity count must not decrease
    orig_act = len(ctx.module_data.get("activities", []))
    new_act = len(enriched.get("activities", []))
    if new_act < orig_act:
        log(f"  [enrich] REJECTED: activity count decreased ({orig_act} → {new_act})")
        mark_phase(ctx, "enrich", "failed", error="activities_decreased")
        return False

    # Vocabulary count must not decrease
    def count_vocab(data: dict) -> int:
        vocab = data.get("vocabulary", [])
        if not vocab:
            return 0
        if isinstance(vocab[0], dict) and "items" in vocab[0]:
            return sum(len(g.get("items", [])) for g in vocab)
        return len(vocab)

    orig_vocab = count_vocab(ctx.module_data)
    new_vocab = count_vocab(enriched)
    if new_vocab < orig_vocab:
        log(f"  [enrich] REJECTED: vocab count decreased ({orig_vocab} → {new_vocab})")
        mark_phase(ctx, "enrich", "failed", error="vocab_decreased")
        return False

    # Write enriched YAML
    save_module_yaml(ctx.yaml_path, enriched)
    ctx.module_data = enriched
    log(f"  [enrich] OK — activities: {orig_act}→{new_act}, vocab: {orig_vocab}→{new_vocab}")
    mark_phase(ctx, "enrich", "complete")
    return True


# ── Phase: Validate ───────────────────────────────────────────────────────────
def phase_validate(ctx: DirectModuleContext) -> bool:
    if is_phase_complete(ctx, "validate"):
        log("  [validate] Already complete, skipping.")
        return True

    log("  [validate] Running validation...")
    vocab_target = get_vocab_target(ctx.slug)
    vr: ValidationResult = validate_file(ctx.yaml_path, vocab_target=vocab_target)
    vr.print_report()

    errors = len(vr.errors)
    warnings = len(vr.warnings)

    if not vr.passed:
        log(f"  [validate] FAILED — {errors} errors, {warnings} warnings")
        mark_phase(ctx, "validate", "failed", errors=errors, warnings=warnings)
        return False

    log(f"  [validate] PASSED — {errors} errors, {warnings} warnings")
    mark_phase(ctx, "validate", "complete", errors=errors, warnings=warnings)
    return True


# ── Phase: Review ─────────────────────────────────────────────────────────────
def phase_review(ctx: DirectModuleContext) -> bool:
    if not ctx.do_review:
        log("  [review] Skipped (use --review to enable)")
        return True

    if is_phase_complete(ctx, "review"):
        log("  [review] Already complete, skipping.")
        return True

    log("  [review] Building review prompt...")
    template_path = PHASES_DIR / "claude" / "direct-review.md"
    if not template_path.exists():
        log(f"  [review] ERROR: Template not found: {template_path}")
        mark_phase(ctx, "review", "failed", error="template_missing")
        return False

    template = template_path.read_text(encoding="utf-8")
    yaml_content = ctx.yaml_path.read_text(encoding="utf-8")

    prompt = template.replace("{{YAML_CONTENT}}", yaml_content)
    prompt = prompt.replace("{{SLUG}}", ctx.slug)
    prompt = prompt.replace("{{LEVEL}}", ctx.level.upper())
    prompt = prompt.replace("{{MODULE_TYPE}}", ctx.module_data.get("type", ""))

    save_artifact(ctx, "review", "prompt.md", prompt)
    log("  [review] Dispatching to Claude...")
    task_id = f"direct-review-{ctx.level}-{ctx.slug}"

    args = [
        VENV_PYTHON,
        str(SCRIPTS_DIR / "ai_agent_bridge/__main__.py"), "ask-gemini",
        "-",
        "--task-id", task_id,
        "--model", "claude-opus-4-6",
        "--stdout-only",
    ]

    try:
        result = subprocess.run(
            args, input=prompt, capture_output=True, text=True,
            timeout=600, cwd=str(PROJECT_ROOT),
        )
    except subprocess.TimeoutExpired:
        log("  [review] TIMEOUT exceeded 600s")
        mark_phase(ctx, "review", "failed", error="timeout")
        return False

    if result.returncode != 0:
        log(f"  [review] Dispatch failed (rc={result.returncode})")
        mark_phase(ctx, "review", "failed", error="dispatch_failed")
        return False

    raw_output = result.stdout.strip()
    save_artifact(ctx, "review", "output-raw.json", raw_output)

    # Try to extract JSON verdict
    try:
        # Look for JSON block in output
        json_start = raw_output.find("{")
        json_end = raw_output.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            verdict = json.loads(raw_output[json_start:json_end])
        else:
            verdict = {"verdict": "UNKNOWN", "raw": raw_output[:500]}
    except json.JSONDecodeError:
        verdict = {"verdict": "UNKNOWN", "raw": raw_output[:500]}

    if verdict.get("verdict") == "PASS":
        log("  [review] PASSED")
        mark_phase(ctx, "review", "complete", verdict="PASS")
        return True
    elif verdict.get("verdict") == "FAIL":
        issues = verdict.get("issues", [])
        log(f"  [review] FAILED — {len(issues)} issues found")
        for issue in issues[:5]:
            log(f"    - {issue}")
        mark_phase(ctx, "review", "failed", verdict="FAIL", issues=issues)
        return False
    else:
        log(f"  [review] Unclear verdict: {verdict.get('verdict', 'UNKNOWN')}")
        mark_phase(ctx, "review", "failed", verdict="UNKNOWN")
        return False


# ── Phase: MDX ────────────────────────────────────────────────────────────────
def phase_mdx(ctx: DirectModuleContext) -> bool:
    if is_phase_complete(ctx, "mdx"):
        log("  [mdx] Already complete, skipping.")
        return True

    log("  [mdx] Generating MDX...")

    args = [
        VENV_PYTHON,
        str(SCRIPTS_DIR / "generate_mdx_direct.py"),
        "--module", str(ctx.yaml_path),
    ]

    result = subprocess.run(args, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        log(f"  [mdx] FAILED (rc={result.returncode})")
        if result.stderr:
            log(f"  stderr: {result.stderr[:500]}")
        mark_phase(ctx, "mdx", "failed", error="mdx_generation")
        return False

    log("  [mdx] OK")
    if result.stdout:
        log(f"  {result.stdout.strip()}")
    mark_phase(ctx, "mdx", "complete")
    return True


# ── Pipeline Runner ───────────────────────────────────────────────────────────
def run_pipeline(ctx: DirectModuleContext, phases: list[str] | None = None) -> bool:
    if phases is None:
        phases = PHASES

    log(f"\n{'='*60}")
    log(f"Pipeline: {ctx.level}/{ctx.slug}")
    log(f"  YAML: {ctx.yaml_path}")
    log(f"  Phases: {' → '.join(phases)}")
    log(f"{'='*60}")

    ctx.module_data = load_module_yaml(ctx.yaml_path)
    ctx.status_data = load_status(ctx)

    if ctx.rebuild:
        log("  [rebuild] Clearing all phase completions...")
        ctx.status_data.pop("phases", None)
        ctx.status_data["status"] = "draft"
        save_status(ctx)

    phase_funcs = {
        "enrich": phase_enrich,
        "validate": phase_validate,
        "review": phase_review,
        "mdx": phase_mdx,
    }

    for phase in phases:
        func = phase_funcs.get(phase)
        if not func:
            log(f"  Unknown phase: {phase}")
            return False
        if not func(ctx):
            log(f"\n  Pipeline STOPPED at phase: {phase}")
            return False

    log(f"\n  Pipeline COMPLETE: {ctx.level}/{ctx.slug} → {ctx.status_data.get('status', '?')}")
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────
def build_context(level: str, slug: str, args: argparse.Namespace) -> DirectModuleContext:
    yaml_path = CURRICULUM_DIR / level / f"{slug}.yaml"
    status_path = CURRICULUM_DIR / level / f"{slug}.status.json"
    orch_dir = CURRICULUM_DIR / level / "orchestration" / slug
    return DirectModuleContext(
        slug=slug,
        level=level,
        yaml_path=yaml_path,
        status_path=status_path,
        orch_dir=orch_dir,
        force_phase=args.force_phase,
        do_review=args.review,
        rebuild=args.rebuild,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build pipeline for l2-uk-direct modules.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("level", help="Level (e.g. a1)")
    parser.add_argument("slug", nargs="?", help="Module slug (e.g. tse) or sequence number (e.g. 8)")
    parser.add_argument("--all", action="store_true", help="Process all modules at this level")
    parser.add_argument("--review", action="store_true", help="Enable cross-agent review phase")
    parser.add_argument("--force-phase", choices=PHASES, help="Force re-run of a specific phase")
    parser.add_argument("--rebuild", action="store_true", help="Clear all phase completions and re-run from scratch")
    parser.add_argument("--validate-only", action="store_true", help="Run only the validate phase")
    parser.add_argument("--mdx-only", action="store_true", help="Run only the mdx phase")

    args = parser.parse_args()

    if not args.slug and not args.all:
        parser.error("Provide a slug or use --all")

    # Determine phases to run
    if args.validate_only:
        phases = ["validate"]
    elif args.mdx_only:
        phases = ["mdx"]
    else:
        phases = list(PHASES)
        if not args.review:
            phases.remove("review")

    # Resolve slug: accept sequence number (e.g. "8") or slug name (e.g. "tse")
    manifest = load_manifest()
    sequence = manifest.get(args.level, [])

    if args.slug and args.slug.isdigit():
        idx = int(args.slug)
        if idx < 1 or idx > len(sequence):
            parser.error(f"Module #{idx} out of range (1-{len(sequence)}) for level {args.level}")
        args.slug = sequence[idx - 1]
        log(f"Resolved #{idx} → {args.slug}")

    # Collect slugs
    if args.all:
        slugs = sequence
        if not slugs:
            log(f"ERROR: No modules found for level '{args.level}'")
            sys.exit(2)
    else:
        slugs = [args.slug]

    # Run
    passed = 0
    failed = 0
    for slug in slugs:
        ctx = build_context(args.level, slug, args)
        if not ctx.yaml_path.exists():
            log(f"SKIP: {ctx.yaml_path} not found")
            failed += 1
            continue
        if run_pipeline(ctx, phases):
            passed += 1
        else:
            failed += 1

    # Summary
    total = passed + failed
    log(f"\n{'='*60}")
    log(f"Results: {passed}/{total} passed, {failed} failed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
