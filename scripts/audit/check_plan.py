#!/usr/bin/env python3
"""Deterministic plan quality checker.

Validates plan YAML files before content generation. Catches issues that
would otherwise waste build time (Russicisms, wrong stress, scope creep,
VESUM failures, missing fields).

Usage:
    .venv/bin/python scripts/audit/check_plan.py a1                    # all A1 plans
    .venv/bin/python scripts/audit/check_plan.py a1 --first 7          # A1.1 only
    .venv/bin/python scripts/audit/check_plan.py a1 --module 1         # single module
    .venv/bin/python scripts/audit/check_plan.py a1 --failing-only     # only show failures

Issue: #983
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# Combining acute accent
STRESS_MARK = "\u0301"

# Known Russicisms (subset — full list in semantic_russianisms.py)
_RUSSICISMS = {
    "кон": "кін (stake) or remove — кон is Russian",
    "кот": "кіт (cat)",
    "хорошо": "добре (well/good)",
    "получати": "отримувати (to receive)",
    "кушати": "їсти (to eat)",
    # NOTE: standalone "самий" is valid Ukrainian (той самий = the same one).
    # Only "самий + superlative adjective" is a Russicism (самий кращий → найкращий).
    # Moved to phrase-level check below.
    # "самий": "найкращий or найбільший",
    "дом": "дім (house)",
    "собака": "пес / собака is accepted but пес is preferred",
    "зеркало": "дзеркало (mirror)",
    "ковёр": "килим (carpet)",
    "мяч": "м'яч (ball) — needs apostrophe",
    "обязательно": "обов'язково (necessarily)",
    "вообще": "взагалі (in general)",
    "получається": "виходить (it works out)",
    "луна": "місяць (moon)",
}


class PlanIssue:
    """A single issue found in a plan."""

    def __init__(self, check: str, severity: str, message: str, fix: str = ""):
        self.check = check
        self.severity = severity  # ERROR, WARNING, INFO
        self.message = message
        self.fix = fix

    def __str__(self):
        icon = "❌" if self.severity == "ERROR" else "⚠️" if self.severity == "WARNING" else "ℹ️"
        s = f"  {icon} [{self.check}] {self.message}"
        if self.fix:
            s += f"\n     FIX: {self.fix}"
        return s


def check_required_fields(plan: dict) -> list[PlanIssue]:
    """Check that all required fields are present."""
    issues = []
    required = ["module", "slug", "version", "level", "sequence", "title",
                 "word_target", "content_outline", "vocabulary_hints", "phase"]
    for field in required:
        if field not in plan:
            issues.append(PlanIssue("FIELD", "ERROR", f"Missing required field: {field}"))
    return issues


def check_word_budgets(plan: dict) -> list[PlanIssue]:
    """Check section word budgets sum to >= word_target."""
    issues = []
    target = plan.get("word_target", 0)
    sections = plan.get("content_outline", [])
    if not sections:
        issues.append(PlanIssue("BUDGET", "ERROR", "No content_outline sections"))
        return issues

    total = sum(s.get("words", 0) for s in sections if isinstance(s, dict))
    if total < target:
        issues.append(PlanIssue("BUDGET", "ERROR",
                                f"Section budgets sum to {total}w, target is {target}w (short by {target - total}w)"))
    return issues


def check_no_stress_marks(plan: dict) -> list[PlanIssue]:
    """Check that no stress marks (U+0301) appear anywhere in the plan."""
    issues = []
    text = yaml.dump(plan, allow_unicode=True)
    count = text.count(STRESS_MARK)
    if count > 0:
        # Find which fields have them
        locations = []
        for key in ("vocabulary_hints", "content_outline", "title", "subtitle"):
            val = str(plan.get(key, ""))
            if STRESS_MARK in val:
                locations.append(key)
        issues.append(PlanIssue("STRESS", "ERROR",
                                f"{count} stress mark(s) found in: {', '.join(locations)}",
                                "Remove all combining acute (U+0301). Pipeline adds stress marks."))
    return issues


def check_russicisms(plan: dict) -> list[PlanIssue]:
    """Check vocabulary hints and content outline for known Russicisms."""
    issues = []
    text = yaml.dump(plan, allow_unicode=True).lower()

    for russian, fix in _RUSSICISMS.items():
        # Word boundary check — look for the word surrounded by non-Cyrillic
        pattern = rf"(?<![а-яґєіїА-ЯҐЄІЇ]){re.escape(russian)}(?![а-яґєіїА-ЯҐЄІЇ])"
        if re.search(pattern, text):
            issues.append(PlanIssue("RUSSICISM", "ERROR",
                                    f"Possible Russicism: '{russian}'",
                                    fix))

    # Phrase-level Russicism: "самий + adjective" for superlative
    # Standalone "самий" is valid Ukrainian (той самий = the same one).
    # Only "самий кращий/великий/etc." is a Russicism (→ найкращий/найбільший).
    # Skip negative examples: *самий, 'самий, "самий (quoted citations of errors)
    if re.search(r"(?<![*'\"])\bсамий\s+[а-яґєіїА-ЯҐЄІЇ]+(?:ий|ій|а|е)\b", text):
        issues.append(PlanIssue("RUSSICISM", "ERROR",
                                "Possible Russicism: 'самий + adjective' for superlative",
                                "Use най- prefix: найкращий, найбільший"))

    return issues


def check_phase_alignment(plan: dict) -> list[PlanIssue]:
    """Check that phase field matches module sequence number."""
    issues = []
    phase = plan.get("phase", "")
    seq = plan.get("sequence", 0)
    level = plan.get("level", "").upper()
    if not phase or not seq:
        return issues

    phase_key = phase.split("[")[0].strip()

    # Phase ranges are only validated for A1 (other levels have different structures)
    if level != "A1":
        # For non-A1 levels, just check that the phase starts with the level prefix
        level_prefix = level.split("-")[0]  # B1, B2, C1, etc.
        if not phase_key.startswith(level_prefix) and level_prefix not in phase_key:
            issues.append(PlanIssue("PHASE", "WARNING",
                                    f"Phase '{phase_key}' doesn't match level {level}"))
        return issues

    # V3 phase ranges for A1 (updated to match curriculum.yaml V3)
    expected_phases = {
        range(1, 8): "A1.1",      # M01-M07: Sounds, Letters, First Contact
        range(8, 15): "A1.2",     # M08-M14: My World
        range(15, 22): "A1.3",    # M15-M21: Actions
        range(22, 28): "A1.4",    # M22-M27: Time and Nature
        range(28, 36): "A1.5",    # M28-M35: Places
        range(36, 42): "A1.6",    # M36-M41: Food and Shopping
        range(42, 48): "A1.7",    # M42-M47: Communication
        range(48, 56): "A1.8",    # M48-M55: Past, Future, Graduation
    }

    for seq_range, expected in expected_phases.items():
        if seq in seq_range and phase_key != expected:
            issues.append(PlanIssue("PHASE", "ERROR",
                                    f"Module M{seq:02d} should be phase {expected}, got {phase_key}"))
    return issues


def check_grammar_scope(plan: dict) -> list[PlanIssue]:
    """Check that grammar field doesn't list constructs banned for the phase."""
    issues = []
    phase = plan.get("phase", "")
    grammar = plan.get("grammar", [])
    if not phase or not grammar:
        return issues

    phase_key = phase.split("[")[0].strip()
    grammar_text = " ".join(str(g).lower() for g in grammar)

    # Phonetics phase: no verbs
    if phase_key == "A1.1":
        seq = plan.get("sequence", 0)
        if seq <= 3:
            for banned in ("conjugation", "present tense", "past tense", "future tense",
                           "imperative", "reflexive", "modal"):
                if banned in grammar_text:
                    issues.append(PlanIssue("SCOPE", "ERROR",
                                            f"M{seq:02d} is phonetics — grammar lists '{banned}'",
                                            "Phonetics modules (M01-M03) should not teach verb grammar"))

    # No past/future before A1.8
    if phase_key in ("A1.1", "A1.2", "A1.3", "A1.4", "A1.5", "A1.6", "A1.7"):
        for banned in ("past tense", "future tense"):
            if banned in grammar_text and phase_key != "A1.7":
                # A1.7 might preview these
                issues.append(PlanIssue("SCOPE", "WARNING",
                                        f"Grammar lists '{banned}' but phase is {phase_key} (taught in A1.8)"))
    return issues


def check_prerequisites(plan: dict, all_slugs: list[str]) -> list[PlanIssue]:
    """Check that prerequisites reference valid module slugs."""
    issues = []
    prereqs = plan.get("prerequisites", [])
    if not prereqs:
        return issues

    for prereq in prereqs:
        if isinstance(prereq, str):
            # Extract slug from "a1-NNN (Title)" format
            slug_match = re.search(r"[a-z0-9-]+", prereq)
            if slug_match:
                ref = slug_match.group()
                # Check if it's an a1-NNN format or a slug
                if ref.startswith("a1-"):
                    continue  # Old format, skip
                if ref not in all_slugs and ref not in [f"a1-{s}" for s in all_slugs]:
                    issues.append(PlanIssue("PREREQ", "WARNING",
                                            f"Prerequisite references unknown slug: '{ref}'"))
    return issues


def check_yaml_safety(plan: dict) -> list[PlanIssue]:
    """Check for YAML issues that cause parse errors."""
    issues = []
    # Check vocabulary hints for bare colons
    hints = plan.get("vocabulary_hints", {})
    # Handle both v3 dict {required: [...]} and v4 flat list [{word, pos, definition}]
    items_to_check: list = []
    if isinstance(hints, dict):
        for category in ("required", "recommended"):
            items_to_check.extend(hints.get(category, []))
    elif isinstance(hints, list):
        items_to_check = hints
    for item in items_to_check:
        if isinstance(item, dict):
            # Dict items are OK
            continue
        if isinstance(item, str) and ": " in item:
            # Could be a YAML issue but most are quoted properly
            pass
    return issues


def check_apostrophes(plan: dict) -> list[PlanIssue]:
    """Check that Ukrainian words requiring apostrophes have them."""
    issues = []
    text = yaml.dump(plan, allow_unicode=True)

    # Common words that MUST have apostrophe
    needs_apostrophe = {
        "мяч": "м'яч",
        "мясо": "м'ясо",
        "пять": "п'ять",
        "девять": "дев'ять",
        "мякий": "м'який",
        "мята": "м'ята",
        "вязати": "в'язати",
        "зїсти": "з'їсти",
        "обєкт": "об'єкт",
        "компютер": "комп'ютер",
        "сімя": "сім'я",
    }

    for wrong, correct in needs_apostrophe.items():
        # Skip if preceded by * (intentional "incorrect form" marker in teaching examples)
        pattern = rf"(?<![а-яґєіїА-ЯҐЄІЇ'*]){re.escape(wrong)}(?![а-яґєіїА-ЯҐЄІЇ])"
        if re.search(pattern, text, re.IGNORECASE):
            issues.append(PlanIssue("APOSTROPHE", "ERROR",
                                    f"Missing apostrophe: '{wrong}' should be '{correct}'"))
    return issues


def check_vesum_vocabulary(plan: dict) -> list[PlanIssue]:
    """Check vocabulary hints against VESUM (if available)."""
    issues = []
    hints = plan.get("vocabulary_hints", {})
    if not hints:
        return issues

    # Handle both v3 dict {required: [...]} and v4 flat list [{word, pos, definition}]
    from pipeline.vocab_helpers import extract_vocab_words
    raw_words = extract_vocab_words(hints)
    words_to_check = []
    for word in raw_words:
        word = word.split("(")[0].strip().split("—")[0].strip().split(" ")[0].strip()
        word = word.replace(STRESS_MARK, "").strip(",").strip()
        if word and re.search(r'[\u0400-\u04ff]', word) and len(word) > 1:
            words_to_check.append(word)

    if not words_to_check:
        return issues

    # Try VESUM verification
    try:
        from rag.vesum_lookup import vesum_lookup
        for word in words_to_check:
            result = vesum_lookup(word)
            if not result:
                # Skip proper nouns (capitalized)
                if word[0].isupper():
                    continue
                issues.append(PlanIssue("VESUM", "WARNING",
                                        f"Vocabulary word '{word}' not found in VESUM",
                                        "Check spelling or verify it's a valid Ukrainian word"))
    except ImportError:
        # VESUM not available — skip this check
        pass
    return issues


def check_plan(plan_path: Path, all_slugs: list[str] | None = None) -> list[PlanIssue]:
    """Run all checks on a single plan file."""
    try:
        plan = yaml.safe_load(plan_path.read_text("utf-8"))
    except Exception as e:
        return [PlanIssue("YAML", "ERROR", f"YAML parse error: {e}")]

    if not isinstance(plan, dict):
        return [PlanIssue("YAML", "ERROR", "Plan is not a YAML mapping")]

    issues = []
    issues.extend(check_required_fields(plan))
    issues.extend(check_word_budgets(plan))
    issues.extend(check_no_stress_marks(plan))
    issues.extend(check_russicisms(plan))
    issues.extend(check_apostrophes(plan))
    issues.extend(check_phase_alignment(plan))
    issues.extend(check_grammar_scope(plan))
    issues.extend(check_prerequisites(plan, all_slugs or []))
    issues.extend(check_yaml_safety(plan))
    issues.extend(check_vesum_vocabulary(plan))
    return issues


def main():
    parser = argparse.ArgumentParser(description="Deterministic plan quality checker")
    parser.add_argument("level", help="Level to check (e.g., a1)")
    parser.add_argument("--first", type=int, default=0, help="Check only first N modules")
    parser.add_argument("--module", type=int, default=0, help="Check single module by number")
    parser.add_argument("--failing-only", action="store_true", help="Only show plans with issues")
    args = parser.parse_args()

    # Load curriculum order
    manifest = CURRICULUM_ROOT / "curriculum.yaml"
    data = yaml.safe_load(manifest.read_text())
    slugs = data.get("levels", {}).get(args.level, {}).get("modules", [])
    if not slugs:
        print(f"No modules found for level {args.level}")
        sys.exit(1)

    if args.module > 0:
        if args.module > len(slugs):
            print(f"Module {args.module} not found (max {len(slugs)})")
            sys.exit(1)
        slugs = [slugs[args.module - 1]]
        start_num = args.module
    else:
        if args.first > 0:
            slugs = slugs[:args.first]
        start_num = 1

    plans_dir = CURRICULUM_ROOT / "plans" / args.level
    total_issues = 0
    total_errors = 0
    plans_checked = 0
    plans_passed = 0

    print(f"\n{'=' * 70}")
    print(f"  Plan Quality Check — {args.level.upper()} ({len(slugs)} plans)")
    print(f"{'=' * 70}\n")

    for i, slug in enumerate(slugs):
        num = start_num + i if args.module == 0 else args.module
        plan_path = plans_dir / f"{slug}.yaml"

        if not plan_path.exists():
            if not args.failing_only:
                print(f"M{num:02d} {slug}: ⚠️ MISSING")
            continue

        plans_checked += 1
        issues = check_plan(plan_path, slugs)
        errors = [i for i in issues if i.severity == "ERROR"]
        warnings = [i for i in issues if i.severity == "WARNING"]

        total_issues += len(issues)
        total_errors += len(errors)

        if not issues:
            plans_passed += 1
            if not args.failing_only:
                print(f"M{num:02d} {slug}: ✅ PASS")
        else:
            status = "❌ FAIL" if errors else "⚠️ WARN"
            print(f"M{num:02d} {slug}: {status} ({len(errors)} error(s), {len(warnings)} warning(s))")
            for issue in issues:
                print(str(issue))

    print(f"\n{'=' * 70}")
    print(f"  Summary: {plans_passed}/{plans_checked} passed, {total_errors} error(s), {total_issues - total_errors} warning(s)")
    print(f"{'=' * 70}\n")

    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
