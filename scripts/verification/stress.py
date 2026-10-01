"""ULIF-first per-form stress oracle (#8398 / #8400).

Exact-form overrides remain authoritative. Only homonym-checked ULIF rows
from a complete forms build are evidence. All agreeing readings collapse
with their row/entry ids; distinct stress choices remain ambiguous unless
caller lemma or morphology resolves them. Dual stress retains both variants
and the source's pedagogical choice. The packed ukrainian-word-stress trie
is a labelled fallback. No dictionary reading means pending, never a guess.

The legacy source envelope is preserved; its digest now covers both source
identities. Per-reading ``source`` and per-result ``stress_source`` name the
selected authority. Vowel indices remain 0-based NFC codepoint offsets.
"""

from __future__ import annotations

import hashlib
import json
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
def _load_override_data() -> dict[str, Any]:
    if not STRESS_OVERRIDES_PATH.exists():
        return {}
    with open(STRESS_OVERRIDES_PATH, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _load_overrides() -> dict[str, str]:
    return {key: value for key, value in _load_override_data().items() if key != "stress_pending"}


def pending_stress_reason(word: str) -> str | None:
    """Why an exact surface form must not use an unconfirmed trie reading."""
    pending = _load_override_data().get("stress_pending", {})
    return pending.get(word) if isinstance(pending, dict) else None


@lru_cache(maxsize=1)
def _trie_path() -> Path:
    import ukrainian_word_stress

    return Path(ukrainian_word_stress.__file__).resolve().parent / "data" / "stress.trie"


def _trie_signature() -> tuple[Path, int, int, int]:
    path = _trie_path()
    stat = path.stat()
    return path, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


@lru_cache(maxsize=1)
def _load_trie_at(signature: tuple[Path, int, int, int]):
    import marisa_trie

    trie = marisa_trie.BytesTrie()
    trie.load(str(signature[0]))
    return trie


def _load_trie():
    """Reload the fallback if its on-disk snapshot changes in a long-lived MCP."""
    return _load_trie_at(_trie_signature())


@lru_cache(maxsize=1)
def _trie_digest_at(signature: tuple[Path, int, int, int]) -> str:
    digest = hashlib.sha256()
    with open(signature[0], "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _trie_digest() -> str:
    return _trie_digest_at(_trie_signature())


@lru_cache(maxsize=1)
def _package_version() -> str:
    import importlib.metadata

    return importlib.metadata.version("ukrainian-word-stress")


def source_info() -> dict[str, Any]:
    """Both authority digests; the combined digest invalidates all stress caches."""
    from scripts.wiki.sources_db import ulif_stress_build

    build = ulif_stress_build()
    ulif_digest = hashlib.sha256(json.dumps(build, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    trie_digest = _trie_digest()
    digest = hashlib.sha256(f"{ulif_digest}:{trie_digest}".encode()).hexdigest()
    return {
        "dictionary": "ukrainian-word-stress (ULIF-derived)",
        "package_version": _package_version(),
        "trie_entries": len(_load_trie()),
        "trie_digest": trie_digest,
        "ulif": {"dictionary": "ULIF ulif_forms (homonym_checked=1)", "build": build, "digest": ulif_digest},
        "digest": digest,
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
        tags = re.split(r"[:|,\s]+", tags.strip())
    if tags:
        from scripts.curriculum.evidence.tags import TagMapper

        atoms = [tag for tag in tags if "=" not in tag]
        supplied.update(TagMapper()(":".join(atoms)) if atoms else [])
        supplied.update(tag.strip() for tag in tags if tag and "=" in tag and tag.strip())
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
        allowed = set(match["vowel_indices"])
        match["input_mismatch"] = not (
            caller_set == allowed or (match.get("dual_stress") and len(caller_set) == 1 and caller_set <= allowed)
        )


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


def transfer_stress_marks(marked_src: str, dest_unstressed: str) -> str:
    """Copy combining-acute positions from *marked_src* onto *dest_unstressed*.

    Used to keep the caller's capitalization while applying a dictionary or
    override form. If the unstressed lengths differ, *dest_unstressed* is
    returned unchanged.
    """
    _, indices = _stress_positions_in_marked_string(marked_src)
    if not indices:
        return dest_unstressed
    if len(_strip_stress(marked_src)) != len(dest_unstressed):
        return dest_unstressed
    out = dest_unstressed
    for index in sorted(indices, reverse=True):
        if index < 0 or index >= len(out):
            return dest_unstressed
        out = out[: index + 1] + "\u0301" + out[index + 1 :]
    return out


def pedagogical_stressed_form(match: dict[str, Any]) -> str:
    """Single-acute learner form for one ``verify_stress`` match.

    The ULIF trie packs dual-acceptable positions (подвійний наголос) and
    occasional primary+secondary into one ``stressed_form`` with two acutes
    (``ро́збі́р``, ``за́вжди́``). A1/A2 pedagogy marks one vowel. Hyphenated
    compounds keep every mark. Overrides already encode the intended form.

    For non-hyphenated packed readings the last marked vowel is the
    primary (``розбі́р``, ``кори́сний``). First-syllable duals such as
    ``завжди`` / ``також`` belong in ``stress_overrides.yaml``.
    """
    if match.get("pedagogical_stressed_form") and not match.get("pedagogical_conflict"):
        return transfer_stress_marks(match["pedagogical_stressed_form"], match["unstressed_form"])
    form = match["stressed_form"]
    unstressed = match["unstressed_form"]
    if match.get("override_applied") or "-" in unstressed:
        return form
    indices = list(match.get("vowel_indices") or [])
    if len(indices) <= 1:
        return form
    if match.get("source") == "ulif":
        return form  # no source teaching choice: preserve both, never guess
    keep = indices[-1]
    return unstressed[: keep + 1] + "\u0301" + unstressed[keep + 1 :]


def _readings_unresolvable_by_tags(candidates: list[dict[str, Any]]) -> bool:
    """True if >=2 candidates share byte-identical required_tags with
    different stress positions — a true meaning-dependent homograph the
    dictionary's tag vocabulary can never disambiguate (round-2 §3b)."""
    seen: dict[tuple[str, ...], set[tuple[int, ...]]] = {}
    for match in candidates:
        key = tuple(match["required_tags"])
        seen.setdefault(key, set()).add(tuple(match["vowel_indices"]))
    return any(len(positions) > 1 for positions in seen.values())


def verify_stress(word: str, pos: str | None = None, tags: str | list[str] | None = None,
                  lemma: str | None = None) -> dict[str, Any]:
    """Return source-attested stress; optional lemma, POS and UD/VESUM tags narrow readings.

    A stressed lemma can distinguish same-spelling lexical homographs. Bare
    lemmas, POS and tags never choose between indistinguishable meanings.
    The source envelope is retained for existing receipts; selected authority
    is in ``stress_source`` and each match's ``source``.
    """
    from scripts.verification.ulif_stress import compatible
    from scripts.verification.ulif_stress import readings as ulif_readings
    from scripts.wiki.sources_db import ulif_stress_rows

    lookup_key = _strip_stress(word).strip()
    source = source_info()
    result = {"input": word, "lookup_key": lookup_key, "status": "pending", "matches": [],
              "unresolvable_by_tags": False, "source": source, "stress_source": "pending"}
    invalid = _classify_invalid(lookup_key)
    if invalid is not None:
        result.update(status="invalid_input", error=invalid, stress_source=None)
        return result
    override = _load_overrides().get(lookup_key)
    if override:
        base, indices = _stress_positions_in_marked_string(override)
        matches = [_build_match(base, [i + 1 for i in indices], [], override_applied=True)]
        matches[0]["source"] = "override"
        result.update(stress_source="override", status="ok")
    elif reason := pending_stress_reason(lookup_key):
        result["reason"] = reason
        return result
    else:
        supplied = _normalize_supplied_tags(pos, tags)
        vesum = _vesum_lookup(lookup_key)
        trusted = ulif_stress_rows(lookup_key)
        matches = ulif_readings(lookup_key, supplied=supplied, lemma=lemma, vesum=vesum) if trusted else []
        if trusted:
            result["stress_source"] = "ulif"
            if not matches:
                result["reason"] = "no ULIF reading matches supplied context"
                return result
        else:
            value = _trie_value(_load_trie(), lookup_key)
            if value is None:
                result["reason"] = "no trusted dictionary reading"
                return result
            all_matches = [_build_match(lookup_key, positions, required, override_applied=False)
                           for required, positions in _parse_dictionary_value(value) if positions]
            matches = [m for m in all_matches if compatible(set(m["required_tags"]), supplied)]
            if not matches:
                result["reason"] = "no trie reading matches supplied context"
                return result
            for match in matches:
                match["source"] = "trie"
                _attach_vesum(match, vesum)
            result["stress_source"] = "trie"
        choices = {tuple(m["vowel_indices"]) for m in matches}
        result["status"] = "ok" if len(choices) == 1 else "ambiguous"
    _apply_input_mismatch(matches, word)
    if override:
        for match in matches:
            _attach_vesum(match, _vesum_lookup(match["unstressed_form"]))
    result.update(matches=matches,
                  unresolvable_by_tags=result["status"] == "ambiguous" and _readings_unresolvable_by_tags(matches))
    return result


def stress_call_summary(payload: dict[str, Any] | None, *, word: str | None = None) -> str:
    """One-line human summary of a ``verify_stress`` payload.

    The MCP text channel used to pretty-print the whole payload, which
    duplicated ``result`` and ``hits``. Callers that need the readings
    still read those structured fields.
    """
    if not isinstance(payload, dict) or not payload:
        if isinstance(word, str) and word.strip():
            return f"{word.strip()} — no result"
        return "invalid_input: word is required"

    label = str(payload.get("input") or (word.strip() if isinstance(word, str) else "") or "word")
    status = str(payload.get("status") or "unknown")
    if status == "invalid_input":
        reason = payload.get("error") or "word is required"
        line = f"{label} — invalid_input: {reason}"
    else:
        matches = payload.get("matches") if isinstance(payload.get("matches"), list) else []
        forms = [
            str(match.get("stressed_form"))
            for match in matches
            if isinstance(match, dict) and match.get("stressed_form")
        ]
        if forms:
            shown = ", ".join(forms[:3])
            if len(forms) > 3:
                shown += f" (+{len(forms) - 3} more)"
            line = f"{label} — {status}: {shown}"
        else:
            line = f"{label} — {status}"
    return " ".join(line.split())


STRESS_BATCH_CAP = 500


def _compact_stress_reading(match: dict[str, Any]) -> dict[str, Any]:
    reading: dict[str, Any] = {
        "stressed_form": match.get("stressed_form"),
        "vowel_indices": list(match.get("vowel_indices") or []),
        "required_tags": list(match.get("required_tags") or []),
        "override_applied": bool(match.get("override_applied")),
    }
    for key in ("source", "evidence", "grammatical_tags", "vesum_analyses", "dual_stress", "variants",
                "pedagogical_stressed_form", "pedagogical_conflict"):
        if key in match:
            reading[key] = match[key]
    vesum = match.get("vesum")
    if vesum is not None:
        reading["vesum"] = vesum
    return reading


def verify_stresses(words: list[str], pos: str | None = None, tags: str | list[str] | None = None,
                    lemma: str | None = None) -> dict[str, Any]:
    """Batch stress lookup. One compact record per word; source envelope once.

    Processes at most ``STRESS_BATCH_CAP`` words. A longer list is truncated
    and the response carries the same style of note as ``vet_vocabulary``.
    ``pos``, when set, is applied to every word in the batch.
    """
    if not isinstance(words, list) or not all(isinstance(word, str) for word in words):
        raise TypeError("words must be a list of strings")

    submitted = len(words)
    batch = words[:STRESS_BATCH_CAP]
    records: list[dict[str, Any]] = []
    source: dict[str, Any] | None = None
    for word in batch:
        result = verify_stress(word, pos=pos, tags=tags, lemma=lemma)
        if source is None:
            source = result.get("source")
        matches = result.get("matches") if isinstance(result.get("matches"), list) else []
        records.append(
            {
                "input": result.get("input", word),
                "status": result.get("status"),
                "source": result.get("stress_source"),
                "readings": [
                    _compact_stress_reading(match) for match in matches if isinstance(match, dict)
                ],
            }
        )
    if source is None:
        source = source_info()
    payload: dict[str, Any] = {"words": records, "source": source}
    if submitted > STRESS_BATCH_CAP:
        payload["note"] = (
            f"Note: received {submitted} words; processed the first {STRESS_BATCH_CAP} (hard cap)."
        )
    return payload
