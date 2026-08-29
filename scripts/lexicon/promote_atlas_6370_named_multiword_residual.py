#!/usr/bin/env python3
"""Admit #6370 residual-27 named legitimate multiword expressions + забоятися.

#6370 residual-27 (2026-08-18, ``claude/atlas-6370-residual-27``) classified 0
space-collapse admits for eight rows that are real Ukrainian multiword
expressions, not OCR space-collapse artifacts: виходити заміж, день тижня,
картопля фрі, перед тим як, сільське господарство, так само, такий самий,
час від часу. Seven of the eight already have an ``approve_for_publish``
decision in ``2026-07-19-ohoiko-ulp-curated-bulk-approve.yaml`` under their
exact clean lemma. ``виходити заміж`` only has a decision for its comma-paired
parent headword (``виходити заміж, вийти``); ``scripts/lexicon/
ohoiko_paired_headword_split.py`` (#6678) sends multiword split legs to a
``multiword_after_split`` residual instead of promoting them, so that leg was
never admitted on its own — a small dedicated inventory + decision row
(2026-08-23) closes that gap without inventing a lemma or gloss.

``забоятися`` was the one unpublished single lemma named on 2026-08-17; #6978
merged its promotion intent but never actually applied it to a manifest
(publish_manifest.py + fingerprint/test changes only). Its inventory +
decision row (2026-08-14-ohoiko-ulp-ocr-space-collapse-approve.yaml) already
exist; this script re-runs the standard promote step against them.

Each admitted multiword entry carries an explicit ``entry_type`` (per
docs/runbooks/word-atlas-entry-model.md) instead of the legacy shape-based
fallback, and reuses ``entry_provenance`` from the already-approved source
inventory rows verbatim — no new gloss or lemma is invented anywhere in this
script. Run from the repository root::

    .venv/bin/python -m scripts.lexicon.promote_atlas_6370_named_multiword_residual --report
    .venv/bin/python -m scripts.lexicon.promote_atlas_6370_named_multiword_residual --write --report

Practice admission matches the teacher P1 promote path
(``promote_teacher_lesson_intake``): each decision row carries
``surface_admission.practice=True``. Daily Word and cloze stay frozen.

This script only mutates the local (gitignored) hydrated Atlas manifest and
its DB-free fingerprint sidecar. Pointer write / release upload is a separate
publish step (see ``scripts/lexicon/publish_manifest.py``).
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import apply_source_inventory_promotion as apply
from scripts.audit import plan_source_inventory_promotion as planner
from scripts.audit.source_inventory_intake import (
    SourceInventoryError,
    read_source_inventory,
    source_inventory_candidates,
)
from scripts.lexicon.build_data_manifest import _lemma_key

DEFAULT_MANIFEST = PROJECT_ROOT / "site/src/data/lexicon-manifest.json"
DEFAULT_FINGERPRINT = PROJECT_ROOT / "site/src/data/lexicon-manifest.fingerprint.json"

BIG_INVENTORY = (
    PROJECT_ROOT / "data/lexicon/source-inventory/oneshot/ohoiko-ulp-curated-2026-07-19-bulk.yaml"
)
BIG_DECISIONS = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory-review-decisions/2026-07-19-ohoiko-ulp-curated-bulk-approve.yaml"
)
LEG_INVENTORY = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory/oneshot/ohoiko-ulp-paired-split-multiword-legs-2026-08-23.yaml"
)
LEG_DECISIONS = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory-review-decisions/"
    "2026-08-23-atlas-6370-paired-split-multiword-leg-approve.yaml"
)
SPACE_COLLAPSE_INVENTORY = (
    PROJECT_ROOT / "data/lexicon/source-inventory/oneshot/ohoiko-ulp-ocr-space-collapse-2026-08-14.yaml"
)
SPACE_COLLAPSE_DECISIONS = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory-review-decisions/2026-08-14-ohoiko-ulp-ocr-space-collapse-approve.yaml"
)

# #6370 residual-27 (2026-08-18): entry_type per docs/runbooks/word-atlas-entry-model.md
# tie-breakers. Evidence is a deterministic dictionary/VESUM lookup (#M-4):
#   - виходити заміж: СУМ-11 lists "виходити (вийти) заміж" as a fixed collocation
#     under за́між (mcp__sources__search_definitions) — literal-but-fixed formula,
#     not figurative -> expression.
#   - час від часу: Фразеологічний словник (ULIF) lists it verbatim as an idiom
#     (mcp__sources__search_idioms) -> phraseologism.
#   - the remaining six have no idiom/proverb/formula dictionary evidence, so per
#     the entry-model tie-breaker they default to multiword_term (domain/course
#     concept or grammatical unit). All components of all eight phrases verified
#     present in VESUM via mcp__sources__verify_words before this batch was built.
TARGET_ENTRY_TYPES: dict[str, str] = {
    "виходити заміж": "expression",
    "день тижня": "multiword_term",
    "картопля фрі": "multiword_term",
    "перед тим як": "multiword_term",
    "сільське господарство": "multiword_term",
    "так само": "multiword_term",
    "такий самий": "multiword_term",
    "час від часу": "phraseologism",
}
ZABOJATYSJA_LEMMA = "забоятися"
# Same opt-in the teacher P1 promoter writes onto approved rows.
PRACTICE_ADMISSION = {"practice": True}


def _build_candidate(lemma: str, inventory_path: Path, *, entry_type: str | None) -> dict[str, Any]:
    """Build one auto_merge candidate entry from an already-committed inventory row."""
    records = [
        record
        for record in read_source_inventory(inventory_path, project_root=PROJECT_ROOT)
        if record.lemma == lemma
    ]
    if not records:
        raise SourceInventoryError(f"{lemma!r} not found in {inventory_path}")
    candidates = source_inventory_candidates(records)
    if len(candidates) != 1:
        raise SourceInventoryError(f"{lemma!r}: expected exactly one candidate in {inventory_path}")
    item = candidates[0]

    entry: dict[str, Any] = {
        "lemma": item.lemma,
        "pos": item.pos,
        "gloss": item.gloss,
        "primary_source": "source_inventory_grow",
        "source_provenance": [dict(payload) for payload in item.source_provenance],
        # Every component of every #6370 residual-27 phrase was independently
        # verified present in VESUM via mcp__sources__verify_words before this
        # batch was authored (see PR description); none is heritage-flagged.
        "heritage_status": {
            "classification": "standard",
            "attestations": [],
            "is_russianism": False,
            "russian_shadow": False,
            "vesum_attested": True,
            "calque_warning": None,
            "warning_severity": "none",
        },
        "surface_admission": dict(PRACTICE_ADMISSION),
    }
    if entry_type:
        entry["entry_type"] = entry_type
    return entry


def _scratch_decision_subset(source_path: Path, lemmas: set[str], out_path: Path) -> Path:
    """Write a decision-ledger subset containing only rows for ``lemmas``.

    Approval fields are copied from the already-committed ledger at
    ``source_path``. ``surface_admission.practice=True`` is stamped here so the
    apply path matches teacher P1; historical ledgers stay browse-only.
    """
    doc = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    rows = [row for row in doc["decisions"] if row.get("lemma") in lemmas]
    found = {row["lemma"] for row in rows}
    missing = lemmas - found
    if missing:
        raise SourceInventoryError(f"{source_path}: no approve_for_publish row for {sorted(missing)}")

    stamped = []
    for row in rows:
        stamped_row = dict(row)
        stamped_row["surface_admission"] = dict(PRACTICE_ADMISSION)
        stamped.append(stamped_row)

    scratch = dict(doc)
    scratch["decisions"] = stamped
    scratch["source_queue"] = dict(doc["source_queue"])
    scratch["source_queue"].pop("first_promotion_batch_size", None)
    scratch["source_queue"]["promotion_batch_size"] = len(rows)
    scratch["source_queue"]["total_queue_rows"] = len(rows)
    scratch["source_queue"]["approved_in_queue"] = len(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.safe_dump(scratch, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    return out_path


def build_candidates_and_decisions(scratch_dir: Path) -> tuple[Path, list[Path]]:
    """Return (candidates_path, decision_files) for the #6370 residual-27 batch."""
    big_lemmas = [lemma for lemma in TARGET_ENTRY_TYPES if lemma != "виходити заміж"]
    candidates = [
        _build_candidate(lemma, BIG_INVENTORY, entry_type=TARGET_ENTRY_TYPES[lemma]) for lemma in big_lemmas
    ]
    candidates.append(
        _build_candidate(
            "виходити заміж", LEG_INVENTORY, entry_type=TARGET_ENTRY_TYPES["виходити заміж"]
        )
    )
    candidates.append(_build_candidate(ZABOJATYSJA_LEMMA, SPACE_COLLAPSE_INVENTORY, entry_type=None))

    payload = {
        "generated_from": "promote_atlas_6370_named_multiword_residual.v1",
        "counts": {
            "total_delta": len(candidates),
            "processed": len(candidates),
            "auto_merge": len(candidates),
            "needs_review": 0,
        },
        "limit": None,
        "auto_merge": candidates,
        "needs_review": [],
    }
    candidates_path = scratch_dir / "atlas-6370-multiword-residual-candidates.json"
    candidates_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    big_scratch = _scratch_decision_subset(
        BIG_DECISIONS, set(big_lemmas), scratch_dir / "big-ledger-subset-decisions.yaml"
    )
    leg_scratch = _scratch_decision_subset(
        LEG_DECISIONS, {"виходити заміж"}, scratch_dir / "leg-ledger-subset-decisions.yaml"
    )
    collapse_scratch = _scratch_decision_subset(
        SPACE_COLLAPSE_DECISIONS,
        {ZABOJATYSJA_LEMMA},
        scratch_dir / "space-collapse-ledger-subset-decisions.yaml",
    )
    decision_files = [big_scratch, leg_scratch, collapse_scratch]
    return candidates_path, decision_files


def _self_check(manifest_path: Path, promoted_lemmas: list[str]) -> int:
    """DB-free structural self-check: no VESUM/sources.db dependency."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {_lemma_key(str(e.get("lemma") or "")): e for e in data["entries"] if isinstance(e, dict)}
    failures: list[str] = []
    for lemma in promoted_lemmas:
        entry = entries.get(_lemma_key(lemma))
        if entry is None:
            failures.append(f"{lemma}: missing")
            continue
        try:
            apply._validate_privacy_safe_provenance(entry)
        except Exception as exc:
            failures.append(str(exc))
        if not (entry.get("gloss") or "").strip():
            failures.append(f"{lemma}: empty gloss")
        if not (entry.get("pos") or "").strip():
            failures.append(f"{lemma}: empty pos")
        expected_entry_type = TARGET_ENTRY_TYPES.get(lemma)
        if expected_entry_type and entry.get("entry_type") != expected_entry_type:
            failures.append(f"{lemma}: entry_type {entry.get('entry_type')!r} != {expected_entry_type!r}")
        admission = entry.get("surface_admission")
        if not isinstance(admission, dict) or admission.get("practice") is not True:
            failures.append(f"{lemma}: missing surface_admission.practice")
    if failures:
        print("SELF-CHECK FAIL", failures[:20], flush=True)
        return 2
    print("SELF-CHECK OK", len(promoted_lemmas), flush=True)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--fingerprint", type=Path, default=DEFAULT_FINGERPRINT)
    parser.add_argument("--write", action="store_true", help="Write manifest + fingerprint sidecar")
    parser.add_argument("--report", action="store_true", help="Print JSON summary")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with tempfile.TemporaryDirectory(prefix="atlas-6370-multiword-") as tmp_dir:
            scratch_dir = Path(tmp_dir)
            candidates_path, decision_files = build_candidates_and_decisions(scratch_dir)
            plan = planner.build_promotion_plan(
                candidates_path=candidates_path,
                decision_files=decision_files,
                manifest_path=args.manifest,
            )
            print("plan", plan["counts"], flush=True)
            if plan["counts"]["missing_candidates"]:
                print("missing_candidates", plan["missing_candidates"], file=sys.stderr, flush=True)
                return 2

            manifest_payload = json.loads(args.manifest.read_text(encoding="utf-8"))
            before = len(manifest_payload["entries"])
            result = apply.apply_promotion_plan(
                manifest_payload,
                plan,
                expected_additions=len(TARGET_ENTRY_TYPES) + 1,
                expected_skipped_existing=0,
            )
            promoted = [row["lemma"] for row in result["promoted_entries"]]

            if args.write and result["counts"]["promoted"]:
                result = apply.write_manifest_if_changed(
                    manifest_payload,
                    result,
                    manifest_path=args.manifest,
                    fingerprint_path=args.fingerprint,
                    self_check=lambda path: _self_check(path, promoted),
                )
            after = (
                len(json.loads(args.manifest.read_text(encoding="utf-8"))["entries"])
                if args.write
                else before + result["counts"]["promoted"]
            )
    except (OSError, SourceInventoryError, apply.SourceInventoryError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except apply.promote.SelfCheckError as exc:
        print(f"self-check failed: exit_code={exc}", file=sys.stderr)
        return 2

    summary = {
        "before": before,
        "after": after,
        "promoted": promoted,
        "counts": result["counts"],
        "outputs": result.get("production_outputs_updated"),
        "dry_run": not args.write,
    }
    print("apply", summary, flush=True)
    if args.report:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
