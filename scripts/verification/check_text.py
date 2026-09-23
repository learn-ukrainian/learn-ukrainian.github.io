"""Text and exercise verification engine (#8398 part C).

Performs comprehensive batch verification of Ukrainian text or exercise items in
a single call:
  - VESUM morphology existence (with sentence-initial capital fallback)
  - Stress oracle verification (chunked at STRESS_BATCH_CAP)
  - Russian-shadow morphology detection (curated problems vs heuristic suspicions)
  - UA-GEC full-span error detection (sentence-bounded contiguous matching)
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Any

from scripts.curriculum.evidence.sources import _signature, _sources_path
from scripts.curriculum.resolver.codes import SKIPPED_KINDS
from scripts.curriculum.resolver.tokenize import (
    Token,
    _strip_stress,
    has_accent,
    lookup_form,
    tokenize,
)
from scripts.verification.check_ru_morph import check_russian_patterns_batch
from scripts.verification.stress import (
    STRESS_BATCH_CAP,
    _stress_positions_in_marked_string,
    source_info,
    verify_stresses,
)
from scripts.verification.vesum import verify_words

VALID_CHECKS = frozenset({"vesum", "stress", "russian_shadow", "ua_gec"})
DEFAULT_CHECKS = ("vesum", "stress", "russian_shadow", "ua_gec")
DEFAULT_UA_GEC_TAGS = ("F/Calque", "F/Collocation")

_VESUM_HASH_CACHE: dict[tuple[int, int], str] = {}
_UA_GEC_INDEX: dict[tuple[str, ...], list[dict[str, Any]]] | None = None
_UA_GEC_SIGNATURE: tuple[int, int, int, int] | None = None
_UA_GEC_MAX_LEN: int = 1


def _vesum_version() -> str:
    """SHA-256 digest of vesum.db, cached by size and mtime."""
    try:
        from scripts.rag.config import VESUM_DB_PATH

        path = Path(VESUM_DB_PATH)
        if path.is_file():
            stat = path.stat()
            key = (stat.st_size, stat.st_mtime_ns)
            if key in _VESUM_HASH_CACHE:
                return _VESUM_HASH_CACHE[key]
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            _VESUM_HASH_CACHE.clear()
            _VESUM_HASH_CACHE[key] = digest
            return digest
    except Exception:
        pass
    return "vesum-source-unversioned"


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


def _get_ua_gec_index() -> tuple[dict[tuple[str, ...], list[dict[str, Any]]], int]:
    """In-memory UA-GEC index keyed on tokenized error tuple (lowercased lookups).

    Invalidated whenever data/sources.db file signature changes.
    """
    global _UA_GEC_INDEX, _UA_GEC_SIGNATURE, _UA_GEC_MAX_LEN
    sources_path = _sources_path()
    current_sig = _signature(sources_path)
    if _UA_GEC_INDEX is not None and current_sig == _UA_GEC_SIGNATURE:
        return _UA_GEC_INDEX, _UA_GEC_MAX_LEN

    index: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    max_len = 1
    if sources_path.is_file():
        conn = sqlite3.connect(f"file:{sources_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT id, error, correct, error_type, doc_id, is_native FROM ua_gec_errors"
            ).fetchall()
            for r in rows:
                err_text = r["error"]
                toks = tuple(
                    t.lookup.lower()
                    for t in tokenize(err_text)
                    if t.kind not in SKIPPED_KINDS
                )
                if not toks:
                    continue
                if len(toks) > max_len:
                    max_len = len(toks)
                row_dict = {
                    "id": r["id"],
                    "error": r["error"],
                    "correct": r["correct"],
                    "error_type": r["error_type"],
                    "doc_id": r["doc_id"],
                    "is_native": r["is_native"],
                }
                index.setdefault(toks, []).append(row_dict)
        finally:
            conn.close()

    _UA_GEC_INDEX = index
    _UA_GEC_SIGNATURE = current_sig
    _UA_GEC_MAX_LEN = max_len
    return index, max_len


def check_text(
    *,
    text: str | None = None,
    items: list[dict[str, Any]] | None = None,
    checks: list[str] | tuple[str, ...] | None = None,
    stress_forms: list[str] | dict[str, str] | None = None,
    max_findings: int = 200,
    ua_gec_tags: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Check Ukrainian text or exercise items in a single call.

    Args:
        text: A single Ukrainian text string. Mutually exclusive with items.
        items: A list of dicts with 'id' and 'text', max 200 items.
        checks: Subset of ('vesum', 'stress', 'russian_shadow', 'ua_gec'). Default all four.
        stress_forms: Optional forms with asserted stress positions.
        max_findings: Maximum number of findings to return (default 200).
        ua_gec_tags: UA-GEC error types to match (default: ['F/Calque', 'F/Collocation']).

    Returns:
        Structured result with provenance, summary, problems, and suspicions.
    """
    # 1. Input validation
    if text is not None and items is not None:
        return {
            "status": "error",
            "error_code": "invalid_input",
            "error": "invalid_input: provide either 'text' or 'items', not both",
        }
    if text is None and items is None:
        return {
            "status": "error",
            "error_code": "invalid_input",
            "error": "invalid_input: provide either 'text' or 'items', neither was provided",
        }

    units: list[tuple[int, Any, str]] = []  # (item_idx, item_id, text)
    if text is not None:
        if not isinstance(text, str):
            return {
                "status": "error",
                "error_code": "invalid_input",
                "error": "invalid_input: 'text' must be a string",
            }
        if has_accent(text):
            return {
                "status": "error",
                "error_code": "accent_in_input",
                "error": "accent_in_input: combining accent in input text",
            }
        units.append((0, None, text))
    else:
        if not isinstance(items, list):
            return {
                "status": "error",
                "error_code": "invalid_input",
                "error": "invalid_input: 'items' must be a list",
            }
        if len(items) > 200:
            return {
                "status": "error",
                "error_code": "invalid_input",
                "error": f"invalid_input: 'items' has {len(items)} items, exceeding maximum 200",
            }
        for idx, item in enumerate(items):
            if not isinstance(item, dict) or "id" not in item or "text" not in item:
                return {
                    "status": "error",
                    "error_code": "invalid_input",
                    "error": "invalid_input: each item must be a mapping with 'id' and 'text'",
                }
            if not isinstance(item["text"], str):
                return {
                    "status": "error",
                    "error_code": "invalid_input",
                    "error": "invalid_input: item 'text' must be a string",
                }
            if has_accent(item["text"]):
                return {
                    "status": "error",
                    "error_code": "accent_in_input",
                    "error": f"accent_in_input: combining accent in item '{item.get('id')}' text",
                }
            units.append((idx, item["id"], item["text"]))

    active_checks = set(DEFAULT_CHECKS) if checks is None else {c for c in checks if c in VALID_CHECKS}

    if max_findings is None or not isinstance(max_findings, int) or max_findings < 0:
        max_findings = 200

    active_ua_gec_tags = set(DEFAULT_UA_GEC_TAGS) if ua_gec_tags is None else set(ua_gec_tags)

    # Process stress_forms
    stress_forms_map: dict[str, str] = {}
    if stress_forms:
        if isinstance(stress_forms, dict):
            for k, v in stress_forms.items():
                if isinstance(k, str) and isinstance(v, str):
                    stress_forms_map[lookup_form(_strip_stress(k))] = v
        elif isinstance(stress_forms, list):
            for sf in stress_forms:
                if isinstance(sf, str):
                    stress_forms_map[lookup_form(_strip_stress(sf))] = sf

    # 2. Tokenize and deduplicate
    total_tokens = 0
    tokens_by_form: dict[str, list[tuple[int, Any, Token]]] = {}
    unit_sentences: list[tuple[int, Any, str, list[Token]]] = []

    for item_idx, item_id, item_text in units:
        unit_toks = tokenize(item_text)
        filtered_toks = [t for t in unit_toks if t.kind not in SKIPPED_KINDS]
        total_tokens += len(filtered_toks)

        for t in filtered_toks:
            tokens_by_form.setdefault(t.lookup, []).append((item_idx, item_id, t))

        # Sentence grouping for UA-GEC
        current_sentence: list[Token] = []
        for t in filtered_toks:
            if t.sentence_initial and current_sentence:
                unit_sentences.append((item_idx, item_id, item_text, current_sentence))
                current_sentence = []
            current_sentence.append(t)
        if current_sentence:
            unit_sentences.append((item_idx, item_id, item_text, current_sentence))

    unique_forms = list(tokens_by_form.keys())

    raw_problems: list[dict[str, Any]] = []
    raw_suspicions: list[dict[str, Any]] = []

    # 3. VESUM check
    vesum_verified_forms: set[str] = set()
    if "vesum" in active_checks and unique_forms:
        sent_init_caps: set[str] = set()
        for form, occurrences in tokens_by_form.items():
            for _, _, t in occurrences:
                if t.sentence_initial and t.capitalised:
                    sent_init_caps.add(form)
                    break

        query_words = list(
            dict.fromkeys(unique_forms + [_lower_first(f) for f in sent_init_caps])
        )
        vesum_map = verify_words(query_words)

        for form in unique_forms:
            is_verified = bool(
                vesum_map.get(form)
                or (form in sent_init_caps and vesum_map.get(_lower_first(form)))
            )

            if is_verified:
                vesum_verified_forms.add(form)
            else:
                occurrences = tokens_by_form[form]
                locs = [[item_id, t.start, t.end] for _, item_id, t in occurrences]
                first_occ = occurrences[0]
                raw_problems.append({
                    "form": form,
                    "check": "vesum",
                    "detail": {"status": "no_vesum_row"},
                    "locations": locs,
                    "_first_loc": (first_occ[0], locs[0][1], locs[0][2]),
                })
    elif "russian_shadow" in active_checks and unique_forms:
        # If vesum was not requested in checks, but russian_shadow needs verified set:
        query_words = list(dict.fromkeys(unique_forms + [_lower_first(f) for f in unique_forms]))
        vesum_map = verify_words(query_words)
        for form in unique_forms:
            if vesum_map.get(form) or vesum_map.get(_lower_first(form)):
                vesum_verified_forms.add(form)

    # 4. Stress check
    stress_source_info: dict[str, Any] | None = None
    stress_notes: list[str] = []
    if "stress" in active_checks and unique_forms:
        stress_query_forms: list[str] = []
        for form in unique_forms:
            if form in stress_forms_map:
                stress_query_forms.append(stress_forms_map[form])
            else:
                stress_query_forms.append(form)

        all_stress_records: list[dict[str, Any]] = []
        for i in range(0, len(stress_query_forms), STRESS_BATCH_CAP):
            chunk = stress_query_forms[i : i + STRESS_BATCH_CAP]
            chunk_res = verify_stresses(chunk)
            if stress_source_info is None:
                stress_source_info = chunk_res.get("source")
            note = chunk_res.get("note")
            if note:
                stress_notes.append(note)
            all_stress_records.extend(chunk_res.get("words", []))

        if stress_source_info is None:
            stress_source_info = source_info()

        for form, rec in zip(unique_forms, all_stress_records, strict=False):
            st = rec.get("status")
            readings = rec.get("readings", [])
            occurrences = tokens_by_form[form]
            locs = [[item_id, t.start, t.end] for _, item_id, t in occurrences]
            first_occ = occurrences[0]

            if form in stress_forms_map:
                asserted = stress_forms_map[form]
                _, asserted_indices = _stress_positions_in_marked_string(asserted)
                has_matching_reading = any(
                    r.get("vowel_indices") == asserted_indices for r in readings
                )
                if not has_matching_reading and readings:
                    raw_problems.append({
                        "form": form,
                        "check": "stress",
                        "detail": {
                            "status": "stress_mismatch",
                            "asserted_form": asserted,
                            "readings": [
                                {
                                    "stressed_form": r.get("stressed_form"),
                                    "vowel_indices": r.get("vowel_indices"),
                                }
                                for r in readings
                            ],
                        },
                        "locations": locs,
                        "_first_loc": (first_occ[0], locs[0][1], locs[0][2]),
                    })
            else:
                if st == "ambiguous":
                    raw_problems.append({
                        "form": form,
                        "check": "stress",
                        "detail": {
                            "status": "ambiguous",
                            "readings": [
                                {
                                    "stressed_form": r.get("stressed_form"),
                                    "vowel_indices": r.get("vowel_indices"),
                                }
                                for r in readings
                            ],
                        },
                        "locations": locs,
                        "_first_loc": (first_occ[0], locs[0][1], locs[0][2]),
                    })
    else:
        stress_source_info = source_info()

    # 5. Russian shadow check
    if "russian_shadow" in active_checks and unique_forms:
        shadow_batch = check_russian_patterns_batch(
            unique_forms,
            verified_words=vesum_verified_forms,
        )
        for form in unique_forms:
            res = shadow_batch.get(form)
            if not res or not res.get("matches_russian"):
                continue
            occurrences = tokens_by_form[form]
            locs = [[item_id, t.start, t.end] for _, item_id, t in occurrences]
            first_occ = occurrences[0]

            if res.get("is_curated"):
                raw_problems.append({
                    "form": form,
                    "check": "russian_shadow",
                    "detail": {
                        "status": "russian_shadow",
                        "curated": True,
                        "russian_lemma": res.get("russian_lemma"),
                        "ukrainian_alternative": res.get("ukrainian_alternative"),
                    },
                    "locations": locs,
                    "_first_loc": (first_occ[0], locs[0][1], locs[0][2]),
                })
            else:
                raw_suspicions.append({
                    "form": form,
                    "check": "russian_shadow",
                    "detail": {
                        "status": "suspicion",
                        "label": "suspicion, not a verdict",
                        "curated": False,
                        "confidence": res.get("confidence", 0.0),
                        "russian_lemma": res.get("russian_lemma"),
                    },
                    "locations": locs,
                    "_first_loc": (first_occ[0], locs[0][1], locs[0][2]),
                })

    # 6. UA-GEC check
    sources_path = _sources_path()
    sources_sig = _signature(sources_path)
    if "ua_gec" in active_checks and unit_sentences:
        ua_gec_index, max_gec_len = _get_ua_gec_index()
        ua_gec_findings: dict[tuple[str, ...], dict[str, Any]] = {}

        for item_idx, item_id, item_text, sentence_tokens in unit_sentences:
            m = len(sentence_tokens)
            s = 0
            while s < m:
                matched = False
                for L in range(min(m - s, max_gec_len), 0, -1):
                    span = sentence_tokens[s : s + L]
                    span_key = tuple(t.lookup.lower() for t in span)
                    matching_rows = ua_gec_index.get(span_key)
                    if matching_rows:
                        active_rows = [
                            r for r in matching_rows if r["error_type"] in active_ua_gec_tags
                        ]
                        if active_rows:
                            start_offset = span[0].start
                            end_offset = span[-1].end
                            loc = [item_id, start_offset, end_offset]
                            form_text = item_text[start_offset:end_offset]

                            if span_key in ua_gec_findings:
                                ua_gec_findings[span_key]["locations"].append(loc)
                            else:
                                corrections_map: dict[str, set[str]] = {}
                                for r in active_rows:
                                    corrections_map.setdefault(r["correct"], set()).add(
                                        str(r["doc_id"])
                                    )
                                corrections = [
                                    {"correct": c, "doc_ids": sorted(list(docs))}
                                    for c, docs in corrections_map.items()
                                ]
                                error_types = sorted(list({r["error_type"] for r in active_rows}))
                                detail: dict[str, Any] = {
                                    "status": "ua_gec_error",
                                    "error_type": error_types[0]
                                    if len(error_types) == 1
                                    else error_types,
                                    "corrections": corrections,
                                }
                                if any(t in ("G/Case", "G/Gender") for t in error_types):
                                    all_docs = sorted(list({str(r["doc_id"]) for r in active_rows}))
                                    detail["note"] = (
                                        f"corrected in that document ({', '.join(all_docs)})"
                                    )
                                ua_gec_findings[span_key] = {
                                    "form": form_text,
                                    "check": "ua_gec",
                                    "detail": detail,
                                    "locations": [loc],
                                    "_first_loc": (item_idx, start_offset, end_offset),
                                }

                            s += L
                            matched = True
                            break
                if not matched:
                    s += 1

        for finding in ua_gec_findings.values():
            raw_problems.append(finding)

    # 7. Sorting and Truncation
    all_findings = (
        [(f, "problem") for f in raw_problems]
        + [(f, "suspicion") for f in raw_suspicions]
    )

    def finding_sort_key(entry: tuple[dict[str, Any], str]) -> tuple[Any, ...]:
        f, cat = entry
        first_loc = f.get("_first_loc", (0, 0, 0))
        return (first_loc[0], first_loc[1], first_loc[2], f["form"], f["check"], cat)

    all_findings.sort(key=finding_sort_key)
    uncut_count = len(all_findings)
    truncated = False
    if uncut_count > max_findings:
        truncated = True
        kept = all_findings[:max_findings]
    else:
        kept = all_findings

    problems: list[dict[str, Any]] = []
    suspicions: list[dict[str, Any]] = []
    for f, cat in kept:
        f.pop("_first_loc", None)
        if cat == "problem":
            problems.append(f)
        else:
            suspicions.append(f)

    # Clean remaining uncut findings if truncated
    for f, _ in all_findings:
        f.pop("_first_loc", None)

    problems_per_check = {
        "vesum": sum(1 for p in raw_problems if p.get("check") == "vesum"),
        "stress": sum(1 for p in raw_problems if p.get("check") == "stress"),
        "russian_shadow": sum(1 for p in raw_problems if p.get("check") == "russian_shadow"),
        "ua_gec": sum(1 for p in raw_problems if p.get("check") == "ua_gec"),
    }

    summary: dict[str, Any] = {
        "tokens": total_tokens,
        "unique_forms": len(unique_forms),
        "problems_per_check": problems_per_check,
        "suspicions_count": len(raw_suspicions),
        "uncut_count": uncut_count,
        "truncated": truncated,
    }
    if stress_notes:
        summary["stress_note"] = "; ".join(stress_notes)

    provenance: dict[str, Any] = {
        "stress": stress_source_info,
        "vesum_version": _vesum_version(),
        "ua_gec_file_signature": list(sources_sig) if sources_sig else None,
    }

    return {
        "provenance": provenance,
        "summary": summary,
        "problems": problems,
        "suspicions": suspicions,
    }
