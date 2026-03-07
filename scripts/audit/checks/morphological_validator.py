"""VESUM-based morphological validator for module content.

Uses VESUM morphological tags (POS, case, gender, tense, person) to
deterministically check Ukrainian words against module-level grammar
constraints. Replaces regex-based rules with 100% accurate tag checks.

Also includes:
- Russicism/replacement detection via LanguageTool word lists (9K+ rules)
- Adjective-noun agreement checking via VESUM gender+case tags

Issue: #753
"""

from __future__ import annotations

import json
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# VESUM tag reference
# ---------------------------------------------------------------------------
# POS: noun, verb, adj, adv, advp, conj, intj, noninfl, numr, part, prep
# Noun tags: noun:anim/inanim:m/f/n:v_naz/v_rod/v_dav/v_zna/v_oru/v_mis/v_kly
# Verb tags: verb:imperf/perf:pres/past/futr/inf/impr:s/p:1/2/3
# Adj tags:  adj:m/f/n/p:v_naz/v_rod/...:compb/compr/super

_CASE_LABELS = {
    "v_naz": "nominative",
    "v_rod": "genitive",
    "v_dav": "dative",
    "v_zna": "accusative",
    "v_oru": "instrumental",
    "v_mis": "locative",
    "v_kly": "vocative",
}

_OBLIQUE_CASES = {"v_rod", "v_dav", "v_zna", "v_oru", "v_mis"}

_CYRILLIC_TOKEN_RE = re.compile(
    r"[А-ЯҐЄІЇа-яґєіїʼ'\u0301]+", re.UNICODE
)

# Stress mark (combining acute accent) — strip before VESUM lookup
_STRESS_MARK = "\u0301"

# ---------------------------------------------------------------------------
# Allowed chunks per module range — memorized phrases exempt from constraints
# ---------------------------------------------------------------------------
# These are taught as fixed chunks, not analyzed grammar.
# Core communicative chunks — taught as fixed phrases, not analyzed grammar.
# Extended through M46 because "будь ласка", "вибачте" contain imperatives
# which are formally forbidden until M47.
_CORE_CHUNKS: set[str] = {
    "до побачення", "до зустрічі", "будь ласка", "на здоров'я",
    "як справи", "мене звати", "дуже добре", "дякую",
    "вибачте", "перепрошую", "смачного",
}

_ALLOWED_CHUNKS: dict[tuple[int, int], set[str]] = {
    # M5-10: Phonology & First Grammar — extra chunks for early modules
    (5, 10): _CORE_CHUNKS | {
        "на жаль", "на добраніч", "до речі", "на щастя",
        "без сумніву", "з повагою", "що ти робиш",
        "що ви робите", "все добре",
    },
    # M11-46: Core chunks persist (imperative-containing phrases exempted)
    (11, 46): _CORE_CHUNKS,
}


def _get_allowed_chunks(module_num: int) -> set[str]:
    """Get allowed memorized chunks for a module number."""
    result: set[str] = set()
    for (lo, hi), chunks in _ALLOWED_CHUNKS.items():
        if lo <= module_num <= hi:
            result |= chunks
    return result


def _is_in_allowed_chunk(word: str, line: str, chunks: set[str]) -> bool:
    """Check if a word appears as part of an allowed memorized chunk."""
    line_lower = line.lower()
    word_lower = word.lower()
    for chunk in chunks:
        if word_lower in chunk and chunk in line_lower:
            return True
    return False


# ---------------------------------------------------------------------------
# Line filtering — skip tables, callouts, code, English-dominant lines
# ---------------------------------------------------------------------------

def _should_skip_line(line: str) -> bool:
    """Return True if line should be excluded from morphological checking."""
    stripped = line.strip()
    if not stripped:
        return True
    # Table rows
    if stripped.startswith("|"):
        return True
    # Callout boxes — strip the > prefix and check the remaining text.
    # We validate callout content but strip callout markers first.
    if stripped.startswith(">"):
        # Strip callout syntax: "> [!tip]", "> [!culture]", "> **bold**" etc.
        inner = re.sub(r"^>+\s*(?:\[![^\]]*\]\s*)?", "", stripped)
        if not inner.strip():
            return True
        # Skip if no Cyrillic at all; otherwise validate
        cyrillic = sum(1 for c in inner if '\u0400' <= c <= '\u04ff')
        if cyrillic == 0:
            return True
        return False  # Validate callout content
    # Code blocks
    if stripped.startswith("```"):
        return True
    # Horizontal rules
    if stripped.startswith("---"):
        return True
    # HTML comments (SCOPE blocks etc.)
    if stripped.startswith("<!--") or stripped.startswith("-->"):
        return True
    # Markdown headings (metalanguage about grammar, not example sentences)
    if stripped.startswith("#"):
        return True
    # Negative example markers
    if any(marker in stripped for marker in ("WRONG:", "INCORRECT:", "❌", "~~")):
        return True
    # Pure English lines (no Ukrainian words to check)
    cyrillic = sum(1 for c in stripped if '\u0400' <= c <= '\u04ff')
    if cyrillic == 0:
        return True
    # Don't skip English-dominant lines — _CYRILLIC_TOKEN_RE already isolates
    # Ukrainian words, so even "The word **книгу** means..." gets checked.
    return False


# ---------------------------------------------------------------------------
# Grammar constraints by module
# ---------------------------------------------------------------------------

from dataclasses import dataclass


@dataclass
class GrammarConstraint:
    """Defines what grammar is allowed/forbidden at a module level."""
    no_verbs: bool = False          # POS=verb forbidden
    no_imperatives: bool = False    # verb with 'impr' in tags
    nominative_only: bool = False   # only v_naz / v_kly for nouns/adjs
    no_accusative: bool = False     # v_zna forbidden
    present_only: bool = False      # no past/futr verb forms
    check_gender: bool = False      # verify gender claims


def _get_constraints(track: str, module_num: int) -> GrammarConstraint:
    """Get grammar constraints for a module."""
    base = track.split("-")[0] if "-" in track else track
    if base != "a1":
        # Non-A1 tracks: imperatives already taught in A1 M47, so no constraint.
        # Only check gender for now.
        return GrammarConstraint(check_gender=True)

    if module_num <= 14:
        return GrammarConstraint(
            no_verbs=True,
            no_imperatives=True,
            nominative_only=module_num >= 5,
            check_gender=True,
        )
    elif module_num <= 24:
        return GrammarConstraint(
            no_imperatives=True,
            present_only=True,
            no_accusative=module_num < 25,
            check_gender=True,
        )
    elif module_num <= 46:
        return GrammarConstraint(
            no_imperatives=True,
            check_gender=True,
        )
    else:
        # M47+: imperatives taught, most grammar available
        return GrammarConstraint(check_gender=True)


# ---------------------------------------------------------------------------
# Core validation
# ---------------------------------------------------------------------------

def _parse_case(tags: str) -> str | None:
    """Extract case from VESUM tags string."""
    for case_code in _CASE_LABELS:
        if case_code in tags:
            return case_code
    return None


def _parse_tense(tags: str) -> str | None:
    """Extract tense from verb tags."""
    for tense in ("pres", "past", "futr", "inf", "impr"):
        if f":{tense}" in tags or tags.startswith(f"verb:{tense}") or f":{tense}:" in tags:
            return tense
    return None


def validate_morphology(
    content: str,
    level: str,
    module_num: int,
    track: str,
    max_issues: int = 15,
) -> list[dict]:
    """Validate Ukrainian words in content against grammar constraints.

    Returns list of deterministic issues compatible with DScreenResult.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

    from rag_batch_verify import vesum_batch_lookup, tokenize_all_ukrainian

    constraints = _get_constraints(track, module_num)
    allowed_chunks = _get_allowed_chunks(module_num)
    issues: list[dict] = []

    # 1. Extract words per line (preserving line context for chunk checking)
    word_lines: list[tuple[str, int, str]] = []  # (word, line_num, full_line)
    lines = content.split("\n")
    for line_num, line in enumerate(lines, 1):
        if _should_skip_line(line):
            continue
        tokens = _CYRILLIC_TOKEN_RE.findall(line)
        for token in tokens:
            word_lines.append((token, line_num, line))

    if not word_lines:
        return []

    # 2. Batch VESUM lookup (strip stress marks for lookup)
    unique_words = list({w.lower().replace(_STRESS_MARK, "") for w, _, _ in word_lines})
    vesum_results = vesum_batch_lookup(unique_words)

    # 3. Check each word against constraints
    seen_violations: set[str] = set()  # deduplicate

    for word, line_num, full_line in word_lines:
        if len(issues) >= max_issues:
            break

        word_clean = word.replace(_STRESS_MARK, "")
        word_lower = word_clean.lower()

        # Skip 1-char tokens (suffix fragments like -є, -и from **-є**)
        if len(word_clean) <= 1:
            continue

        # Skip if in allowed chunk
        if _is_in_allowed_chunk(word.replace(_STRESS_MARK, ""), full_line.replace(_STRESS_MARK, ""), allowed_chunks):
            continue

        matches = vesum_results.get(word_lower, [])

        if not matches:
            # Word not found — already handled by existing VESUM check
            continue

        # Check each constraint
        dedup_key = f"{word_lower}:{line_num}"
        if dedup_key in seen_violations:
            continue

        # Aggregate POS info across all VESUM entries for this word
        all_pos = {m["pos"] for m in matches}
        all_tags = [m["tags"] for m in matches]
        has_verb = "verb" in all_pos
        only_verb = all_pos == {"verb"}
        has_impr = any("impr" in t for t in all_tags)

        # --- Imperative check (most specific — check first) ---
        if constraints.no_imperatives and has_impr:
            # Only flag if word can't be interpreted as non-imperative
            non_impr = [m for m in matches if "impr" not in m["tags"]]
            if not non_impr:
                seen_violations.add(dedup_key)
                impr_tags = next(m["tags"] for m in matches if "impr" in m["tags"])
                issues.append({
                    "type": "MORPHOLOGICAL_VIOLATION",
                    "severity": "HIGH",
                    "location": f"~line {line_num}",
                    "text": (
                        f"Imperative '{word}' (VESUM: {impr_tags}) — "
                        f"imperatives not taught until M47."
                    ),
                    "fix": (
                        f"Replace '{word}' with English instruction. "
                        f"E.g., use 'Remember that...' instead of Ukrainian imperatives."
                    ),
                })
                continue

        # --- No verbs constraint ---
        if constraints.no_verbs and only_verb:
            seen_violations.add(dedup_key)
            verb_tags = matches[0]["tags"]
            issues.append({
                "type": "MORPHOLOGICAL_VIOLATION",
                "severity": "HIGH",
                "location": f"~line {line_num}",
                "text": (
                    f"Verb '{word}' (VESUM: {verb_tags}) in pre-verb module M{module_num}. "
                    f"Verbs are forbidden before M15."
                ),
                "fix": (
                    f"Replace verb '{word}' with an English equivalent or "
                    f"a noun phrase. Students haven't learned verbs yet."
                ),
            })
            continue

        # --- No accusative constraint ---
        if constraints.no_accusative:
            for match in matches:
                if match["pos"] in ("noun", "adj") and "v_zna" in match["tags"]:
                    # Allow escape if word has a non-accusative nominal form
                    # OR a non-nominal POS (e.g., "дію" = verb "діяти")
                    has_non_acc = any(
                        m["pos"] not in ("noun", "adj")
                        or "v_zna" not in m["tags"]
                        for m in matches
                    )
                    if not has_non_acc:
                        seen_violations.add(dedup_key)
                        issues.append({
                            "type": "MORPHOLOGICAL_VIOLATION",
                            "severity": "HIGH",
                            "location": f"~line {line_num}",
                            "text": (
                                f"Accusative '{word}' (VESUM: {match['tags']}) "
                                f"in M{module_num}. Accusative not taught until M25."
                            ),
                            "fix": (
                                f"Replace '{word}' (accusative) with nominative form "
                                f"or use English equivalent."
                            ),
                        })
                    break
            if dedup_key in seen_violations:
                continue

        # --- Nominative only constraint ---
        if constraints.nominative_only:
            # Skip if word has non-noun/adj interpretations (e.g., чому = adverb)
            has_non_nominal = any(m["pos"] not in ("noun", "adj") for m in matches)
            if not has_non_nominal:
                for match in matches:
                    if match["pos"] in ("noun", "adj"):
                        case = _parse_case(match["tags"])
                        if case and case in _OBLIQUE_CASES:
                            has_nom = any(
                                _parse_case(m["tags"]) in ("v_naz", "v_kly", None)
                                for m in matches
                                if m["pos"] in ("noun", "adj")
                            )
                            if not has_nom:
                                case_label = _CASE_LABELS.get(case, case)
                                seen_violations.add(dedup_key)
                                issues.append({
                                    "type": "MORPHOLOGICAL_VIOLATION",
                                    "severity": "HIGH",
                                    "location": f"~line {line_num}",
                                    "text": (
                                        f"Non-nominative '{word}' ({case_label}, VESUM: {match['tags']}) "
                                        f"in M{module_num}. Only nominative case allowed before M25."
                                    ),
                                    "fix": (
                                        f"Replace '{word}' ({case_label}) with its nominative form "
                                        f"or use English equivalent."
                                    ),
                                })
                        break
            if dedup_key in seen_violations:
                continue

        # --- Present tense only constraint ---
        if constraints.present_only and has_verb:
            for match in matches:
                if match["pos"] == "verb":
                    tense = _parse_tense(match["tags"])
                    if tense in ("past", "futr"):
                        # Check if word has a valid non-past interpretation:
                        # either a present/inf verb form, or a non-verb POS
                        # (e.g., "став" = noun "pond", not just past of "стати")
                        has_valid = any(
                            m["pos"] != "verb"
                            or _parse_tense(m["tags"]) in ("pres", "inf", None)
                            for m in matches
                        )
                        if not has_valid:
                            seen_violations.add(dedup_key)
                            issues.append({
                                "type": "MORPHOLOGICAL_VIOLATION",
                                "severity": "HIGH",
                                "location": f"~line {line_num}",
                                "text": (
                                    f"Non-present verb '{word}' ({tense} tense, VESUM: {match['tags']}) "
                                    f"in M{module_num}. Only present tense available before M36."
                                ),
                                "fix": (
                                    f"Replace '{word}' with present tense form or English."
                                ),
                            })
                        break

    # --- Russicism / replacement check (all modules) ---
    replacement_issues = check_replacements(content, max_issues=max_issues - len(issues))
    issues.extend(replacement_issues)

    # --- Agreement check (all modules) ---
    agreement_issues = check_agreement(
        word_lines, vesum_results, max_issues=max_issues - len(issues)
    )
    issues.extend(agreement_issues)

    return issues


# ---------------------------------------------------------------------------
# Russicism / LanguageTool replacement check
# ---------------------------------------------------------------------------

_LT_REPLACEMENTS: dict[str, dict] | None = None
_LT_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "lt_replacements.json"


def _load_replacements() -> dict[str, dict]:
    """Lazy-load LanguageTool replacement dictionary."""
    global _LT_REPLACEMENTS
    if _LT_REPLACEMENTS is None:
        if _LT_PATH.exists():
            with open(_LT_PATH, "r") as f:
                _LT_REPLACEMENTS = json.load(f)
        else:
            _LT_REPLACEMENTS = {}
    return _LT_REPLACEMENTS


def check_replacements(
    content: str,
    max_issues: int = 10,
) -> list[dict]:
    """Check content for Russianisms and non-standard forms using LanguageTool rules."""
    replacements = _load_replacements()
    if not replacements:
        return []

    issues: list[dict] = []
    seen: set[str] = set()

    for line_num, line in enumerate(content.split("\n"), 1):
        if _should_skip_line(line):
            continue
        tokens = _CYRILLIC_TOKEN_RE.findall(line)
        for token in tokens:
            if len(issues) >= max_issues:
                return issues
            word_lower = token.lower().replace(_STRESS_MARK, "")
            if word_lower in seen or len(word_lower) <= 2:
                continue
            entry = replacements.get(word_lower)
            if entry:
                seen.add(word_lower)
                suggestions = entry["suggestions"]
                source = entry["source"]
                severity = "HIGH" if source == "replace" else "MEDIUM"
                issues.append({
                    "type": "RUSSICISM_OR_NONSTANDARD",
                    "severity": severity,
                    "location": f"~line {line_num}",
                    "text": (
                        f"Non-standard form '{token}' — "
                        f"prefer: {', '.join(suggestions)}"
                    ),
                    "fix": (
                        f"Replace '{token}' with '{suggestions[0]}'"
                        + (f" (or: {', '.join(suggestions[1:])})" if len(suggestions) > 1 else "")
                    ),
                })
    return issues


# ---------------------------------------------------------------------------
# Adjective-noun agreement check
# ---------------------------------------------------------------------------

_GENDER_CODES = {"m", "f", "n", "p"}
_CASE_CODES = {"v_naz", "v_rod", "v_dav", "v_zna", "v_oru", "v_mis", "v_kly"}


def _extract_gender_case_pairs(tags: str) -> set[tuple[str, str]]:
    """Extract (gender, case) pairs from a VESUM tag string."""
    parts = tags.split(":")
    genders = [p for p in parts if p in _GENDER_CODES]
    cases = [p for p in parts if p in _CASE_CODES]
    return {(g, c) for g in genders for c in cases}


# Words that VESUM tags as adj but function as pronouns/particles — skip in agreement
_AGREEMENT_SKIP = {
    "це", "то", "той", "та", "те", "ті", "цей", "ця", "ці",
    "який", "яка", "яке", "які", "весь", "вся", "все", "всі",
    "мій", "моя", "моє", "мої", "твій", "твоя", "твоє", "твої",
    "наш", "наша", "наше", "наші", "ваш", "ваша", "ваше", "ваші",
    "його", "її", "їх", "свій", "своя", "своє", "свої",
    "сам", "сама", "саме", "самі", "кожний", "кожна", "кожне", "кожні",
    "інший", "інша", "інше", "інші", "такий", "така", "таке", "такі",
}


def check_agreement(
    word_lines: list[tuple[str, int, str]],
    vesum_results: dict[str, list[dict]],
    max_issues: int = 5,
) -> list[dict]:
    """Check adjacent adjective-noun pairs for gender/case agreement."""
    issues: list[dict] = []
    seen: set[str] = set()

    # Group words by line, with full_line for boundary checking
    by_line: dict[int, list[tuple[str, str, str]]] = {}  # line -> [(orig, lower, full_line)]
    for word, line_num, full_line in word_lines:
        word_clean = word.replace(_STRESS_MARK, "")
        word_lower = word_clean.lower()
        by_line.setdefault(line_num, []).append((word, word_lower, full_line))

    _SENT_BOUNDARY_RE = re.compile(r"[.!?;]")

    for line_num, words in by_line.items():
        if len(issues) >= max_issues:
            break
        for i in range(len(words) - 1):
            orig_a, lower_a, full_line = words[i]
            orig_b, lower_b, _ = words[i + 1]

            # Check if there's a sentence boundary between the two words
            clean_a = orig_a.replace(_STRESS_MARK, "")
            clean_b = orig_b.replace(_STRESS_MARK, "")
            idx_a = full_line.find(clean_a)
            idx_b = full_line.find(clean_b, idx_a + len(clean_a) if idx_a >= 0 else 0)
            if idx_a >= 0 and idx_b >= 0:
                between = full_line[idx_a + len(clean_a):idx_b]
                if _SENT_BOUNDARY_RE.search(between):
                    continue  # Different sentences

            # Strip stress marks for VESUM lookup
            lookup_a = lower_a.replace(_STRESS_MARK, "")
            lookup_b = lower_b.replace(_STRESS_MARK, "")

            # Skip pronouns/determiners that VESUM tags as adj
            if lookup_a in _AGREEMENT_SKIP or lookup_b in _AGREEMENT_SKIP:
                continue

            matches_a = vesum_results.get(lookup_a, [])
            matches_b = vesum_results.get(lookup_b, [])
            if not matches_a or not matches_b:
                continue

            # Skip words that are primarily adverbs (e.g., "дуже")
            a_has_adv = any(m["pos"] == "adv" for m in matches_a)
            b_has_adv = any(m["pos"] == "adv" for m in matches_b)
            if a_has_adv or b_has_adv:
                continue

            # Check if A is adj and B is noun (or vice versa)
            a_is_adj = any(m["pos"] == "adj" for m in matches_a)
            b_is_noun = any(m["pos"] in ("noun", "adj") for m in matches_b)
            # Also check reverse: noun then adj
            a_is_noun = any(m["pos"] in ("noun",) for m in matches_a)
            b_is_adj = any(m["pos"] == "adj" for m in matches_b)

            adj_matches = None
            noun_matches = None
            adj_word = None
            noun_word = None

            if a_is_adj and b_is_noun:
                adj_matches = [m for m in matches_a if m["pos"] == "adj"]
                noun_matches = [m for m in matches_b if m["pos"] in ("noun", "adj")]
                adj_word, noun_word = orig_a, orig_b
            elif a_is_noun and b_is_adj:
                noun_matches = [m for m in matches_a if m["pos"] in ("noun",)]
                adj_matches = [m for m in matches_b if m["pos"] == "adj"]
                adj_word, noun_word = orig_b, orig_a
            else:
                continue

            # Get all gender+case combos for each
            adj_gc = set()
            for m in adj_matches:
                adj_gc |= _extract_gender_case_pairs(m["tags"])
            noun_gc = set()
            for m in noun_matches:
                noun_gc |= _extract_gender_case_pairs(m["tags"])

            # If no overlap → agreement error
            if adj_gc and noun_gc and not (adj_gc & noun_gc):
                dedup_key = f"agr:{lookup_a}:{lookup_b}"
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                adj_genders = {g for g, _ in adj_gc}
                noun_genders = {g for g, _ in noun_gc}
                issues.append({
                    "type": "AGREEMENT_ERROR",
                    "severity": "HIGH",
                    "location": f"~line {line_num}",
                    "text": (
                        f"Agreement mismatch: '{adj_word}' ({'/'.join(sorted(adj_genders))}) "
                        f"+ '{noun_word}' ({'/'.join(sorted(noun_genders))})"
                    ),
                    "fix": (
                        f"Change '{adj_word}' to match the gender/case of '{noun_word}', "
                        f"or vice versa."
                    ),
                })
    return issues
