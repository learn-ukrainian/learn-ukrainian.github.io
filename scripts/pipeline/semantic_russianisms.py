"""Semantic Russicism detector — catches words that exist in Ukrainian
but carry a Russian meaning when paired with certain translations.

Used by preflight to auto-fix plans before content generation.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

# Ensure scripts/ is on the path for pipeline_lib import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.core import log

# Word + Russian meaning → Ukrainian equivalent.
# These words ARE valid Ukrainian but mean something different than in Russian.
SEMANTIC_FALSE_FRIENDS: list[dict] = [
    # --- High-confidence entries (verified) ---
    {
        "word": "лук",
        "russian_meanings": ["onion", "цибуля", "onions"],
        "ukrainian_meaning": "bow (weapon)",
        "replacement": "цибуля",
        "replacement_translation": "onion",
    },
    {
        "word": "город",
        "russian_meanings": ["city", "місто", "town"],
        "ukrainian_meaning": "garden, vegetable patch",
        "replacement": "місто",
        "replacement_translation": "city",
    },
    {
        "word": "неділя",
        "russian_meanings": ["week", "тиждень"],
        "ukrainian_meaning": "Sunday",
        "replacement": "тиждень",
        "replacement_translation": "week",
    },
    # рушник removed: IS the standard Ukrainian word for towel (including generic use)
    # дурний removed: SUM defines it as "lacking intelligence" — "stupid" IS correct Ukrainian
    # --- Added from Gemini false-friends audit (2026-03-16) ---
    {
        "word": "річ",
        "russian_meanings": ["speech"],
        "ukrainian_meaning": "thing, item",
        "replacement": "промова",
        "replacement_translation": "speech",
    },
    {
        "word": "шар",
        "russian_meanings": ["ball", "sphere"],
        "ukrainian_meaning": "layer",
        "replacement": "куля",
        "replacement_translation": "ball",
    },
    {
        "word": "мешкати",
        "russian_meanings": ["to dawdle", "to delay", "dawdle", "delay"],
        "ukrainian_meaning": "to live, to dwell",
        "replacement": "баритися",
        "replacement_translation": "to delay",
    },
    # гадати removed: SUM meaning #3 IS ворожити; "to guess" = "I suppose" is valid Ukrainian
    {
        "word": "лічити",
        "russian_meanings": ["to treat", "to heal", "treatment"],
        "ukrainian_meaning": "to count",
        "replacement": "лікувати",
        "replacement_translation": "to treat (medically)",
    },
    {
        "word": "наглий",
        "russian_meanings": ["arrogant", "impudent", "insolent"],
        "ukrainian_meaning": "sudden, unexpected",
        "replacement": "зухвалий",
        "replacement_translation": "arrogant",
    },
    {
        "word": "лаяти",
        "russian_meanings": ["to bark", "bark", "barking"],
        "ukrainian_meaning": "to scold, to swear at",
        "replacement": "гавкати",
        "replacement_translation": "to bark",
    },
    {
        "word": "палиця",
        "russian_meanings": ["finger"],
        "ukrainian_meaning": "stick, cane",
        "replacement": "палець",
        "replacement_translation": "finger",
    },
    {
        "word": "сварка",
        "russian_meanings": ["welding"],
        "ukrainian_meaning": "quarrel, argument",
        "replacement": "зварювання",
        "replacement_translation": "welding",
    },
]


def scan_plan_for_russianisms(plan_path: Path) -> list[dict]:
    """Scan a plan's vocabulary_hints AND content_outline for semantic Russianisms.

    Returns list of findings: [{word, meaning_found, fix, category, original_entry, ...}]
    """
    if not plan_path.exists():
        return []

    try:
        with open(plan_path) as f:
            plan = yaml.safe_load(f)
    except Exception:
        return []

    if not isinstance(plan, dict):
        return []

    findings = []

    # 1. Scan vocabulary_hints
    vocab = plan.get("vocabulary_hints", {})
    if isinstance(vocab, list):
        for item in vocab:
            if isinstance(item, str):
                _check_vocab_entry(item, "vocabulary_hints", findings)
    elif isinstance(vocab, dict):
        for category in ["required", "recommended", "sight_words"]:
            items = vocab.get(category, [])
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, str):
                    continue
                _check_vocab_entry(item, f"vocabulary_hints.{category}", findings)

    # 2. Scan content_outline points
    outline = plan.get("content_outline", [])
    if isinstance(outline, list):
        for section in outline:
            if not isinstance(section, dict):
                continue
            section_name = section.get("section", "")
            points = section.get("points", [])
            if not isinstance(points, list):
                continue
            for point in points:
                if isinstance(point, str):
                    _check_vocab_entry(point, f"content_outline.{section_name}", findings)

    return findings


def scan_research_for_russianisms(research_path: Path) -> list[dict]:
    """Scan research output for semantic Russianisms.

    Returns list of findings (same format as plan scanner).
    """
    if not research_path or not research_path.exists():
        return []

    try:
        text = research_path.read_text("utf-8")
    except Exception:
        return []

    findings = []
    for line in text.split("\n"):
        _check_vocab_entry(line.strip(), "research", findings)
    return findings


# Negation patterns that indicate the line is WARNING about the false friend, not using it
_NEGATION_PATTERNS = re.compile(
    r"(?:not|NOT|≠|!=|не\b|НЕ\b|false.friend|trap|common.error|common.mistake|помилк)",
    re.IGNORECASE,
)


def _check_vocab_entry(entry: str, category: str, findings: list[dict]) -> None:
    """Check a single vocabulary_hints entry for semantic Russianisms."""
    entry_lower = entry.lower()

    # Skip lines that warn ABOUT the false friend (negation context)
    if category == "research" and _NEGATION_PATTERNS.search(entry):
        return

    for ff in SEMANTIC_FALSE_FRIENDS:
        word = ff["word"]
        # Check if this entry is about this word
        if not re.search(rf"\b{re.escape(word)}\b", entry_lower):
            continue

        # Check if the translation matches a Russian meaning
        for russian_meaning in ff["russian_meanings"]:
            if russian_meaning.lower() in entry_lower:
                findings.append({
                    "word": word,
                    "meaning_found": russian_meaning,
                    "ukrainian_meaning": ff["ukrainian_meaning"],
                    "replacement": ff["replacement"],
                    "replacement_translation": ff["replacement_translation"],
                    "category": category,
                    "original_entry": entry,
                })
                break


def fix_plan_russianisms(plan_path: Path, findings: list[dict]) -> int:
    """Auto-fix semantic Russianisms in a plan file.

    Returns number of fixes applied.
    """
    if not findings or not plan_path.exists():
        return 0

    content = plan_path.read_text("utf-8")
    fixes = 0

    for finding in findings:
        if not finding["replacement"]:
            log(f"  preflight-russicism: FLAG — '{finding['word']}' used as "
                f"'{finding['meaning_found']}' (Ukrainian meaning: {finding['ukrainian_meaning']}). "
                "Manual review needed.")
            continue

        old = finding["original_entry"]
        new = old
        category = finding.get("category", "")

        if category.startswith("content_outline") or category == "research":
            # In content_outline/research: the Ukrainian word is correct, the English
            # meaning is wrong. Do a direct text replacement in the file content —
            # find the word+meaning pattern and replace the meaning.
            # Use the simple pattern: word ... meaning (handles YAML wrapping)
            pattern = rf"(\b{re.escape(finding['word'])}\b[^)]*?){re.escape(finding['meaning_found'])}"
            replacement = rf"\g<1>{finding['ukrainian_meaning'].split(',')[0].strip()}"
            new_content = re.sub(pattern, replacement, content, count=1, flags=re.IGNORECASE)
            if new_content != content:
                content = new_content
                fixes += 1
                log(f"  preflight-russicism: FIXED — '{finding['word']}' meaning "
                    f"'{finding['meaning_found']}' → '{finding['ukrainian_meaning']}' "
                    f"in {category}")
            continue
        else:
            # In vocabulary_hints: replace the word AND the translation.
            new = re.sub(
                rf"\b{re.escape(finding['word'])}\b",
                finding["replacement"],
                new,
                count=1,
            )
            if finding["replacement_translation"] and finding["meaning_found"]:
                new = new.replace(
                    f"({finding['meaning_found']}",
                    f"({finding['replacement_translation']}",
                    1,
                )

        if old != new and old in content:
            content = content.replace(old, new, 1)
            fixes += 1
            log(f"  preflight-russicism: FIXED — '{finding['word']}' ({finding['meaning_found']}) "
                f"→ '{finding['replacement']}' ({finding['replacement_translation']})")

    if fixes > 0:
        plan_path.write_text(content, "utf-8")

    return fixes


def scan_and_fix_plan(plan_path: Path) -> tuple[list[dict], int]:
    """Scan a plan for semantic Russianisms and auto-fix what we can.

    Returns (findings, fixes_applied).
    """
    findings = scan_plan_for_russianisms(plan_path)
    if not findings:
        return [], 0
    fixes = fix_plan_russianisms(plan_path, findings)
    return findings, fixes
