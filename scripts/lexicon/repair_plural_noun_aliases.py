#!/usr/bin/env python3
"""Repair already-hydrated Atlas manifests with unsafe plural-noun aliases.

The source builder now keeps explicit ``pos: noun:pl`` vocabulary as its own
Atlas entry when the singular citation form was not taught. This script applies
the same rule to an existing release manifest without rebuilding every entry.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_SOURCES_DB = ROOT / "data" / "sources.db"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lexicon import enrich_manifest


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_kaikki_lookup(path: Path) -> dict[str, dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _course_usage_key(row: dict[str, Any]) -> tuple[object, object, object]:
    return (row.get("track"), row.get("module_num"), row.get("slug"))


def _merge_course_usage(target: dict[str, Any], source: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[object, object, object, object]] = set()
    for entry in (target, source):
        for row in entry.get("course_usage") or []:
            if not isinstance(row, dict):
                continue
            merged = dict(row)
            merged["context"] = "built_vocabulary"
            key = (*_course_usage_key(merged), merged.get("context"))
            if key in seen:
                continue
            seen.add(key)
            rows.append(merged)
    if rows:
        target["course_usage"] = rows


def _unsafe_plural_alias_source(entry: dict[str, Any]) -> str | None:
    if entry.get("primary_source") != "built_vocabulary_normalized":
        return None
    if _has_english_anchor(entry):
        return None
    normalizations = entry.get("atlas_normalizations")
    if not isinstance(normalizations, list):
        return None
    for norm in normalizations:
        if not isinstance(norm, dict):
            continue
        if norm.get("kind") != "vesum_inflection_to_lemma":
            continue
        if norm.get("target_lemma") != entry.get("lemma"):
            continue
        reason = str(norm.get("reason") or "")
        if "pos='noun:pl'" not in reason and 'pos="noun:pl"' not in reason:
            continue
        source_lemma = str(norm.get("source_lemma") or "").strip()
        if source_lemma:
            return source_lemma
    return None


def _has_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_english_anchor(entry: dict[str, Any]) -> bool:
    if _has_text(entry.get("gloss")):
        return True
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, dict):
        return False
    translation = enrichment.get("translation")
    if isinstance(translation, dict):
        terms = translation.get("en")
        if isinstance(terms, list) and any(_has_text(term) for term in terms):
            return True
    meaning = enrichment.get("meaning")
    if not isinstance(meaning, dict):
        return False
    source = str(meaning.get("source") or "")
    definitions = meaning.get("definitions")
    return "Wiktionary" in source and isinstance(definitions, list) and any(_has_text(item) for item in definitions)


def _refresh_entry(
    conn: sqlite3.Connection,
    entry: dict[str, Any],
    kaikki_lookup: dict[str, dict[str, Any]],
) -> None:
    enrich_manifest.enrich_entry(
        entry,
        conn,
        kaikki_lookup,
        has_sum11_flags=enrich_manifest._sum11_has_flag_columns(conn),
    )


def repair_plural_noun_aliases(
    manifest: dict[str, Any],
    *,
    conn: sqlite3.Connection | None = None,
    kaikki_lookup: dict[str, dict[str, Any]] | None = None,
    refresh_enrichment: bool = False,
) -> dict[str, Any]:
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError("manifest entries must be a list")

    by_lemma = {entry.get("lemma"): entry for entry in entries if isinstance(entry, dict)}
    remove_ids: set[int] = set()
    promoted: list[str] = []
    candidates: list[tuple[dict[str, Any], dict[str, Any], str]] = []
    alias_slugs_by_source: dict[str, set[object]] = {}
    repairs: list[tuple[dict[str, Any], dict[str, Any], str]] = []

    for entry in list(entries):
        if not isinstance(entry, dict):
            continue
        source_lemma = _unsafe_plural_alias_source(entry)
        if not source_lemma:
            continue
        surface = by_lemma.get(source_lemma)
        if not isinstance(surface, dict):
            continue
        candidates.append((entry, surface, source_lemma))
        alias_slugs_by_source.setdefault(source_lemma, set()).add(entry.get("url_slug"))

    for entry, surface, source_lemma in candidates:
        form_of = surface.get("form_of")
        if not isinstance(form_of, dict) or form_of.get("url_slug") not in alias_slugs_by_source[source_lemma]:
            continue
        repairs.append((entry, surface, source_lemma))

    refreshed_surface_ids: set[int] = set()
    for entry, surface, source_lemma in repairs:
        first_surface_repair = id(surface) not in refreshed_surface_ids

        if first_surface_repair:
            surface.pop("form_of", None)
            surface["primary_source"] = "built_vocabulary"
        _merge_course_usage(surface, entry)
        remove_ids.add(id(entry))
        promoted.append(source_lemma)

        if first_surface_repair and refresh_enrichment and conn is not None:
            _refresh_entry(conn, surface, kaikki_lookup or {})
        refreshed_surface_ids.add(id(surface))

    if remove_ids:
        manifest["entries"] = [entry for entry in entries if id(entry) not in remove_ids]
        stats = manifest.setdefault("stats", {})
        if isinstance(stats, dict):
            stats["lemmas_total"] = len(manifest["entries"])
            stats["form_of_count"] = sum(
                1 for entry in manifest["entries"] if isinstance(entry, dict) and "form_of" in entry
            )

    return {
        "promoted_plural_entries": promoted,
        "removed_aliases": len(remove_ids),
        "entries_total": len(manifest.get("entries") or []),
    }


def _refresh_manifest_fingerprint(manifest: dict[str, Any]) -> None:
    fingerprint_payload = enrich_manifest.write_fingerprint(enrich_manifest.DEFAULT_FINGERPRINT, root=ROOT)
    manifest["manifest_fingerprint"] = {
        "schema_version": fingerprint_payload["schema_version"],
        "fingerprint": fingerprint_payload["fingerprint"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Repair explicit plural noun Atlas aliases.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--kaikki-lookup", type=Path, default=enrich_manifest.KAIKKI_LOOKUP)
    parser.add_argument(
        "--refresh-enrichment",
        action="store_true",
        help="Re-run enrich_entry on promoted plural entries. Default keeps existing enriched form data.",
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)

    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    sources_db = args.sources_db if args.sources_db.is_absolute() else ROOT / args.sources_db
    kaikki_path = args.kaikki_lookup if args.kaikki_lookup.is_absolute() else ROOT / args.kaikki_lookup

    manifest = _load_json(manifest_path)
    kaikki_lookup = _load_kaikki_lookup(kaikki_path)
    if args.refresh_enrichment:
        with sqlite3.connect(sources_db) as conn:
            summary = repair_plural_noun_aliases(
                manifest,
                conn=conn,
                kaikki_lookup=kaikki_lookup,
                refresh_enrichment=True,
            )
    else:
        summary = repair_plural_noun_aliases(manifest)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.write:
        _refresh_manifest_fingerprint(manifest)
        _write_json(manifest_path, manifest)
    else:
        print("Dry run only; pass --write to update the manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
