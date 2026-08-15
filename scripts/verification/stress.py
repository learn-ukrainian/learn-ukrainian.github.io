"""Stress oracle: stressed form + stressed-vowel index for a Ukrainian word.

Implements the design pinned on issue #6515 (design note + K3 cross-family
review + round-2 revision — see the issue for the full rationale). Summary
of the contract this module implements:

- Source of truth: the offline `ukrainian_word_stress` trie (ULIF-derived,
  ``ukrainian_word_stress/data/stress.trie``), looked up on-demand via
  ``Disambiguation.Dictionary`` (no Stanza — sentence context doesn't apply
  to isolated single-word oracle calls).
- ``vowel_index`` uses the same convention as
  ``scripts/audit/generate_practice_deck.py::_stress_position``: the 0-based
  codepoint index of the stressed vowel in the NFC-normalized unstressed
  form. That convention is what ``site/src/components/PracticeStress.tsx``
  already consumes.
- U+0301/U+0300 handling follows the #5375/#6832 convention: strip combining
  stress marks for the lookup key, keep the caller's original bytes in
  ``input``.
- ``scripts/data/stress_overrides.yaml`` is applied as a pre-lookup patch,
  keyed by *exact* lemma string match only (never extended to inflected
  forms) — matching its one existing consumer,
  ``scripts/generate_mdx/generate_ipa.py``.
- The trie packs ambiguous readings into a private byte layout
  (``compile_dict.py``'s ``POS_SEP``/``REC_SEP``/``accent_pos`` scheme) that
  the package's public API (``Stressifier``, ``find_accent_positions``)
  collapses into a single resolved answer. Enumerating separate readings —
  required for ``status="ambiguous"`` — needs that packed layout directly.
  Round-2 design note §3c sanctions this, gated by the version pin
  (``requirements-lock.txt``) + the trie digest below: a package bump
  changes the digest, which forces revalidation, and
  ``TestStressGolden::test_zamok_golden_entry`` (tests/test_stress_oracle.py)
  fails loudly if the packing format itself changes.
- Some ambiguous entries have byte-identical required_tags across distinct
  stress positions (true meaning-dependent homographs, e.g. за́мок "castle"
  vs замо́к "lock" — both ``Number=Sing|Case=Nom|Gender=Masc|upos=NOUN``).
  No tag combination the dictionary offers can disambiguate those further;
  see ``unresolvable_by_tags`` in the return payload.
- VESUM (``data/vesum.db``) and the stress dictionary are two disjoint
  dictionaries with no shared key beyond the ``word_form`` string itself —
  VESUM carries zero stress information. The VESUM join here is
  intentionally conservative: it only attaches a VESUM record to a reading
  when exactly one VESUM row is left after filtering by the reading's own
  ``upos`` tag (when it has one); anything more ambiguous is left ``null``
  rather than guessed.
- Not implemented (explicitly out of scope for this PR, per the design
  note's own framing as an optional "keep the door open" cross-check, not a
  pinned deliverable): the ``query_ulif`` live cross-check and the mphdict
  headword cross-check. Both are hydration/network-dependent and orthogonal
  to correctness — the trie stays the sole source of truth.

Extension beyond the pinned schema, needed for correctness: hyphenated
compound entries (e.g. "попереково-крижовими") can carry *more than one*
stress mark in a single trie value. The pinned schema's ``vowel_index`` stays
a single int (the primary/lowest-index mark, for schema compatibility);
``vowel_indices`` (plural, always present) carries the full list.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STRESS_OVERRIDES_PATH = PROJECT_ROOT / "scripts" / "data" / "stress_overrides.yaml"

_STRESS_MARK_RE = re.compile("[\u0300\u0301]")  # combining grave + acute accent
_UKRAINIAN_WORD_RE = re.compile(r"^[А-Яа-яЄєІіЇїҐґ'’ʼ-]+$")
_UKRAINIAN_VOWELS = frozenset("аеєиіїоуюяАЕЄИІЇОУЮЯ")

# UD upos (as decompressed from the trie's packed tag bytes) -> VESUM `pos`
# column value. Best-effort, used only to narrow the VESUM join for readings
# that carry an upos tag; an unmapped/absent upos just skips the filter.
_UPOS_TO_VESUM_POS = {
    "NOUN": "noun",
    "PROPN": "noun",
    "VERB": "verb",
    "ADJ": "adj",
    "ADV": "adv",
    "NUM": "numr",
    "ADP": "prep",
    "CCONJ": "conj",
    "PART": "part",
    "INTJ": "intj",
}


def _strip_stress(text: str) -> str:
    """U+0301/U+0300-stripped, NFC-normalized form (the #5375/#6832 convention)."""
    normalized = unicodedata.normalize("NFKD", text)
    normalized = _STRESS_MARK_RE.sub("", normalized)
    return unicodedata.normalize("NFC", normalized)


def _has_whitespace(text: str) -> bool:
    return any(ch.isspace() for ch in text)


def _count_vowels(text: str) -> int:
    return sum(1 for ch in text if ch in _UKRAINIAN_VOWELS)


def _stress_positions_in_marked_string(marked: str) -> tuple[str, list[int]]:
    """Return (unstressed NFC form, [0-based codepoint vowel indices]).

    Generalizes ``generate_practice_deck.py::_stress_position`` (which
    handles exactly one mark) to any number of combining stress marks, for
    hyphenated-compound and override-yaml inputs.
    """
    nfd = unicodedata.normalize("NFD", marked)
    indices: list[int] = []
    working: list[str] = []
    for ch in nfd:
        if ch in ("\u0301", "\u0300"):
            prefix_nfc = unicodedata.normalize("NFC", "".join(working))
            indices.append(len(prefix_nfc) - 1)
        else:
            working.append(ch)
    unstressed_nfc = unicodedata.normalize("NFC", "".join(working))
    return unstressed_nfc, indices


@lru_cache(maxsize=1)
def _load_overrides() -> dict[str, str]:
    if not STRESS_OVERRIDES_PATH.exists():
        return {}
    with open(STRESS_OVERRIDES_PATH, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _trie_path() -> Path:
    import ukrainian_word_stress

    return Path(ukrainian_word_stress.__file__).resolve().parent / "data" / "stress.trie"


@lru_cache(maxsize=1)
def _load_trie():
    import marisa_trie

    trie = marisa_trie.BytesTrie()
    trie.load(str(_trie_path()))
    return trie


@lru_cache(maxsize=1)
def _trie_digest() -> str:
    digest = hashlib.sha256()
    with open(_trie_path(), "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


@lru_cache(maxsize=1)
def _package_version() -> str:
    import importlib.metadata

    return importlib.metadata.version("ukrainian-word-stress")


def source_info() -> dict[str, Any]:
    """Reproducibility envelope: package version + trie entry count + digest."""
    trie = _load_trie()
    return {
        "dictionary": "ukrainian-word-stress (ULIF-derived)",
        "package_version": _package_version(),
        "trie_entries": len(trie),
        "digest": _trie_digest(),
    }


def _trie_value(trie, word: str) -> bytes | None:
    """Exact + case/apostrophe-variant lookup.

    Mirrors ``ukrainian_word_stress.stressify_._trie_value``'s fallback
    order. Reimplemented (rather than imported) so the hot lookup path
    doesn't depend on a leading-underscore package-private symbol; only the
    genuinely undocumented part — the packed-value byte layout, parsed by
    ``_parse_dictionary_value`` below — is sanctioned private-API use.
    """
    if word in trie:
        return trie[word][0]
    candidates = [word.lower(), word.title(), word.capitalize()]
    normalized = word.translate(str.maketrans("’ʼ`", "'''"))
    if normalized != word:
        candidates += [normalized, normalized.lower(), normalized.title(), normalized.capitalize()]
    for candidate in candidates:
        if candidate != word and candidate in trie:
            return trie[candidate][0]
    return None


def _parse_dictionary_value(value: bytes) -> list[tuple[list[str], list[int]]]:
    """Enumerate every (required_tags, accent_positions) reading packed into
    one trie value. See the module docstring for why this needs the
    package-private byte layout.
    """
    from ukrainian_word_stress.tags import TAGS, decompress_tags

    pos_sep = TAGS["POS-separator"]
    rec_sep = TAGS["Record-separator"]

    if rec_sep not in value:
        return [([], [int(b) for b in value])]

    readings: list[tuple[list[str], list[int]]] = []
    for item in value.split(rec_sep):
        if not item:
            continue
        accents, _, tags = item.partition(pos_sep)
        readings.append((decompress_tags(tags), [int(b) for b in accents]))
    return readings


def _apply_accents(base: str, positions: list[int]) -> str:
    for position in sorted(positions, reverse=True):
        base = base[:position] + "\u0301" + base[position:]
    return base


def _classify_invalid(clean: str) -> str | None:
    """Return an error message if `clean` can't be stress-checked, else None.

    Mirrors ``scripts/lexicon/enrich_manifest.py::_stress_word``'s guard
    order (empty -> multi-word -> non-Cyrillic -> too-short-to-have-stress),
    surfaced as a distinct ``invalid_input`` status per round-2 §3(d) rather
    than being folded into ``not_found``.
    """
    if not clean:
        return "empty or whitespace-only input"
    if _has_whitespace(clean):
        return "multi-word input (verify_stress takes a single word)"
    if not _UKRAINIAN_WORD_RE.fullmatch(clean):
        return "not a single Ukrainian word (non-Cyrillic or disallowed characters)"
    if _count_vowels(clean) < 2:
        return "single-syllable word (no stress position to mark)"
    return None


def _normalize_supplied_tags(pos: str | None, tags: str | list[str] | None) -> set[str]:
    supplied: set[str] = set()
    if pos:
        pos_clean = pos.strip()
        if pos_clean:
            supplied.add(pos_clean if pos_clean.startswith("upos=") else f"upos={pos_clean.upper()}")
    if isinstance(tags, str):
        tags = re.split(r"[,\s]+", tags.strip())
    if tags:
        supplied.update(tag.strip() for tag in tags if tag and tag.strip())
    return supplied


def _vesum_lookup(word_form: str) -> list[dict]:
    """Best-effort VESUM lookup; never raises (VESUM join is supplementary)."""
    try:
        from scripts.verification.vesum import verify_word

        return verify_word(word_form)
    except Exception:
        return []


def _attach_vesum(match: dict[str, Any], vesum_matches: list[dict]) -> None:
    candidates = vesum_matches
    upos = next((tag.split("=", 1)[1] for tag in match["required_tags"] if tag.startswith("upos=")), None)
    vesum_pos = _UPOS_TO_VESUM_POS.get(upos) if upos else None
    if vesum_pos:
        filtered = [m for m in candidates if m.get("pos") == vesum_pos]
        candidates = filtered
    match["vesum"] = candidates[0] if len(candidates) == 1 else None


def _apply_input_mismatch(matches: list[dict[str, Any]], word: str) -> None:
    if not _STRESS_MARK_RE.search(unicodedata.normalize("NFD", word)):
        return  # no stress mark in the caller's input: key stays omitted
    _, caller_positions = _stress_positions_in_marked_string(word)
    caller_set = set(caller_positions)
    for match in matches:
        match["input_mismatch"] = caller_set != set(match["vowel_indices"])


def _build_match(unstressed_form: str, positions: list[int], required_tags: list[str], *, override_applied: bool) -> dict[str, Any]:
    vowel_indices = sorted(p - 1 for p in positions)
    return {
        "stressed_form": _apply_accents(unstressed_form, positions),
        "unstressed_form": unstressed_form,
        "vowel_index": vowel_indices[0],
        "vowel_indices": vowel_indices,
        "vesum": None,
        "required_tags": required_tags,
        "override_applied": override_applied,
    }


def _readings_unresolvable_by_tags(candidates: list[dict[str, Any]]) -> bool:
    """True if >=2 candidates share byte-identical required_tags with
    different stress positions — a true meaning-dependent homograph the
    dictionary's tag vocabulary can never disambiguate (round-2 §3b)."""
    seen: dict[tuple[str, ...], set[tuple[int, ...]]] = {}
    for match in candidates:
        key = tuple(match["required_tags"])
        seen.setdefault(key, set()).add(tuple(match["vowel_indices"]))
    return any(len(positions) > 1 for positions in seen.values())


def verify_stress(word: str, pos: str | None = None, tags: str | list[str] | None = None) -> dict[str, Any]:
    """Look up the stress position of a Ukrainian word.

    Args:
        word: bare lemma, inflected form, or U+0301/U+0300-marked form.
        pos: optional POS to help disambiguate a heteronym (e.g. "NOUN" or
            "upos=NOUN").
        tags: optional additional dictionary-native tags to help
            disambiguate (e.g. "Case=Nom,Gender=Masc" or
            ["Case=Nom", "Gender=Masc"]) — same vocabulary as each match's
            own ``required_tags``.

    Returns:
        The JSON-shaped envelope documented in the module docstring / issue
        #6515.
    """
    lookup_key = _strip_stress(word).strip()
    invalid_reason = _classify_invalid(lookup_key)
    source = source_info()

    if invalid_reason is not None:
        return {
            "input": word,
            "lookup_key": lookup_key,
            "status": "invalid_input",
            "matches": [],
            "unresolvable_by_tags": False,
            "source": source,
            "error": invalid_reason,
        }

    override = _load_overrides().get(lookup_key)
    if override:
        unstressed_override, positions = _stress_positions_in_marked_string(override)
        matches = [_build_match(unstressed_override, [p + 1 for p in positions], [], override_applied=True)]
        status = "ok"
    else:
        trie = _load_trie()
        value = _trie_value(trie, lookup_key)
        if value is None:
            return {
                "input": word,
                "lookup_key": lookup_key,
                "status": "not_found",
                "matches": [],
                "unresolvable_by_tags": False,
                "source": source,
            }

        readings = _parse_dictionary_value(value)
        all_matches = [
            _build_match(lookup_key, positions, required_tags, override_applied=False)
            for required_tags, positions in readings
        ]

        if len(all_matches) == 1:
            matches = all_matches
            status = "ok"
        else:
            supplied = _normalize_supplied_tags(pos, tags)
            filtered = [m for m in all_matches if supplied and set(m["required_tags"]) <= supplied]
            candidates = filtered if filtered else all_matches
            matches = candidates
            status = "ok" if len(candidates) == 1 else "ambiguous"

    _apply_input_mismatch(matches, word)

    vesum_matches = _vesum_lookup(matches[0]["unstressed_form"]) if matches else []
    for match in matches:
        _attach_vesum(match, vesum_matches)

    return {
        "input": word,
        "lookup_key": lookup_key,
        "status": status,
        "matches": matches,
        "unresolvable_by_tags": status == "ambiguous" and _readings_unresolvable_by_tags(matches),
        "source": source,
    }
