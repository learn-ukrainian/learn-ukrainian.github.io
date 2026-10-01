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
# Apostrophe spellings inside a word: ʼ ' ’ and the YAML single-quoted escape ''.
# Without the last two a word splits at the apostrophe and each half is stressed
# as its own word (дерев''яний → дере́в + яний), contradicting the dictionary.
_APOSTROPHE_RE = re.compile(r"''|[ʼ'’]")
_CYRILLIC_WORD_RE = re.compile(
    rf"(?<![{_CYRILLIC_LETTER_CLASS}])"
    rf"([{_CYRILLIC_BASE_CLASS}][{_CYRILLIC_LETTER_CLASS}]*(?:(?:''|[ʼ'’])[{_CYRILLIC_BASE_CLASS}][{_CYRILLIC_LETTER_CLASS}]*)*)"
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
    base = os.environ.get("STANZA_RESOURCES_DIR") or os.path.join(os.path.expanduser("~"), "stanza_resources")
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
            _stressifier = Stressifier(stress_symbol=StressSymbol.CombiningAcuteAccent, disambiguation="dictionary")
            _stressifier.nlp = _load_context_parser()
    return _stressifier


def _load_context_parser():
    """Load installed context models offline; morphology works without a lemma model."""
    try:
        import stanza
    except ImportError:
        return None
    for processors in ("tokenize,pos,mwt,lemma", "tokenize,pos,mwt"):
        try:
            return stanza.Pipeline("uk", processors=processors, download_method=None, logging_level="ERROR")
        except (OSError, RuntimeError, ValueError):
            continue
    logger.warning("stress_annotator: local context models unavailable; ambiguity stays bare")
    return None


def _count_syllables(word: str) -> int:
    """Count syllables by counting vowels."""
    return sum(1 for c in word if c in _VOWELS)


def _already_stressed(word: str) -> bool:
    """Check if word already has a stress mark."""
    return STRESS_MARK in word


def _strip_surface_stress(word: str) -> str:
    return word.replace(STRESS_MARK, "")


def _restore_apostrophes(stressed: str, original: str) -> str:
    """Put the surface apostrophe spellings of *original* back into *stressed*."""
    surface = iter(_APOSTROPHE_RE.findall(original))
    return re.sub("'", lambda _: next(surface, "'"), stressed)


def _oracle_choice(
    word: str, *, lemma: str | None = None, pos: str | None = None, tags: str | None = None
) -> str | None:
    """Use only a resolved oracle reading; dual stress keeps a valid existing mark."""
    from scripts.verification.stress import (
        _stress_positions_in_marked_string,
        pedagogical_stressed_form,
        transfer_stress_marks,
        verify_stress,
    )

    clean = _strip_surface_stress(word)
    if _count_syllables(clean) < 2:
        return None
    lookup = clean if pos == "PROPN" else clean.lower()
    result = verify_stress(lookup, lemma=lemma, pos=pos, tags=tags)
    if clean != clean.lower() and not (lemma or pos or tags):
        cased = verify_stress(clean)
        if {tuple(m["vowel_indices"]) for m in cased.get("matches", [])} != {
            tuple(m["vowel_indices"]) for m in result.get("matches", [])
        }:
            return None
    matches = result.get("matches") or []
    if result["status"] != "ok" or not matches:
        return None
    allowed: set[int] = set()
    for match in matches:
        allowed.update(match.get("vowel_indices") or [])
    _, current = _stress_positions_in_marked_string(word)
    if len(current) == 1 and current[0] in allowed:
        return word
    if matches[0].get("pedagogical_conflict"):
        return None
    return transfer_stress_marks(pedagogical_stressed_form(matches[0]), clean)


def _build_skip_mask(
    text: str,
    extra_ranges: list[tuple[int, int]] | None = None,
) -> list[tuple[int, int]]:
    """Build list of (start, end) ranges to skip (comments, code, URLs)."""
    ranges = list(extra_ranges or [])
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
    text: str,
    orig_words: list[re.Match],
) -> dict[int, str]:
    """Use Stanza's lemma/POS/features as context, then query the same oracle.

    Stanza supplies morphology, never an accent or a first-reading choice.
    An absent parser, offset mismatch or unresolved meaning leaves the word bare.
    """
    try:
        parser = getattr(_get_stressifier(), "nlp", None)
    except (ImportError, OSError, RuntimeError, ValueError):
        logger.warning("stress_annotator: context unavailable; ambiguity stays bare")
        return {}
    if parser is None:
        return {}
    # Parse bare text and map token offsets back, so already-accented input
    # receives the same morphology and the second pass remains idempotent.
    bare_chars: list[str] = []
    bare_offsets = [0]
    for char in text:
        if char != STRESS_MARK:
            bare_chars.append(char)
        bare_offsets.append(len(bare_chars))
    by_start = {bare_offsets[m.start(1)]: m for m in orig_words}
    stress_map: dict[int, str] = {}
    try:
        parsed = parser("".join(bare_chars))
        for token in parsed.iter_tokens():
            match = by_start.get(token.start_char)
            if match is None or token.end_char != bare_offsets[match.end(1)]:
                continue
            analysis = token.to_dict()[0]
            word = _APOSTROPHE_RE.sub("'", match.group(1))
            chosen = _oracle_choice(
                word, lemma=analysis.get("lemma"), pos=analysis.get("upos"), tags=analysis.get("feats")
            )
            if chosen is not None:
                stress_map[match.start(1)] = chosen
    except Exception:
        logger.debug("stress_annotator: context parser failed", exc_info=True)
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


def annotate_stress(
    text: str,
    *,
    protected_ranges: list[tuple[int, int]] | None = None,
) -> tuple[str, int]:
    """Add and repair stress marks on Ukrainian words in text.

    Returns (annotated_text, count_of_words_changed). Words starting inside
    ``protected_ranges`` (character offsets) are left untouched.

    Strategy:
    - Only stress words with 2+ syllables (single-syllable = obvious)
    - Skip words inside HTML comments, code blocks, URLs, JSX tags
    - Unique ``verify_stress`` hits: repair wrong/double marks; keep a
      single acute on an allowed vowel; fill unstressed words
    - Heteronyms: Stanza morphology joined to the oracle; unresolved forms stay bare
    - Add a focused second pass for DialogueBox uk="..." values
    """
    from scripts.verification.stress import pending_stress_reason

    skip_ranges = _build_skip_mask(text, protected_ranges)
    matches = list(_CYRILLIC_WORD_RE.finditer(text))
    replacements: dict[int, str] = {}
    unresolved: list[re.Match[str]] = []

    for match in matches:
        if _in_skip_range(match.start(), skip_ranges):
            continue
        word = _APOSTROPHE_RE.sub("'", match.group(1))
        if _count_syllables(_strip_surface_stress(word)) < 2:
            continue
        # A pending form has no authoritative accent. Remove any old mark and
        # keep it out of the sentence Stressifier fallback as well.
        clean = _strip_surface_stress(word)
        if pending_stress_reason(clean) or pending_stress_reason(clean.lower()):
            if clean != word:
                replacements[match.start(1)] = _restore_apostrophes(clean, match.group(1))
            continue
        chosen = _oracle_choice(word)
        if chosen is None:
            unresolved.append(match)
            continue
        if chosen != word:
            replacements[match.start(1)] = _restore_apostrophes(chosen, match.group(1))

    if unresolved:
        stress_map = _build_sentence_stress_map(text, matches)
        for match in unresolved:
            word = _APOSTROPHE_RE.sub("'", match.group(1))
            clean = _strip_surface_stress(word)
            # No resolved context means no learner accent, including stale marks.
            chosen = stress_map.get(match.start(1), clean)
            if chosen != word:
                replacements[match.start(1)] = _restore_apostrophes(chosen, match.group(1))

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


# Same spotted-misspelling keys as lesson_gates._ERROR_KEYS (compared lowercased).
_ACTIVITY_ERROR_KEYS = frozenset({"error", "errorword", "incorrect", "error_word"})


def activity_error_ranges(text: str) -> list[tuple[int, int]]:
    """Character ranges of intentional misspellings in an activities.yaml text.

    Covers every value under an error key plus each whole-word copy of that
    value inside the same item (the sentence that carries it, option chips
    that repeat it). Works on YAML node positions, so the file is never
    re-serialized.
    """
    import yaml

    try:
        root = yaml.compose(text)
    except yaml.YAMLError:
        return []

    ranges: list[tuple[int, int]] = []

    def scalars(node) -> list:
        if isinstance(node, yaml.ScalarNode):
            return [node]
        if isinstance(node, yaml.SequenceNode):
            return [s for child in node.value for s in scalars(child)]
        if isinstance(node, yaml.MappingNode):
            return [s for _, child in node.value for s in scalars(child)]
        return []

    def walk(node) -> None:
        if isinstance(node, yaml.SequenceNode):
            for child in node.value:
                walk(child)
            return
        if not isinstance(node, yaml.MappingNode):
            return
        for key, value in node.value:
            if isinstance(key, yaml.ScalarNode) and str(key.value).lower() in _ACTIVITY_ERROR_KEYS:
                for scalar in scalars(value):
                    ranges.append((scalar.start_mark.index, scalar.end_mark.index))
                    form = str(scalar.value).strip()
                    if not _CYRILLIC_WORD_RE.search(form):
                        continue
                    copy_re = re.compile(
                        rf"(?<![{_CYRILLIC_LETTER_CLASS}ʼ']){re.escape(form)}(?![{_CYRILLIC_LETTER_CLASS}ʼ'])"
                    )
                    start = node.start_mark.index
                    for m in copy_re.finditer(text[start : node.end_mark.index]):
                        ranges.append((start + m.start(), start + m.end()))
            else:
                walk(value)

    walk(root)
    return ranges


def annotate_file(path: Path) -> int:
    """Add stress marks to a content file in-place.

    ``activities.yaml`` keeps its intentional misspellings (error chips) as-is.

    Returns count of words stressed.
    """
    if not path.exists():
        return 0

    text = path.read_text("utf-8")

    protected = activity_error_ranges(text) if path.name == "activities.yaml" else None
    annotated, count = annotate_stress(text, protected_ranges=protected)

    if count > 0:
        path.write_text(annotated, "utf-8")
        logger.info("stress_annotator: added stress marks to %d words in %s", count, path.name)

    return count
