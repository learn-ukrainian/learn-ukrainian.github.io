#!/usr/bin/env python3
"""LLM adversarial plan review via Gemini.

Sends a plan YAML to Gemini for adversarial review before content generation.
Catches pedagogy issues, bad dialogues, wrong grammar scope, vocabulary
problems that deterministic checks (check_plan.py) miss.

Usage:
    .venv/bin/python scripts/audit/review_plan.py a1 sounds-letters-and-hello
    .venv/bin/python scripts/audit/review_plan.py a1 --all
    .venv/bin/python scripts/audit/review_plan.py a1 --all --dry-run  # show prompt, skip Gemini

Issue: #984
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

GEMINI_MODEL = "gemini-3.1-pro-preview"
GEMINI_TIMEOUT = 120  # seconds


# ---------------------------------------------------------------------------
# Level config loader
# ---------------------------------------------------------------------------

def get_level_config(level: str) -> dict:
    """Load level configuration from audit config."""
    from audit.config import LEVEL_CONFIG
    key = level.upper()
    if key in LEVEL_CONFIG:
        return LEVEL_CONFIG[key]
    return {"target_words": 0}


# ---------------------------------------------------------------------------
# Plan loader
# ---------------------------------------------------------------------------

def load_plan(level: str, slug: str) -> dict | None:
    """Load a plan YAML, returning None if not found or unparseable."""
    plan_path = CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"
    if not plan_path.exists():
        return None
    try:
        return yaml.safe_load(plan_path.read_text("utf-8"))
    except yaml.YAMLError:
        return None


def get_all_slugs(level: str) -> list[str]:
    """Get all module slugs for a level from curriculum.yaml."""
    manifest = CURRICULUM_ROOT / "curriculum.yaml"
    data = yaml.safe_load(manifest.read_text("utf-8"))
    return data.get("levels", {}).get(level, {}).get("modules", [])


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

REVIEW_PROMPT_TEMPLATE = """\
You are an adversarial reviewer for a Ukrainian language curriculum. Your job \
is to find problems a deterministic linter cannot catch: pedagogy mistakes, \
unnatural vocabulary choices, Russianisms hiding in example words, unrealistic \
dialogue scenarios, grammar scope creep, and content outline issues.

The following deterministic checks ALREADY run (do NOT duplicate them):
- Missing required YAML fields
- Section word budgets summing to < word_target
- Stress marks (U+0301) in plan text
- Known Russicism word list
- Missing apostrophes (м'яч, п'ять, etc.)
- Phase/sequence alignment
- Grammar scope vs. phase (e.g., no verbs in A1.1 phonetics)
- Prerequisite slug validation
- VESUM vocabulary verification

Focus on what machines CANNOT catch:

## 1. Linguistic Accuracy
- Vocabulary hints that are valid Ukrainian words but unnatural choices \
(e.g., using a bookish synonym when a colloquial one is standard)
- Calques from English or Russian that VESUM accepts but native speakers \
would not say (e.g., "приймати душ" instead of "брати душ")
- Words listed at the wrong frequency tier for the level

## 2. Pedagogy
- Grammar constructs too advanced for the stated phase/level
- Prerequisites that should exist but are missing
- Learning objectives that don't match the content outline
- Section ordering that doesn't follow a logical teaching progression
- Too many new concepts introduced at once

## 3. Vocabulary
- Words in vocabulary_hints that are too advanced for the level
- Missing high-frequency words that should be taught at this stage
- Vocabulary that doesn't connect to the module's theme

## 4. Dialogue & Activity Realism
- Activity hints that describe artificial/interrogation-style scenarios
- Dialogue patterns that no native speaker would use in real life
- Activities that test content recall instead of language skills \
(e.g., "What year did X happen?" instead of comprehension questions)

## 5. Content Outline
- Sections that overlap or repeat
- Word budget distribution that is unreasonable (e.g., 50 words for a \
complex grammar topic)
- Missing essential subtopics for the module's theme
- Points that are vague filler vs. concrete teaching content

---

## Level Configuration
- Level: {level}
- Word target: {target_words}
- Phase: {phase}

## Plan YAML
```yaml
{plan_yaml}
```

---

## Output Format

Respond with ONLY this JSON (no markdown fences, no explanation outside JSON):
{{
  "verdict": "<PASS or FIX or REWRITE>",
  "score": <1-10>,
  "summary": "<2-3 sentence overall assessment>",
  "findings": [
    {{
      "category": "<linguistic|pedagogy|vocabulary|dialogue|outline>",
      "severity": "<critical|major|minor>",
      "location": "<field name or section title where the issue is>",
      "issue": "<what is wrong>",
      "fix": "<how to fix it>"
    }}
  ]
}}

Verdict rules:
- PASS: score >= 8, no critical findings
- FIX: score 5-7, has major findings but plan is salvageable with edits
- REWRITE: score < 5, fundamental pedagogy or structure problems
"""


def build_review_prompt(plan: dict, level: str) -> str:
    """Build the full review prompt for a plan."""
    level_config = get_level_config(level)
    plan_yaml = yaml.dump(plan, allow_unicode=True, default_flow_style=False)
    return REVIEW_PROMPT_TEMPLATE.format(
        level=level.upper(),
        target_words=level_config.get("target_words", "unknown"),
        phase=plan.get("phase", "unknown"),
        plan_yaml=plan_yaml,
    )


# ---------------------------------------------------------------------------
# Gemini dispatch
# ---------------------------------------------------------------------------

def call_gemini(prompt: str) -> tuple[bool, str]:
    """Call Gemini CLI directly and return (success, raw_output)."""
    try:
        result = subprocess.run(
            ["gemini", "-m", GEMINI_MODEL, "-y"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=GEMINI_TIMEOUT,
        )
        output = (result.stdout or "") + (result.stderr or "")
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT: Gemini did not respond within {GEMINI_TIMEOUT}s"
    except FileNotFoundError:
        return False, "ERROR: 'gemini' CLI not found. Install gemini-cli."


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def parse_review_response(raw: str) -> dict | None:
    """Extract structured JSON from Gemini's response."""
    # Strip markdown code fences around JSON blocks only
    cleaned = re.sub(r"```json\s*\n?", "", raw)
    cleaned = re.sub(r"\n?```", "", cleaned)

    # Try progressively shorter substrings from first { to last }
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end > start:
        candidate = cleaned[start : end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and "verdict" in parsed:
                return parsed
        except json.JSONDecodeError:
            pass

    # Fallback: regex for verdict + score (findings are lost, but at least
    # the user sees the verdict and knows to check the raw report)
    verdict_match = re.search(r'"verdict"\s*:\s*"(PASS|FIX|REWRITE)"', raw)
    score_match = re.search(r'"score"\s*:\s*(\d+)', raw)
    if verdict_match and score_match:
        return {
            "verdict": verdict_match.group(1),
            "score": int(score_match.group(1)),
            "summary": "Parsed from non-JSON response (findings may be missing)",
            "findings": [],
        }

    return None


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def format_report(slug: str, level: str, parsed: dict, raw: str) -> str:
    """Format the review result as a markdown report."""
    verdict = parsed.get("verdict", "UNKNOWN")
    score = parsed.get("score", 0)
    summary = parsed.get("summary", "")
    findings = parsed.get("findings", [])

    icon = {"PASS": "PASS", "FIX": "FIX", "REWRITE": "REWRITE"}.get(verdict, "???")

    lines = [
        f"# Plan Review: {slug}",
        "",
        f"- **Level**: {level.upper()}",
        f"- **Verdict**: {icon} ({score}/10)",
        f"- **Date**: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}",
        f"- **Model**: {GEMINI_MODEL}",
        "",
        "## Summary",
        "",
        summary,
        "",
    ]

    if findings:
        lines.append("## Findings")
        lines.append("")

        # Group by severity
        for severity in ("critical", "major", "minor"):
            sev_findings = [f for f in findings if f.get("severity") == severity]
            if not sev_findings:
                continue
            lines.append(f"### {severity.title()}")
            lines.append("")
            for f in sev_findings:
                cat = f.get("category", "?")
                loc = f.get("location", "?")
                issue = f.get("issue", "?")
                fix = f.get("fix", "")
                lines.append(f"- **[{cat}]** `{loc}`: {issue}")
                if fix:
                    lines.append(f"  - Fix: {fix}")
            lines.append("")

    lines.append("---")
    lines.append("*Generated by review_plan.py (issue #984)*")

    return "\n".join(lines)


def save_report(level: str, slug: str, report: str) -> Path:
    """Save report to the audit subdirectory under plans."""
    audit_dir = CURRICULUM_ROOT / "plans" / level / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    report_path = audit_dir / f"{slug}-plan-review.md"
    report_path.write_text(report, encoding="utf-8")
    return report_path


# ---------------------------------------------------------------------------
# Single plan review
# ---------------------------------------------------------------------------

def review_plan(level: str, slug: str, *, dry_run: bool = False) -> dict:
    """Review a single plan. Returns result dict with verdict/score/path."""
    plan = load_plan(level, slug)
    if plan is None:
        return {"slug": slug, "error": f"Plan not found: plans/{level}/{slug}.yaml"}

    prompt = build_review_prompt(plan, level)

    if dry_run:
        print(f"\n{'=' * 70}")
        print(f"DRY RUN: {slug} ({len(prompt)} chars)")
        print(f"{'=' * 70}")
        print(prompt[:2000])
        if len(prompt) > 2000:
            print(f"\n... [{len(prompt) - 2000} more chars] ...")
        return {"slug": slug, "verdict": "DRY_RUN", "prompt_chars": len(prompt)}

    print(f"  Reviewing {slug}...", end=" ", flush=True)
    ok, raw = call_gemini(prompt)

    if not ok:
        print("ERROR")
        return {"slug": slug, "error": f"Gemini call failed: {raw[:200]}"}

    parsed = parse_review_response(raw)
    if parsed is None:
        print("PARSE_ERROR")
        # Save raw response for debugging
        err_path = save_report(
            level, slug,
            f"# Plan Review: {slug}\n\n**ERROR**: Could not parse Gemini response.\n\n"
            f"## Raw Response\n\n```\n{raw}\n```\n",
        )
        return {"slug": slug, "error": "Could not parse response", "path": str(err_path)}

    report = format_report(slug, level, parsed, raw)
    report_path = save_report(level, slug, report)

    verdict = parsed.get("verdict", "?")
    score = parsed.get("score", 0)
    print(f"{verdict} ({score}/10)")

    return {
        "slug": slug,
        "verdict": verdict,
        "score": score,
        "findings": len(parsed.get("findings", [])),
        "path": str(report_path),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="LLM adversarial plan review via Gemini"
    )
    parser.add_argument("level", help="Level to review (e.g., a1)")
    parser.add_argument("slug", nargs="?", help="Module slug (omit for --all)")
    parser.add_argument("--all", action="store_true", help="Review all plans for level")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show prompt without calling Gemini"
    )
    args = parser.parse_args()

    if not args.slug and not args.all:
        parser.error("Provide a slug or use --all")

    if args.slug and args.all:
        parser.error("Cannot specify both a slug and --all")

    if args.all:
        slugs = get_all_slugs(args.level)
        if not slugs:
            print(f"No modules found for level {args.level}")
            sys.exit(1)

        print(f"\n{'=' * 70}")
        print(f"  Adversarial Plan Review — {args.level.upper()} ({len(slugs)} plans)")
        print(f"{'=' * 70}\n")

        results = []
        for slug in slugs:
            plan_path = CURRICULUM_ROOT / "plans" / args.level / f"{slug}.yaml"
            if not plan_path.exists():
                print(f"  {slug}: SKIP (no plan file)")
                continue
            result = review_plan(args.level, slug, dry_run=args.dry_run)
            results.append(result)

        # Summary
        if not args.dry_run:
            print(f"\n{'=' * 70}")
            verdicts = {}
            for r in results:
                v = r.get("verdict", r.get("error", "ERROR"))
                verdicts[v] = verdicts.get(v, 0) + 1
            for v, count in sorted(verdicts.items()):
                print(f"  {v}: {count}")
            print(f"  Total: {len(results)}")
            print(f"{'=' * 70}\n")
    else:
        result = review_plan(args.level, args.slug, dry_run=args.dry_run)
        if "error" in result:
            print(f"ERROR: {result['error']}")
            sys.exit(1)


if __name__ == "__main__":
    main()
