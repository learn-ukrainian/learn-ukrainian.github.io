"""Census and regenerate the Ohoiko intake damaged by detached OCR acutes.

Raw source chunks and the historical #10181 inventory remain immutable. This
command produces a separate source-inventory delta; it never builds a runtime.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import types
from pathlib import Path
from typing import Any

import yaml

from scripts.audit.source_inventory_review_decisions import source_inventory_key
from scripts.common.scratch import ensure_scratch_root
from scripts.ingest import ohoiko_books_ingest as words
from scripts.ingest import ohoiko_verbs_ingest as verbs
from scripts.lexicon import promote_grow_candidates as promote
from scripts.lexicon.curated_ohoiko_ulp_repromote import _norm_lemma
from scripts.lexicon.published_record_dispositions import canonical_sha256, load_dispositions
from scripts.lib.readonly_sqlite import open_readonly
from scripts.verification.vesum import InspectionStatus, inspect_word

ROOT = Path(__file__).resolve().parents[2]
BATCH = "ohoiko-ocr-acute-rejoin-2026-10-28"
INVENTORY = f"registry/lexicon/source-inventory/oneshot/{BATCH}.yaml"
LOGICAL_INVENTORY = INVENTORY.replace("registry/", "data/", 1)
DECISIONS = "registry/lexicon/source-inventory-review-decisions/2026-10-28-ohoiko-ocr-acute-rejoin-approve.yaml"


def _baseline_parser(ref: str, module: str) -> types.ModuleType:
    source = subprocess.run(
        ["git", "show", f"{ref}:scripts/ingest/{module}.py"], cwd=ROOT,
        check=True, capture_output=True, text=True, timeout=30,
    ).stdout
    name = f"_ohoiko_before_{module}"
    loaded = types.ModuleType(name)
    loaded.__file__ = str(ROOT / "scripts/ingest" / f"{module}.py")
    sys.modules[name] = loaded  # dataclass resolves its module while loading
    try:
        exec(compile(source, loaded.__file__, "exec"), loaded.__dict__)
    finally:
        del sys.modules[name]
    return loaded


def census(sources_db: Path, baseline_ref: str) -> dict[str, Any]:
    """Run both real parsers on the same complete, read-only L0 selections."""
    with open_readonly(sources_db) as conn:
        selections = {}
        for family, source in (("words", words.BOOKS["1000-words"].source_file), ("verbs", verbs.SOURCE_FILE)):
            selections[family] = [
                {"chunk_id": cid, "text": text}
                for cid, text in conn.execute(
                    "SELECT chunk_id, text FROM textbooks WHERE source_file = ? ORDER BY chunk_id", (source,),
                )
            ]
    if [len(selections[k]) for k in ("words", "verbs")] != [1000, 500]:
        raise ValueError("the full 1000-word / 500-verb source denominator is required")
    changes = []
    with tempfile.TemporaryDirectory(prefix="ohoiko-census-", dir=ensure_scratch_root()) as directory:
        for family, current, module in (
            ("words", words, "ohoiko_books_ingest"), ("verbs", verbs, "ohoiko_verbs_ingest"),
        ):
            records = selections[family]
            path = Path(directory) / f"{family}.txt"
            text = "\n".join(
                r["text"] if family == "words" else f"№{int(r['chunk_id'].rsplit('_e', 1)[1])}\n{r['text']}"
                for r in records
            )
            path.write_text(text, encoding="utf-8")
            old = _baseline_parser(baseline_ref, module)
            kwargs = {"max_entry_number": 1000} if family == "words" else {}
            before, after = old.parse_book(path, **kwargs), current.parse_book(path, **kwargs)
            expected = set(range(1, len(records) + 1))
            if {e.number for e in before} != expected or {e.number for e in after} != expected:
                raise ValueError(f"{family}: parser omitted or changed source entry numbers")
            raw_by_number = {int(r["chunk_id"].rsplit('_e', 1)[1]): r for r in records}
            before_by_number = {e.number: e for e in before}
            for entry in after:
                prior = before_by_number[entry.number]
                old_head = prior.headword if family == "words" else prior.title
                head = entry.headword if family == "words" else entry.title
                if old_head == head:
                    continue
                raw = raw_by_number[entry.number]
                if family == "words":
                    forms = [_norm_lemma(part) for part in head.split(",")]
                    gloss = entry.english
                    pos = "noun"
                else:
                    # Preserve the existing curated book convention: bare
                    # infinitives, with optional [ся] left to the lexical adapter.
                    forms = [_norm_lemma(part.split()[0]) for part in head.split("|")]
                    gloss = next((line.strip() for line in entry.body_lines[1:6] if line.strip().startswith("to ")), "")
                    pos = "verb"
                if not gloss or any(inspect_word(form).status != InspectionStatus.CLEAN for form in forms):
                    raise ValueError(f"{raw['chunk_id']}: missing raw gloss or VESUM attestation; unresolved")
                changes.append({
                    "chunk_id": raw["chunk_id"], "number": entry.number,
                    "book": "1000-words" if family == "words" else "500-verbs",
                    "before": _norm_lemma(old_head), "restored": forms, "pos": pos, "gloss": gloss,
                    "raw_sha256": hashlib.sha256(raw["text"].encode()).hexdigest(),
                })
    return {
        "source_counts": {k: len(v) for k, v in selections.items()},
        "selection_sha256": canonical_sha256(selections), "baseline_ref": baseline_ref,
        "changes": changes, "unresolved": [],
    }


def source_documents(report: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    heads, decisions = [], []
    for change in report["changes"]:
        for form in change["restored"]:
            locator = f"ohoiko-{change['book']} entry {change['number']} :: acute-rejoin::{change['before']} -> {form}"
            heads.append({
                "lemma": form, "pos": change["pos"], "gloss": change["gloss"], "locator": locator,
                "context": f"Detached OCR acute rejoined; raw record SHA-256 {change['raw_sha256']}. "
                           "Stress is not inferred from OCR; canonical head is VESUM-attested.",
            })
            decisions.append({
                "lemma": form, "decision": "approve_for_publish", "approved_pos": change["pos"],
                "approved_gloss": change["gloss"], "sense_note": "Source-backed OCR header restoration; no surface admission.",
                "source_inventory": {
                    "key": source_inventory_key(lemma=form, inventory_path=LOGICAL_INVENTORY, locator=locator),
                    "path": LOGICAL_INVENTORY, "locator": locator, "source_id": BATCH, "source_family": "ohoiko",
                },
                "evidence_refs": ["VESUM via Sources verify_words / inspect_word", f"raw record SHA-256 {change['raw_sha256']}"],
            })
    inventory = {"version": 1, "kind": "atlas_source_inventory", "sources": [{
        "id": BATCH, "source_family": "ohoiko", "extraction_mode": "ocr_acute_rejoin",
        "title": "Ohoiko detached-acute headword corrections", "locator": "numbered Ohoiko source records",
        "notes": "Independent correction inventory; historical bulk rows and #10181 holds remain immutable.",
        "headwords": heads,
    }]}
    ledger = {
        "version": 1, "kind": "atlas_source_inventory_review_decisions", "batch_id": BATCH,
        "batch_label": BATCH, "reviewer": "operator-ordered-source-restoration", "reviewed_at": "2026-10-28",
        "source_queue": {"workflow": "source_inventory_publish_review_queue.v1", "total_queue_rows": len(heads),
                         "approved_in_queue": len(heads), "promotion_batch_size": len(heads)},
        "production_outputs_updated": [], "decisions": decisions,
    }
    return inventory, ledger


def repair_legacy_entries(manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, list[str]]]:
    """Apply existing holds and canonical alias identity to damaged legacy rows."""
    authority = load_dispositions()
    result = copy.deepcopy(manifest)
    repairs = {"removed_held": [], "merged_duplicate": []}
    active_ids = {row["row_id"] for row in authority.active_holds}
    held = {r["entry"]["lemma"]: r for r in authority.preservation["records"]
            if r["row_id"] in active_ids & {"10181-02", "10181-04", "10181-05", "10181-06"}}
    entries = result["entries"]
    targets = {e.get("url_slug") for e in entries if not e.get("form_of")}
    survivors = []
    for entry in entries:
        lemma = entry.get("lemma")
        if lemma in held:
            if canonical_sha256(entry) != held[lemma]["payload_sha256"]:
                raise ValueError(f"{lemma}: held payload changed; refusing to discard mixed or unknown evidence")
            repairs["removed_held"].append(lemma)
            continue
        if lemma == "проєк":
            if "проєкт" not in targets:
                raise ValueError("promote the corrected проєкт source before repairing its legacy identity")
            provenance = entry.get("source_provenance") or []
            if not provenance or any(
                p.get("source_family") != "ohoiko" or p.get("source_locator") != "ohoiko-1000-words entry 685"
                for p in provenance
            ) or entry.get("course_usage"):
                raise ValueError("проєк: refusing to discard unknown or mixed source contributions")
            aliases = yaml.safe_load((ROOT / "registry/lexicon/curated_aliases.yaml").read_text())["aliases"]
            if not any(a.get("alias") == "проєк" and a.get("target_slug") == "проєкт" for a in aliases):
                raise ValueError("the existing проєк -> проєкт identity alias is required")
            repairs["merged_duplicate"].append(lemma)
            continue
        survivors.append(entry)
    result["entries"] = survivors
    if any(repairs.values()):
        promote._refresh_manifest_metadata(result)
    authority.validate_manifest(result)
    return result, repairs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Census detached-acute Ohoiko headwords and regenerate their source correction delta.\n"
                    "Use before the next Atlas build; never use to publish a runtime or release a hold.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.lexicon.repair_ohoiko_headwords --sources-db data/sources.db --baseline-ref <pre-fix-SHA>
  .venv/bin/python -m scripts.lexicon.repair_ohoiko_headwords --sources-db data/sources.db --baseline-ref <pre-fix-SHA> --write-source-data
  .venv/bin/python -m scripts.lexicon.repair_ohoiko_headwords --manifest staging/manifest.json --repair-out staging/repaired.json
Outputs: JSON census or identity plan on stdout. Explicit flags write only source delta YAML or a verified staged manifest.
Exit codes: 0 success; 1 missing evidence, changed held payload, or failed manifest verification; 2 invalid arguments.
Related: docs/runbooks/word-atlas-ohoiko-headword-repair.md; #10181, #10453, #11904.
""",
    )
    parser.add_argument("--sources-db", type=Path, help="Read-only local Sources DB, e.g. data/sources.db (default: none)")
    parser.add_argument("--baseline-ref", help="Trusted pre-fix Git revision for both old parsers (default: none)")
    parser.add_argument("--write-source-data", action="store_true", help="Regenerate the dedicated correction inventory and ledger (default: dry run)")
    parser.add_argument("--manifest", type=Path, help="Explicit staged legacy manifest to repair (default: none)")
    parser.add_argument("--repair-out", type=Path, help="Write verified repaired manifest to a different staging path (default: dry run)")
    args = parser.parse_args()
    if args.manifest:
        if args.sources_db or args.baseline_ref or args.write_source_data:
            parser.error("manifest repair and source census are separate operations")
        repaired, report = repair_legacy_entries(json.loads(args.manifest.read_text()))
        if args.repair_out:
            if args.repair_out.resolve() == args.manifest.resolve():
                parser.error("--repair-out must be a separate staged file")
            promote._validate_before_write(repaired, args.repair_out, promote.verify_prospective_manifest)
            promote._write_json_atomically(args.repair_out, repaired)
    else:
        if not args.sources_db or not args.baseline_ref or args.repair_out:
            parser.error("source census requires --sources-db and --baseline-ref")
        report = census(args.sources_db, args.baseline_ref)
        if args.write_source_data:
            for relative, doc in zip((INVENTORY, DECISIONS), source_documents(report), strict=True):
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
