#!/usr/bin/env python3
"""Split Ohoiko/ULP paired comma headwords and classify/promote VESUM-ok legs (#6370).

Binding split policy (do not invent lemmas):
  1. Split on ASCII comma ``,`` only.
  2. Strip whitespace.
  3. Strip trailing parenthetical tags (`` (1)``, `` (verb)``, …) via
     ``\\s*\\([^)]*\\)\\s*$`` repeatedly.
  4. Drop empty legs.
  5. Each leg must be a single orthographic word (no spaces). Multiword legs
     → ``multiword_after_split`` residual, not promote.
  6. Classify each leg with the same VESUM + heritage path as #6528.
  7. Promote only legs that are missing from Atlas and ``single_word_vesum_ok``.
  8. Never hand-inject EN glosses; never invent lemmas not in the split legs.
  9. OPSEC: public labels stay Ohoiko/ULP (teacher only if a teacher surface appears).
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit.source_inventory_review_decisions import source_inventory_key
from scripts.lexicon import curated_ohoiko_ulp_repromote as promo
from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.heritage_classifier import classify_lemma
from scripts.lexicon.lemma_normalization import strip_acute_stress
from scripts.verification.vesum import verify_word

DEFAULT_INVENTORY = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory/oneshot/ohoiko-ulp-curated-2026-07-19-bulk.yaml"
)
DEFAULT_MANIFEST = PROJECT_ROOT / "site/src/data/lexicon-manifest.json"
DEFAULT_BATCH_ID = "ohoiko-ulp-paired-split-legs-2026-08-12"
TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
LATIN_A = "a"
HERITAGE_HOLD = frozenset({"russianism", "calque", "surzhyk", "sovietism"})
LOOKALIKE_LATIN_TO_CYRILLIC = str.maketrans(
    {
        "a": "а",
        "i": "і",
        "I": "І",
        "e": "е",
        "o": "о",
        "p": "р",
        "c": "с",
        "y": "у",
        "x": "х",
        "A": "А",
        "E": "Е",
        "O": "О",
        "P": "Р",
        "C": "С",
        "X": "Х",
    }
)


def recover_latin_lookalike(text: str) -> str:
    """Map lookalike Latin characters to Cyrillic (binding policy #6370)."""
    return text.translate(LOOKALIKE_LATIN_TO_CYRILLIC)


def resolve_leg_lemma(lemma: str) -> str:
    """Return clean Cyrillic lemma after acute stress strip and 1:1 lookalike substitution if VESUM hits."""
    raw = strip_acute_stress(lemma).strip()
    if not raw:
        return raw
    recovered = recover_latin_lookalike(raw)
    if recovered != raw and has_cyrillic(recovered):
        hits = verify_word(recovered) or []
        if hits:
            return recovered
    return raw


def strip_trailing_parentheticals(text: str) -> str:
    """Strip trailing ``(...)`` tags repeatedly (policy step 3)."""
    cleaned = text
    while True:
        updated = TRAILING_PAREN_RE.sub("", cleaned).strip()
        if updated == cleaned:
            return updated
        cleaned = updated


def split_paired_headword(raw: str) -> list[str]:
    """Split a paired inventory string into orthographic legs (policy steps 1–4)."""
    legs: list[str] = []
    for part in str(raw).split(","):
        leg = strip_trailing_parentheticals(part.strip())
        if leg:
            legs.append(leg)
    return legs


def is_single_orthographic_word(leg: str) -> bool:
    """True when the leg has no whitespace (policy step 5)."""
    return bool(leg) and (" " not in leg) and ("\t" not in leg)


def has_cyrillic(text: str) -> bool:
    return any("\u0400" <= ch <= "\u04ff" for ch in text)


def classify_single_word_leg(lemma: str) -> str:
    """Classify one single-word leg with the #6528 VESUM + heritage path."""
    raw = strip_acute_stress(lemma).strip()
    if not raw:
        return "single_word_vesum_absent"
    if " " in raw or "(" in raw or ")" in raw:
        return "multiword_phrases_other"

    effective = raw
    hits = verify_word(effective) or []
    if not hits:
        recovered = recover_latin_lookalike(raw)
        if recovered != raw and has_cyrillic(recovered):
            hits = verify_word(recovered) or []
            if hits:
                effective = recovered

    if not hits:
        return "single_word_vesum_absent"

    hs = classify_lemma(effective)
    cl = str(hs.get("classification") or "")
    if hs.get("is_russianism") or hs.get("russian_shadow") or cl in HERITAGE_HOLD:
        return "single_word_heritage_flag"
    return "single_word_vesum_ok"


def classify_inventory_lemma(lemma: str) -> str:
    """Structural residual category for a full inventory lemma string (#6528)."""
    raw = strip_acute_stress(lemma).strip()
    if "," in raw:
        return "paired_headwords_comma"
    if "/" in raw:
        return "paired_headwords_slash"
    if " " in raw or "(" in raw or ")" in raw:
        return "multiword_phrases_other"
    return classify_single_word_leg(raw)


def classify_split_leg(leg: str) -> str:
    """Classify one split leg; multiword legs stay in ``multiword_after_split``."""
    if not is_single_orthographic_word(leg):
        return "multiword_after_split"
    return classify_single_word_leg(leg)


def load_inventory_records(inventory_path: Path) -> list[dict[str, Any]]:
    doc = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    for src in doc.get("sources") or []:
        for hw in src.get("headwords") or []:
            lemma = str(hw.get("lemma") or "").strip()
            if not lemma:
                continue
            records.append(
                {
                    "lemma": lemma,
                    "pos": hw.get("pos"),
                    "gloss": hw.get("gloss"),
                    "locator": hw.get("locator"),
                    "source_id": src.get("id"),
                    "source_family": src.get("source_family"),
                }
            )
    return records


def atlas_lemma_keys(manifest_path: Path) -> tuple[int, set[str]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest["entries"]
    keys = {_lemma_key(str(e.get("lemma") or "")) for e in entries if isinstance(e, dict)}
    return len(entries), keys


def unique_by_lemma_key(records: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for row in records:
        lemma = str(row["lemma"])
        eff_lemma = resolve_leg_lemma(lemma)
        by_key.setdefault(_lemma_key(eff_lemma), {**dict(row), "lemma": eff_lemma})
    return by_key


def derive_inventory_residual(
    *,
    inventory_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    """Re-derive inventory residual vs live Atlas (same categories as #6528)."""
    records = load_inventory_records(inventory_path)
    by_key = unique_by_lemma_key(records)
    entry_count, atlas_keys = atlas_lemma_keys(manifest_path)
    missing = {k: r for k, r in by_key.items() if k not in atlas_keys}

    cats: dict[str, list[str]] = {}
    heritage_details: dict[str, dict[str, Any]] = {}
    for _k, row in sorted(missing.items()):
        lemma = str(row["lemma"])
        cat = classify_inventory_lemma(lemma)
        cats.setdefault(cat, []).append(lemma)
        if cat == "single_word_heritage_flag":
            hs = classify_lemma(strip_acute_stress(lemma).strip())
            heritage_details[lemma] = {
                "classification": hs.get("classification"),
                "is_russianism": hs.get("is_russianism"),
                "russian_shadow": hs.get("russian_shadow"),
                "warning_severity": hs.get("warning_severity"),
            }

    counts = {c: len(v) for c, v in sorted(cats.items())}
    return {
        "schema": "atlas-6370-ohoiko-residual.v1",
        "inventory_path": str(inventory_path),
        "manifest_path": str(manifest_path),
        "manifest_entries": entry_count,
        "inventory_records": len(records),
        "unique_inventory_lemma_keys": len(by_key),
        "inventory_present_in_atlas": len(by_key) - len(missing),
        "residual_missing": len(missing),
        "counts": counts,
        "lemmas_by_category": {c: sorted(v) for c, v in cats.items()},
        "samples": {c: sorted(v)[:20] for c, v in cats.items()},
        "heritage_details": heritage_details,
    }


def analyze_paired_splits(
    *,
    paired_lemmas: Sequence[str],
    atlas_keys: set[str],
    inventory_rows_by_lemma: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Split paired residual strings and classify each leg."""
    leg_cats: dict[str, list[str]] = {}
    promote_legs: list[dict[str, Any]] = []
    already_present: list[str] = []
    per_pair: list[dict[str, Any]] = []
    seen_promote: set[str] = set()

    for paired in paired_lemmas:
        legs = split_paired_headword(paired)
        leg_rows: list[dict[str, Any]] = []
        for leg in legs:
            eff_leg = resolve_leg_lemma(leg)
            cat = classify_split_leg(eff_leg)
            leg_cats.setdefault(cat, []).append(eff_leg)
            key = _lemma_key(eff_leg)
            in_atlas = key in atlas_keys
            row: dict[str, Any] = {
                "leg": eff_leg,
                "category": cat,
                "in_atlas": in_atlas,
            }
            if in_atlas:
                already_present.append(eff_leg)
            elif cat == "single_word_vesum_ok" and key not in seen_promote:
                seen_promote.add(key)
                parent = (inventory_rows_by_lemma or {}).get(paired) or {}
                promote_legs.append(
                    {
                        "lemma": eff_leg,
                        "paired_source": paired,
                        "pos": parent.get("pos"),
                        "gloss": parent.get("gloss"),
                        "locator": parent.get("locator"),
                        "source_id": parent.get("source_id"),
                        "source_family": parent.get("source_family") or "ohoiko",
                    }
                )
                row["promote"] = True
            leg_rows.append(row)
        per_pair.append({"paired": paired, "legs": leg_rows})

    return {
        "paired_count": len(paired_lemmas),
        "leg_counts": {c: len(v) for c, v in sorted(leg_cats.items())},
        "legs_by_category": {c: sorted(set(v)) for c, v in leg_cats.items()},
        "already_present_legs": sorted(set(already_present)),
        "already_present_count": len(set(already_present)),
        "promote_candidate_count": len(promote_legs),
        "promote_candidates": sorted(promote_legs, key=lambda r: r["lemma"]),
        "pairs": per_pair,
    }


def _vesum_pos(lemma: str) -> str | None:
    return promo._vesum_pos(lemma)


def _sum11_gloss(conn: sqlite3.Connection, lemma: str) -> str | None:
    return promo._sum11_gloss(conn, lemma)


def resolve_leg_pos_gloss(
    leg_row: Mapping[str, Any],
    *,
    sum_conn: sqlite3.Connection | None,
) -> tuple[str, str]:
    """Resolve POS/gloss without inventing EN: VESUM POS + parent gloss or SUM11."""
    lemma = str(leg_row["lemma"])
    pos = _vesum_pos(lemma) or "unknown"
    parent_gloss = str(leg_row.get("gloss") or "").strip()
    if parent_gloss:
        gloss = parent_gloss
    elif sum_conn is not None:
        gloss = _sum11_gloss(sum_conn, lemma) or lemma
    else:
        gloss = lemma
    return pos, gloss


def build_split_leg_rows(
    promote_candidates: Sequence[Mapping[str, Any]],
    *,
    sources_db: Path | None = None,
) -> list[dict[str, Any]]:
    """Materialize inventory rows for promotable split legs only."""
    db = sources_db or (PROJECT_ROOT / "data" / "sources.db")
    rows: list[dict[str, Any]] = []
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as conn:
        for cand in promote_candidates:
            lemma = str(cand["lemma"])
            family = str(cand.get("source_family") or "ohoiko")
            if family == "teacher_lesson":
                # OPSEC: prefer Ohoiko/ULP labels unless a teacher surface is required.
                family = "ohoiko"
            pos, gloss = resolve_leg_pos_gloss(cand, sum_conn=conn)
            parent_locator = str(cand.get("locator") or "ohoiko-paired-split")
            rows.append(
                {
                    "lemma": lemma,
                    "pos": pos,
                    "gloss": gloss,
                    "locator": f"{parent_locator} :: paired-split::{lemma}",
                    "source_id": cand.get("source_id"),
                    "source_family": family,
                    "extraction_mode": "paired_headword_split",
                    "paired_source": cand.get("paired_source"),
                }
            )
    return dedupe_leg_rows(rows)


def dedupe_leg_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        key = _lemma_key(str(row["lemma"]))
        if key in seen:
            continue
        seen.add(key)
        out.append(dict(row))
    return out


def write_split_inventory(rows: Sequence[Mapping[str, Any]], path: Path, *, batch_id: str) -> Path:
    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        family = str(row["source_family"])
        item = {
            "lemma": row["lemma"],
            "pos": row["pos"],
            "gloss": row["gloss"],
            "locator": row["locator"],
            "context": (
                f"Paired-headword split from {row.get('paired_source')!r}; "
                f"curated {family} auto-approve; #6370 policy — no invented lemmas."
            ),
        }
        by_family.setdefault(family, []).append(item)
    sources = []
    for family, headwords in sorted(by_family.items()):
        sources.append(
            {
                "id": f"{batch_id}-{family}",
                "source_family": family,
                "extraction_mode": "paired_headword_split",
                "title": f"{family} paired-headword split legs {batch_id}",
                "locator": "private Ohoiko/ULP extracts — lemmas only committed",
                "notes": (
                    "Split legs only from inventory paired comma headwords. "
                    "Derived headword metadata only; raw private copyrighted material "
                    "is local-only and not committed."
                ),
                "headwords": headwords,
            }
        )
    doc = {"version": 1, "kind": "atlas_source_inventory", "sources": sources}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    return path


def write_split_decisions(
    rows: Sequence[Mapping[str, Any]],
    path: Path,
    *,
    inventory_rel: str,
    batch_id: str,
) -> Path:
    decisions = []
    for row in rows:
        lemma = str(row["lemma"])
        locator = str(row["locator"])
        family = str(row["source_family"])
        inventory_source_id = f"{batch_id}-{family}"
        key = source_inventory_key(lemma=lemma, inventory_path=inventory_rel, locator=locator)
        decisions.append(
            {
                "lemma": lemma,
                "decision": "approve_for_publish",
                "approved_pos": row["pos"],
                "approved_gloss": row["gloss"],
                "sense_note": (
                    f"paired-headword split auto-approve from {row.get('paired_source')!r}; "
                    "no invented lemmas; no hand-injected EN"
                ),
                "source_inventory": {
                    "key": key,
                    "path": inventory_rel,
                    "locator": locator,
                    "source_id": inventory_source_id,
                    "source_family": family,
                },
                "evidence_refs": [
                    f"curated source family {family}",
                    "paired comma split policy #6370",
                    "VESUM attestation + heritage classifier",
                ],
            }
        )
    doc = {
        "version": 1,
        "kind": "atlas_source_inventory_review_decisions",
        "batch_id": f"source-inventory-{batch_id}",
        "batch_label": batch_id,
        "reviewer": "operator-curated-source-trust",
        "reviewed_at": "2026-08-12",
        "source_queue": {
            "workflow": "source_inventory_publish_review_queue.v1",
            "total_queue_rows": len(decisions),
            "approved_in_queue": len(decisions),
            "promotion_batch_size": len(decisions),
        },
        "production_outputs_updated": [],
        "decisions": decisions,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--out", type=Path, help="Write residual / split analysis JSON")
    p.add_argument("--rederive", action="store_true", help="Re-derive inventory residual")
    p.add_argument("--analyze-paired", action="store_true", help="Analyze paired splits")
    p.add_argument(
        "--write-promote-artifacts",
        action="store_true",
        help="Write split-leg inventory + decisions for VESUM-ok missing legs",
    )
    p.add_argument(
        "--inventory-out",
        type=Path,
        default=PROJECT_ROOT
        / "data/lexicon/source-inventory/oneshot/ohoiko-ulp-paired-split-legs-2026-08-12.yaml",
    )
    p.add_argument(
        "--decisions-out",
        type=Path,
        default=PROJECT_ROOT
        / "data/lexicon/source-inventory-review-decisions/"
        "2026-08-12-ohoiko-ulp-paired-split-legs-approve.yaml",
    )
    p.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    residual = derive_inventory_residual(
        inventory_path=args.inventory,
        manifest_path=args.manifest,
    )
    print(
        json.dumps(
            {
                "manifest_entries": residual["manifest_entries"],
                "residual_missing": residual["residual_missing"],
                "counts": residual["counts"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    payload: dict[str, Any] = {"residual": residual}
    analysis: dict[str, Any] | None = None
    if args.analyze_paired or args.write_promote_artifacts:
        _entry_count, atlas_keys = atlas_lemma_keys(args.manifest)
        paired = residual["lemmas_by_category"].get("paired_headwords_comma") or []
        rows_by_lemma = {
            str(r["lemma"]): r for r in load_inventory_records(args.inventory)
        }
        analysis = analyze_paired_splits(
            paired_lemmas=paired,
            atlas_keys=atlas_keys,
            inventory_rows_by_lemma=rows_by_lemma,
        )
        payload["paired_split"] = {
            "paired_count": analysis["paired_count"],
            "leg_counts": analysis["leg_counts"],
            "already_present_count": analysis["already_present_count"],
            "promote_candidate_count": analysis["promote_candidate_count"],
            "legs_by_category": analysis["legs_by_category"],
            "promote_candidate_lemmas": [r["lemma"] for r in analysis["promote_candidates"]],
        }
        print(
            json.dumps(
                {
                    "paired_count": analysis["paired_count"],
                    "leg_counts": analysis["leg_counts"],
                    "already_present_count": analysis["already_present_count"],
                    "promote_candidate_count": analysis["promote_candidate_count"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        if args.write_promote_artifacts:
            rows = build_split_leg_rows(analysis["promote_candidates"])
            inv_rel = str(args.inventory_out.relative_to(PROJECT_ROOT))
            write_split_inventory(rows, args.inventory_out, batch_id=args.batch_id)
            write_split_decisions(
                rows,
                args.decisions_out,
                inventory_rel=inv_rel,
                batch_id=args.batch_id,
            )
            payload["promote_artifacts"] = {
                "inventory": str(args.inventory_out),
                "decisions": str(args.decisions_out),
                "rows": len(rows),
            }
            print(json.dumps(payload["promote_artifacts"], ensure_ascii=False), flush=True)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        lean = {
            "schema": "atlas-6370-paired-split-residual.v1",
            "generated_from": "ohoiko_paired_headword_split",
            **payload,
        }
        args.out.write_text(json.dumps(lean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
