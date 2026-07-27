"""Convert Alona curated seed JSONL (v5 shape) → ADR-017 lexical source JSONL.

The seed rows look like::

    {"row": 1, "ua": "…", "en": "…", "sentence": "…", "sentence_status": "ok",
     "matched_form": "…", "provenance": {...}}

This emits the multi-record JSONL that ``lexical_projection.build_projection``
ingests (source / lemma_entry / sense / attestation / practice_deck /
practice_deck_item).  Rows with ``sentence_status != "ok"`` or empty sentence
still emit lemma+sense (gloss-only); they omit attestation + deck item.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

from scripts.atlas.lexical_projection import (
    canonical_json,
    deterministic_attestation_id,
)

ROOT = Path(__file__).resolve().parents[2]
UA_SLUG_RE = re.compile(r"[^а-яіїєґa-z0-9]+", re.IGNORECASE)
APOSTROPHE = str.maketrans({"’": "'", "ʼ": "'", "'": "'"})


def entry_slug(lemma: str) -> str:
    """Stable NFC slug for a Ukrainian lemma (lowercase, punctuation → hyphen)."""
    normalized = unicodedata.normalize("NFC", lemma.strip()).translate(APOSTROPHE).casefold()
    slug = UA_SLUG_RE.sub("-", normalized).strip("-")
    if not slug:
        digest = hashlib.sha1(lemma.encode("utf-8")).hexdigest()[:10]
        slug = f"entry-{digest}"
    return slug


def _source_id_from_provenance(prov: dict[str, Any]) -> str:
    table = str(prov.get("table") or "unknown")
    author = str(prov.get("author") or prov.get("credit") or "anon")
    source_file = str(prov.get("source_file") or "")
    title = " ".join(unicodedata.normalize("NFC", str(prov.get("title") or "")).split())
    raw = f"{table}:{author}:{source_file}:{title}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"{table}-{digest}"


def _source_kind(prov: dict[str, Any]) -> str:
    table = str(prov.get("table") or "")
    if table == "textbooks":
        return "textbook"
    if table == "wikipedia":
        return "wikipedia"
    return "literary"


def _rights_for_display(display: str | None) -> tuple[str, str, str]:
    """license_type, attribution_type, rights_status from seed display rule."""
    if display == "public_domain":
        return "public_domain", "required", "redistributable"
    # short_quotation and unknown → conservative citation stamp
    return "citation_with_attribution", "required", "short_quotation"


def convert_seed_row(row: dict[str, Any], *, deck_slug: str) -> list[dict[str, Any]]:
    """Expand one seed row into ordered ADR-017 records."""
    ua = str(row.get("ua") or "").strip()
    en = str(row.get("en") or "").strip()
    if not ua:
        raise ValueError("seed row requires non-empty ua")
    slug = entry_slug(ua)
    sense_slug = f"{slug}:core"
    records: list[dict[str, Any]] = [
        {
            "record_type": "lemma_entry",
            "entry_slug": slug,
            "lemma": ua,
            "display_head": ua,
            "entry_type": "lemma",
            "route_path": f"/dictionary/{slug}",
            "visibility": "public",
        },
        {
            "record_type": "sense",
            "sense_slug": sense_slug,
            "entry_slug": slug,
            "sense_key": "core",
            "definition": {"en": en} if en else {},
            "review_state": "approved",
        },
    ]

    sentence = str(row.get("sentence") or "").strip()
    status = str(row.get("sentence_status") or "")
    prov = row.get("provenance") if isinstance(row.get("provenance"), dict) else None
    if status != "ok" or not sentence or not prov:
        return records

    source_id = _source_id_from_provenance(prov)
    # Seed rows can share a corpus chunk; uniquify chunk_id with the seed row so
    # deterministic attestation keys never collide across lemmas.
    base_chunk = str(prov.get("chunk_id") or "chunk")
    chunk_id = f"{base_chunk}#seed-{row.get('row', 0)}"
    span_start = int(prov.get("span_start") or 0)
    span_end = int(prov.get("span_end") or (span_start + max(len(sentence), 1)))
    if span_end <= span_start:
        span_end = span_start + max(len(sentence), 1)
    license_type, attribution_type, rights_status = _rights_for_display(
        str(prov.get("display") or "") or None
    )
    source_kind = _source_kind(prov)
    source_record: dict[str, Any] = {
        "record_type": "source",
        "source_id": source_id,
        "source_work": str(prov.get("title") or prov.get("source_file") or source_id),
        "author": prov.get("author"),
        "author_uk": prov.get("author"),
        "file_path": prov.get("source_file"),
        "source_kind": source_kind,
        "license_type": license_type,
        "attribution_type": attribution_type,
        "rights_status": rights_status,
    }
    if source_kind == "literary":
        source_record["language_period"] = "modern"
    attestation_id = deterministic_attestation_id(source_id, chunk_id, span_start, span_end)
    attestation: dict[str, Any] = {
        "record_type": "attestation",
        "attestation_id": attestation_id,
        "sense_slug": sense_slug,
        "source_id": source_id,
        "chunk_id": chunk_id,
        "span_start": span_start,
        "span_end": span_end,
        "text": sentence,
        "extraction_mode": str(row.get("sentence_query") or "corpus"),
        "review_state": "approved",
    }
    # Textbook gate requires chunk_text; seed rows already passed exercise
    # screening at attach time, so the clean sentence is a safe stand-in when
    # the full chunk is not re-hydrated here.
    if source_kind == "textbook":
        attestation["chunk_text"] = sentence
    if row.get("matched_form"):
        attestation["matched_form"] = row["matched_form"]
    records.extend(
        [
            source_record,
            attestation,
            {
                "record_type": "practice_deck_item",
                "deck_slug": deck_slug,
                "sense_slug": sense_slug,
                "attestation_id": attestation_id,
                "card_template": "recognition",
            },
        ]
    )
    return records


def convert_seed_file(
    input_path: Path,
    *,
    deck_slug: str = "alona-curated-v5",
    deck_title: str = "Alona curated seed v5",
) -> list[dict[str, Any]]:
    """Read seed JSONL and emit de-duplicated ADR-017 records."""
    rows = [
        json.loads(line)
        for line in input_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    records: list[dict[str, Any]] = [
        {
            "record_type": "practice_deck",
            "deck_slug": deck_slug,
            "title": deck_title,
            "version": "v5",
            "scope": "curated-seed",
        }
    ]
    seen_sources: set[str] = set()
    seen_lemmas: set[str] = set()
    seen_attestations: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        expanded = convert_seed_row(row, deck_slug=deck_slug)
        skip_rest = False
        for record in expanded:
            if skip_rest:
                break
            rtype = record["record_type"]
            if rtype == "source":
                sid = str(record["source_id"])
                if sid in seen_sources:
                    continue
                seen_sources.add(sid)
            if rtype == "lemma_entry":
                slug = str(record["entry_slug"])
                if slug in seen_lemmas:
                    # Duplicate lemma (aspect pairs): skip this expansion.
                    skip_rest = True
                    break
                seen_lemmas.add(slug)
            if rtype == "attestation":
                aid = str(record["attestation_id"])
                if aid in seen_attestations:
                    continue
                seen_attestations.add(aid)
            records.append(record)
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(f"{canonical_json(record)}\n" for record in records),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Alona seed JSONL (v5 shape)")
    parser.add_argument("--output", type=Path, required=True, help="ADR-017 lexical JSONL")
    parser.add_argument("--deck-slug", default="alona-curated-v5")
    parser.add_argument("--deck-title", default="Alona curated seed v5")
    args = parser.parse_args(argv)
    records = convert_seed_file(
        args.input, deck_slug=args.deck_slug, deck_title=args.deck_title
    )
    write_jsonl(args.output, records)
    print(f"wrote {len(records)} records → {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
