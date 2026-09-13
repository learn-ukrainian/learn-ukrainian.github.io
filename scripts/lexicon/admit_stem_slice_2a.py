#!/usr/bin/env python3
"""Admit Slice 2A of STEM textbook headwords into the Atlas manifest and DB.

Takes the 118 verified STEM textbook candidates that have authentic ВТС/СУМ-20
definitions and learner English glosses, updates their respective textbook
glossary YAML files (moving them from residual to headwords), and admits them
into the Atlas manifest and data/atlas.db.

Usage::

    .venv/bin/python -m scripts.lexicon.admit_stem_slice_2a [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import urllib.parse
from pathlib import Path
from typing import Any

import yaml

os.environ["LEXICON_SLOVNYK_OFFLINE"] = "1"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.atlas.atlas_db import migrate_manifest, validate_alias_targets
from scripts.audit import generate_search_index
from scripts.lexicon import enrich_manifest
from scripts.lexicon.build_data_manifest import _lemma_key, _slug_for_url
from scripts.lexicon.enrich_manifest import (
    _definition_body,
    _load_slovnyk_cache_file,
    _slovnyk_cache_path,
)
from scripts.lexicon.lemma_normalization import strip_acute_stress
from scripts.lexicon.manifest_fingerprint import write_fingerprint

DEFAULT_CANDIDATES_PATH = PROJECT_ROOT / "data/lexicon/stem_slice_2a_candidates.json"
MANIFEST_PATH = PROJECT_ROOT / "site/src/data/lexicon-manifest.json"
FINGERPRINT_PATH = PROJECT_ROOT / "site/src/data/lexicon-manifest.fingerprint.json"
ATLAS_DB_PATH = PROJECT_ROOT / "data/atlas.db"
SOURCES_DB_PATH = PROJECT_ROOT / "data/sources.db"

_POS_MAP = {
    "adj": "adjective",
    "adjective": "adjective",
    "adv": "adverb",
    "adverb": "adverb",
    "verb": "verb",
    "noun": "noun",
    "prep": "preposition",
    "preposition": "preposition",
    "conj": "conjunction",
    "numr": "numeral",
    "numeral": "numeral",
    "pron": "pronoun",
    "pronoun": "pronoun",
    "part": "particle",
    "intj": "interjection",
}

EXCLUDED_LEMMAS = {"кг", "км", "коп", "мм", "см", "найдовший", "починаючи"}


def load_vetted_stem_candidates(
    candidates_path: Path, manifest_keys: set[str]
) -> list[dict[str, Any]]:
    raw = json.loads(candidates_path.read_text(encoding="utf-8"))
    vetted: list[dict[str, Any]] = []

    for item in raw:
        lemma = strip_acute_stress(str(item.get("lemma") or "").strip())
        if not lemma or lemma in EXCLUDED_LEMMAS:
            continue
        key = _lemma_key(lemma)
        if key in manifest_keys:
            continue

        cache_file = _slovnyk_cache_path(lemma)
        if not cache_file.is_file():
            continue
        cache_data = _load_slovnyk_cache_file(cache_file)
        lookups = cache_data.get("lookups") or {}
        vts = lookups.get("vts")
        if not isinstance(vts, dict) or not vts.get("text"):
            continue

        def_text = _definition_body(
            vts["text"],
            headword=str(vts.get("word") or lemma),
            strip_leading_headword=True,
            limit=320,
        )
        if not def_text:
            continue

        en_gloss = str(item.get("en_gloss") or "").strip()
        if not en_gloss:
            ukreng = lookups.get("ukreng")
            if isinstance(ukreng, dict) and ukreng.get("text"):
                en_gloss = _definition_body(
                    ukreng["text"],
                    headword=str(ukreng.get("word") or lemma),
                    strip_leading_headword=True,
                    limit=200,
                )
        if not en_gloss:
            continue

        pos_raw = str(item.get("pos") or "noun").strip().lower()
        pos = _POS_MAP.get(pos_raw, "noun")

        source_url = str(
            vts.get("source_url")
            or f"https://slovnyk.me/dict/vts/{urllib.parse.quote(lemma)}"
        )

        vetted.append(
            {
                "lemma": lemma,
                "pos": pos,
                "pos_short": pos_raw,
                "en_gloss": en_gloss,
                "uk_def": def_text,
                "source_url": source_url,
                "source_book": str(item.get("source_book") or "").strip(),
                "locator": str(item.get("locator") or "glossary").strip() or "glossary",
            }
        )

    return vetted


def build_atlas_entry(cand: dict[str, Any]) -> dict[str, Any]:
    lemma = cand["lemma"]
    pos = cand["pos"]
    gloss = cand["en_gloss"]
    def_text = cand["uk_def"]
    source_url = cand["source_url"]
    source_book = cand["source_book"] or "textbook-stem"

    en_terms = [g.strip() for g in re.split(r"[;,]", gloss) if g.strip()]
    if not en_terms:
        en_terms = [gloss]

    return {
        "lemma": lemma,
        "url_slug": _slug_for_url(lemma),
        "gloss": gloss,
        "pos": pos,
        "entry_type": "lemma",
        "review_state": "approved",
        "primary_source": "textbook",
        "source_provenance": [
            {
                "source_family": "textbook",
                "source_locator": source_book,
                "extraction_mode": "headword_inventory",
                "visibility": "public",
                "redistributable": True,
            }
        ],
        "surface_admission": {"practice": True},
        "heritage_status": {
            "classification": "standard",
            "attestations": [],
            "is_russianism": False,
            "russian_shadow": False,
            "sovietization_risk": 0,
            "calque_warning": None,
            "vesum_attested": True,
            "warning_severity": "none",
        },
        "definition_cards": [
            {
                "id": "vts",
                "source_dict": "vts",
                "source_label": "ВТС (Великий тлумачний словник сучасної української мови)",
                "definition": def_text,
                "definitions": [def_text],
                "source_url": source_url,
                "sovietization_risk": 0,
            }
        ],
        "enrichment": {
            "meaning": {
                "uk": def_text,
                "source": "vts",
                "source_url": source_url,
            },
            "translation": {
                "en": en_terms,
                "source": "textbook glossary",
            },
            "sources": ["vts", "textbook glossary"],
        },
    }


def update_source_inventory_glossaries(
    vetted: list[dict[str, Any]], dry_run: bool = False
) -> int:
    by_book: dict[str, list[dict[str, Any]]] = {}
    for cand in vetted:
        book = cand["source_book"]
        if book:
            by_book.setdefault(book, []).append(cand)

    updated_books = 0
    for book_id, cands in by_book.items():
        found_paths = list(
            (PROJECT_ROOT / "data/lexicon/source-inventory").glob(
                f"grade-*/*{book_id}*.yaml"
            )
        )
        if not found_paths:
            found_paths = list(
                (PROJECT_ROOT / "data/lexicon/source-inventory").glob(
                    f"*{book_id}*.yaml"
                )
            )
        if not found_paths:
            continue

        path = found_paths[0]
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not data.get("sources"):
            continue

        source = data["sources"][0]
        # Ensure accidental residual on source is cleared if previously present
        source.pop("residual", None)
        headwords = source.setdefault("headwords", [])

        residual = data.get("residual")
        if not isinstance(residual, list):
            residual = []
            data["residual"] = residual

        hw_lemmas = {_lemma_key(str(h.get("lemma") or "")) for h in headwords}
        modified = False

        for c in cands:
            clemma = c["lemma"]
            ckey = _lemma_key(clemma)
            if ckey in hw_lemmas:
                continue

            orig_count = None
            found_in_residual = False
            new_residual = []
            for r in residual:
                if isinstance(r, dict) and _lemma_key(str(r.get("lemma") or "")) == ckey:
                    orig_count = r.get("count")
                    found_in_residual = True
                else:
                    new_residual.append(r)
            residual[:] = new_residual

            final_count = orig_count if isinstance(orig_count, int) and orig_count > 0 else 10

            headwords.append(
                {
                    "lemma": clemma,
                    "pos": c["pos_short"],
                    "count": final_count,
                    "locator": c["locator"],
                    "gloss": c["en_gloss"],
                    "gloss_source": "ukreng",
                    "context": c["uk_def"],
                    "context_source": "vts",
                    "context_url": c["source_url"],
                }
            )
            hw_lemmas.add(ckey)
            modified = True

            if found_in_residual and isinstance(data.get("stats"), dict):
                st = data["stats"]
                if "admitted" in st:
                    st["admitted"] += 1
                if "residual_this_batch" in st and st["residual_this_batch"] > 0:
                    st["residual_this_batch"] -= 1
                if st.get("attempted", 0) > 0 and "admitted" in st:
                    st["richness"] = round(st["admitted"] / st["attempted"], 2)

        if modified:
            updated_books += 1
            if not dry_run:
                path.write_text(
                    yaml.safe_dump(
                        data,
                        allow_unicode=True,
                        sort_keys=False,
                        default_flow_style=False,
                        width=1000,
                    ),
                    encoding="utf-8",
                )

    return updated_books


def admit_slice_2a(
    *,
    candidates_path: Path = DEFAULT_CANDIDATES_PATH,
    dry_run: bool = False,
) -> dict[str, Any]:
    print(f"Loading manifest from {MANIFEST_PATH}...")
    manifest_data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = manifest_data.get("entries", [])
    manifest_keys = {_lemma_key(str(e.get("lemma") or "")) for e in entries if isinstance(e, dict)}
    print(f"Current manifest entries: {len(entries)}")

    print(f"Loading vetted candidates from {candidates_path}...")
    vetted = load_vetted_stem_candidates(candidates_path, manifest_keys)
    print(f"Vetted STEM candidates ready for admission: {len(vetted)}")
    if not vetted:
        return {"admitted": 0, "status": "no candidates"}

    new_entries = [build_atlas_entry(c) for c in vetted]

    print(f"Updating textbook glossaries for {len(vetted)} words...")
    updated_books = update_source_inventory_glossaries(vetted, dry_run=dry_run)
    print(f"Updated {updated_books} textbook glossary YAML files.")

    all_entries = entries + new_entries
    all_entries.sort(key=lambda e: _lemma_key(str(e.get("lemma") or "")))
    manifest_data["entries"] = all_entries
    manifest_data["entries_count"] = len(all_entries)

    print(f"Enriching {len(new_entries)} newly promoted entries...")
    kaikki_lookup = enrich_manifest._load_kaikki_lookup()
    enriched_count = 0
    with sqlite3.connect(f"file:{SOURCES_DB_PATH}?mode=ro", uri=True) as conn:
        has_flags = enrich_manifest._sum11_has_flag_columns(conn)
        for idx, entry in enumerate(new_entries, 1):
            if enrich_manifest.enrich_entry(entry, conn, kaikki_lookup, has_sum11_flags=has_flags):
                enriched_count += 1
            if idx % 10 == 0 or idx == len(new_entries):
                print(f"  [{idx}/{len(new_entries)}] enriched ({entry['lemma']})", flush=True)
    print(f"Targeted enrichment completed: {enriched_count} entries enriched.")

    if not dry_run:
        print(f"Writing updated manifest to {MANIFEST_PATH}...")
        MANIFEST_PATH.write_text(
            json.dumps(manifest_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Updating fingerprint sidecar {FINGERPRINT_PATH}...")
        write_fingerprint(FINGERPRINT_PATH, root=PROJECT_ROOT)

        print(f"Rebuilding SQLite atlas.db at {ATLAS_DB_PATH}...")
        db_counts = migrate_manifest(MANIFEST_PATH, ATLAS_DB_PATH)
        print(f"atlas.db migration counts: {db_counts}")
        validate_alias_targets(ATLAS_DB_PATH)

        print(f"Rebuilding search index from {ATLAS_DB_PATH}...")
        generate_search_index.main(["--db", str(ATLAS_DB_PATH)])
        print("Search index rebuild complete.")

    return {
        "admitted": len(new_entries),
        "enriched": enriched_count,
        "updated_books": updated_books,
        "total_entries": len(all_entries),
        "dry_run": dry_run,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidates-file",
        type=Path,
        default=DEFAULT_CANDIDATES_PATH,
        help="Path to vetted STEM candidates JSON",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes to disk")
    args = parser.parse_args()

    summary = admit_slice_2a(candidates_path=args.candidates_file, dry_run=args.dry_run)
    print("Summary:", json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
