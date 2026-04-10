#!/usr/bin/env python3
"""validate_direct.py — Schema + pedagogical validator for l2-uk-direct modules.

Usage:
  .venv/bin/python scripts/validate_direct.py curriculum/l2-uk-direct/a1/abetka.yaml
  .venv/bin/python scripts/validate_direct.py --all
  .venv/bin/python scripts/validate_direct.py --level a1

Exit codes:
  0 = all checks passed
  1 = validation errors found
  2 = usage / file-not-found error
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

# ── Constants ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "curriculum/l2-uk-direct/manifest.yaml"

PRE_LITERACY_MODULES = {"abetka", "sklad"}
PRE_LITERACY_ACTIVITY_TYPES = {"watch_and_repeat", "classify", "image_to_letter"}
ALL_ACTIVITY_TYPES = {
    # pre-literacy
    "watch_and_repeat", "classify", "image_to_letter",
    # post-literacy
    "true_false", "build_sentence", "match_sound", "pattern_drill",
    "riddle", "tongue_twister", "reading", "proverb_drill",
}
VALID_MODULE_TYPES = {"script_foundation", "vocabulary", "grammar", "checkpoint", "communicative", "reading", "writing", "practice", "review"}
VALID_LEVELS = {"a1", "a2", "b1", "b2"}

# Full Ukrainian alphabet (33 uppercase letters)
UKRAINIAN_ALPHABET = set("АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ")

YOUTUBE_RE = re.compile(
    r"^https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}$"
)
# Matches Latin a-z / A-Z — used to flag non-Ukrainian content
LATIN_RE = re.compile(r"[a-zA-Z]")


# ── Result collector ───────────────────────────────────────────────────────────
class ValidationResult:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.infos: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def info(self, msg: str) -> None:
        self.infos.append(msg)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def print_report(self) -> None:
        status = "✅ PASS" if self.passed else "❌ FAIL"
        print(f"\n{status}  {self.path}")
        print(f"  {'─' * 60}")
        for e in self.errors:
            print(f"  ✗ ERROR:   {e}")
        for w in self.warnings:
            print(f"  ⚠ WARNING: {w}")
        for i in self.infos:
            print(f"  ℹ INFO:    {i}")
        if not self.errors and not self.warnings and not self.infos:
            print("  All checks passed.")


# ── Individual checkers ───────────────────────────────────────────────────────
def check_header(data: dict, result: ValidationResult) -> None:
    for field in ["module", "track", "level", "type", "title"]:
        if field not in data:
            result.error(f"Missing required top-level field: '{field}'")

    if data.get("track") != "l2-uk-direct":
        result.error(f"track must be 'l2-uk-direct', got '{data.get('track')}'")

    if data.get("level") not in VALID_LEVELS:
        result.error(f"level must be in {VALID_LEVELS}, got '{data.get('level')}'")

    if data.get("type") not in VALID_MODULE_TYPES:
        result.error(
            f"type must be in {VALID_MODULE_TYPES}, got '{data.get('type')}'"
        )


def check_video_url(url: Any, context: str, result: ValidationResult) -> None:
    if url is None:
        return  # null is explicitly allowed (not yet sourced)
    if not isinstance(url, str):
        result.error(f"{context}: must be a string or null, got {type(url).__name__}")
        return
    if not YOUTUBE_RE.match(url):
        result.error(
            f"{context}: invalid YouTube URL.\n"
            f"    Expected: https://www.youtube.com/watch?v=XXXXXXXXXXX (11 chars)\n"
            f"    Got:      {url}"
        )


def check_letters(data: dict, result: ValidationResult) -> None:
    letters = data.get("letters", [])
    if not letters:
        result.warn("No 'letters' section found in script_foundation module")
        return

    key_words_seen: set[str] = set()
    emojis_seen: dict[str, str] = {}

    for i, entry in enumerate(letters):
        ctx = f"letters[{i}] ({entry.get('upper', '?')})"

        for field in ["upper", "lower", "sound_type", "key_word", "emoji", "pronunciation_video"]:
            if field not in entry:
                result.error(f"{ctx}: missing required field '{field}'")

        kw = entry.get("key_word", "")
        if kw and kw in key_words_seen:
            result.warn(f"{ctx}: duplicate key_word '{kw}'")
        if kw:
            key_words_seen.add(kw)

        em = entry.get("emoji", "")
        if em and em in emojis_seen:
            result.error(
                f"{ctx}: duplicate emoji '{em}' — already used by letter {emojis_seen[em]}"
            )
        if em:
            emojis_seen[em] = entry.get("upper", "?")

        check_video_url(
            entry.get("pronunciation_video"),
            f"{ctx}.pronunciation_video",
            result,
        )

    null_images = sum(1 for e in letters if e.get("image_url") is None)
    total = len(letters)
    result.info(f"images_sourced: {total - null_images}/{total}")


def check_vocabulary(data: dict, result: ValidationResult) -> None:
    vocab = data.get("vocabulary", [])
    if not vocab:
        return

    # Detect format: grouped (category + items) vs flat (word + examples)
    if vocab and isinstance(vocab[0], dict) and "items" in vocab[0]:
        # Grouped format: [{category: ..., items: [{word, emoji, sentence}, ...]}, ...]
        total_words = 0
        for i, group in enumerate(vocab):
            cat = group.get("category", f"group_{i}")
            items = group.get("items", [])
            if not items:
                result.warn(f"vocabulary group '{cat}': empty items list")
            for j, item in enumerate(items):
                ctx = f"vocabulary/{cat}[{j}]"
                if "word" not in item and "phrase" not in item and "infinitive" not in item:
                    result.error(f"{ctx}: missing 'word', 'phrase', or 'infinitive'")
                total_words += 1
        result.info(f"vocabulary: {total_words} words across {len(vocab)} categories")
    else:
        # Flat format: [{word, pronunciation_video, category, examples}, ...]
        for i, entry in enumerate(vocab):
            ctx = f"vocabulary[{i}] ({entry.get('word', '?')})"

            for field in ["word", "pronunciation_video", "category", "examples"]:
                if field not in entry:
                    result.error(f"{ctx}: missing required field '{field}'")

            examples = entry.get("examples", [])
            if len(examples) < 2:
                result.error(f"{ctx}: must have ≥ 2 examples, found {len(examples)}")

            for j, ex in enumerate(examples):
                if LATIN_RE.search(ex):
                    result.warn(f"{ctx}.examples[{j}]: possible non-Ukrainian text: '{ex[:60]}'")

            check_video_url(
                entry.get("pronunciation_video"),
                f"{ctx}.pronunciation_video",
                result,
            )


def check_activities(data: dict, result: ValidationResult) -> None:
    activities = data.get("activities")
    if activities is None:
        result.error("Missing 'activities' section")
        return

    module_name = data.get("module", "")
    is_pre_literacy = module_name in PRE_LITERACY_MODULES

    for i, act in enumerate(activities):
        ctx = f"activities[{i}]"
        act_type = act.get("type")

        if act_type not in ALL_ACTIVITY_TYPES:
            result.error(f"{ctx}: unknown activity type '{act_type}'")
            continue

        if is_pre_literacy and act_type not in PRE_LITERACY_ACTIVITY_TYPES:
            result.error(
                f"{ctx}: type '{act_type}' is NOT allowed in pre-literacy "
                f"module '{module_name}'. Allowed: {sorted(PRE_LITERACY_ACTIVITY_TYPES)}"
            )

        _dispatch_activity_check(act, act_type, ctx, result)


def _check_watch_and_repeat(act: dict, ctx: str, result: ValidationResult) -> None:
    items = act.get("items", [])
    if not items:
        result.error(f"{ctx}: watch_and_repeat must have at least 1 item")
    for j, item in enumerate(items):
        check_video_url(item.get("video"), f"{ctx}.items[{j}].video", result)


def _check_image_to_letter(act: dict, ctx: str, result: ValidationResult) -> None:
    items = act.get("items", [])
    if len(items) < 5:
        result.warn(f"{ctx}: only {len(items)} items (recommend ≥ 10)")
    emojis_in_activity: set[str] = set()
    for j, item in enumerate(items):
        em = item.get("emoji", "")
        if not item.get("emoji"):
            result.error(f"{ctx}.items[{j}]: missing 'emoji'")
        if not item.get("answer"):
            result.error(f"{ctx}.items[{j}]: missing 'answer'")
        if not item.get("distractors"):
            result.error(f"{ctx}.items[{j}]: missing 'distractors'")
        if em and em in emojis_in_activity:
            result.error(f"{ctx}.items[{j}]: duplicate emoji '{em}' in image_to_letter")
        if em:
            emojis_in_activity.add(em)


def _check_true_false(act: dict, ctx: str, result: ValidationResult) -> None:
    items = act.get("items", [])
    if len(items) < 3:
        result.error(f"{ctx}: true_false must have ≥ 3 items, found {len(items)}")
    for j, item in enumerate(items):
        if "statement" not in item:
            result.error(f"{ctx}.items[{j}]: missing 'statement'")
        if "answer" not in item:
            result.error(f"{ctx}.items[{j}]: missing 'answer'")
        elif not isinstance(item["answer"], bool):
            result.error(
                f"{ctx}.items[{j}]: 'answer' must be boolean (true/false), "
                f"got {type(item['answer']).__name__}"
            )
        stmt = item.get("statement", "")
        if stmt and LATIN_RE.search(stmt):
            result.warn(f"{ctx}.items[{j}]: possible non-Ukrainian text: '{stmt[:60]}'")


def _check_pattern_drill(act: dict, ctx: str, result: ValidationResult) -> None:
    if "prompt" not in act:
        result.error(f"{ctx}: pattern_drill missing 'prompt'")
    items = act.get("items", [])
    if len(items) < 3:
        result.warn(f"{ctx}: only {len(items)} items (recommend ≥ 5)")
    for j, item in enumerate(items):
        if "given" not in item:
            result.error(f"{ctx}.items[{j}]: missing 'given'")
        if "answer" not in item:
            result.error(f"{ctx}.items[{j}]: missing 'answer'")


def _check_build_sentence(act: dict, ctx: str, result: ValidationResult) -> None:
    sentences = act.get("sentences", [])
    if len(sentences) < 3:
        result.warn(f"{ctx}: only {len(sentences)} sentences (recommend ≥ 5)")
    for j, s in enumerate(sentences):
        if "words" not in s:
            result.error(f"{ctx}.sentences[{j}]: missing 'words'")
        if "correct" not in s:
            result.error(f"{ctx}.sentences[{j}]: missing 'correct'")


def _check_reading(act: dict, ctx: str, result: ValidationResult) -> None:
    has_text = bool(act.get("text"))
    has_items = bool(act.get("items")) or bool(act.get("sentences"))
    if not has_text and not has_items:
        result.error(f"{ctx}: reading missing 'text' or 'items'")
    text = act.get("text", "")
    if text and LATIN_RE.search(text):
        result.warn(f"{ctx}: reading text may contain non-Ukrainian characters")
    if has_items:
        for item in (act.get("items") or act.get("sentences") or []):
            item_text = item.get("text", "") if isinstance(item, dict) else ""
            if item_text and LATIN_RE.search(item_text):
                result.warn(f"{ctx}: reading item may contain non-Ukrainian characters")
    questions = act.get("questions", [])
    if not questions and not act.get("true_false_items") and not has_items:
        result.warn(f"{ctx}: reading has no comprehension questions or true_false_items")


# Dispatch table mapping activity type to checker function
_ACTIVITY_CHECKERS: dict[str, Any] = {
    "watch_and_repeat": _check_watch_and_repeat,
    "image_to_letter": _check_image_to_letter,
    "true_false": _check_true_false,
    "pattern_drill": _check_pattern_drill,
    "build_sentence": _check_build_sentence,
    "reading": _check_reading,
}


def _dispatch_activity_check(
    act: dict, act_type: str, ctx: str, result: ValidationResult
) -> None:
    checker = _ACTIVITY_CHECKERS.get(act_type)
    if checker:
        checker(act, ctx, result)
        return

    if act_type == "classify":
        if not act.get("categories"):
            result.error(f"{ctx}: classify must have 'categories'")
    elif act_type == "riddle":
        if not act.get("answer"):
            result.error(f"{ctx}: riddle missing 'answer'")
        if not act.get("clues"):
            result.error(f"{ctx}: riddle missing 'clues'")
    elif act_type == "tongue_twister":
        if not act.get("text"):
            result.error(f"{ctx}: tongue_twister missing 'text'")
    elif act_type == "proverb_drill" and not (
        act.get("proverb") or act.get("items")
    ):
        result.error(f"{ctx}: proverb_drill missing 'proverb' or 'items'")


# ── File-level validator ──────────────────────────────────────────────────────
def count_vocab_items(data: dict) -> int:
    """Count total vocabulary items in a module."""
    vocab = data.get("vocabulary", [])
    if not vocab:
        return 0
    if isinstance(vocab[0], dict) and "items" in vocab[0]:
        return sum(len(g.get("items", [])) for g in vocab)
    return len(vocab)


def validate_file(yaml_path: Path, vocab_target: int = 0) -> ValidationResult:
    result = ValidationResult(yaml_path)

    if not yaml_path.exists():
        result.error(f"File not found: {yaml_path}")
        return result

    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        result.error(f"YAML parse error: {e}")
        return result

    if not isinstance(data, dict):
        result.error("YAML root must be a mapping (dict), got something else")
        return result

    check_header(data, result)

    module_type = data.get("type")
    if module_type == "script_foundation":
        check_letters(data, result)
    if module_type in ("vocabulary", "grammar", "communicative", "reading", "writing"):
        check_vocabulary(data, result)

    check_activities(data, result)

    # Vocabulary target check
    if vocab_target > 0:
        actual = count_vocab_items(data)
        if actual < vocab_target:
            result.warn(f"Vocabulary below target: {actual}/{vocab_target} words")
        else:
            result.info(f"Vocabulary meets target: {actual}/{vocab_target} words")

    return result


# ── Alphabet completeness check ──────────────────────────────────────────────
def check_alphabet_completeness(level: str = "a1") -> tuple[set[str], set[str]]:
    """Check that all script_foundation modules together cover the full alphabet.

    Returns (taught, missing) where both are sets of uppercase letters.
    """
    if not MANIFEST_PATH.exists():
        return set(), UKRAINIAN_ALPHABET

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    taught: set[str] = set()
    for slug in manifest.get("levels", {}).get(level, {}).get("sequence", []):
        p = REPO_ROOT / f"curriculum/l2-uk-direct/{level}/{slug}.yaml"
        if not p.exists():
            continue
        with open(p, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data.get("type") != "script_foundation":
            continue
        for letter in data.get("letters", []):
            taught.add(letter.get("upper", ""))
    taught.discard("")
    missing = UKRAINIAN_ALPHABET - taught
    return taught, missing


# ── Manifest helpers ──────────────────────────────────────────────────────────
def find_modules_in_manifest(level: str | None = None) -> list[Path]:
    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(2)

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    paths: list[Path] = []
    for lvl_name, lvl_data in manifest.get("levels", {}).items():
        if level and lvl_name != level:
            continue
        for slug in lvl_data.get("sequence", []):
            p = REPO_ROOT / f"curriculum/l2-uk-direct/{lvl_name}/{slug}.yaml"
            paths.append(p)
    return paths


# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate l2-uk-direct module YAML files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/validate_direct.py curriculum/l2-uk-direct/a1/abetka.yaml
  .venv/bin/python scripts/validate_direct.py --level a1
  .venv/bin/python scripts/validate_direct.py --all
""",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("path", nargs="?", type=Path, help="Single module YAML file")
    group.add_argument("--all", action="store_true", help="Validate all modules in manifest")
    group.add_argument("--level", metavar="LEVEL", help="Validate all modules at a level (e.g. a1)")
    args = parser.parse_args()

    if args.path:
        paths = [args.path]
    elif args.all:
        paths = find_modules_in_manifest()
    elif args.level:
        paths = find_modules_in_manifest(level=args.level)
    else:
        parser.print_help()
        sys.exit(2)

    results: list[ValidationResult] = []
    for p in paths:
        r = validate_file(p)
        r.print_report()
        results.append(r)

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n{'─' * 62}")
    print(f"Results: {passed}/{total} passed")

    # Alphabet completeness check when validating a full level
    if args.all or args.level:
        level = args.level or "a1"
        taught, missing = check_alphabet_completeness(level)
        if missing:
            print(f"\n  ✗ ALPHABET INCOMPLETE ({level}): {len(missing)} letters missing: {sorted(missing)}")
            sys.exit(1)
        else:
            print(f"\n  ✅ Alphabet complete ({level}): all {len(taught)} letters covered")

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
