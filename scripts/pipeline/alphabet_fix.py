"""Deterministic alphabet chart fixer — corrects Gemini's consistent
letter classification errors in content about the Ukrainian alphabet.

Gemini consistently confuses visually similar Cyrillic letters:
- В↔У in vowel lists (В is consonant, У is vowel)
- І↔Й in vowel/consonant lists (І is vowel, Й is consonant)
- Duplicate Й, missing І in alphabet listings

This script fixes these deterministically after content generation.
"""

from __future__ import annotations

import re
from pathlib import Path

# Correct classifications
VOWELS = "А, О, У, Е, И, І"
IOTATED = "Я, Ю, Є, Ї"
ALL_VOWELS = "А, О, У, Е, И, І, Я, Ю, Є, Ї"
CONSONANTS = "Б, В, Г, Ґ, Д, Ж, З, Й, К, Л, М, Н, П, Р, С, Т, Ф, Х, Ц, Ч, Ш, Щ"
ALPHABET = "А Б В Г Ґ Д Е Є Ж З И І Ї Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я"


def fix_alphabet_charts(content: str) -> tuple[str, list[str]]:
    """Fix known letter classification errors in content.

    Returns (fixed_content, list_of_fixes_applied).
    """
    fixes = []

    # Fix 1: Alphabet listing — ensure correct 33-letter order
    # Match any line that looks like a full alphabet listing (30+ Cyrillic letters)
    def fix_alphabet_line(match: re.Match) -> str:
        line = match.group(0)
        # Check if it has the common errors
        if "Й" in line and line.count("Й") > 1:
            fixes.append("Duplicate Й removed from alphabet listing")
        if "І" not in line and "Й" in line:
            fixes.append("Missing І restored in alphabet listing")
        # Replace with correct alphabet
        prefix = match.group(1) if match.lastindex else ""
        return f"{prefix}{ALPHABET}"

    # Match lines with 25+ Cyrillic capital letters (likely alphabet listings)
    content = re.sub(
        r"^([-*|>\s]*)([А-ЯҐЄІЇЁ][,\s]*){25,}$",
        fix_alphabet_line,
        content,
        flags=re.MULTILINE,
    )

    # Fix 2: Base vowel lists — replace В with У, Й with І
    def fix_vowel_list(match: re.Match) -> str:
        line = match.group(0)
        fixed = line
        if re.search(r"\bВ\b", fixed) and "У" not in fixed.split(":")[1] if ":" in fixed else True:
            fixed = re.sub(r"\bВ\b", "У", fixed, count=1)
            if fixed != line:
                fixes.append("В→У in vowel list (В is a consonant)")
        if re.search(r"\bЙ\b", fixed) and "І" not in fixed.split(":")[1] if ":" in fixed else True:
            fixed = re.sub(r"\bЙ\b", "І", fixed, count=1)
            if fixed != line:
                fixes.append("Й→І in vowel list (Й is a consonant)")
        return fixed

    # Match lines containing "Голосні" or "vowel" with a list of letters
    content = re.sub(
        r"^.*(?:Голосні|[Vv]owel|[Bb]ase).*?:.*[А-ЯҐЄІЇЁ].*$",
        fix_vowel_list,
        content,
        flags=re.MULTILINE,
    )

    # Fix 3: Consonant lists — replace І with Й
    def fix_consonant_list(match: re.Match) -> str:
        line = match.group(0)
        # Only fix if І appears in the consonant list AND Й is missing
        after_colon = line.split(":")[-1] if ":" in line else line
        if re.search(r"\bІ\b", after_colon) and not re.search(r"\bЙ\b", after_colon):
            fixed = line.replace(", І,", ", Й,").replace(", І ", ", Й ")
            if fixed != line:
                fixes.append("І→Й in consonant list (І is a vowel)")
                return fixed
        return line

    content = re.sub(
        r"^.*(?:Приголосні|[Cc]onsonant).*?:.*[А-ЯҐЄІЇЁ].*$",
        fix_consonant_list,
        content,
        flags=re.MULTILINE,
    )

    return content, fixes


def fix_file(path: Path) -> int:
    """Fix alphabet charts in a file. Returns number of fixes applied."""
    if not path.exists():
        return 0
    content = path.read_text("utf-8")
    fixed, fixes = fix_alphabet_charts(content)
    if fixes:
        path.write_text(fixed, "utf-8")
    return len(fixes)
