"""Verification of the level word store (_words.yaml and _words.registry.yaml).

Re-derives every fact from current sources; read-only.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.verification import stress

from . import codes, lock, registry, sources
from .words import count_vowels, find_plans_citing, load_schema

REPO_ROOT = Path(__file__).resolve().parents[3]


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

            if entry == "unresolved":
                cites = find_plans_citing(word_id, plans_base)
                if cites:
                    errors.append(f"{codes.UNRESOLVED_CITED}: unresolved word {word_id} ({lemma}) is cited by {cites}")
                else:
                    unresolved_uncited_count += 1
                continue

            # Resolved entry
            entry_id = entry.get("entry_id")
            paradigm_res = sources_instance.inspect_lemma_forms(lemma, pos)
            forms_by_entry = paradigm_res.forms_by_entry

            if entry_id not in forms_by_entry:
                errors.append(f"{codes.FORM_MISMATCH}: entry {entry_id} for {lemma} ({pos}) no longer in VESUM")
                continue

            vesum_forms = forms_by_entry[entry_id]
            vesum_map = {(f["word_form"], f["tags"]): f for f in vesum_forms}

            stored_forms = word.get("forms", [])
            total_forms += len(stored_forms)

            for sf in stored_forms:
                form_str = sf["form"]
                tags_str = sf["tags"]
                key = (form_str, tags_str)

                if key not in vesum_map:
                    errors.append(
                        f"{codes.FORM_MISMATCH}: form {form_str!r} with tags {tags_str!r} no longer in VESUM for {word_id}"
                    )
                    continue

                vf = vesum_map[key]

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
                if sf.get("stress_source") == "ulif":
                    ulif_group = sources_instance.ulif_entries([lemma]).raw.get(lemma, [])
                    if not sources_instance.ulif_group_checked(ulif_group):
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

                if stress_mismatch:
                    msg = (
                        f"form {form_str!r} ({word_id}): stored ({stored_stress_source}, {stored_stressed}) "
                        f"!= current ({expected_source}, {expected_stressed})"
                    )
                    if source_version_changed:
                        if strict:
                            errors.append(f"{codes.SOURCE_CHANGED}: {msg}")
                        else:
                            warnings.append(f"{codes.SOURCE_CHANGED}: {msg}")
                    else:
                        errors.append(f"{codes.STRESS_MISMATCH}: {msg}")

                if stored_stress_source == "pending":
                    pending_forms_count += 1
                if sf.get("override") is True:
                    override_forms_count += 1

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
            "  0: Store verified cleanly (or source_changed under non-strict)\n"
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

    args = parser.parse_args(argv)

    result = verify_words_store(
        args.level,
        evidence_dir=args.evidence_dir,
        plans_dir=args.plans_dir,
        strict=args.strict,
        report=lambda msg: print(f"progress: {msg}", file=sys.stderr),
    )

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


if __name__ == "__main__":
    sys.exit(main())
