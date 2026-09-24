"""Verification of the level word store (_words.yaml and _words.registry.yaml).

Re-derives every fact from current sources; read-only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.verification import stress

from . import codes, lock, pack, registry, sources
from .words import (
    cefr_field,
    cited_rows,
    count_vowels,
    extract_ulif_paradigm_forms,
    find_plans_citing,
    load_schema,
    store_scheme,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _without_identity(value: Any, *, legacy: bool) -> Any:
    """Value part of a cited record: drop row_sha256 (and row_id for legacy stores, which never had it)."""
    if not isinstance(value, dict):
        return value
    dropped = {"row_sha256", "row_id"} if legacy else {"row_sha256"}
    return {key: item for key, item in value.items() if key not in dropped}


def _drift(strict: bool, errors: list[str], warnings: list[str], message: str) -> None:
    """SOURCE_CHANGED is an error under --strict and a warning otherwise; never silent."""
    line = f"{codes.SOURCE_CHANGED}: {message}"
    if strict:
        errors.append(line)
    else:
        warnings.append(line)


def verify_words_store(
    level: str,
    *,
    evidence_dir: Path | None = None,
    plans_dir: Path | None = None,
    sources_instance: sources.Sources | None = None,
    strict: bool = False,
    report: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Verify an existing level word store against sources, ledger, and lock."""
    evidence_base = (
        Path(evidence_dir) if evidence_dir is not None else REPO_ROOT / "curriculum/l2-uk-en/evidence" / level
    )
    plans_base = Path(plans_dir) if plans_dir is not None else REPO_ROOT / "curriculum/l2-uk-en/lesson-plans" / level

    store_path = evidence_base / "_words.yaml"
    registry_path = evidence_base / "_words.registry.yaml"

    errors: list[str] = []
    warnings: list[str] = []

    if not store_path.is_file():
        return {
            "status": "failed",
            "level": level,
            "errors": [f"{codes.SOURCE_UNAVAILABLE}: store file missing at {store_path}"],
            "warnings": [],
        }

    if not registry_path.is_file():
        return {
            "status": "failed",
            "level": level,
            "errors": [f"{codes.SOURCE_UNAVAILABLE}: registry file missing at {registry_path}"],
            "warnings": [],
        }

    # 1. Lock checks
    if not lock.check(store_path):
        errors.append(f"{codes.LOCK_MISMATCH}: store file lock mismatch: {store_path}")
    if not lock.check(registry_path):
        errors.append(f"{codes.LOCK_MISMATCH}: registry file lock mismatch: {registry_path}")

    # 2. Schema check
    try:
        store_doc = yaml.safe_load(store_path.read_text(encoding="utf-8"))
        if not isinstance(store_doc, dict):
            errors.append(f"{codes.INVALID_REQUEST}: {store_path} is not a valid YAML mapping")
            return {
                "status": "failed",
                "level": level,
                "errors": errors,
                "warnings": warnings,
            }
        schema = load_schema("evidence-words-v1.schema.json")
        validator = Draft202012Validator(schema)
        schema_errs = list(validator.iter_errors(store_doc))
        for err in schema_errs:
            errors.append(f"{codes.FORM_MISMATCH}: schema error: {err.message}")
    except Exception as exc:
        errors.append(f"{codes.INVALID_REQUEST}: failed parsing {store_path}: {exc}")
        return {
            "status": "failed",
            "level": level,
            "errors": errors,
            "warnings": warnings,
        }

    # 3. Registry check
    try:
        registry_records = registry.load(registry_path)
        registry.check_store(registry_records, store_doc.get("words", []))
    except Exception as exc:
        errors.append(str(exc))

    owns_sources = False
    if sources_instance is None:
        sources_instance = sources.Sources(report=report)
        owns_sources = True

    try:
        # 4. Compare source versions
        built_with = store_doc.get("built_with", {})
        current_vesum = sources_instance._vesum_identity()[0]
        current_trie = stress.source_info()["digest"]
        source_version_changed = built_with.get("vesum") != current_vesum or built_with.get("trie") != current_trie

        # 4b. sources.db identity scheme (rows-v2: cited rows; file-v1: retired file digest)
        scheme = store_scheme(store_doc)
        legacy = scheme != sources.SOURCES_DB_SCHEME
        if legacy:
            msg = (
                f"{codes.LEGACY_IDENTITY}: built_with.sources_db is a file digest ({scheme}); "
                f"rebuild the store for {sources.SOURCES_DB_SCHEME}"
            )
            if strict:
                errors.append(msg)
            else:
                warnings.append(msg)
        else:
            recorded_aggregate = sources.aggregate_digest(
                pair for word in store_doc.get("words", []) for pair in cited_rows(word)
            )
            if recorded_aggregate != built_with.get("sources_db"):
                errors.append(
                    f"{codes.LOCK_MISMATCH}: built_with.sources_db {str(built_with.get('sources_db'))[:12]}... "
                    f"does not aggregate the recorded row_sha256 values ({recorded_aggregate[:12]}...)"
                )
        rows_drifted_total = 0

        pending_forms_count = 0
        override_forms_count = 0
        unresolved_uncited_count = 0
        total_forms = 0

        words_list = store_doc.get("words", [])

        # Check numeric ID ordering
        prev_num = 0
        for w in words_list:
            cur_num = registry.number(w["id"])
            if cur_num <= prev_num:
                errors.append(f"{codes.REGISTRY_MISMATCH}: word ids not in strictly increasing order: {w['id']}")
            prev_num = cur_num

        for word in words_list:
            word_id = word["id"]
            lemma = word["lemma"]
            pos = word["pos"]
            entry = word.get("entry")

            word_rows_drifted = False

            def cited_row_check(
                label: str, stored: Any, expected: Any, *, word_id: str = word_id, lemma: str = lemma
            ) -> None:
                """rows-v2 per-record identity: missing → FORM_MISMATCH; drift → SOURCE_CHANGED."""
                nonlocal word_rows_drifted
                if legacy or not isinstance(stored, dict):
                    return
                recorded = stored.get("row_sha256")
                if not recorded:
                    errors.append(f"{codes.FORM_MISMATCH}: {label} of {word_id} ({lemma}) has no row_sha256")
                    return
                current = expected.get("row_sha256") if isinstance(expected, dict) else None
                if current is None:
                    word_rows_drifted = True
                    _drift(
                        strict, errors, warnings, f"{label} of {word_id} ({lemma}): cited row missing at its locator"
                    )
                elif current != recorded:
                    word_rows_drifted = True
                    _drift(
                        strict,
                        errors,
                        warnings,
                        f"{label} of {word_id} ({lemma}): cited row changed "
                        f"(recorded {recorded[:12]}..., current {current[:12]}...)",
                    )

            # Check CEFR against source
            cefr_hits = sources_instance.cefr_levels([lemma]).raw.get(lemma, [])
            exact_cefr = next((h for h in cefr_hits if sources.normalize_spelling(h.get("word", "")) == lemma), None)
            expected_cefr = None
            if exact_cefr and exact_cefr.get("level") in {"A1", "A2", "B1", "B2", "C1", "C2"}:
                expected_cefr = cefr_field(exact_cefr)

            stored_cefr = word.get("cefr")
            if _without_identity(stored_cefr, legacy=legacy) != _without_identity(expected_cefr, legacy=legacy):
                errors.append(
                    f"{codes.CEFR_MISMATCH}: stored CEFR {_without_identity(stored_cefr, legacy=legacy)} differs from "
                    f"source {_without_identity(expected_cefr, legacy=legacy)} for {word_id} ({lemma})"
                )
            cited_row_check("cefr", stored_cefr, expected_cefr)

            # Check Gloss against source
            gloss_rows = sources_instance.gloss_rows([(lemma, pos)]).raw.get((lemma, pos), [])
            expected_gloss = None
            expected_gloss_source = None
            if gloss_rows:
                first_row = gloss_rows[0]
                raw_trans = first_row.get("translations", "")
                if isinstance(raw_trans, str):
                    try:
                        parsed_trans = json.loads(raw_trans)
                    except Exception:
                        parsed_trans = [raw_trans]
                else:
                    parsed_trans = raw_trans
                if parsed_trans and isinstance(parsed_trans, list) and len(parsed_trans) > 0:
                    first_str = str(parsed_trans[0])
                    if first_str:
                        expected_gloss = first_str
                        expected_gloss_source = {
                            "table": "dmklinger_uk_en",
                            "id": first_row["id"],
                            "row_sha256": sources.row_digest(first_row),
                        }

            stored_gloss = word.get("gloss_en")
            stored_gloss_source = word.get("gloss_source")
            if stored_gloss != expected_gloss or _without_identity(stored_gloss_source, legacy=legacy) != (
                _without_identity(expected_gloss_source, legacy=legacy)
            ):
                errors.append(
                    f"{codes.GLOSS_MISMATCH}: stored gloss ({stored_gloss!r}, "
                    f"{_without_identity(stored_gloss_source, legacy=legacy)}) differs from source "
                    f"({expected_gloss!r}, {_without_identity(expected_gloss_source, legacy=legacy)}) "
                    f"for {word_id} ({lemma})"
                )
            cited_row_check("gloss_source", stored_gloss_source, expected_gloss_source)

            # Heritage hits are copied by value; each carries the identity of the rows it was read from.
            stored_heritage = word.get("heritage")
            if isinstance(stored_heritage, list) and stored_heritage and not legacy:
                current_hits = sources_instance.heritage([lemma]).raw.get(lemma, [])
                current_digests = [hit.get("row_sha256") for hit in current_hits]
                recorded_digests = []
                for index, hit in enumerate(stored_heritage):
                    recorded = hit.get("row_sha256") if isinstance(hit, dict) else None
                    if not recorded:
                        errors.append(
                            f"{codes.FORM_MISMATCH}: heritage[{index}] of {word_id} ({lemma}) has no row_sha256"
                        )
                        continue
                    if sources.heritage_hit_digest(hit) != recorded:
                        errors.append(
                            f"{codes.LOCK_MISMATCH}: heritage[{index}] of {word_id} ({lemma}) "
                            f"does not match its own row_sha256"
                        )
                    recorded_digests.append(recorded)
                if recorded_digests and recorded_digests != current_digests:
                    word_rows_drifted = True
                    _drift(
                        strict,
                        errors,
                        warnings,
                        f"heritage of {word_id} ({lemma}): cited rows changed "
                        f"({len(recorded_digests)} recorded, {len(current_digests)} current)",
                    )

            if entry == "unresolved":
                cites = find_plans_citing(word_id, plans_base)
                if cites:
                    errors.append(f"{codes.UNRESOLVED_CITED}: unresolved word {word_id} ({lemma}) is cited by {cites}")
                else:
                    unresolved_uncited_count += 1
                rows_drifted_total += int(word_rows_drifted)
                continue

            # Resolved entry
            paradigm_res = sources_instance.inspect_lemma_forms(lemma, pos)
            forms_by_entry = paradigm_res.forms_by_entry

            # ULIF spelling group check for this word (also gates ULIF-keyed entries)
            ulif_group = sources_instance.ulif_entries([lemma]).raw.get(lemma, [])
            ulif_checked = sources_instance.ulif_group_checked(ulif_group)

            if isinstance(entry, dict) and entry.get("source") == "vesum":
                entry_id = entry.get("entry_id")
            elif isinstance(entry, dict) and entry.get("source") == "ulif":
                req_hi = entry.get("key", [None, 1])[1]
                ulif_homonym = next((e for e in ulif_group if e.get("homonym_index") == req_hi), None)
                if ulif_homonym is None:
                    errors.append(f"{codes.FORM_MISMATCH}: entry {entry} for {lemma} ({pos}) not found in ULIF")
                    continue
                if len(forms_by_entry) == 1:
                    entry_id = next(iter(forms_by_entry))
                else:
                    sorted_eids = sorted(forms_by_entry.keys())
                    if isinstance(req_hi, int) and 1 <= req_hi <= len(sorted_eids):
                        entry_id = sorted_eids[req_hi - 1]
                    else:
                        entry_id = None
            else:
                entry_id = None

            if entry_id is None or entry_id not in forms_by_entry:
                errors.append(f"{codes.FORM_MISMATCH}: entry {entry} for {lemma} ({pos}) no longer in VESUM")
                continue

            vesum_forms = forms_by_entry[entry_id]
            stored_forms = word.get("forms", [])
            total_forms += len(stored_forms)

            # Compare the complete paradigm, including count and form ordering
            if len(stored_forms) != len(vesum_forms):
                errors.append(
                    f"{codes.FORM_MISMATCH}: paradigm length mismatch for {word_id} ({lemma}): "
                    f"{len(stored_forms)} stored forms vs {len(vesum_forms)} in VESUM"
                )

            # ULIF spelling group was fetched above during entry resolution
            matching_entry = None
            if ulif_checked:
                if isinstance(entry, dict) and entry.get("source") == "ulif":
                    matching_entry = next((e for e in ulif_group if e.get("homonym_index") == entry["key"][1]), None)
                elif isinstance(word.get("ulif"), dict) and word["ulif"].get("source") == "ulif":
                    matching_entry = next(
                        (e for e in ulif_group if e.get("homonym_index") == word["ulif"]["key"][1]), None
                    )
                elif len(ulif_group) == 1:
                    matching_entry = ulif_group[0]

            ulif_forms = extract_ulif_paradigm_forms(matching_entry) if (ulif_checked and matching_entry) else {}

            # The stored ulif object cites one entry row (with its ordered sections).
            stored_ulif = word.get("ulif")
            if isinstance(stored_ulif, dict):
                expected_ulif = None
                if matching_entry is not None:
                    expected_ulif = {"row_sha256": sources.row_digest(matching_entry)}
                cited_row_check("ulif", stored_ulif, expected_ulif)
            rows_drifted_total += int(word_rows_drifted)
            # A stress mismatch is SOURCE_CHANGED only when a source this word copies from moved.
            word_source_changed = source_version_changed or word_rows_drifted

            for idx, (sf, vf) in enumerate(zip(stored_forms, vesum_forms, strict=False)):
                form_str = sf.get("form")
                tags_str = sf.get("tags")
                vf_form = vf.get("word_form")
                vf_tags = vf.get("tags")

                if form_str != vf_form or tags_str != vf_tags:
                    errors.append(
                        f"{codes.FORM_MISMATCH}: form at index {idx} mismatch for {word_id}: "
                        f"({form_str!r}, {tags_str!r}) vs VESUM ({vf_form!r}, {vf_tags!r})"
                    )
                    continue

                # Excluding marker check
                vf_markers = vf.get("markers", [])
                has_excluding = any(
                    (m["marker"] if isinstance(m, dict) else m) in codes.EXCLUDING_MARKERS for m in vf_markers
                )
                if sf.get("learner") is True and has_excluding:
                    errors.append(
                        f"{codes.LEARNER_MARKER}: form {form_str!r} of {word_id} is marked learner: true but carries excluding marker: {vf_markers}"
                    )

                # ULIF check
                if sf.get("stress_source") == "ulif" and not ulif_checked:
                    errors.append(
                        f"{codes.UNCHECKED_ULIF}: form {form_str!r} of {word_id} has stress_source: ulif but group is unchecked"
                    )

                # Stress check
                stored_stress_source = sf.get("stress_source")
                stored_stressed = sf.get("stressed")

                if stored_stress_source == "none" and stored_stressed != form_str:
                    errors.append(
                        f"{codes.STRESS_MISMATCH}: stress_source none requires stressed == form: {form_str!r} vs {stored_stressed!r}"
                    )

                # Re-derive rule 4 stress
                if count_vowels(form_str) == 1:
                    expected_source = "none"
                    expected_stressed = form_str
                elif ulif_checked and matching_entry and form_str in ulif_forms:
                    expected_source = "ulif"
                    expected_stressed = ulif_forms[form_str]
                else:
                    stress_res = sources_instance.stress_for_form(form_str, tags_str)
                    raw_st = stress_res.raw
                    st_status = raw_st.get("status")
                    matches = raw_st.get("matches", [])
                    if st_status == "ok" and len(matches) == 1:
                        expected_source = "trie"
                        expected_stressed = matches[0]["stressed_form"]
                    else:
                        expected_source = "pending"
                        expected_stressed = None

                stress_mismatch = False
                if stored_stress_source != expected_source or (
                    expected_stressed is not None and stored_stressed != expected_stressed
                ):
                    stress_mismatch = True
                if stored_stress_source == "pending" and "stressed" in sf:
                    stress_mismatch = True

                if stress_mismatch:
                    msg = (
                        f"form {form_str!r} ({word_id}): stored ({stored_stress_source}, {stored_stressed}) "
                        f"!= current ({expected_source}, {expected_stressed})"
                    )
                    if word_source_changed:
                        _drift(strict, errors, warnings, msg)
                    else:
                        errors.append(f"{codes.STRESS_MISMATCH}: {msg}")

                if stored_stress_source == "pending":
                    pending_forms_count += 1
                if sf.get("override") is True:
                    override_forms_count += 1

            if len(stored_forms) > len(vesum_forms):
                for sf in stored_forms[len(vesum_forms) :]:
                    errors.append(f"{codes.FORM_MISMATCH}: extra form {sf.get('form')!r} for {word_id} not in VESUM")

        status = "failed" if errors else ("warning" if warnings else "ok")

        return {
            "status": status,
            "level": level,
            "strict": strict,
            "words_count": len(words_list),
            "forms_count": total_forms,
            "pending_forms_count": pending_forms_count,
            "override_forms_count": override_forms_count,
            "unresolved_uncited_count": unresolved_uncited_count,
            "source_version_changed": source_version_changed,
            "sources_db_scheme": scheme,
            "cited_rows_drifted_words": rows_drifted_total,
            "snapshot": sources_instance.snapshot_report(),
            "errors": errors,
            "warnings": warnings,
        }
    finally:
        if owns_sources:
            sources_instance.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.curriculum.evidence words-verify",
        description=(
            "Verify integrity of the level word store (_words.yaml) against sources and ledger.\n"
            "Use in CI and preflight to detect corruption or unauthorized edits; read-only."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.curriculum.evidence words-verify a1\n"
            "  .venv/bin/python -m scripts.curriculum.evidence words-verify a1 --strict\n"
            "  .venv/bin/python -m scripts.curriculum.evidence words-verify a1 --json\n\n"
            "Outputs:\n"
            "  None (read-only verification check)\n\n"
            "Exit codes:\n"
            "  0: Store verified cleanly (or source_changed/legacy_identity under non-strict)\n"
            "  1: Lock mismatch, registry disagreement, corruption, or source_changed under --strict\n\n"
            "Outcome Codes:\n"
            f"{codes.help_text()}\n"
        ),
    )
    parser.add_argument("level", help="Target curriculum level slug (e.g. 'a1', 'a2')")
    parser.add_argument("--strict", action="store_true", help="Fail on source_changed instead of warning")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON result to stdout")
    parser.add_argument("--evidence-dir", type=Path, default=None, help="Override evidence output directory")
    parser.add_argument("--plans-dir", type=Path, default=None, help="Override lesson plans directory")
    parser.add_argument(
        "--sources-db", type=Path, default=None, help="Override sources database path (default: data/sources.db)"
    )
    parser.add_argument("--vesum-db", type=Path, default=None, help="Override VESUM database path")

    args = parser.parse_args(argv)

    report = lambda msg: print(f"progress: {msg}", file=sys.stderr)  # noqa: E731
    explicit_sources = None
    if args.sources_db is not None or args.vesum_db is not None:
        explicit_sources = sources.Sources(sources_db=args.sources_db, vesum_db=args.vesum_db, report=report)

    try:
        result = verify_words_store(
            args.level,
            evidence_dir=args.evidence_dir,
            plans_dir=args.plans_dir,
            sources_instance=explicit_sources,
            strict=args.strict,
            report=report,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "failed", "error": str(exc)}, indent=2))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        if explicit_sources is not None:
            explicit_sources.close()

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Word Store Verification: level={result['level']} status={result['status'].upper()}")
        print(f"Verified: {result.get('words_count', 0)} records, {result.get('forms_count', 0)} forms")
        print("Open records / reports:")
        print(f"  pending forms: {result.get('pending_forms_count', 0)}")
        print(f"  override forms: {result.get('override_forms_count', 0)}")
        print(f"  unresolved un-cited records: {result.get('unresolved_uncited_count', 0)}")

        for warn in result.get("warnings", []):
            print(f"WARNING: {warn}", file=sys.stderr)
        for err in result.get("errors", []):
            print(f"ERROR: {err}", file=sys.stderr)

    return 1 if result["status"] == "failed" else 0


def verify_pack(
    level: str,
    slug: str,
    *,
    evidence_dir: Path | None = None,
    plans_dir: Path | None = None,
    sources_instance: sources.Sources | None = None,
    standard_path: Path | None = None,
    offline: bool = False,
    strict: bool = False,
    report: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Verify integrity of a module evidence pack against sources, locks, and State Standard."""
    if strict and offline:
        return {
            "status": "failed",
            "level": level,
            "slug": slug,
            "module": f"{level}/{slug}",
            "errors": [f"{codes.INVALID_REQUEST}: --strict and --offline together are refused"],
            "warnings": [],
            "reports": [],
            "chunk_id_moved": [],
            "not_checked": [],
        }

    evidence_base = (
        Path(evidence_dir) if evidence_dir is not None else REPO_ROOT / "curriculum/l2-uk-en/evidence" / level
    )
    pack_path = evidence_base / f"{slug}.yaml"

    errors: list[str] = []
    warnings: list[str] = []
    reports: list[str] = []
    chunk_id_moved: list[str] = []
    not_checked: list[str] = []

    if not pack_path.is_file():
        return {
            "status": "failed",
            "level": level,
            "slug": slug,
            "module": f"{level}/{slug}",
            "errors": [f"{codes.SOURCE_UNAVAILABLE}: pack file missing at {pack_path}"],
            "warnings": [],
            "reports": [],
            "chunk_id_moved": [],
            "not_checked": [],
        }

    # 1. Lock check
    if not lock.check(pack_path):
        errors.append(f"{codes.LOCK_MISMATCH}: pack file lock mismatch: {pack_path}")

    # 2. Schema check & forbidden words field
    try:
        pack_doc = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
        if not isinstance(pack_doc, dict):
            errors.append(f"{codes.INVALID_REQUEST}: {pack_path} is not a valid YAML mapping")
            return {
                "status": "failed",
                "level": level,
                "slug": slug,
                "module": f"{level}/{slug}",
                "errors": errors,
                "warnings": warnings,
                "reports": reports,
                "chunk_id_moved": chunk_id_moved,
                "not_checked": not_checked,
            }

        if "words" in pack_doc:
            errors.append(f"{codes.WORDS_FIELD_FORBIDDEN}: pack contains forbidden 'words' field")

        schema = load_schema("evidence-pack-v1.schema.json")
        validator = Draft202012Validator(schema)
        for err in validator.iter_errors(pack_doc):
            errors.append(f"{codes.FORM_MISMATCH}: schema error: {err.message}")
    except Exception as exc:
        errors.append(f"{codes.INVALID_REQUEST}: failed parsing {pack_path}: {exc}")
        return {
            "status": "failed",
            "level": level,
            "slug": slug,
            "module": f"{level}/{slug}",
            "errors": errors,
            "warnings": warnings,
            "reports": reports,
            "chunk_id_moved": chunk_id_moved,
            "not_checked": not_checked,
        }

    owns_sources = False
    if sources_instance is None:
        sources_instance = sources.Sources(standard_path=standard_path, report=report)
        owns_sources = True

    try:
        # 3. sources.db identity scheme: rows-v2 verifies each cited row below;
        #    file-v1 recorded a file digest, which only the retired file hash could check.
        built_with = pack_doc.get("built_with", {})
        scheme = pack.pack_scheme(pack_doc)
        legacy = scheme != sources.SOURCES_DB_SCHEME
        rows_drifted: list[str] = []
        if legacy:
            msg = (
                f"{codes.LEGACY_IDENTITY}: built_with.sources_db is a file digest ({scheme}); "
                f"rebuild the pack for {sources.SOURCES_DB_SCHEME}"
            )
            if strict:
                errors.append(msg)
            else:
                warnings.append(msg)
        else:
            recorded_aggregate = sources.aggregate_digest(pack.cited_rows(pack_doc))
            if recorded_aggregate != built_with.get("sources_db"):
                errors.append(
                    f"{codes.LOCK_MISMATCH}: built_with.sources_db {str(built_with.get('sources_db'))[:12]}... "
                    f"does not aggregate the recorded row_sha256 values ({recorded_aggregate[:12]}...)"
                )

        def cited_row_check(item_id: str, source: dict[str, Any], row: dict[str, Any] | None) -> None:
            """rows-v2: a cited row must exist at its locator and still digest to what the pack recorded."""
            if legacy:
                return
            recorded = source.get("row_sha256") if isinstance(source, dict) else None
            if not recorded:
                errors.append(f"{codes.FORM_MISMATCH}: {item_id} source has no row_sha256")
                return
            if row is None:
                rows_drifted.append(item_id)
                _drift(strict, errors, warnings, f"{item_id} cited row missing at its locator {pack.locator(source)}")
                return
            current = sources.row_digest(row)
            if current != recorded:
                rows_drifted.append(item_id)
                _drift(
                    strict,
                    errors,
                    warnings,
                    f"{item_id} cited row changed (recorded {recorded[:12]}..., current {current[:12]}...)",
                )

        # Helper to verify quotes against chunk and source_file
        def verify_quote(
            item_id: str,
            quote: str,
            recorded_sha: str,
            source: dict[str, Any],
            table: str = "textbooks",
        ) -> None:
            source_file = source["file"]
            chunk_id = source["chunk_id"]
            actual_sha = hashlib.sha256(quote.encode("utf-8")).hexdigest()
            if actual_sha != recorded_sha:
                errors.append(
                    f"{codes.LOCK_MISMATCH}: {item_id} quote sha256 mismatch: recorded {recorded_sha[:12]}..., actual {actual_sha[:12]}..."
                )

            norm_quote = " ".join(sources.normalize_spelling(quote).split())
            if table == "textbooks":
                chunk = sources_instance.get_textbook_chunk(chunk_id)
            else:
                chunk = sources_instance.get_literary_chunk(chunk_id)

            # The cited row's identity is judged on its own, before any file-level
            # quote fallback: a missing or changed row is drift even when the quote
            # survives elsewhere in the file (chunk_id_moved stays an extra report).
            cited_row_check(item_id, source, chunk)

            found_in_chunk = False
            if chunk is not None:
                norm_chunk = " ".join(sources.normalize_spelling(chunk["text"]).split())
                if norm_quote in norm_chunk:
                    found_in_chunk = True

            if not found_in_chunk:
                # Substring search over concatenated text of source_file's chunks in section order
                if table == "textbooks":
                    file_chunks = sources_instance.get_textbook_file_chunks(source_file)
                else:
                    file_chunks = sources_instance.get_literary_file_chunks(source_file)
                norm_file = " ".join(sources.normalize_spelling(" ".join(c["text"] for c in file_chunks)).split())
                if norm_quote in norm_file:
                    chunk_id_moved.append(item_id)
                    reports.append(
                        f"{codes.CHUNK_ID_MOVED}: {item_id} chunk_id {chunk_id} moved but quote found in file {source_file}"
                    )
                else:
                    errors.append(
                        f"{codes.QUOTE_MISMATCH}: {item_id} quote no longer found in source_file {source_file}: {quote[:40]!r}"
                    )

        # 4. Texts
        for t in pack_doc.get("texts", []):
            verify_quote(t["id"], t["quote"], t["sha256"], t["source"], table="textbooks")

        # 5. Exercises
        for x in pack_doc.get("exercises", []):
            verify_quote(x["id"], x["quote"], x["sha256"], x["source"], table="textbooks")

        # 6. Examples
        for ex in pack_doc.get("examples", []):
            kind = ex["source"].get("kind")
            table = "literary_texts" if kind == "literary" else "textbooks"
            verify_quote(ex["id"], ex["text"], ex["sha256"], ex["source"], table=table)

        # 7. Errors
        for err_rec in pack_doc.get("errors", []):
            row_id = err_rec["source"]["id"]
            row = sources_instance.get_ua_gec_error_by_id(row_id)
            if row is None:
                errors.append(f"{codes.ERROR_MISMATCH}: error {err_rec['id']} row {row_id} not found in ua_gec_errors")
            elif row["error"] != err_rec["incorrect"] or row["correct"] != err_rec["correct"]:
                errors.append(
                    f"{codes.ERROR_MISMATCH}: error {err_rec['id']} content changed in source: "
                    f"expected ({err_rec['incorrect']!r}, {err_rec['correct']!r}), "
                    f"got ({row['error']!r}, {row['correct']!r})"
                )
            cited_row_check(err_rec["id"], err_rec["source"], row)

        # 8. Notes
        for note_rec in pack_doc.get("notes", []):
            row_id = note_rec["source"]["id"]
            row = sources_instance.get_style_guide_entry(row_id)
            if row is None:
                errors.append(f"{codes.ERROR_MISMATCH}: note {note_rec['id']} row {row_id} not found in style_guide")
            elif row["word"] != note_rec["word"] or row["text"] != note_rec["text"]:
                errors.append(
                    f"{codes.ERROR_MISMATCH}: note {note_rec['id']} content changed in source: "
                    f"expected word={note_rec['word']!r}, text={note_rec['text'][:40]!r}, "
                    f"got word={row['word']!r}, text={row['text'][:40]!r}"
                )
            cited_row_check(note_rec["id"], note_rec["source"], row)

        # 9. Standard
        for std_rec in pack_doc.get("standard", []):
            lines_str = std_rec["lines"]
            start_str, end_str = lines_str.split("-")
            cur_text, cur_sha = sources_instance.get_standard_lines(int(start_str), int(end_str))
            if cur_sha != std_rec["file_sha256"]:
                errors.append(
                    f"{codes.STANDARD_MISMATCH}: standard {std_rec['id']} file_sha256 changed: "
                    f"expected {std_rec['file_sha256'][:12]}..., got {cur_sha[:12]}..."
                )
            if cur_text != std_rec["text"]:
                errors.append(
                    f"{codes.STANDARD_MISMATCH}: standard {std_rec['id']} text for lines {lines_str} changed: "
                    f"expected {std_rec['text'][:40]!r}, got {cur_text[:40]!r}"
                )

        # 10. Videos
        for vid_rec in pack_doc.get("videos", []):
            if offline:
                not_checked.append(vid_rec["id"])
                reports.append(f"{codes.NOT_CHECKED}: video {vid_rec['id']} not checked (offline)")
            else:
                try:
                    res = sources_instance.check_url(vid_rec["url"], timeout=10.0)
                    if res["http_status"] != 200:
                        msg = f"video {vid_rec['id']} url {vid_rec['url']} returned status {res['http_status']}"
                        if strict:
                            errors.append(f"{codes.INVALID_REQUEST}: {msg}")
                        else:
                            warnings.append(f"{codes.NOT_CHECKED}: {msg}")
                except Exception as exc:
                    msg = f"video {vid_rec['id']} url check failed: {exc}"
                    if strict:
                        errors.append(f"{codes.INVALID_REQUEST}: {msg}")
                    else:
                        warnings.append(f"{codes.NOT_CHECKED}: {msg}")

        # 11. Unsupported
        open_unsupported = [
            u["id"] for u in pack_doc.get("unsupported", []) if isinstance(u, dict) and u.get("status") == "open"
        ]
        resolved_unsupported = [
            u["id"] for u in pack_doc.get("unsupported", []) if isinstance(u, dict) and u.get("status") == "resolved"
        ]
        if open_unsupported:
            msg = f"{codes.OPEN_UNSUPPORTED}: {len(open_unsupported)} unsupported records open: {open_unsupported}"
            reports.append(msg)
            if strict:
                errors.append(msg)

        if rows_drifted:
            reports.append(f"{codes.SOURCE_CHANGED}: {len(rows_drifted)} cited rows drifted: {rows_drifted}")

        status = "failed" if errors else ("warning" if warnings else "ok")

        return {
            "status": status,
            "level": level,
            "slug": slug,
            "module": f"{level}/{slug}",
            "texts_count": len(pack_doc.get("texts", [])),
            "exercises_count": len(pack_doc.get("exercises", [])),
            "examples_count": len(pack_doc.get("examples", [])),
            "errors_count": len(pack_doc.get("errors", [])),
            "notes_count": len(pack_doc.get("notes", [])),
            "videos_count": len(pack_doc.get("videos", [])),
            "standard_count": len(pack_doc.get("standard", [])),
            "unsupported_open_count": len(open_unsupported),
            "unsupported_resolved_count": len(resolved_unsupported),
            "sources_db_scheme": scheme,
            "cited_rows_drifted": rows_drifted,
            "chunk_id_moved": chunk_id_moved,
            "not_checked": not_checked,
            "snapshot": sources_instance.snapshot_report(),
            "reports": reports,
            "warnings": warnings,
            "errors": errors,
        }
    finally:
        if owns_sources:
            sources_instance.close()


def main_pack(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.curriculum.evidence pack-verify",
        description=(
            "Verify integrity of a module evidence pack (<slug>.yaml) against sources, locks, and State Standard.\n"
            "Use in CI and preflight to detect quote shifts, source edits, or open claims; read-only."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.curriculum.evidence pack-verify a1 alphabet\n"
            "  .venv/bin/python -m scripts.curriculum.evidence pack-verify a1 alphabet --strict\n"
            "  .venv/bin/python -m scripts.curriculum.evidence pack-verify a1 alphabet --offline\n"
            "  .venv/bin/python -m scripts.curriculum.evidence pack-verify a1 alphabet --json\n\n"
            "Outputs:\n"
            "  None (read-only verification check)\n\n"
            "Exit codes:\n"
            "  0: Pack verified cleanly (or source_changed/legacy_identity/open_unsupported under non-strict)\n"
            "  1: Lock mismatch, quote mismatch, error mismatch, standard mismatch, open unsupported under --strict, or refused --strict --offline\n\n"
            "Outcome Codes:\n"
            f"{codes.help_text()}\n"
        ),
    )
    parser.add_argument("level", help="Target curriculum level slug (e.g. 'a1', 'a2')")
    parser.add_argument("slug", help="Target module slug (e.g. 'alphabet', 'introductions')")
    parser.add_argument("--strict", action="store_true", help="Fail on source_changed or open unsupported")
    parser.add_argument("--offline", action="store_true", help="Do not check video URLs over network")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON result to stdout")
    parser.add_argument("--evidence-dir", type=Path, default=None, help="Override evidence output directory")
    parser.add_argument("--plans-dir", type=Path, default=None, help="Override lesson plans directory")
    parser.add_argument(
        "--sources-db", type=Path, default=None, help="Override sources database path (default: data/sources.db)"
    )
    parser.add_argument("--vesum-db", type=Path, default=None, help="Override VESUM database path")
    parser.add_argument("--standard-path", type=Path, default=None, help="Override State Standard file path")

    args = parser.parse_args(argv)

    report = lambda msg: print(f"progress: {msg}", file=sys.stderr)  # noqa: E731
    explicit_sources = None
    if args.sources_db is not None or args.vesum_db is not None or args.standard_path is not None:
        explicit_sources = sources.Sources(
            sources_db=args.sources_db,
            vesum_db=args.vesum_db,
            standard_path=args.standard_path,
            report=report,
        )

    try:
        result = verify_pack(
            args.level,
            args.slug,
            evidence_dir=args.evidence_dir,
            plans_dir=args.plans_dir,
            sources_instance=explicit_sources,
            standard_path=args.standard_path,
            offline=args.offline,
            strict=args.strict,
            report=report,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "failed", "error": str(exc)}, indent=2))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        if explicit_sources is not None:
            explicit_sources.close()

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Evidence Pack Verification: module={result['module']} status={result['status'].upper()}")
        print(
            f"Verified: texts={result['texts_count']}, exercises={result['exercises_count']}, "
            f"examples={result['examples_count']}, errors={result['errors_count']}, "
            f"notes={result['notes_count']}, videos={result['videos_count']}, "
            f"standard={result['standard_count']}"
        )
        print(f"Unsupported: {result['unsupported_open_count']} open, {result['unsupported_resolved_count']} resolved")
        if result["chunk_id_moved"]:
            print(f"Moved chunk IDs (matching text): {result['chunk_id_moved']}")
        if result["not_checked"]:
            print(f"Not checked: {result['not_checked']}")
        for rep in result.get("reports", []):
            print(f"REPORT: {rep}")
        for warn in result.get("warnings", []):
            print(f"WARNING: {warn}", file=sys.stderr)
        for err in result.get("errors", []):
            print(f"ERROR: {err}", file=sys.stderr)

    return 1 if result["status"] == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())
