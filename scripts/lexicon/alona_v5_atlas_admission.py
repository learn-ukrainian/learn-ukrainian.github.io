"""Prepare and verify the public Atlas + Practice admission for Alona v5.

The operator-curated v5 JSONL is private task input. This command emits a
public replay seed, derives only missing Atlas candidates through the existing
grow promoter, and writes the Practice overlay only after the manifest has a
real CEFR enrichment block. It never assigns CEFR itself.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lexicon.build_data_manifest import _lemma_key, _slug_for_url
from scripts.lexicon.grow_lexicon_from_content import _vesum_pos

PRACTICE_SCHEMA = "alona-v5-practice-seed-v1"
PUBLIC_SCHEMA = "alona-v5-atlas-admission-seed-v1"


def _text(value: object) -> str:
    return str(value or "").strip()


def _canonical_lemma(value: str) -> str:
    return value[:1].lower() + value[1:] if value else value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"seed rows must be JSON objects: {path}")
    return rows


def normalize_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Project private/raw input to the stable public admission schema."""
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(rows, start=1):
        lemma = _text(raw.get("lemma") or raw.get("ua"))
        gloss = _text(raw.get("gloss") or raw.get("en"))
        if not lemma:
            raise ValueError(f"seed row {index} has no lemma")
        status = _text(raw.get("sentenceStatus") or raw.get("sentence_status")) or "no_hit"
        row: dict[str, Any] = {
            "seedRow": raw.get("seedRow") or raw.get("row") or index,
            "lemma": _canonical_lemma(lemma),
            "gloss": gloss,
            "slug": _slug_for_url(_canonical_lemma(lemma)),
            "sentenceStatus": status,
        }
        sentence = _text(raw.get("example") or raw.get("sentence"))
        provenance = raw.get("provenance")
        if sentence:
            row["example"] = sentence
        if isinstance(provenance, dict):
            # The public projection never carries a path to the private source
            # document; only corpus attestation provenance survives.
            row["provenance"] = provenance
        normalized.append(row)
    return normalized


def write_public_seed(rows: list[dict[str, Any]], path: Path) -> None:
    payload = {
        "schema": PUBLIC_SCHEMA,
        "selectionNote": "All active Alona v5 curated rows; private document path omitted.",
        "entries": rows,
    }
    _write_json(path, payload)


def read_public_seed(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != PUBLIC_SCHEMA:
        raise ValueError(f"unsupported Alona public seed schema: {path}")
    entries = payload.get("entries")
    if not isinstance(entries, list) or not all(isinstance(row, dict) for row in entries):
        raise ValueError(f"public seed entries must be objects: {path}")
    return entries


def _entry_type(lemma: str) -> str:
    words = lemma.split()
    if len(words) < 2:
        return "lemma"
    # VESUM decides whether this is a verb-led expression; every other
    # multiword head remains the entry-model's documented multiword term.
    return "expression" if _vesum_pos(words[0]) == "verb" else "multiword_term"


def _manifest_entries(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("entries") if isinstance(payload, dict) else None
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise ValueError(f"manifest entries must be objects: {path}")
    return entries


def candidates_for_manifest(rows: list[dict[str, Any]], manifest_path: Path) -> dict[str, Any]:
    manifest_entries = _manifest_entries(manifest_path)
    existing = {_lemma_key(_text(entry.get("lemma"))) for entry in manifest_entries}
    existing_slugs = {_text(entry.get("url_slug")) for entry in manifest_entries}
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        lemma = _text(row.get("lemma"))
        key = _lemma_key(lemma)
        if key in existing or _text(row.get("slug")) in existing_slugs or key in seen:
            continue
        seen.add(key)
        candidates.append(
            {
                "lemma": lemma,
                "gloss": _text(row.get("gloss")),
                "pos": _vesum_pos(lemma),
                "entry_type": _entry_type(lemma),
                "primary_source": "alona_v5_curated_seed",
            }
        )
    return {"auto_merge": candidates, "needs_review": []}


def _cefr(entry: dict[str, Any]) -> tuple[str, str] | None:
    enrichment = entry.get("enrichment")
    value = enrichment.get("cefr") if isinstance(enrichment, dict) else None
    level = _text(value.get("level")) if isinstance(value, dict) else _text(value)
    if level not in {"A1", "A2", "B1", "B2", "C1", "C2"}:
        return None
    source = _text(value.get("source")) if isinstance(value, dict) else ""
    return level, source or "existing manifest CEFR"


def prepare_practice_seed(rows: list[dict[str, Any]], manifest_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    public_entries = [
        entry
        for entry in _manifest_entries(manifest_path)
        if _text(entry.get("lemma")) and _text(entry.get("url_slug")) and entry.get("pos") != "grammar term"
    ]
    routes = {
        _lemma_key(_text(entry.get("lemma"))): entry
        for entry in public_entries
    }
    routes_by_slug = {_text(entry.get("url_slug")): entry for entry in public_entries}
    atlas_failures: list[dict[str, Any]] = []
    skipped_no_cefr: list[dict[str, Any]] = []
    practice_rows: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    cefr_sources: Counter[str] = Counter()
    for row in rows:
        lemma = _text(row.get("lemma"))
        target = routes.get(_lemma_key(lemma)) or routes_by_slug.get(_text(row.get("slug")))
        if target is None:
            atlas_failures.append({"seedRow": row.get("seedRow"), "lemma": lemma, "reason": "missing_public_route"})
            continue
        status = _text(row.get("sentenceStatus"))
        status_counts[status] += 1
        if status != "ok":
            continue
        example = _text(row.get("example"))
        provenance = row.get("provenance")
        if not example or not isinstance(provenance, dict):
            atlas_failures.append({"seedRow": row.get("seedRow"), "lemma": lemma, "reason": "ok_row_missing_attestation"})
            continue
        cefr = _cefr(target)
        if cefr is None:
            skipped_no_cefr.append({"seedRow": row.get("seedRow"), "lemma": lemma})
            continue
        level, source = cefr
        cefr_sources[source] += 1
        practice_rows.append({"seedRow": row.get("seedRow"), "lemma": _text(target.get("lemma")), "slug": _text(target.get("url_slug")), "cefr": level, "example": example, "provenance": provenance, "sentenceStatus": "ok"})
    report = {
        "schema": "alona-v5-atlas-admission-report-v1",
        "counts": {
            "active_seed_rows": len(rows), "unique_seed_lemmas": len({_lemma_key(_text(row.get("lemma"))) for row in rows}),
            "public_atlas_rows": len(rows) - len(atlas_failures), "atlas_failures": len(atlas_failures),
            "sentence_status": dict(sorted(status_counts.items())), "practice_admitted_rows": len(practice_rows),
            "practice_skipped_no_cefr": len(skipped_no_cefr), "practice_cefr_sources": dict(sorted(cefr_sources.items())),
        },
        "atlas_failures": atlas_failures,
        "practice_skipped_no_cefr": skipped_no_cefr,
    }
    seed = {"schema": PRACTICE_SCHEMA, "deckSlug": "alona-v5-full", "title": "Alona v5 curated practice admission", "selectionNote": "All sentence_status=ok rows whose public Atlas route has pipeline-derived CEFR. Recognition-first; no cloze targets.", "entries": practice_rows}
    return seed, report


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Raw v5 JSONL or public v5 seed JSON")
    parser.add_argument("--public-seed-out", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--candidates-out", type=Path)
    parser.add_argument("--practice-seed-out", type=Path)
    parser.add_argument("--report-out", type=Path)
    args = parser.parse_args(argv)
    rows = read_public_seed(args.input) if args.input.suffix == ".json" else normalize_rows(_read_jsonl(args.input))
    if args.public_seed_out:
        write_public_seed(rows, args.public_seed_out)
    if args.candidates_out:
        if not args.manifest:
            parser.error("--candidates-out requires --manifest")
        _write_json(args.candidates_out, candidates_for_manifest(rows, args.manifest))
    if args.practice_seed_out or args.report_out:
        if not args.manifest:
            parser.error("practice/report output requires --manifest")
        seed, report = prepare_practice_seed(rows, args.manifest)
        if args.practice_seed_out:
            _write_json(args.practice_seed_out, seed)
        if args.report_out:
            _write_json(args.report_out, report)
        if report["atlas_failures"]:
            print(f"Atlas admission has {len(report['atlas_failures'])} hard failure(s)", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
