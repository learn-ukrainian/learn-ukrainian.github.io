"""Text and exercise verification engine (#8398 part C).

Performs comprehensive batch verification of Ukrainian text or exercise items in
a single call:
  - VESUM morphology existence (with sentence-initial capital fallback)
  - Stress oracle verification (chunked at STRESS_BATCH_CAP)
  - Russian-shadow morphology detection (curated problems vs heuristic suspicions)
  - UA-GEC full-span error detection (multi-token problems vs single-token suspicions)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from scripts.curriculum.evidence.sources import _signature
from scripts.curriculum.resolver.codes import SKIPPED_KINDS
from scripts.curriculum.resolver.tokenize import (
    Token,
    has_accent,
    lookup_form,
    tokenize,
)
from scripts.lexicon.calque_corrections import CURATED_CALQUES, LEXICALISED_SAFE
from scripts.storage.topology import ActiveDatabaseNetworkError, require_local_active_sources_db
from scripts.verification.check_ru_morph import (
    KNOWN_SHADOW_LEMMAS,
    _morph_uk,
    check_russian_patterns_batch,
)
from scripts.verification.stress import (
    STRESS_BATCH_CAP,
    _stress_positions_in_marked_string,
    _strip_stress,
    source_info,
    verify_stresses,
)
from scripts.verification.vesum import _resolve_vesum_db_path, verify_words

VALID_CHECKS = frozenset({"vesum", "stress", "russian_shadow", "ua_gec"})
DEFAULT_CHECKS = ("vesum", "stress", "russian_shadow", "ua_gec")
VALID_UA_GEC_TAGS = frozenset({"F/Calque", "F/Collocation", "G/Case", "G/Gender"})
DEFAULT_UA_GEC_TAGS = ("F/Calque", "F/Collocation")
_CLOSED_CLASS_POS = frozenset({"conj", "conjunction", "prep", "preposition", "part", "particle", "pron", "pronoun"})

_VESUM_VERSION_CACHE: tuple[tuple[int, int], str] | None = None
_UA_GEC_INDEX: dict[tuple[str, ...], list[dict[str, Any]]] | None = None
_UA_GEC_SIGNATURE: tuple[int, int, int, int] | None = None
_UA_GEC_MAX_LEN: int = 1
_UA_GEC_DROPPED_SKIPPED_KIND: int = 0


def _sources_path_resolved() -> Path:
    path = require_local_active_sources_db()
    if path.is_file():
        return path
    try:
        from scripts.guardrails.worktree_containment import resolve_main_root

        main_root = resolve_main_root(Path(__file__).resolve().parents[2])
        main_path = require_local_active_sources_db(main_root)
        if main_path.is_file():
            return main_path
    except Exception:
        pass
    return path


def _vesum_path_resolved() -> Path:
    return _resolve_vesum_db_path()


def _vesum_version() -> str:
    """Canonical VESUM identity from vesum_build_metadata.canonical_jsonl_sha256.

    Cached by (size, mtime_ns) to avoid querying SQLite on every warm call.
    """
    global _VESUM_VERSION_CACHE
    try:
        path = _vesum_path_resolved()
        if path.is_file():
            stat = path.stat()
            key = (stat.st_size, stat.st_mtime_ns)
            if _VESUM_VERSION_CACHE is not None and _VESUM_VERSION_CACHE[0] == key:
                return _VESUM_VERSION_CACHE[1]
            conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            try:
                cur = conn.execute("SELECT value FROM vesum_build_metadata WHERE key = 'canonical_jsonl_sha256'")
                row = cur.fetchone()
                if row and row[0]:
                    digest = str(row[0])
                    _VESUM_VERSION_CACHE = (key, digest)
                    return digest
            finally:
                conn.close()
    except Exception:
        pass
    return "vesum-source-unversioned"


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


def _is_closed_class_token(
    token_str: str,
    vesum_map: dict[str, list[dict[str, Any]]],
) -> bool:
    """True if token has at least one VESUM reading in {conjunction, preposition, pronoun, particle}.

    A token with no VESUM row is NOT closed-class.
    """
    matches = vesum_map.get(token_str) or vesum_map.get(token_str.lower()) or vesum_map.get(_lower_first(token_str))
    if matches is None:
        try:
            res = verify_words([token_str, token_str.lower()], db_path=_vesum_path_resolved())
            matches = res.get(token_str) or res.get(token_str.lower()) or []
            vesum_map[token_str] = matches
        except FileNotFoundError:
            raise
        except Exception:
            matches = []
    if not matches:
        return False
    for m in matches:
        pos = m.get("pos", "")
        if pos in _CLOSED_CLASS_POS:
            return True
        tags = m.get("tags", "")
        if "pron" in tags.split(":"):
            return True
    return False


def _get_ua_gec_index() -> tuple[dict[tuple[str, ...], list[dict[str, Any]]], int, int]:
    """In-memory UA-GEC index keyed on tokenized error tuple (lowercased lookups).

    Rows whose error text contains skipped-kind tokens (latin, digits) are dropped
    from the index to avoid sub-span false matches.

    Invalidated whenever data/sources.db file signature changes.
    """
    global _UA_GEC_INDEX, _UA_GEC_SIGNATURE, _UA_GEC_MAX_LEN, _UA_GEC_DROPPED_SKIPPED_KIND
    sources_path = _sources_path_resolved()
    if not sources_path.is_file():
        raise FileNotFoundError(f"sources database not found at {sources_path}")
    current_sig = _signature(sources_path)
    if _UA_GEC_INDEX is not None and current_sig == _UA_GEC_SIGNATURE:
        return _UA_GEC_INDEX, _UA_GEC_MAX_LEN, _UA_GEC_DROPPED_SKIPPED_KIND

    index: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    max_len = 1
    dropped_count = 0
    conn = sqlite3.connect(f"file:{sources_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT id, error, correct, error_type, doc_id, is_native FROM ua_gec_errors").fetchall()
        for r in rows:
            err_text = r["error"]
            raw_toks = tokenize(err_text)
            if any(t.kind in SKIPPED_KINDS for t in raw_toks):
                dropped_count += 1
                continue
            toks = tuple(t.lookup.lower() for t in raw_toks if t.kind not in SKIPPED_KINDS)
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
    _UA_GEC_DROPPED_SKIPPED_KIND = dropped_count
    return index, max_len, dropped_count


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

    if checks is not None:
        if not isinstance(checks, (list, tuple, set, frozenset)) or len(checks) == 0:
            return {
                "status": "error",
                "error_code": "invalid_input",
                "error": "invalid_input: 'checks' must be a nonempty list or tuple",
            }
        unknown_checks = [c for c in checks if c not in VALID_CHECKS]
        if unknown_checks:
            return {
                "status": "error",
                "error_code": "invalid_input",
                "error": f"invalid_input: unknown check(s): {', '.join(repr(c) for c in unknown_checks)}. Valid checks: {', '.join(sorted(VALID_CHECKS))}",
            }
        active_checks = set(checks)
    else:
        active_checks = set(DEFAULT_CHECKS)

    if isinstance(max_findings, bool) or not isinstance(max_findings, int) or max_findings < 1:
        return {
            "status": "error",
            "error_code": "invalid_input",
            "error": "invalid_input: 'max_findings' must be an integer >= 1",
        }

    if ua_gec_tags is not None:
        if (
            isinstance(ua_gec_tags, str)
            or not isinstance(ua_gec_tags, (list, tuple, set, frozenset))
            or len(ua_gec_tags) == 0
        ):
            return {
                "status": "error",
                "error_code": "invalid_input",
                "error": "invalid_input: 'ua_gec_tags' must be a nonempty list or tuple of valid tags",
            }
        unknown_tags = [t for t in ua_gec_tags if t not in VALID_UA_GEC_TAGS]
        if unknown_tags:
            return {
                "status": "error",
                "error_code": "invalid_input",
                "error": f"invalid_input: unknown ua_gec_tags: {', '.join(repr(t) for t in unknown_tags)}. Valid tags: {', '.join(sorted(VALID_UA_GEC_TAGS))}",
            }
        active_ua_gec_tags = set(ua_gec_tags)
    else:
        active_ua_gec_tags = set(DEFAULT_UA_GEC_TAGS)

    # Process stress_forms (case-insensitive lookup form)
    stress_forms_map: dict[str, str] = {}
    if stress_forms:
        if isinstance(stress_forms, dict):
            for k, v in stress_forms.items():
                if isinstance(k, str) and isinstance(v, str):
                    stress_forms_map[lookup_form(_strip_stress(k)).lower()] = v
        elif isinstance(stress_forms, list):
            for sf in stress_forms:
                if isinstance(sf, str):
                    stress_forms_map[lookup_form(_strip_stress(sf)).lower()] = sf

    # 2. Tokenize and deduplicate
    total_tokens = 0
    tokens_by_form: dict[str, list[tuple[int, Any, Token]]] = {}
    unit_sentences: list[tuple[int, Any, str, list[Token]]] = []

    for item_idx, item_id, item_text in units:
        unit_toks = tokenize(item_text)
        current_sentence: list[Token] = []

        for t in unit_toks:
            if t.kind in SKIPPED_KINDS:
                # Skipped-kind tokens (latin, digits) break contiguity for UA-GEC spans
                if current_sentence:
                    unit_sentences.append((item_idx, item_id, item_text, current_sentence))
                    current_sentence = []
                continue

            total_tokens += 1
            tokens_by_form.setdefault(t.lookup, []).append((item_idx, item_id, t))

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
    vesum_map: dict[str, list[dict[str, Any]]] = {}
    vesum_path: Path | None = None
    if ("vesum" in active_checks or "russian_shadow" in active_checks) and unique_forms:
        vesum_path = _vesum_path_resolved()
        if not vesum_path.is_file():
            return {
                "status": "error",
                "error_code": "source_unavailable",
                "error": f"source_unavailable: VESUM database not found at {vesum_path}",
            }

    if "vesum" in active_checks and unique_forms:
        sent_init_caps: set[str] = set()
        for form, occurrences in tokens_by_form.items():
            for _, _, t in occurrences:
                if t.sentence_initial and t.capitalised:
                    sent_init_caps.add(form)
                    break

        query_words = list(dict.fromkeys(unique_forms + [_lower_first(f) for f in sent_init_caps]))
        try:
            vesum_map = verify_words(query_words, db_path=vesum_path)
        except FileNotFoundError as err:
            return {
                "status": "error",
                "error_code": "source_unavailable",
                "error": f"source_unavailable: {err}",
            }

        for form in unique_forms:
            is_verified = bool(vesum_map.get(form) or (form in sent_init_caps and vesum_map.get(_lower_first(form))))

            if is_verified:
                vesum_verified_forms.add(form)
            else:
                occurrences = tokens_by_form[form]
                locs = [[item_id, t.start, t.end] for _, item_id, t in occurrences]
                first_occ = occurrences[0]
                raw_problems.append(
                    {
                        "form": form,
                        "check": "vesum",
                        "detail": {"status": "no_vesum_row"},
                        "locations": locs,
                        "_first_loc": (first_occ[0], locs[0][1], locs[0][2]),
                    }
                )
    elif "russian_shadow" in active_checks and unique_forms:
        # If vesum was not requested in checks, but russian_shadow needs verified set:
        query_words = list(dict.fromkeys(unique_forms + [_lower_first(f) for f in unique_forms]))
        try:
            vesum_map = verify_words(query_words, db_path=vesum_path)
        except FileNotFoundError as err:
            return {
                "status": "error",
                "error_code": "source_unavailable",
                "error": f"source_unavailable: {err}",
            }
        for form in unique_forms:
            if vesum_map.get(form) or vesum_map.get(_lower_first(form)):
                vesum_verified_forms.add(form)

    # 4. Stress check
    stress_source_info: dict[str, Any] | None = None
    stress_notes: list[str] = []
    if "stress" in active_checks and unique_forms:
        all_stress_records: list[dict[str, Any]] = []
        for i in range(0, len(unique_forms), STRESS_BATCH_CAP):
            chunk = unique_forms[i : i + STRESS_BATCH_CAP]
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

            norm_f = form.lower()
            if st == "ambiguous":
                if norm_f in stress_forms_map:
                    asserted = stress_forms_map[norm_f]
                    _, asserted_indices = _stress_positions_in_marked_string(asserted)
                    has_matching_reading = any(r.get("vowel_indices") == asserted_indices for r in readings)
                    if has_matching_reading:
                        # Ambiguity resolved by caller-asserted stress reading
                        continue

                raw_problems.append(
                    {
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
                    }
                )
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
            norm_word = form.lower().strip()
            occurrences = tokens_by_form[form]
            locs = [[item_id, t.start, t.end] for _, item_id, t in occurrences]
            first_occ = occurrences[0]

            # Curated detection: check form and uk_lemma (excluding LEXICALISED_SAFE)
            is_curated = False
            curated_list: str | None = None
            ukrainian_alternative: str | None = None

            if norm_word not in LEXICALISED_SAFE:
                uk_parses = _morph_uk.parse(norm_word)
                uk_lemma = uk_parses[0].normal_form if uk_parses else norm_word
                if uk_lemma not in LEXICALISED_SAFE:
                    if norm_word in CURATED_CALQUES or uk_lemma in CURATED_CALQUES:
                        is_curated = True
                        curated_list = "curated_calques"
                        calque_info = CURATED_CALQUES.get(norm_word) or CURATED_CALQUES.get(uk_lemma)
                        if calque_info and "corrections" in calque_info:
                            corrs = calque_info["corrections"]
                            ukrainian_alternative = ", ".join(corrs) if isinstance(corrs, list) else str(corrs)
                    elif norm_word in KNOWN_SHADOW_LEMMAS or uk_lemma in KNOWN_SHADOW_LEMMAS:
                        is_curated = True
                        curated_list = "known_shadow_lemmas"

            if is_curated:
                raw_problems.append(
                    {
                        "form": form,
                        "check": "russian_shadow",
                        "detail": {
                            "status": "russian_shadow",
                            "curated": True,
                            "curated_list": curated_list,
                            "russian_lemma": res.get("russian_lemma") if res else None,
                            "ukrainian_alternative": ukrainian_alternative,
                        },
                        "locations": locs,
                        "_first_loc": (first_occ[0], locs[0][1], locs[0][2]),
                    }
                )
            elif res and res.get("matches_russian"):
                raw_suspicions.append(
                    {
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
                    }
                )

    # 6. UA-GEC check
    dropped_gec_rows = 0
    sources_sig = None
    ua_gec_index: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    max_gec_len = 1

    if "ua_gec" in active_checks:
        try:
            sources_path = _sources_path_resolved()
            sources_sig = _signature(sources_path)
            ua_gec_index, max_gec_len, dropped_gec_rows = _get_ua_gec_index()
        except (FileNotFoundError, ActiveDatabaseNetworkError) as err:
            return {
                "status": "error",
                "error_code": "source_unavailable",
                "error": f"source_unavailable: {err}",
            }

    if "ua_gec" in active_checks and unit_sentences and ua_gec_index:
        if not vesum_map and unique_forms:
            vesum_path = _vesum_path_resolved()
            if not vesum_path.is_file():
                return {
                    "status": "error",
                    "error_code": "source_unavailable",
                    "error": f"source_unavailable: VESUM database not found at {vesum_path}",
                }
            query_words = list(dict.fromkeys(unique_forms + [_lower_first(f) for f in unique_forms]))
            try:
                vesum_map = verify_words(query_words, db_path=vesum_path)
            except FileNotFoundError as err:
                return {
                    "status": "error",
                    "error_code": "source_unavailable",
                    "error": f"source_unavailable: {err}",
                }
            except Exception:
                vesum_map = {}
        ua_gec_findings: dict[tuple[str, ...], dict[str, Any]] = {}

        for item_idx, item_id, item_text, sentence_tokens in unit_sentences:
            m = len(sentence_tokens)
            for s in range(m):
                for L in range(min(m - s, max_gec_len), 0, -1):
                    span = sentence_tokens[s : s + L]
                    span_key = tuple(t.lookup.lower() for t in span)
                    matching_rows = ua_gec_index.get(span_key)
                    if not matching_rows:
                        continue
                    active_rows = [r for r in matching_rows if r["error_type"] in active_ua_gec_tags]
                    if not active_rows:
                        continue

                    start_offset = span[0].start
                    end_offset = span[-1].end
                    loc = [item_id, start_offset, end_offset]
                    form_text = item_text[start_offset:end_offset]

                    if span_key in ua_gec_findings:
                        if loc not in ua_gec_findings[span_key]["locations"]:
                            ua_gec_findings[span_key]["locations"].append(loc)
                    else:
                        corrections_map: dict[str, set[str]] = {}
                        for r in active_rows:
                            corrections_map.setdefault(r["correct"], set()).add(str(r["doc_id"]))
                        corrections = [
                            {"correct": c, "doc_ids": sorted(list(docs))} for c, docs in corrections_map.items()
                        ]
                        error_types = sorted(list({r["error_type"] for r in active_rows}))
                        all_docs = sorted(list({str(r["doc_id"]) for r in active_rows}))
                        is_single_token = len(span_key) == 1
                        try:
                            is_closed_class_span = all(_is_closed_class_token(t.lookup, vesum_map) for t in span)
                        except FileNotFoundError as err:
                            return {
                                "status": "error",
                                "error_code": "source_unavailable",
                                "error": f"source_unavailable: {err}",
                            }
                        is_collocation = any(r["error_type"] == "F/Collocation" for r in active_rows)
                        is_multi_token_calque = (
                            (not is_single_token)
                            and (not is_collocation)
                            and (not is_closed_class_span)
                            and all(r["error_type"] == "F/Calque" for r in active_rows)
                        )
                        if is_multi_token_calque:
                            detail: dict[str, Any] = {
                                "status": "ua_gec_error",
                                "error_type": error_types[0] if len(error_types) == 1 else error_types,
                                "doc_ids": all_docs,
                                "corrections": corrections,
                            }
                            is_suspicion = False
                        else:
                            if is_closed_class_span:
                                label = (
                                    "UA-GEC correction of function words; depends on sentence context; "
                                    "suspicion, not a verdict"
                                )
                            else:
                                label = "UA-GEC correction in one document's context; suspicion, not a verdict"
                            detail = {
                                "status": "suspicion",
                                "label": label,
                                "error_type": error_types[0] if len(error_types) == 1 else error_types,
                                "doc_ids": all_docs,
                                "corrections": corrections,
                            }
                            is_suspicion = True

                        if any(t in ("G/Case", "G/Gender") for t in error_types):
                            detail["note"] = f"corrected in that document ({', '.join(all_docs)})"
                        ua_gec_findings[span_key] = {
                            "form": form_text,
                            "check": "ua_gec",
                            "detail": detail,
                            "locations": [loc],
                            "_first_loc": (item_idx, start_offset, end_offset),
                            "_is_suspicion": is_suspicion,
                        }

        for finding in ua_gec_findings.values():
            if finding.pop("_is_suspicion", False):
                raw_suspicions.append(finding)
            else:
                raw_problems.append(finding)

    # 7. Sorting and Truncation
    all_findings = [(f, "problem") for f in raw_problems] + [(f, "suspicion") for f in raw_suspicions]

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
        "ua_gec_dropped_skipped_kind_rows": dropped_gec_rows,
    }

    return {
        "provenance": provenance,
        "summary": summary,
        "problems": problems,
        "suspicions": suspicions,
    }
