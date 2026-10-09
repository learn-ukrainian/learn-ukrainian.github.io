"""Withdraw or restore the six preserved published records (#10181).

Dry-run by default. An explicit manifest path is always required; this command
changes no ledger, recovery material, runtime projection or publication pointer.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lexicon import manifest_io
from scripts.lexicon.published_record_dispositions import (
    DispositionError,
    Dispositions,
    canonical_sha256,
    load_dispositions,
    ordered_digest,
    validate_route_references,
)


def _refresh_present_counts(manifest: dict[str, Any]) -> None:
    """Use existing build predicates, refreshing only PRESENT known counters."""
    entries = manifest["entries"]
    stats = manifest.get("stats", {})
    values = {
        "lemmas_total": len(entries),
        "from_built": sum(str(e.get("primary_source", "")).startswith("built_vocabulary") for e in entries),
        "form_of_count": sum("form_of" in e for e in entries),
    }
    for key, value in values.items():
        if key in stats:
            stats[key] = value
    if "entries_count" in manifest:
        manifest["entries_count"] = len(entries)


def prospective_manifest(manifest: dict[str, Any], authority: Dispositions, action: str) -> dict[str, Any]:
    """Derive one exact transaction, conserving every survivor and its order."""
    preserved = authority.preservation
    tx, records = preserved["transaction"], preserved["records"]
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise DispositionError("manifest entries must be a list")
    if action == "withdraw":
        if len(authority.active_holds) != 6 or authority.released_ids:
            raise DispositionError("withdraw requires all six active holds")
        if len(entries) != tx["before_entries"]:
            raise DispositionError("withdraw denominator diverged")
        for record in records:
            index = record["original_index_zero_based"]
            if canonical_sha256(entries[index]) != record["payload_sha256"]:
                raise DispositionError("withdraw payload/position diverged")
        positions = {r["original_index_zero_based"] for r in records}
        survivors = [entry for i, entry in enumerate(entries) if i not in positions]
        envelope = copy.deepcopy(preserved["original_manifest_envelope"])
        if {k: v for k, v in manifest.items() if k != "entries"} != envelope:
            raise DispositionError("original envelope diverged")
        result = {
            key: survivors if key == "entries" else envelope[key] for key in preserved["original_top_level_order"]
        }
        _refresh_present_counts(result)
        authority.validate_manifest(result)
    elif action == "restore":
        if authority.active_holds or authority.released_ids != {r["row_id"] for r in records}:
            raise DispositionError("restore requires six explicit reviewed releases")
        if len(entries) != tx["after_entries"]:
            raise DispositionError("restore denominator diverged")
        survivors = entries
        restored = list(entries)
        for record in records:
            restored.insert(record["original_index_zero_based"], copy.deepcopy(record["entry"]))
        envelope = copy.deepcopy(preserved["original_manifest_envelope"])
        result = {key: restored if key == "entries" else envelope[key] for key in preserved["original_top_level_order"]}
        validate_route_references(
            result, {r["entry"]["url_slug"] for r in records}, {r["entry"]["lemma"] for r in records}
        )
    else:
        raise DispositionError("unsupported action")
    if ordered_digest(survivors) != tx["ordered_survivor_sha256"]:
        raise DispositionError("ordered survivors diverged")
    expected = tx["after_sha256" if action == "withdraw" else "before_sha256"]
    if hashlib.sha256(manifest_io.serialize_manifest(result)).hexdigest() != expected:
        raise DispositionError("prospective transaction digest diverged")
    return result


def dispose(manifest_path: Path, action: str, *, write: bool = False) -> dict[str, Any]:
    """Re-read authority and manifest before the existing atomic replacement."""
    authority = load_dispositions()
    raw = manifest_path.read_bytes()
    current_sha = hashlib.sha256(raw).hexdigest()
    manifest = json.loads(raw)
    tx = authority.preservation["transaction"]
    before, after = tx["before_sha256"], tx["after_sha256"]
    if action not in {"withdraw", "restore"}:
        raise DispositionError("unsupported action")
    if action == "restore" and (authority.active_holds or len(authority.released_ids) != 6):
        raise DispositionError("restore requires six explicit reviewed releases")
    if action == "withdraw" and (len(authority.active_holds) != 6 or authority.released_ids):
        raise DispositionError("withdraw requires all six active holds")
    already = after if action == "withdraw" else before
    expected_input = before if action == "withdraw" else after
    if current_sha == already:
        authority.validate_manifest(manifest)
        return {"action": action, "state": "already_applied", "sha256": current_sha, "written": False}
    if current_sha != expected_input:
        raise DispositionError("manifest diverged from exact before/after states")
    result = prospective_manifest(manifest, authority, action)
    checked = load_dispositions()
    if (
        canonical_sha256(checked.ledger) != canonical_sha256(authority.ledger)
        or checked.preservation != authority.preservation
    ):
        raise DispositionError("authority changed during transaction")
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != current_sha:
        raise DispositionError("manifest changed during transaction")
    if write:
        manifest_io.write_manifest(manifest_path, result)
    return {
        "action": action,
        "state": "applied" if write else "dry_run",
        "sha256": already,
        "written": write,
        "preserved": 6,
        "survivors": tx["after_entries"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: .venv/bin/python -m scripts.lexicon.dispose_published_records --manifest COPY.json --action withdraw\n"
        "Inputs: mandatory tracked ledger/preservation and an explicit manifest.\n"
        "Outputs: JSON transaction receipt; only --write replaces the manifest atomically.\n"
        "Exit codes: 0 exact dry-run/apply/no-op; 2 contract or I/O failure (no replacement).\n"
        "Related: scripts.lexicon.verify_manifest; issue #10181.",
    )
    parser.add_argument("--manifest", type=Path, required=True, help="Explicit prospective manifest path")
    parser.add_argument("--action", choices=("withdraw", "restore"), required=True)
    parser.add_argument(
        "--write", action="store_true", help="Apply the validated atomic replacement (default: dry-run)"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        print(json.dumps(dispose(args.manifest, args.action, write=args.write), sort_keys=True))
    except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
