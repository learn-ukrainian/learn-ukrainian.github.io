"""Post-process content to add stress marks using ukrainian-word-stress.

Reads generated .md content, finds Ukrainian words, adds combining acute
accent (U+0301) on the stressed vowel for words with 2+ syllables.
Marks every multi-syllable Ukrainian word occurrence. The annotator is
idempotent: a second pass adds no marks. Already-stressed words are
repaired when they disagree with the Sources ``verify_stress`` oracle
(wrong vowel, or two acutes packed onto one non-hyphenated form). A
single acute on an allowed dictionary vowel is kept.

Uses sentence-level processing for context-aware heteronym disambiguation.
The Stressifier uses Stanza NLP internally — feeding full sentences allows
it to resolve heteronyms like вікна́ (gen sg) vs ві́кна (nom pl) via POS tags.

Called after content generation, before MDX generation.

Issue: #981, #1019
"""

from __future__ import annotations

import contextlib
import logging
import os
import re
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

STRESS_MARK = "\u0301"

# Match Ukrainian words (2+ Cyrillic chars, may include apostrophe/soft sign/stress mark)
# Use lookbehind/lookahead instead of \b — \b doesn't work with Cyrillic
# Include \u0301 (combining acute accent) so already-stressed words are matched whole
_CYRILLIC_BASE_CLASS = "А-ЯҐЄІЇа-яґєії"
_CYRILLIC_LETTER_CLASS = f"{_CYRILLIC_BASE_CLASS}\u0301"
_CYRILLIC_WORD_RE = re.compile(
    rf"(?<![{_CYRILLIC_LETTER_CLASS}])"
    rf"([{_CYRILLIC_BASE_CLASS}][{_CYRILLIC_LETTER_CLASS}]*(?:[ʼ'][{_CYRILLIC_BASE_CLASS}][{_CYRILLIC_LETTER_CLASS}]*)*)"
    rf"(?![{_CYRILLIC_LETTER_CLASS}])",
    re.UNICODE,
)

# Ukrainian vowels — needed to count syllables
_VOWELS = set("аеиіїоуюяєАЕИІЇОУЮЯЄ")

# Contexts to skip: inside HTML comments, code blocks, URLs, JSX/HTML tags.
# DialogueBox uk="..." values are annotated in a focused second pass because
# they are learner-facing Ukrainian inside an otherwise-skipped JSX tag.
_SKIP_PATTERNS = [
    re.compile(r"<!--.*?-->", re.DOTALL),
    re.compile(r"```.*?```", re.DOTALL),
    re.compile(r"`[^`]+`"),
    re.compile(r"https?://\S+"),
    re.compile(r"<[^>]+>"),  # JSX/HTML tags
]

# Lazy-loaded Stressifier
_stressifier = None


def _stanza_download_lock_path() -> Path:
    """Path to the inter-process lock guarding first-time Stanza model setup.

    Keyed to the shared Stanza resources directory (``STANZA_RESOURCES_DIR``
    or ``~/stanza_resources``) so that every process that downloads into that
    directory contends on the same lock. Falls back to the system temp dir if
    the resources directory cannot be created.
    """
    base = os.environ.get("STANZA_RESOURCES_DIR") or os.path.join(
        os.path.expanduser("~"), "stanza_resources"
    )
    if not base.startswith("~"):
        try:
            Path(base).mkdir(parents=True, exist_ok=True)
            return Path(base) / ".uk-model-download.lock"
        except OSError:
            pass
    return Path(tempfile.gettempdir()) / "stanza-uk-model-download.lock"


@contextlib.contextmanager
def _model_download_lock():
    """Serialize first-time Stressifier construction across processes.

    The Stressifier constructor lazily downloads the Stanza Ukrainian model
    into a shared resources directory. When several processes start cold at
    once — ``pytest -n auto`` workers, or concurrent V7 builds — they each
    write the same model file simultaneously, corrupting it and tripping
    Stanza's md5 check (``ValueError: md5 for .../uk/tokenize/iu.pt is ...,
    expected ...``) — a flaky ``Test (pytest)`` failure on the whole
    stress_annotator mutation class plus the ULP stress tests. Holding an
    inter-process file lock around construction makes the download/load
    atomic, so only the first process downloads and the rest load the
    verified file from disk.
    """
    try:
        from filelock import FileLock, Timeout
    except ImportError:
        # filelock is a pinned dependency, but never let its absence turn a
        # working stress pass into a hard failure — degrade to unlocked.
        yield
        return

    lock = FileLock(str(_stanza_download_lock_path()), timeout=900)
    try:
        with lock:
            yield
    except Timeout:
        # Extremely unlikely (a model download takes seconds). Proceed
        # unlocked rather than introducing a new failure mode.
        logger.warning("stress_annotator: timed out acquiring model download lock; proceeding unlocked")
        yield


def _get_stressifier():
    """Lazy load the Stressifier (loads Stanza model on first call)."""
    global _stressifier
    if _stressifier is None:
        from ukrainian_word_stress import Stressifier, StressSymbol

        with _model_download_lock():
            _stressifier = Stressifier(stress_symbol=StressSymbol.CombiningAcuteAccent)
    return _stressifier


def _count_syllables(word: str) -> int:
    """Count syllables by counting vowels."""
    return sum(1 for c in word if c in _VOWELS)


def _already_stressed(word: str) -> bool:
    """Check if word already has a stress mark."""
    return STRESS_MARK in word


def _strip_surface_stress(word: str) -> str:
    return word.replace(STRESS_MARK, "")


def _collapse_non_hyphen_multi_acute(word: str) -> str:
    """Keep one acute on non-hyphenated forms; hyphenated compounds keep all."""
    from scripts.verification.stress import _stress_positions_in_marked_string

    if "-" in _strip_surface_stress(word) or word.count(STRESS_MARK) <= 1:
        return word
    bare, indices = _stress_positions_in_marked_string(word)
    if len(indices) <= 1:
        return word
    keep = indices[-1]
    return bare[: keep + 1] + STRESS_MARK + bare[keep + 1 :]


def _oracle_choice(word: str) -> str | None:
    """Pedagogical surface form from verify_stress, or None if unresolved.

    Lookup is casefolded so title-case ``Мене`` does not hit a different
    trie key than ``мене``. A single acute already on an allowed vowel is
    kept (подвійний наголос: either listed position is acceptable).
    Ambiguous dictionary readings (Правила, Підсумок) take the first
    pedagogical form when the surface is unstressed.
    """
    from scripts.verification.stress import (
        _stress_positions_in_marked_string,
        pedagogical_stressed_form,
        transfer_stress_marks,
        verify_stress,
    )

    clean = _strip_surface_stress(word)
    if _count_syllables(clean) < 2:
        return None
    result = verify_stress(clean.lower())
    matches = result.get("matches") or []
    if result["status"] not in {"ok", "ambiguous"} or not matches:
        return None
    allowed: set[int] = set()
    for match in matches:
        allowed.update(match.get("vowel_indices") or [])
    _, current = _stress_positions_in_marked_string(word)
    if len(current) == 1 and current[0] in allowed:
        return word
    return transfer_stress_marks(pedagogical_stressed_form(matches[0]), clean)


def _build_skip_mask(text: str) -> list[tuple[int, int]]:
    """Build list of (start, end) ranges to skip (comments, code, URLs)."""
    ranges = []
    for pattern in _SKIP_PATTERNS:
        for m in pattern.finditer(text):
            ranges.append((m.start(), m.end()))
    # Sort and merge overlapping ranges
    ranges.sort()
    merged = []
    for start, end in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _in_skip_range(pos: int, skip_ranges: list[tuple[int, int]]) -> bool:
    """Check if position falls within a skip range (binary search)."""
    lo, hi = 0, len(skip_ranges) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        s, e = skip_ranges[mid]
        if pos < s:
            hi = mid - 1
        elif pos >= e:
            lo = mid + 1
        else:
            return True
    return False


def _build_sentence_stress_map(
    text: str, orig_words: list[re.Match],
) -> dict[int, str]:
    """Build a map of word positions to their stressed forms using sentence context.

    Feeds the full text to the Stressifier in one call so that Stanza can use
    sentence context for heteronym disambiguation. This is both faster (one
    Stanza pass) and more accurate (full context available).

    Args:
        text: Full document text.
        orig_words: Pre-computed Cyrillic word matches from the text.

    Returns dict mapping match-start-position -> stressed word form.
    """
    stressifier = _get_stressifier()
    stress_map: dict[int, str] = {}

    try:
        stressed_text = stressifier(text)
    except Exception:
        logger.debug("stress_annotator: stressifier failed on full text")
        return stress_map

    stressed_words = list(_CYRILLIC_WORD_RE.finditer(stressed_text))

    if len(orig_words) != len(stressed_words):
        logger.warning(
            "stress_annotator: word count mismatch (%d vs %d), "
            "falling back to per-word stress",
            len(orig_words),
            len(stressed_words),
        )
        for m in orig_words:
            word = m.group(1)
            if _count_syllables(word) < 2 or _already_stressed(word):
                continue
            try:
                stressed = stressifier(word)
            except Exception:
                continue
            if STRESS_MARK in stressed and stressed.replace(STRESS_MARK, "") == word.replace(STRESS_MARK, ""):
                stress_map[m.start(1)] = stressed
        return stress_map

    for orig_m, stress_m in zip(orig_words, stressed_words, strict=False):
        orig_word = orig_m.group(1)
        stressed_word = stress_m.group(1)

        # Strip stress marks from BOTH sides before comparing — the original
        # text may already contain some stress marks from vocab_gen or manual
        # annotation. Without this, pre-stressed words like "Зву́ки" fail the
        # comparison because stressed_clean="Звуки" != orig="Зву́ки".
        if stressed_word.replace(STRESS_MARK, "") != orig_word.replace(STRESS_MARK, ""):
            continue

        if STRESS_MARK in stressed_word:
            stress_map[orig_m.start(1)] = stressed_word

    return stress_map


_DIALOGUEBOX_UK_ATTR_RE = re.compile(
    r"(<DialogueBox\b[^>]*\buk\s*=\s*\")(?P<uk>[^\"]*)(\")",
    re.DOTALL,
)


def _annotate_dialoguebox_uk_attrs(text: str) -> tuple[str, int]:
    """Annotate Ukrainian inside DialogueBox uk="..." props only."""
    total = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal total
        value = match.group("uk")
        annotated, count = annotate_stress(value)
        total += count
        return f"{match.group(1)}{annotated}{match.group(3)}"

    return _DIALOGUEBOX_UK_ATTR_RE.sub(replace, text), total


def annotate_stress(text: str) -> tuple[str, int]:
    """Add and repair stress marks on Ukrainian words in text.

    Returns (annotated_text, count_of_words_changed).

    Strategy:
    - Only stress words with 2+ syllables (single-syllable = obvious)
    - Skip words inside HTML comments, code blocks, URLs, JSX tags
    - Unique ``verify_stress`` hits: repair wrong/double marks; keep a
      single acute on an allowed vowel; fill unstressed words
    - Heteronyms / not-found: sentence Stressifier, then collapse duals
    - Add a focused second pass for DialogueBox uk="..." values
    """
    from scripts.verification.stress import transfer_stress_marks

    skip_ranges = _build_skip_mask(text)
    matches = list(_CYRILLIC_WORD_RE.finditer(text))
    replacements: dict[int, str] = {}
    unresolved: list[re.Match[str]] = []

    for match in matches:
        if _in_skip_range(match.start(), skip_ranges):
            continue
        word = match.group(1)
        if _count_syllables(_strip_surface_stress(word)) < 2:
            continue
        chosen = _oracle_choice(word)
        if chosen is None:
            unresolved.append(match)
            continue
        if chosen != word:
            replacements[match.start(1)] = chosen

    if unresolved:
        stress_map = _build_sentence_stress_map(text, matches)
        stressifier = _get_stressifier()
        for match in unresolved:
            pos = match.start(1)
            word = match.group(1)
            clean = _strip_surface_stress(word)
            stressed = stress_map.get(pos)
            if stressed is None:
                try:
                    stressed = stressifier(clean)
                except Exception:
                    continue
                if STRESS_MARK not in stressed or _strip_surface_stress(stressed) != clean:
                    continue
            collapsed = transfer_stress_marks(
                _collapse_non_hyphen_multi_acute(stressed), clean,
            )
            if _already_stressed(word) and word.count(STRESS_MARK) == 1:
                continue
            if collapsed != word:
                replacements[pos] = collapsed

    result = list(text)
    count = 0
    for match in reversed(matches):
        replacement = replacements.get(match.start(1))
        if replacement is None:
            continue
        start, end = match.start(1), match.end(1)
        result[start:end] = list(replacement)
        count += 1

    annotated = "".join(result)
    annotated, attr_count = _annotate_dialoguebox_uk_attrs(annotated)
    return annotated, count + attr_count


def annotate_file(path: Path) -> int:
    """Add stress marks to a content .md file in-place.

    Returns count of words stressed.
    """
    if not path.exists():
        return 0

    text = path.read_text("utf-8")

    annotated, count = annotate_stress(text)

    if count > 0:
        path.write_text(annotated, "utf-8")
        logger.info("stress_annotator: added stress marks to %d words in %s", count, path.name)

    return count
