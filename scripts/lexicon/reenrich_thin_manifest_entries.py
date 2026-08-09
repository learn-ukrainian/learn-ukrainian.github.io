#!/usr/bin/env python3
"""Re-enrich Atlas entries that passed the old gate but lack English anchors."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"

CIRCUIT_BREAKER_EXIT_CODE = 70
CANARY_FAILURE_EXIT_CODE = 75
DEFAULT_CANARY_CONTROLS: dict[str, list[dict[str, Any]]] = {
    "proverbs": [{"lemma": "вода", "pos": "noun", "url_slug": "вода"}],
    "usage_notes": [{"lemma": "аби", "pos": "conjunction", "url_slug": "аби"}],
    "grinchenko": [{"lemma": "хліб", "pos": "noun", "url_slug": "хліб"}],
    "forms": [{"lemma": "свіжий", "pos": "adjective", "url_slug": "свіжий"}],
}
DEFAULT_CANARY_LEMMAS = ["вода", "аби", "хліб", "свіжий"]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit.audit_atlas_thin_enriched import (
    has_learner_english_anchor,
    thin_old_gate_entries,
)
from scripts.lexicon import enrich_manifest
from scripts.lexicon.manifest_io import load_manifest
from scripts.lexicon.publish_manifest import (
    DEFAULT_GZIP,
    DEFAULT_POINTER,
    build_pointer_payload,
    evaluate_manifest_pointer_write_gate,
    gzip_manifest,
    write_pointer,
)


def _is_proper_noun_entry(entry: dict[str, Any]) -> bool:
    pos = str(entry.get("pos") or "").casefold()
    return "proper noun" in pos or pos == "name" or pos == "toponym"


def _categorize_entry(entry: dict[str, Any]) -> str:
    if has_learner_english_anchor(entry) or _has_translation(entry):
        return "ENRICHED"
    if _is_proper_noun_entry(entry) or entry.get("deterministic_exclusion"):
        return "DETERMINISTIC_EXCLUSION"
    return "UNRESOLVED_RESIDUAL"


def _entry_layer_coverage(entry: dict[str, Any]) -> dict[str, bool]:
    sec = entry.get("sections") if isinstance(entry.get("sections"), dict) else {}
    enr = entry.get("enrichment") if isinstance(entry.get("enrichment"), dict) else {}
    attestation = enr.get("literary_attestation")
    cards = enr.get("definition_cards")
    att_list = attestation if isinstance(attestation, list) else []
    card_list = cards if isinstance(cards, list) else []
    has_grinchenko = any(
        isinstance(c, dict)
        and (
            c.get("id") == "grinchenko"
            or c.get("source") == "Грінченко"
            or "grinchenko" in str(c.get("source") or "").casefold()
        )
        for c in att_list + card_list
    )
    morphology = enr.get("morphology") if isinstance(enr.get("morphology"), dict) else {}
    has_forms = bool(morphology.get("forms"))
    return {
        "proverbs": bool(sec.get("proverbs")),
        "usage_notes": bool(sec.get("usage_notes")),
        "grinchenko": has_grinchenko,
        "forms": has_forms,
    }


def run_canary_check(
    conn: sqlite3.Connection,
    kaikki_lookup: dict[str, dict[str, Any]],
    *,
    canary_controls: dict[str, list[dict[str, Any]]] | None = None,
    canary_lemmas: list[str] | None = None,
    has_sum11_flags: bool = False,
) -> dict[str, Any]:
    """Pre-flight positive control canary check on known-good control entries.

    Each layer (proverbs, usage_notes, grinchenko, forms) must be proven fillable
    by at least one positive control entry evaluated with its real POS.
    """
    if canary_controls is None:
        if canary_lemmas is not None:
            canary_controls = {
                layer: [{"lemma": lemma, "pos": "noun", "url_slug": lemma} for lemma in canary_lemmas]
                for layer in ("proverbs", "usage_notes", "grinchenko", "forms")
            }
        else:
            canary_controls = DEFAULT_CANARY_CONTROLS

    results: dict[str, Any] = {}
    for layer in ("proverbs", "usage_notes", "grinchenko", "forms"):
        controls = canary_controls.get(layer, [])
        layer_passed = False
        for ctrl in controls:
            entry = dict(ctrl)
            enrich_manifest.enrich_entry(
                entry,
                conn,
                kaikki_lookup,
                has_sum11_flags=has_sum11_flags,
            )
            coverage = _entry_layer_coverage(entry)
            lemma_key = f"{ctrl['lemma']}:{layer}"
            results[lemma_key] = {**coverage, "tested_layer": layer, "passed": coverage[layer]}
            if coverage[layer]:
                layer_passed = True
                break
        if not layer_passed:
            return {
                "success": False,
                "failed_layer": layer,
                "missing_layers": [layer],
                "details": results,
            }
    return {"success": True, "details": results}


def write_target_snapshot(targets: list[dict[str, Any]], snapshot_file: Path) -> dict[str, Any]:
    slugs = [str(e.get("url_slug")) for e in targets if isinstance(e, dict) and e.get("url_slug")]
    sha256 = hashlib.sha256(json.dumps(slugs, ensure_ascii=False).encode("utf-8")).hexdigest()
    snapshot = {
        "slugs": slugs,
        "count": len(slugs),
        "sha256": sha256,
    }
    snapshot_file.parent.mkdir(parents=True, exist_ok=True)
    snapshot_file.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return snapshot



def _load_kaikki_lookup(path: Path) -> dict[str, dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_local_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_slug_filter(path: Path) -> set[str]:
    """Load a url_slug allowlist restricting re-enrichment to a scoped residual.

    Accepts either a bare JSON array of slugs, or an audit-style object with a
    ``class_b_detail`` list of ``{"slug": ...}`` records (the shape produced by
    the #6369 Class-B no-English-gloss residual dump).
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {str(slug) for slug in data}
    if isinstance(data, dict):
        detail = data.get("class_b_detail")
        if isinstance(detail, list):
            return {str(item["slug"]) for item in detail if isinstance(item, dict) and item.get("slug")}
    raise ValueError(f"{path} must contain a JSON array of slugs or a 'class_b_detail' list")


def _refresh_manifest_fingerprint(manifest: dict[str, Any]) -> None:
    fingerprint_payload = enrich_manifest.write_fingerprint(enrich_manifest.DEFAULT_FINGERPRINT, root=ROOT)
    manifest["manifest_fingerprint"] = {
        "schema_version": fingerprint_payload["schema_version"],
        "fingerprint": fingerprint_payload["fingerprint"],
    }


def _write_default_release_pointer(
    manifest_path: Path,
    *,
    bootstrap_no_baseline: bool = False,
    allow_richness_regression_reason: str | None = None,
) -> dict[str, Any] | None:
    if manifest_path.resolve() != DEFAULT_MANIFEST.resolve():
        return None
    richness_gate = evaluate_manifest_pointer_write_gate(
        manifest_path,
        bootstrap_no_baseline=bootstrap_no_baseline,
        allow_richness_regression_reason=allow_richness_regression_reason,
    )
    gzip_manifest(manifest_path, DEFAULT_GZIP)
    pointer = build_pointer_payload(
        manifest_path=manifest_path,
        gzip_path=DEFAULT_GZIP,
        richness_gate=richness_gate,
    )
    write_pointer(DEFAULT_POINTER, pointer)
    return pointer


def _preserve_existing_metadata(
    entry: dict[str, Any],
    *,
    existing_cefr: dict[str, Any] | None,
    existing_wiki_reference: dict[str, Any] | None,
) -> None:
    enrichment = entry.get("enrichment")
    if isinstance(enrichment, dict) and existing_cefr and "cefr" not in enrichment:
        enrichment["cefr"] = existing_cefr
        sources = set(enrichment.get("sources") or [])
        source = existing_cefr.get("source")
        if source:
            sources.add(str(source))
        if sources:
            enrichment["sources"] = sorted(sources)
    if existing_wiki_reference and "wiki_reference" not in entry:
        entry["wiki_reference"] = existing_wiki_reference


def _add_source(enrichment: dict[str, Any], source: object) -> None:
    if not source:
        return
    sources = set(enrichment.get("sources") or [])
    sources.add(str(source))
    enrichment["sources"] = sorted(sources)


def _translation_for_entry(
    conn: sqlite3.Connection,
    entry: dict[str, Any],
    kaikki_lookup: dict[str, dict[str, Any]],
    *,
    cached_slovnyk_only: bool = False,
) -> dict[str, object] | None:
    lemma = str(entry.get("lemma") or "")
    entry_pos = entry.get("pos")
    gloss_hints = enrich_manifest._surface_gloss_hints(entry)
    slovnyk_cache = enrich_manifest._slovnyk_cache(lemma)
    if cached_slovnyk_only and not enrich_manifest._cache_has_lookup(
        slovnyk_cache,
        enrich_manifest._SLOVNYK_UKRENG_SLUG,
    ):
        slovnyk_cache = None
    translation = enrich_manifest._translation(
        conn,
        lemma,
        kaikki_lookup,
        entry_pos=entry_pos,
        gloss_hints=gloss_hints,
        slovnyk_cache=slovnyk_cache,
    )
    if translation:
        return translation
    fallback_base = enrich_manifest._base_lookup_for_entry(lemma, entry_pos)
    if not fallback_base:
        return None
    fallback_cache = enrich_manifest._slovnyk_cache(fallback_base)
    if cached_slovnyk_only and not enrich_manifest._cache_has_lookup(
        fallback_cache,
        enrich_manifest._SLOVNYK_UKRENG_SLUG,
    ):
        fallback_cache = None
    translation = enrich_manifest._translation(
        conn,
        fallback_base,
        kaikki_lookup,
        entry_pos=entry_pos,
        gloss_hints=gloss_hints,
        slovnyk_cache=fallback_cache,
    )
    if not translation:
        return None
    return enrich_manifest._with_base_source_label(translation, fallback_base)


def _reenrich_translation_only(
    conn: sqlite3.Connection,
    entry: dict[str, Any],
    kaikki_lookup: dict[str, dict[str, Any]],
    *,
    cached_slovnyk_only: bool = False,
) -> None:
    translation = _translation_for_entry(
        conn,
        entry,
        kaikki_lookup,
        cached_slovnyk_only=cached_slovnyk_only,
    )
    if not translation:
        return
    enrichment = entry.setdefault("enrichment", {})
    if not isinstance(enrichment, dict):
        enrichment = {}
        entry["enrichment"] = enrichment
    enrichment["translation"] = translation
    _add_source(enrichment, translation.get("source"))


def _reenrich_full_entry(
    conn: sqlite3.Connection,
    entry: dict[str, Any],
    kaikki_lookup: dict[str, dict[str, Any]],
    *,
    has_sum11_flags: bool,
) -> None:
    enrich_manifest.enrich_entry(
        entry,
        conn,
        kaikki_lookup,
        has_sum11_flags=has_sum11_flags,
    )


def _has_translation(entry: dict[str, Any]) -> bool:
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, dict):
        return False
    translation = enrichment.get("translation")
    if not isinstance(translation, dict):
        return False
    terms = translation.get("en")
    return isinstance(terms, list) and any(str(term).strip() for term in terms)


def missing_translation_entries(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict) and not _has_translation(entry)]


def reenrich_thin_entries(
    manifest: dict[str, Any],
    *,
    conn: sqlite3.Connection,
    kaikki_lookup: dict[str, dict[str, Any]],
    limit: int | None = None,
    full_entry: bool = False,
    refresh_wiki: bool = False,
    target: str = "missing-anchor",
    cached_slovnyk_only: bool = False,
    slug_filter: set[str] | None = None,
    circuit_breaker_limit: int | None = 50,
    work_dir: Path | None = None,
    checkpoint_interval: int = 100,
) -> dict[str, Any]:
    if target == "missing-translation":
        targets = missing_translation_entries(manifest)
    elif target == "missing-anchor":
        targets = thin_old_gate_entries(manifest)
    elif target == "full-catalog":
        targets = [entry for entry in manifest.get("entries", []) if isinstance(entry, dict)]
        full_entry = True
    else:
        raise ValueError(f"unsupported re-enrichment target: {target}")
    if slug_filter is not None:
        targets = [entry for entry in targets if entry.get("url_slug") in slug_filter]
    if limit is not None:
        targets = targets[:limit]

    snapshot_info = None
    if work_dir is not None:
        snapshot_file = work_dir / "target_snapshot.json"
        snapshot_info = write_target_snapshot(targets, snapshot_file)
    else:
        slugs = [str(e.get("url_slug")) for e in targets if isinstance(e, dict) and e.get("url_slug")]
        sha256 = hashlib.sha256(json.dumps(slugs, ensure_ascii=False).encode("utf-8")).hexdigest()
        snapshot_info = {"count": len(slugs), "sha256": sha256}

    has_sum11_flags = enrich_manifest._sum11_has_flag_columns(conn)
    original_wiki_reference = enrich_manifest._wiki_reference
    if not refresh_wiki:
        enrich_manifest._wiki_reference = lambda *args, **kwargs: None

    changed = 0
    gained_anchor = 0
    filled_translation = 0
    consecutive_misses = 0
    circuit_breaker_tripped = False

    try:
        for idx, entry in enumerate(targets):
            enrichment = entry.get("enrichment") if isinstance(entry.get("enrichment"), dict) else {}
            existing_cefr = enrichment.get("cefr") if isinstance(enrichment, dict) else None
            existing_wiki_reference = entry.get("wiki_reference")
            had_anchor = has_learner_english_anchor(entry)
            had_translation = _has_translation(entry)
            before = json.dumps(entry, ensure_ascii=False, sort_keys=True)
            if full_entry:
                _reenrich_full_entry(
                    conn,
                    entry,
                    kaikki_lookup,
                    has_sum11_flags=has_sum11_flags,
                )
            else:
                _reenrich_translation_only(
                    conn,
                    entry,
                    kaikki_lookup,
                    cached_slovnyk_only=cached_slovnyk_only,
                )
            _preserve_existing_metadata(
                entry,
                existing_cefr=existing_cefr if isinstance(existing_cefr, dict) else None,
                existing_wiki_reference=(
                    existing_wiki_reference if isinstance(existing_wiki_reference, dict) else None
                ),
            )
            was_enriched = had_anchor or had_translation or (_categorize_entry(entry) == "ENRICHED")
            after = json.dumps(entry, ensure_ascii=False, sort_keys=True)
            if after != before:
                changed += 1

            is_now_enriched = has_learner_english_anchor(entry) or _has_translation(entry) or (_categorize_entry(entry) == "ENRICHED")
            if was_enriched or is_now_enriched or after != before:
                consecutive_misses = 0
            else:
                consecutive_misses += 1

            if not had_anchor and has_learner_english_anchor(entry):
                gained_anchor += 1
            if not had_translation and _has_translation(entry):
                filled_translation += 1

            if (
                circuit_breaker_limit is not None
                and circuit_breaker_limit > 0
                and consecutive_misses >= circuit_breaker_limit
            ):
                circuit_breaker_tripped = True
                break

            if work_dir is not None and checkpoint_interval > 0 and (idx + 1) % checkpoint_interval == 0:
                _write_manifest(work_dir / "manifest.json", manifest)

    finally:
        enrich_manifest._wiki_reference = original_wiki_reference

    categories = {"ENRICHED": 0, "DETERMINISTIC_EXCLUSION": 0, "UNRESOLVED_RESIDUAL": 0}
    layer_counters = {"proverbs": 0, "usage_notes": 0, "grinchenko": 0, "forms": 0}

    for entry in targets:
        cat = _categorize_entry(entry)
        categories[cat] += 1
        coverage = _entry_layer_coverage(entry)
        for layer, covered in coverage.items():
            if covered:
                layer_counters[layer] += 1

    remaining = thin_old_gate_entries(manifest)
    return {
        "target": target,
        "targets": len(targets),
        "target_snapshot": snapshot_info,
        "changed": changed,
        "filled_translation": filled_translation,
        "gained_english_anchor": gained_anchor,
        "remaining_old_gate_no_english_anchor": len(remaining),
        "categorical_binning": categories,
        "layer_counters": layer_counters,
        "circuit_breaker_tripped": circuit_breaker_tripped,
        "consecutive_misses": consecutive_misses,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Re-enrich old-gate-enriched Atlas entries missing learner English anchors."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--local",
        action="store_true",
        help="Read manifest path directly instead of hydrating the canonical release asset.",
    )
    parser.add_argument("--sources-db", type=Path, default=enrich_manifest.SOURCES_DB)
    parser.add_argument("--kaikki-lookup", type=Path, default=enrich_manifest.KAIKKI_LOOKUP)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--full-entry",
        action="store_true",
        help="Run full enrich_entry for each target. Default only recomputes translation anchors.",
    )
    parser.add_argument(
        "--target",
        choices=("missing-anchor", "missing-translation", "full-catalog"),
        default="missing-anchor",
        help=(
            "Select entries to re-enrich. Default keeps the old gate repair behavior; "
            "missing-translation fills sourced translation cards; full-catalog re-enriches all catalog entries."
        ),
    )
    parser.add_argument(
        "--cached-slovnyk-only",
        action="store_true",
        help="Use existing Slovnyk.me Ukrainian-English cache rows only; do not live-fetch missing Slovnyk entries.",
    )
    parser.add_argument(
        "--slugs-file",
        type=Path,
        default=None,
        help=(
            "Restrict re-enrichment to entries whose url_slug appears in this JSON file "
            "(bare JSON array of slugs, or an audit dump with a 'class_b_detail' list)."
        ),
    )
    parser.add_argument(
        "--canary",
        action="store_true",
        help="Run positive-control pre-flight canary check on known-good control lemmas.",
    )
    parser.add_argument(
        "--canary-lemmas",
        type=str,
        default=None,
        help="Comma-separated list of control lemmas for canary check.",
    )
    parser.add_argument(
        "--circuit-breaker-limit",
        type=int,
        default=50,
        help="Abort if N consecutive target entries experience total source/cache misses. Default 50.",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="Directory to save run snapshots, manifest checkpoints, and logs.",
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=100,
        help="Checkpoint manifest write interval (number of entries). Default 100.",
    )
    parser.add_argument("--refresh-wiki", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--allow-richness-regression",
        metavar="REASON",
        help="Record an operator decision to permit a richness regression while writing the pointer.",
    )
    parser.add_argument(
        "--bootstrap-no-baseline",
        action="store_true",
        help="Write only an initial pointer when no canonical release asset exists; records bootstrap=true.",
    )
    args = parser.parse_args()

    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    sources_db = args.sources_db if args.sources_db.is_absolute() else ROOT / args.sources_db
    kaikki_path = args.kaikki_lookup if args.kaikki_lookup.is_absolute() else ROOT / args.kaikki_lookup
    work_dir = (args.work_dir if args.work_dir.is_absolute() else ROOT / args.work_dir) if args.work_dir else None

    manifest = _read_local_manifest(manifest_path) if args.local else load_manifest(manifest_path)
    kaikki_lookup = _load_kaikki_lookup(kaikki_path)
    slug_filter = _load_slug_filter(args.slugs_file) if args.slugs_file else None

    with sqlite3.connect(sources_db) as conn:
        has_flags = enrich_manifest._sum11_has_flag_columns(conn)

        if args.canary or args.target == "full-catalog":
            lemmas = [s.strip() for s in args.canary_lemmas.split(",")] if args.canary_lemmas else None
            canary_res = run_canary_check(conn, kaikki_lookup, canary_lemmas=lemmas, has_sum11_flags=has_flags)
            if not canary_res["success"]:
                print(
                    json.dumps(
                        {
                            "error": "canary_failed",
                            "canary_result": canary_res,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    file=sys.stderr,
                )
                return CANARY_FAILURE_EXIT_CODE
            if args.canary:
                print(json.dumps({"canary_passed": True, "details": canary_res["details"]}, ensure_ascii=False, indent=2))
                return 0

        summary = reenrich_thin_entries(
            manifest,
            conn=conn,
            kaikki_lookup=kaikki_lookup,
            limit=args.limit,
            full_entry=args.full_entry,
            refresh_wiki=args.refresh_wiki,
            target=args.target,
            cached_slovnyk_only=args.cached_slovnyk_only,
            slug_filter=slug_filter,
            circuit_breaker_limit=args.circuit_breaker_limit,
            work_dir=work_dir,
            checkpoint_interval=args.checkpoint_interval,
        )

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if summary.get("circuit_breaker_tripped"):
        print(
            json.dumps(
                {
                    "error": "circuit_breaker_tripped",
                    "consecutive_misses": summary.get("consecutive_misses"),
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return CIRCUIT_BREAKER_EXIT_CODE

    if args.write:
        _refresh_manifest_fingerprint(manifest)
        _write_manifest(manifest_path, manifest)
        pointer = _write_default_release_pointer(
            manifest_path,
            bootstrap_no_baseline=args.bootstrap_no_baseline,
            allow_richness_regression_reason=args.allow_richness_regression,
        )
        if pointer:
            print(
                "Updated local atlas-manifest pointer "
                f"{pointer['manifest_fingerprint']} {pointer['json_sha256']}"
            )
    else:
        print("Dry run only; pass --write to update the manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

