"""
Euphony (Милозвучність) Checker

Detects violations of Ukrainian euphony rules in prose:
  Rule 1: Conjunction і/й alternation — й only between vowels
  Rule 2: Preposition у/в alternation — phonetic position
  Rule 3: Preposition з/із/зі alternation — consonant clusters

Severity: WARNING (non-blocking — edge cases exist in poetry,
quoted speech, and stylistic usage).

Track exemptions: OES, RUTH (historical Ruthenian texts).
Issue: #593
"""

import re
from typing import List, Dict

# Tracks where historical texts may violate modern euphony rules
EXEMPT_TRACKS = {"oes", "ruth"}

# Ukrainian vowels (lowercase)
_VOWELS = set("аеєиіїоуюя")

# Consonant clusters that trigger з → із/зі
_Z_CLUSTERS = {"зб", "зд", "зг", "зм", "зн", "зр", "зв", "зл"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_track(file_path: str) -> str | None:
    if not file_path:
        return None
    path = str(file_path)
    for track in ["istorio", "bio", "hist", "b2-pro", "c1-pro",
                  "oes", "ruth", "lit", "a1", "a2", "b1", "b2", "c1", "c2"]:
        if f"/{track}/" in path:
            return track
    return None


def _ends_with_vowel(word: str) -> bool:
    """Check if word ends with a Ukrainian vowel."""
    clean = word.rstrip(".,;:!?»\"')\u201d\u2019\u00bb")
    return bool(clean) and clean[-1].lower() in _VOWELS


def _starts_with_vowel(word: str) -> bool:
    """Check if word starts with a Ukrainian vowel."""
    clean = word.lstrip("«\"'(\u201c\u2018\u00ab")
    return bool(clean) and clean[0].lower() in _VOWELS


def _starts_with_consonant_cluster(word: str) -> bool:
    """Check if word starts with 2+ consonants (triggers в → у)."""
    clean = word.lstrip("«\"'(\u201c\u2018\u00ab").lower()
    if len(clean) < 2:
        return False
    return clean[0] not in _VOWELS and clean[1] not in _VOWELS


def _starts_with_v_or_f(word: str) -> bool:
    """Check if word starts with в or ф."""
    clean = word.lstrip("«\"'(\u201c\u2018\u00ab").lower()
    return bool(clean) and clean[0] in ("в", "ф")


def _starts_with_z_or_s(word: str) -> bool:
    """Check if word starts with з, с, ш, or ч."""
    clean = word.lstrip("«\"'(\u201c\u2018\u00ab").lower()
    return bool(clean) and clean[0] in ("з", "с", "ш", "ч")


def _starts_with_z_cluster(word: str) -> bool:
    """Check if word starts with a з-cluster (зб, зд, etc.)."""
    clean = word.lstrip("«\"'(\u201c\u2018\u00ab").lower()
    return len(clean) >= 2 and clean[:2] in _Z_CLUSTERS


_CYRILLIC = set("абвгґдеєжзиіїйклмнопрстуфхцчшщьюяАБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ")
_LATIN = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")


def _is_predominantly_latin(line: str) -> bool:
    """Return True if line has more Latin than Cyrillic characters.

    Skips lines that are English text — euphony rules don't apply there.
    """
    cyrillic = sum(1 for c in line if c in _CYRILLIC)
    latin = sum(1 for c in line if c in _LATIN)
    if cyrillic + latin == 0:
        return False
    return latin > cyrillic


def _skip_line(line: str) -> bool:
    """Return True for non-prose lines that should be skipped."""
    stripped = line.strip()
    if not stripped:
        return True
    # Headers, tables, blockquotes, code fences, frontmatter, HTML comments
    if stripped[0] in ("#", "|", ">", "`"):
        return True
    if stripped.startswith("---"):
        return True
    if stripped.startswith("<!--"):
        return True
    # Markdown links/images on their own line
    if stripped.startswith("![") or stripped.startswith("[!"):
        return True
    # English text — euphony rules only apply to Ukrainian prose
    if _is_predominantly_latin(stripped):
        return True
    return False


def _clean_word(word: str) -> str:
    """Strip punctuation for phonetic analysis."""
    return word.strip(".,;:!?«»\"'()\u201c\u201d\u2018\u2019\u00ab\u00bb—–-")


# ---------------------------------------------------------------------------
# Rule checks
# ---------------------------------------------------------------------------

def _check_rule1_iy(words: list[str], line_num: int) -> List[Dict]:
    """Rule 1: Conjunction і/й — й only between vowels."""
    violations = []
    for i, word in enumerate(words):
        lower = word.lower().strip(".,;:!?«»\"'()\u201c\u201d")
        if lower not in ("і", "й"):
            continue

        prev_word = _clean_word(words[i - 1]) if i > 0 else ""
        next_word = _clean_word(words[i + 1]) if i + 1 < len(words) else ""

        if not prev_word or not next_word:
            continue

        prev_vowel = _ends_with_vowel(prev_word)
        next_vowel = _starts_with_vowel(next_word)

        if lower == "і" and prev_vowel and next_vowel:
            # і between vowels → should be й
            violations.append({
                "type": "EUPHONY",
                "severity": "warning",
                "issue": (
                    f"Line {line_num}: «{prev_word} і {next_word}» — "
                    f"і між голосними; має бути «й {next_word}»"
                ),
                "fix": f"Replace «і» with «й» (between vowels)",
                "line": line_num,
            })
        elif lower == "й" and not prev_vowel:
            # й after consonant → should be і (regardless of what follows)
            violations.append({
                "type": "EUPHONY",
                "severity": "warning",
                "issue": (
                    f"Line {line_num}: «{prev_word} й {next_word}» — "
                    f"й після приголосного; має бути «і {next_word}»"
                ),
                "fix": f"Replace «й» with «і» (й cannot follow a consonant)",
                "line": line_num,
            })
        # Note: й after vowel + before consonant (e.g., "вона й працює",
        # "ще й не") is acceptable — not flagged. Only і between vowels
        # and й after consonant are clear violations.

    return violations


def _check_rule2_uv(words: list[str], line_num: int) -> List[Dict]:
    """Rule 2: Preposition у/в alternation."""
    violations = []
    for i, word in enumerate(words):
        lower = word.lower().strip(".,;:!?«»\"'()\u201c\u201d")
        if lower not in ("у", "в"):
            continue

        next_word = _clean_word(words[i + 1]) if i + 1 < len(words) else ""
        if not next_word:
            continue

        if lower == "у" and _starts_with_vowel(next_word):
            # у before vowel → should be в
            violations.append({
                "type": "EUPHONY",
                "severity": "warning",
                "issue": (
                    f"Line {line_num}: «у {next_word}» — "
                    f"у перед голосним; має бути «в {next_word}»"
                ),
                "fix": f"Replace «у» with «в» (before vowel)",
                "line": line_num,
            })
        elif lower == "в" and _starts_with_v_or_f(next_word):
            # в before в/ф → should be у
            violations.append({
                "type": "EUPHONY",
                "severity": "warning",
                "issue": (
                    f"Line {line_num}: «в {next_word}» — "
                    f"в перед в/ф; має бути «у {next_word}»"
                ),
                "fix": f"Replace «в» with «у» (before в or ф)",
                "line": line_num,
            })
        elif lower == "в" and _starts_with_consonant_cluster(next_word):
            # в before consonant cluster → should be у
            violations.append({
                "type": "EUPHONY",
                "severity": "warning",
                "issue": (
                    f"Line {line_num}: «в {next_word}» — "
                    f"в перед збігом приголосних; має бути «у {next_word}»"
                ),
                "fix": f"Replace «в» with «у» (before consonant cluster)",
                "line": line_num,
            })

    return violations


def _check_rule3_ziz(words: list[str], line_num: int) -> List[Dict]:
    """Rule 3: Preposition з/із/зі alternation."""
    violations = []
    for i, word in enumerate(words):
        lower = word.lower().strip(".,;:!?«»\"'()\u201c\u201d")
        if lower != "з":
            continue

        next_word = _clean_word(words[i + 1]) if i + 1 < len(words) else ""
        if not next_word:
            continue

        if _starts_with_z_or_s(next_word):
            # з before з/с/ш/ч → should be із
            violations.append({
                "type": "EUPHONY",
                "severity": "warning",
                "issue": (
                    f"Line {line_num}: «з {next_word}» — "
                    f"з перед з/с/ш/ч; має бути «із {next_word}»"
                ),
                "fix": f"Replace «з» with «із» (before sibilant)",
                "line": line_num,
            })
        elif _starts_with_z_cluster(next_word):
            # з before з-cluster → should be із or зі
            violations.append({
                "type": "EUPHONY",
                "severity": "warning",
                "issue": (
                    f"Line {line_num}: «з {next_word}» — "
                    f"з перед збігом приголосних; має бути «із {next_word}»"
                ),
                "fix": f"Replace «з» with «із» or «зі» (before consonant cluster)",
                "line": line_num,
            })

    return violations


# ---------------------------------------------------------------------------
# Auto-fixer
# ---------------------------------------------------------------------------

def _swap_preserve_case(original: str, old_char: str, new_char: str) -> str:
    """Swap a single character while preserving case. E.g., В→У, в→у."""
    if original[0].isupper():
        return original.replace(old_char.lower(), new_char.lower(), 1).replace(
            old_char.upper(), new_char.upper(), 1
        )
    return original.replace(old_char, new_char, 1)


def _fix_line_rule1(words: list[str]) -> tuple[list[str], int]:
    """Fix Rule 1: і↔й alternation. Returns (fixed_words, fix_count)."""
    result = list(words)
    fixes = 0
    for i, word in enumerate(result):
        lower = word.lower().strip(".,;:!?«»\"'()\u201c\u201d")
        if lower not in ("і", "й"):
            continue
        prev_word = _clean_word(result[i - 1]) if i > 0 else ""
        next_word = _clean_word(result[i + 1]) if i + 1 < len(result) else ""
        if not prev_word or not next_word:
            continue

        if lower == "і" and _ends_with_vowel(prev_word) and _starts_with_vowel(next_word):
            result[i] = result[i].replace("і", "й").replace("І", "Й")
            fixes += 1
        elif lower == "й" and not _ends_with_vowel(prev_word):
            result[i] = result[i].replace("й", "і").replace("Й", "І")
            fixes += 1
    return result, fixes


def _fix_line_rule2(words: list[str]) -> tuple[list[str], int]:
    """Fix Rule 2: у↔в alternation. Returns (fixed_words, fix_count)."""
    result = list(words)
    fixes = 0
    for i, word in enumerate(result):
        lower = word.lower().strip(".,;:!?«»\"'()\u201c\u201d")
        if lower not in ("у", "в"):
            continue
        next_word = _clean_word(result[i + 1]) if i + 1 < len(result) else ""
        if not next_word:
            continue

        if lower == "у" and _starts_with_vowel(next_word):
            result[i] = _swap_preserve_case(result[i], "у", "в")
            fixes += 1
        elif lower == "в" and _starts_with_v_or_f(next_word):
            result[i] = _swap_preserve_case(result[i], "в", "у")
            fixes += 1
        elif lower == "в" and _starts_with_consonant_cluster(next_word):
            result[i] = _swap_preserve_case(result[i], "в", "у")
            fixes += 1
    return result, fixes


def _fix_line_rule3(words: list[str]) -> tuple[list[str], int]:
    """Fix Rule 3: з→із/зі alternation. Returns (fixed_words, fix_count)."""
    result = list(words)
    fixes = 0
    for i, word in enumerate(result):
        lower = word.lower().strip(".,;:!?«»\"'()\u201c\u201d")
        if lower != "з":
            continue
        next_word = _clean_word(result[i + 1]) if i + 1 < len(result) else ""
        if not next_word:
            continue

        if _starts_with_z_or_s(next_word) or _starts_with_z_cluster(next_word):
            result[i] = result[i].replace("з", "із").replace("З", "Із")
            fixes += 1
    return result, fixes


def auto_fix_euphony(content: str, file_path: str = "") -> tuple[str, int]:
    """Apply deterministic euphony fixes to Ukrainian prose.

    Processes Rules 1-3 (word-level phonetic alternation).

    Returns (fixed_content, total_fixes).
    """
    track = _detect_track(file_path)
    if track in EXEMPT_TRACKS:
        return content, 0

    lines = content.split("\n")
    total_fixes = 0
    in_frontmatter = False
    frontmatter_count = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped == "---":
            frontmatter_count += 1
            if frontmatter_count <= 2:
                in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if _skip_line(line):
            continue

        words = line.split()
        if len(words) < 2:
            continue

        # Apply Rules 1-3
        fixed_words = list(words)
        line_fixes = 0

        fixed_words, n = _fix_line_rule1(fixed_words)
        line_fixes += n
        fixed_words, n = _fix_line_rule2(fixed_words)
        line_fixes += n
        fixed_words, n = _fix_line_rule3(fixed_words)
        line_fixes += n

        if line_fixes > 0:
            # Reconstruct line preserving leading whitespace
            leading = line[: len(line) - len(line.lstrip())]
            lines[i] = leading + " ".join(fixed_words)
            total_fixes += line_fixes

    return "\n".join(lines), total_fixes


# ---------------------------------------------------------------------------
# Main check
# ---------------------------------------------------------------------------

def check_euphony_violations(content: str, file_path: str = "") -> List[Dict]:
    """
    Scan Ukrainian prose for euphony rule violations.

    Returns violations in standard audit format:
        {'type', 'severity', 'issue', 'fix', 'line'}
    """
    track = _detect_track(file_path)
    if track in EXEMPT_TRACKS:
        return []

    violations: List[Dict] = []
    lines = content.splitlines()

    # Track frontmatter state
    in_frontmatter = False
    frontmatter_count = 0

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        # Handle frontmatter delimiters
        if stripped == "---":
            frontmatter_count += 1
            if frontmatter_count <= 2:
                in_frontmatter = not in_frontmatter
            continue

        if in_frontmatter:
            continue

        if _skip_line(line):
            continue

        # Tokenize for Rules 1-3
        words = line.split()
        if len(words) < 2:
            continue

        violations.extend(_check_rule1_iy(words, line_num))
        violations.extend(_check_rule2_uv(words, line_num))
        violations.extend(_check_rule3_ziz(words, line_num))

    return violations
