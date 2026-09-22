"""Build and update the level word store (_words.yaml and _words.registry.yaml).

The builder copies from sources; it never writes a Ukrainian form, stress, or gloss.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.verification import stress

from . import codes, lock, registry, sources

REPO_ROOT = Path(__file__).resolve().parents[3]
UKRAINIAN_VOWELS = frozenset("аеєиіїоуюяАЕЄИІЇОУЮЯ")


def count_vowels(word: str) -> int:
    """Count Ukrainian vowels to gate monosyllables before calling the oracle."""
    return sum(1 for ch in word if ch in UKRAINIAN_VOWELS)


def get_mcp_commit(repo_root: Path = REPO_ROOT) -> str:
    """Retrieve the 40-hex commit hash of HEAD for built_with."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        sha = proc.stdout.strip()
        if len(sha) == 40 and re.fullmatch(r"[0-9a-f]{40}", sha):
            return sha
    except Exception:
        pass
    return "0" * 40


def load_schema(name: str) -> dict[str, Any]:
    schema_path = REPO_ROOT / f"schemas/{name}"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_request_data(data: Any) -> None:
    schema = load_schema("evidence-words-request-v1.schema.json")
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(data))
    if errors:
        first = errors[0]
        raise ValueError(f"{codes.INVALID_REQUEST}: {first.message}")


def validate_store_data(data: Any) -> None:
    schema = load_schema("evidence-words-v1.schema.json")
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(data))
    if errors:
        first = errors[0]
        raise ValueError(f"{codes.INVALID_REQUEST}: store validation failed: {first.message}")


def find_plans_citing(word_id: str, plans_dir: Path | None) -> list[str]:
    """Find relative paths of lesson plans citing a given word id."""
    if plans_dir is None or not plans_dir.is_dir():
        return []
    pattern = re.compile(r"\b" + re.escape(word_id) + r"\b")
    citing: list[str] = []
    for plan_file in sorted(plans_dir.rglob("*.yaml")):
        if plan_file.name.startswith("."):
            continue
        try:
            text = plan_file.read_text(encoding="utf-8")
            if pattern.search(text):
                citing.append(str(plan_file.relative_to(plans_dir)))
        except OSError:
            continue
    return citing


def build_words(
    level: str,
    request_path: Path,
    *,
    evidence_dir: Path | None = None,
    plans_dir: Path | None = None,
    sources_instance: sources.Sources | None = None,
    dry_run: bool = False,
    stamp: bool = False,
    mcp_commit: str | None = None,
    report: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Build or update a level word store from a validated request file."""
    request_path = Path(request_path)
    if not request_path.is_file():
        raise FileNotFoundError(f"{codes.INVALID_REQUEST}: request file not found: {request_path}")

    request_raw = yaml.safe_load(request_path.read_text(encoding="utf-8"))
    validate_request_data(request_raw)

    if request_raw.get("level") != level:
        raise ValueError(
            f"{codes.INVALID_REQUEST}: request level {request_raw.get('level')!r} does not match {level!r}"
        )

    evidence_base = (
        Path(evidence_dir) if evidence_dir is not None else REPO_ROOT / "curriculum/l2-uk-en/evidence" / level
    )
    plans_base = Path(plans_dir) if plans_dir is not None else REPO_ROOT / "curriculum/l2-uk-en/lesson-plans" / level

    store_path = evidence_base / "_words.yaml"
    registry_path = evidence_base / "_words.registry.yaml"

    registry_records = registry.load(registry_path) if registry_path.exists() else []
    active_reg_ids = {r["id"] for r in registry_records if not r.get("retired")}

    existing_words: dict[str, dict[str, Any]] = {}
    if store_path.exists():
        lock.require(store_path)
        existing_doc = yaml.safe_load(store_path.read_text(encoding="utf-8"))
        validate_store_data(existing_doc)
        existing_words = {w["id"]: w for w in existing_doc.get("words", []) if w["id"] in active_reg_ids}

    owns_sources = False
    if sources_instance is None:
        sources_instance = sources.Sources(report=report)
        owns_sources = True

    try:
        commit_sha = mcp_commit if mcp_commit is not None else get_mcp_commit()
        sources_db_hash = sources_instance._fingerprint(sources_instance.sources_db)[0]
        vesum_hash = sources_instance._vesum_identity()[0]
        trie_hash = stress.source_info()["digest"]

        overrides_hash = (
            sources._file_hash(stress.STRESS_OVERRIDES_PATH) if stress.STRESS_OVERRIDES_PATH.exists() else None
        )

        built_fingerprint = hashlib.sha256(
            f"{sources_db_hash}:{vesum_hash}:{trie_hash}:{commit_sha}".encode()
        ).hexdigest()

        # Gather requests
        requested_words = request_raw["words"]
        lemmas_requested = [sources.normalize_spelling(rw["lemma"]) for rw in requested_words]
        lemma_pos_pairs = [(sources.normalize_spelling(rw["lemma"]), rw["pos"]) for rw in requested_words]

        # Batch queries
        ulif_batch = sources_instance.ulif_entries(lemmas_requested).raw
        cefr_batch = sources_instance.cefr_levels(lemmas_requested).raw
        gloss_batch = sources_instance.gloss_rows(lemma_pos_pairs).raw
        ru_batch = sources_instance.russian_patterns(lemmas_requested)
        ru_patterns_raw = ru_batch.raw

        words_out: dict[str, dict[str, Any]] = dict(existing_words)
        changed_ids: list[str] = []

        for rw in requested_words:
            lemma = sources.normalize_spelling(rw["lemma"])
            pos = rw["pos"]
            want = rw["want"]
            entry_req = rw.get("entry")
            note = rw.get("note")

            paradigm_res = sources_instance.inspect_lemma_forms(lemma, pos)
            forms_by_entry = paradigm_res.forms_by_entry

            if not forms_by_entry:
                raise ValueError(f"{codes.INVALID_REQUEST}: no VESUM entries for lemma {lemma!r} ({pos})")

            # Determine entry
            if len(forms_by_entry) == 1:
                single_entry_id = next(iter(forms_by_entry))
                if (
                    entry_req is not None
                    and entry_req.get("source") == "vesum"
                    and entry_req.get("entry_id") != single_entry_id
                ):
                    raise ValueError(
                        f"{codes.INVALID_REQUEST}: entry_id mismatch for {lemma!r}: "
                        f"{entry_req.get('entry_id')} vs {single_entry_id}"
                    )
                entry: dict[str, Any] | str = {"source": "vesum", "entry_id": single_entry_id}
            else:
                if entry_req is not None and entry_req.get("source") == "vesum":
                    req_eid = entry_req.get("entry_id")
                    if req_eid in forms_by_entry:
                        entry = {"source": "vesum", "entry_id": req_eid}
                    else:
                        raise ValueError(
                            f"{codes.INVALID_REQUEST}: requested entry_id {req_eid} not found for {lemma!r}"
                        )
                elif entry_req is not None and entry_req.get("source") == "ulif":
                    entry = entry_req
                else:
                    entry = "unresolved"

            # Allocate or verify id
            if want == "new":
                word_id = registry.allocate(
                    registry_records,
                    lemma=lemma,
                    pos=pos,
                    entry=entry,
                    allocated_at_build=built_fingerprint,
                )
            else:
                word_id = want
                existing_reg = next((r for r in registry_records if r["id"] == word_id and not r.get("retired")), None)
                if existing_reg is None:
                    raise ValueError(f"{codes.REGISTRY_MISMATCH}: active id {word_id} not found in registry")
                if existing_reg["lemma"] != lemma or existing_reg["pos"] != pos:
                    raise ValueError(
                        f"{codes.REGISTRY_MISMATCH}: id {word_id} lemma/pos mismatch: "
                        f"({lemma}, {pos}) vs ({existing_reg['lemma']}, {existing_reg['pos']})"
                    )
                if existing_reg["entry"] != "unresolved" and entry != existing_reg["entry"]:
                    raise ValueError(
                        f"{codes.REGISTRY_MISMATCH}: id {word_id} entry cannot change: "
                        f"{entry} vs {existing_reg['entry']}"
                    )

            # Check ULIF spelling group
            ulif_group = ulif_batch.get(lemma, [])
            ulif_checked = sources_instance.ulif_group_checked(ulif_group)
            ulif_field: dict[str, Any] | str = "pending"
            if ulif_checked:
                # Find matching ULIF entry
                matching_entry = None
                if entry_req is not None and entry_req.get("source") == "ulif":
                    matching_entry = next(
                        (e for e in ulif_group if e.get("homonym_index") == entry_req.get("homonym_index")), None
                    )
                elif len(ulif_group) == 1:
                    matching_entry = ulif_group[0]
                if matching_entry is not None:
                    ulif_field = {
                        "source": "ulif",
                        "key": [
                            matching_entry.get("canonical_headword", lemma),
                            matching_entry["homonym_index"],
                        ],
                    }

            word_doc: dict[str, Any] = {
                "id": word_id,
                "lemma": lemma,
                "pos": pos,
                "entry": entry,
                "ulif": ulif_field,
            }

            if entry == "unresolved":
                candidates: list[dict[str, Any]] = []
                for cand_eid, cand_forms in sorted(forms_by_entry.items()):
                    sample_forms = [f["word_form"] for f in cand_forms[:3]]
                    candidates.append({"entry_id": cand_eid, "forms": sample_forms})
                word_doc["candidates"] = candidates
                word_doc["forms"] = []
            else:
                entry_id = entry["entry_id"]
                forms_source = forms_by_entry[entry_id]
                forms_list: list[dict[str, Any]] = []

                for f in forms_source:
                    form_str = f["word_form"]
                    tags_str = f["tags"]
                    markers = f.get("markers", [])

                    is_learner = not any(
                        (m["marker"] if isinstance(m, dict) else m) in codes.EXCLUDING_MARKERS for m in markers
                    )

                    # Rule 4: stress per form
                    # a. Monosyllables gated before oracle
                    vowel_count = count_vowels(form_str)
                    if vowel_count == 1:
                        stress_source = "none"
                        stressed = form_str
                        f_entry: dict[str, Any] = {
                            "form": form_str,
                            "tags": tags_str,
                            "stressed": stressed,
                            "stress_source": stress_source,
                            "markers": markers,
                            "learner": is_learner,
                        }
                    else:
                        # b. trie oracle
                        stress_res = sources_instance.stress_for_form(form_str, tags_str)
                        raw_stress = stress_res.raw
                        status = raw_stress.get("status")
                        matches = raw_stress.get("matches", [])

                        if status == "ok" and len(matches) == 1:
                            stress_source = "trie"
                            stressed = matches[0]["stressed_form"]
                            f_entry = {
                                "form": form_str,
                                "tags": tags_str,
                                "stressed": stressed,
                                "stress_source": stress_source,
                                "markers": markers,
                                "learner": is_learner,
                            }
                            if matches[0].get("override_applied"):
                                f_entry["override"] = True
                        elif status == "ambiguous":
                            stress_source = "pending"
                            f_entry = {
                                "form": form_str,
                                "tags": tags_str,
                                "stress_source": stress_source,
                                "markers": markers,
                                "learner": is_learner,
                            }
                            if matches:
                                f_entry["stress_candidates"] = matches
                            if raw_stress.get("unresolvable_by_tags"):
                                f_entry["unresolvable_by_tags"] = True
                        else:  # not_found or invalid_input
                            stress_source = "pending"
                            f_entry = {
                                "form": form_str,
                                "tags": tags_str,
                                "stress_source": stress_source,
                                "markers": markers,
                                "learner": is_learner,
                            }

                    forms_list.append(f_entry)

                word_doc["forms"] = forms_list

            # Rule 6: Other fields
            # CEFR: exact match only
            cefr_hits = cefr_batch.get(lemma, [])
            exact_cefr = next((h for h in cefr_hits if sources.normalize_spelling(h.get("word", "")) == lemma), None)
            if exact_cefr and exact_cefr.get("level") in {"A1", "A2", "B1", "B2", "C1", "C2"}:
                word_doc["cefr"] = {"level": exact_cefr["level"], "source": "puls"}

            # Gloss: first translation of matching row
            gloss_rows = gloss_batch.get((lemma, pos), [])
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
                        word_doc["gloss_en"] = first_str
                        word_doc["gloss_source"] = {"table": "dmklinger_uk_en", "id": first_row["id"]}

            # Russian shadow & heritage
            pat = ru_patterns_raw.get(lemma, {})
            is_shadow = bool(pat.get("matches_russian", False))
            score = float(pat.get("confidence", 0.0))
            word_doc["shadow"] = {"russian_shadow": is_shadow, "score": score}
            if is_shadow:
                heritage_hits = sources_instance.heritage([lemma]).raw.get(lemma, [])
                if heritage_hits:
                    word_doc["heritage"] = heritage_hits

            # Note
            if note:
                word_doc["note"] = note

            if word_id in existing_words and existing_words[word_id] != word_doc:
                changed_ids.append(word_id)

            words_out[word_id] = word_doc

        # Check citing plans for any changed existing records (Rule 7)
        changed_plans_map: dict[str, list[str]] = {}
        for cid in changed_ids:
            citing = find_plans_citing(cid, plans_base)
            if citing:
                changed_plans_map[cid] = citing

        # Sort store records by numeric id
        sorted_words = [words_out[wid] for wid in sorted(words_out.keys(), key=registry.number)]

        # Check store against registry
        registry.check_store(registry_records, sorted_words)

        built_with: dict[str, Any] = {
            "mcp_commit": commit_sha,
            "sources_db": sources_db_hash,
            "vesum": vesum_hash,
            "trie": trie_hash,
            "ulif_forms": "pending",
        }
        if overrides_hash is not None:
            built_with["overrides_sha256"] = overrides_hash
        built_with["russian_patterns"] = ru_batch.content_hash

        if stamp:
            built_with["built_at"] = datetime.now(UTC).isoformat()

        store_doc = {
            "evidence_schema": 1,
            "level": level,
            "built_with": built_with,
            "words": sorted_words,
        }

        validate_store_data(store_doc)

        # Write files if not dry-run
        store_lock_digest = None
        registry_lock_digest = None
        if not dry_run:
            store_bytes = lock.yaml_bytes(store_doc)
            store_lock_digest = lock.write(store_path, store_bytes)
            registry_lock_digest = registry.write(registry_path, registry_records)

        # Collect summary metrics
        total_forms = sum(len(w.get("forms", [])) for w in sorted_words)
        stress_counts = {"trie": 0, "none": 0, "ulif": 0, "pending": 0}
        override_count = 0
        for w in sorted_words:
            for f in w.get("forms", []):
                s_source = f.get("stress_source")
                if s_source in stress_counts:
                    stress_counts[s_source] += 1
                if f.get("override") is True:
                    override_count += 1

        unresolved_count = sum(1 for w in sorted_words if w.get("entry") == "unresolved")
        resolved_count = len(sorted_words) - unresolved_count

        return {
            "status": "ok",
            "level": level,
            "dry_run": dry_run,
            "words_count": len(sorted_words),
            "resolved_count": resolved_count,
            "unresolved_count": unresolved_count,
            "forms_count": total_forms,
            "stress_sources": stress_counts,
            "overrides_count": override_count,
            "changed_ids": changed_ids,
            "affected_plans": changed_plans_map,
            "tag_map": sources_instance.mapper.summary(),
            "store_path": str(store_path),
            "registry_path": str(registry_path),
            "store_lock": store_lock_digest,
            "registry_lock": registry_lock_digest,
            "store": store_doc,
        }
    finally:
        if owns_sources:
            sources_instance.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.curriculum.evidence build-words",
        description=(
            "Build or update a per-level word store (_words.yaml) and allocation ledger.\n"
            "Use to ground curriculum vocabulary in dictionaries; never type Ukrainian strings by hand."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.curriculum.evidence build-words a1 --request path/to/req.yaml\n"
            "  .venv/bin/python -m scripts.curriculum.evidence build-words a1 --request req.yaml --dry-run\n"
            "  .venv/bin/python -m scripts.curriculum.evidence build-words a1 --request req.yaml --json\n\n"
            "Outputs:\n"
            "  curriculum/l2-uk-en/evidence/<level>/_words.yaml (+ .lock)\n"
            "  curriculum/l2-uk-en/evidence/<level>/_words.registry.yaml (+ .lock)\n\n"
            "Exit codes:\n"
            "  0: Build succeeded or dry-run complete without error\n"
            "  1: Request invalid, schema validation failed, or source unavailable\n\n"
            "Outcome Codes:\n"
            f"{codes.help_text()}\n"
        ),
    )
    parser.add_argument("level", help="Target curriculum level slug (e.g. 'a1', 'a2')")
    parser.add_argument("--request", required=True, type=Path, help="Path to input request YAML file")
    parser.add_argument("--dry-run", action="store_true", help="Compute word store without writing files")
    parser.add_argument(
        "--stamp", action="store_true", help="Include built_at timestamp in built_with (breaks build determinism)"
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON result to stdout")
    parser.add_argument("--evidence-dir", type=Path, default=None, help="Override evidence output directory")
    parser.add_argument("--plans-dir", type=Path, default=None, help="Override lesson plans directory")

    args = parser.parse_args(argv)

    try:
        result = build_words(
            args.level,
            args.request,
            evidence_dir=args.evidence_dir,
            plans_dir=args.plans_dir,
            dry_run=args.dry_run,
            stamp=args.stamp,
            report=lambda msg: print(f"progress: {msg}", file=sys.stderr),
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "failed", "error": str(exc)}, indent=2))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        # store dict might be large; output clean JSON summary with store
        output = dict(result)
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"Word Store Build: level={result['level']} (dry-run: {result['dry_run']})")
        print(
            f"Records: {result['words_count']} ({result['resolved_count']} resolved, {result['unresolved_count']} unresolved)"
        )
        sc = result["stress_sources"]
        print(
            f"Forms: {result['forms_count']} (trie: {sc['trie']}, none: {sc['none']}, ulif: {sc['ulif']}, pending: {sc['pending']})"
        )
        print(f"Overrides: {result['overrides_count']}")
        print("ULIF status: pending on all records (0 checked groups)")
        tm = result["tag_map"]
        print(f"Tag-map report: known_atoms={tm['known_atoms']}, unknown_atoms={tm['unknown_atoms']}")
        if result["changed_ids"]:
            print(f"Changed existing records: {result['changed_ids']}")
            if result["affected_plans"]:
                print(f"Affected plans citing changed records: {result['affected_plans']}")
        if not result["dry_run"]:
            print(f"Store written: {result['store_path']} (lock: {result['store_lock'][:16]}...)")
            print(f"Registry written: {result['registry_path']} (lock: {result['registry_lock'][:16]}...)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
