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

# Strikethrough content (~~wrong form~~) — deliberate errors to strip before checking
_STRIKETHROUGH_RE = re.compile(r"~~[^~]+~~")

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
    return any(word_lower in chunk and chunk in line_lower for chunk in chunks)


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
    # HTML comment <!-- deliberate-error --> — skip entire line
    if "<!-- deliberate-error" in stripped:
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
        return cyrillic == 0  # Validate callout content only if it has Cyrillic
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
    if any(marker in stripped for marker in ("WRONG:", "INCORRECT:", "❌")):
        return True
    # Pure English lines (no Ukrainian words to check)
    cyrillic = sum(1 for c in stripped if '\u0400' <= c <= '\u04ff')
    # Don't skip English-dominant lines — _CYRILLIC_TOKEN_RE already isolates
    # Ukrainian words, so even "The word **книгу** means..." gets checked.
    return cyrillic == 0


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


def _extract_word_lines(content_clean: str) -> list[tuple[str, int, str]]:
    """Extract (word, line_num, full_line) tuples from content, skipping non-prose lines."""
    word_lines: list[tuple[str, int, str]] = []
    lines = content_clean.split("\n")
    for line_num, line in enumerate(lines, 1):
        if _should_skip_line(line):
            continue
        tokens = _CYRILLIC_TOKEN_RE.findall(line)
        for token in tokens:
            word_lines.append((token, line_num, line))
    return word_lines


def _check_imperative(
    word: str, line_num: int, matches: list[dict],
) -> dict | None:
    """Check for imperative violation. Returns issue dict or None."""
    non_impr = [m for m in matches if "impr" not in m["tags"]]
    if non_impr:
        return None
    impr_tags = next(m["tags"] for m in matches if "impr" in m["tags"])
    return {
        "type": "MORPHOLOGICAL_VIOLATION",
        "severity": "HIGH",
        "location": f"~line {line_num}",
        "text": f"Imperative '{word}' (VESUM: {impr_tags}) — imperatives not taught until M47.",
        "fix": f"Replace '{word}' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.",
    }


def _check_no_verbs(
    word: str, line_num: int, module_num: int, matches: list[dict],
) -> dict | None:
    """Check for verb-forbidden violation. Returns issue dict or None."""
    verb_tags = matches[0]["tags"]
    return {
        "type": "MORPHOLOGICAL_VIOLATION",
        "severity": "HIGH",
        "location": f"~line {line_num}",
        "text": f"Verb '{word}' (VESUM: {verb_tags}) in pre-verb module M{module_num}. Verbs are forbidden before M15.",
        "fix": f"Replace verb '{word}' with an English equivalent or a noun phrase. Students haven't learned verbs yet.",
    }


def _check_no_accusative(
    word: str, line_num: int, module_num: int, matches: list[dict],
) -> dict | None:
    """Check for accusative violation. Returns issue dict or None."""
    for match in matches:
        if match["pos"] in ("noun", "adj") and "v_zna" in match["tags"]:
            has_non_acc = any(
                m["pos"] not in ("noun", "adj") or "v_zna" not in m["tags"]
                for m in matches
            )
            if not has_non_acc:
                return {
                    "type": "MORPHOLOGICAL_VIOLATION",
                    "severity": "HIGH",
                    "location": f"~line {line_num}",
                    "text": f"Accusative '{word}' (VESUM: {match['tags']}) in M{module_num}. Accusative not taught until M25.",
                    "fix": f"Replace '{word}' (accusative) with nominative form or use English equivalent.",
                }
            break
    return None


def _check_nominative_only(
    word: str, line_num: int, module_num: int, matches: list[dict],
) -> dict | None:
    """Check for non-nominative case violation. Returns issue dict or None."""
    has_non_nominal = any(m["pos"] not in ("noun", "adj") for m in matches)
    if has_non_nominal:
        return None
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
                    return {
                        "type": "MORPHOLOGICAL_VIOLATION",
                        "severity": "HIGH",
                        "location": f"~line {line_num}",
                        "text": f"Non-nominative '{word}' ({case_label}, VESUM: {match['tags']}) in M{module_num}. Only nominative case allowed before M25.",
                        "fix": f"Replace '{word}' ({case_label}) with its nominative form or use English equivalent.",
                    }
            break
    return None


def _check_present_only(
    word: str, line_num: int, module_num: int, matches: list[dict],
) -> dict | None:
    """Check for non-present tense violation. Returns issue dict or None."""
    for match in matches:
        if match["pos"] == "verb":
            tense = _parse_tense(match["tags"])
            if tense in ("past", "futr"):
                has_valid = any(
                    m["pos"] != "verb"
                    or _parse_tense(m["tags"]) in ("pres", "inf", None)
                    for m in matches
                )
                if not has_valid:
                    return {
                        "type": "MORPHOLOGICAL_VIOLATION",
                        "severity": "HIGH",
                        "location": f"~line {line_num}",
                        "text": f"Non-present verb '{word}' ({tense} tense, VESUM: {match['tags']}) in M{module_num}. Only present tense available before M36.",
                        "fix": f"Replace '{word}' with present tense form or English.",
                    }
            break
    return None


def _check_word_constraints(
    word: str, line_num: int, module_num: int,
    matches: list[dict], constraints: GrammarConstraint,
) -> dict | None:
    """Check a single word against all grammar constraints. Returns first violation or None."""
    all_pos = {m["pos"] for m in matches}
    all_tags = [m["tags"] for m in matches]
    has_verb = "verb" in all_pos
    only_verb = all_pos == {"verb"}
    has_impr = any("impr" in t for t in all_tags)

    if constraints.no_imperatives and has_impr:
        issue = _check_imperative(word, line_num, matches)
        if issue:
            return issue

    if constraints.no_verbs and only_verb:
        return _check_no_verbs(word, line_num, module_num, matches)

    if constraints.no_accusative:
        issue = _check_no_accusative(word, line_num, module_num, matches)
        if issue:
            return issue

    if constraints.nominative_only:
        issue = _check_nominative_only(word, line_num, module_num, matches)
        if issue:
            return issue

    if constraints.present_only and has_verb:
        issue = _check_present_only(word, line_num, module_num, matches)
        if issue:
            return issue

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

    from rag_batch_verify import vesum_batch_lookup

    constraints = _get_constraints(track, module_num)
    allowed_chunks = _get_allowed_chunks(module_num)
    issues: list[dict] = []

    content_clean = _STRIKETHROUGH_RE.sub("", content)
    word_lines = _extract_word_lines(content_clean)

    if not word_lines:
        return []

    unique_words = list({w.lower().replace(_STRESS_MARK, "") for w, _, _ in word_lines})
    vesum_results = vesum_batch_lookup(unique_words)

    seen_violations: set[str] = set()

    for word, line_num, full_line in word_lines:
        if len(issues) >= max_issues:
            break

        word_clean = word.replace(_STRESS_MARK, "")
        word_lower = word_clean.lower()

        if len(word_clean) <= 1:
            continue

        if _is_in_allowed_chunk(word.replace(_STRESS_MARK, ""), full_line.replace(_STRESS_MARK, ""), allowed_chunks):
            continue

        matches = vesum_results.get(word_lower, [])
        if not matches:
            continue

        dedup_key = f"{word_lower}:{line_num}"
        if dedup_key in seen_violations:
            continue

        issue = _check_word_constraints(word, line_num, module_num, matches, constraints)
        if issue:
            seen_violations.add(dedup_key)
            issues.append(issue)

    replacement_issues = check_replacements(content_clean, max_issues=max_issues - len(issues))
    issues.extend(replacement_issues)

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
            with open(_LT_PATH) as f:
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
        # Strip deliberate errors (~~wrong form~~) before tokenizing
        clean_line = _STRIKETHROUGH_RE.sub("", line)
        tokens = _CYRILLIC_TOKEN_RE.findall(clean_line)
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


def _group_words_by_line(
    word_lines: list[tuple[str, int, str]],
) -> dict[int, list[tuple[str, str, str]]]:
    """Group words by line number. Returns line_num -> [(orig, lower, full_line)]."""
    by_line: dict[int, list[tuple[str, str, str]]] = {}
    for word, line_num, full_line in word_lines:
        word_clean = word.replace(_STRESS_MARK, "")
        word_lower = word_clean.lower()
        by_line.setdefault(line_num, []).append((word, word_lower, full_line))
    return by_line


def _has_sentence_boundary(orig_a: str, orig_b: str, full_line: str) -> bool:
    """Check if there's a sentence boundary between two adjacent words."""
    _SENT_BOUNDARY_RE = re.compile(r"[.!?;]")
    clean_a = orig_a.replace(_STRESS_MARK, "")
    clean_b = orig_b.replace(_STRESS_MARK, "")
    idx_a = full_line.find(clean_a)
    idx_b = full_line.find(clean_b, idx_a + len(clean_a) if idx_a >= 0 else 0)
    if idx_a >= 0 and idx_b >= 0:
        between = full_line[idx_a + len(clean_a):idx_b]
        return bool(_SENT_BOUNDARY_RE.search(between))
    return False


def _resolve_adj_noun_pair(
    matches_a: list[dict], matches_b: list[dict],
    orig_a: str, orig_b: str,
) -> tuple[list[dict] | None, list[dict] | None, str | None, str | None]:
    """Identify adj-noun pair from two adjacent words. Returns (adj_matches, noun_matches, adj_word, noun_word) or all-None."""
    a_is_adj = any(m["pos"] == "adj" for m in matches_a)
    b_is_noun = any(m["pos"] in ("noun", "adj") for m in matches_b)
    a_is_noun = any(m["pos"] in ("noun",) for m in matches_a)
    b_is_adj = any(m["pos"] == "adj" for m in matches_b)

    if a_is_adj and b_is_noun:
        return (
            [m for m in matches_a if m["pos"] == "adj"],
            [m for m in matches_b if m["pos"] in ("noun", "adj")],
            orig_a, orig_b,
        )
    elif a_is_noun and b_is_adj:
        return (
            [m for m in matches_b if m["pos"] == "adj"],
            [m for m in matches_a if m["pos"] in ("noun",)],
            orig_b, orig_a,
        )
    return None, None, None, None


def _check_pair_agreement(
    adj_matches: list[dict], noun_matches: list[dict],
    adj_word: str, noun_word: str, line_num: int,
) -> dict | None:
    """Check gender/case agreement for an adj-noun pair. Returns issue dict or None."""
    adj_gc: set[tuple[str, str]] = set()
    for m in adj_matches:
        adj_gc |= _extract_gender_case_pairs(m["tags"])
    noun_gc: set[tuple[str, str]] = set()
    for m in noun_matches:
        noun_gc |= _extract_gender_case_pairs(m["tags"])

    if adj_gc and noun_gc and not (adj_gc & noun_gc):
        adj_genders = {g for g, _ in adj_gc}
        noun_genders = {g for g, _ in noun_gc}
        return {
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
        }
    return None


def check_agreement(
    word_lines: list[tuple[str, int, str]],
    vesum_results: dict[str, list[dict]],
    max_issues: int = 5,
) -> list[dict]:
    """Check adjacent adjective-noun pairs for gender/case agreement."""
    issues: list[dict] = []
    seen: set[str] = set()

    by_line = _group_words_by_line(word_lines)

    for line_num, words in by_line.items():
        if len(issues) >= max_issues:
            break
        for i in range(len(words) - 1):
            orig_a, lower_a, full_line = words[i]
            orig_b, lower_b, _ = words[i + 1]

            if _has_sentence_boundary(orig_a, orig_b, full_line):
                continue

            lookup_a = lower_a.replace(_STRESS_MARK, "")
            lookup_b = lower_b.replace(_STRESS_MARK, "")

            if lookup_a in _AGREEMENT_SKIP or lookup_b in _AGREEMENT_SKIP:
                continue

            matches_a = vesum_results.get(lookup_a, [])
            matches_b = vesum_results.get(lookup_b, [])
            if not matches_a or not matches_b:
                continue

            if any(m["pos"] == "adv" for m in matches_a) or any(m["pos"] == "adv" for m in matches_b):
                continue

            adj_matches, noun_matches, adj_word, noun_word = _resolve_adj_noun_pair(
                matches_a, matches_b, orig_a, orig_b,
            )
            if adj_matches is None:
                continue

            dedup_key = f"agr:{lookup_a}:{lookup_b}"
            if dedup_key in seen:
                continue

            issue = _check_pair_agreement(adj_matches, noun_matches, adj_word, noun_word, line_num)
            if issue:
                seen.add(dedup_key)
                issues.append(issue)
    return issues
