#!/usr/bin/env python3
"""Re-enrich Atlas entries that passed the old gate but lack English anchors."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"

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
) -> dict[str, Any]:
    if target == "missing-translation":
        targets = missing_translation_entries(manifest)
    elif target == "missing-anchor":
        targets = thin_old_gate_entries(manifest)
    else:
        raise ValueError(f"unsupported re-enrichment target: {target}")
    if limit is not None:
        targets = targets[:limit]

    has_sum11_flags = enrich_manifest._sum11_has_flag_columns(conn)
    original_wiki_reference = enrich_manifest._wiki_reference
    if not refresh_wiki:
        enrich_manifest._wiki_reference = lambda *args, **kwargs: None

    changed = 0
    gained_anchor = 0
    filled_translation = 0
    try:
        for entry in targets:
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
            after = json.dumps(entry, ensure_ascii=False, sort_keys=True)
            if after != before:
                changed += 1
            if not had_anchor and has_learner_english_anchor(entry):
                gained_anchor += 1
            if not had_translation and _has_translation(entry):
                filled_translation += 1
    finally:
        enrich_manifest._wiki_reference = original_wiki_reference

    remaining = thin_old_gate_entries(manifest)
    return {
        "target": target,
        "targets": len(targets),
        "changed": changed,
        "filled_translation": filled_translation,
        "gained_english_anchor": gained_anchor,
        "remaining_old_gate_no_english_anchor": len(remaining),
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
        choices=("missing-anchor", "missing-translation"),
        default="missing-anchor",
        help=(
            "Select entries to re-enrich. Default keeps the old gate repair behavior; "
            "missing-translation fills sourced translation cards where deterministic sources exist."
        ),
    )
    parser.add_argument(
        "--cached-slovnyk-only",
        action="store_true",
        help="Use existing Slovnyk.me Ukrainian-English cache rows only; do not live-fetch missing Slovnyk entries.",
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

    manifest = _read_local_manifest(manifest_path) if args.local else load_manifest(manifest_path)
    kaikki_lookup = _load_kaikki_lookup(kaikki_path)
    with sqlite3.connect(sources_db) as conn:
        summary = reenrich_thin_entries(
            manifest,
            conn=conn,
            kaikki_lookup=kaikki_lookup,
            limit=args.limit,
            full_entry=args.full_entry,
            refresh_wiki=args.refresh_wiki,
            target=args.target,
            cached_slovnyk_only=args.cached_slovnyk_only,
        )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
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
