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
    {
        "word": "рушник",
        "russian_meanings": ["towel (generic)"],
        "ukrainian_meaning": "embroidered ritual towel",
        "replacement": None,  # context-dependent — just flag
        "replacement_translation": None,
    },
    {
        "word": "дурний",
        "russian_meanings": ["stupid", "idiot"],
        "ukrainian_meaning": "silly, foolish (milder connotation)",
        "replacement": None,  # flag only
        "replacement_translation": None,
    },
]


def scan_plan_for_russianisms(plan_path: Path) -> list[dict]:
    """Scan a plan's vocabulary_hints for semantic Russianisms.

    Returns list of findings: [{word, meaning_found, fix, line}]
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
    vocab = plan.get("vocabulary_hints", {})

    # vocabulary_hints can be a dict with categories or a flat list
    if isinstance(vocab, list):
        for item in vocab:
            if isinstance(item, str):
                _check_vocab_entry(item, "flat", findings)
    elif isinstance(vocab, dict):
        for category in ["required", "recommended", "sight_words"]:
            items = vocab.get(category, [])
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, str):
                    continue
                _check_vocab_entry(item, category, findings)

    return findings


def _check_vocab_entry(entry: str, category: str, findings: list[dict]) -> None:
    """Check a single vocabulary_hints entry for semantic Russianisms."""
    entry_lower = entry.lower()

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
        # Build replacement entry
        new = old
        # Replace the word
        new = re.sub(
            rf"\b{re.escape(finding['word'])}\b",
            finding["replacement"],
            new,
            count=1,
        )
        # Replace the translation if we have one
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
