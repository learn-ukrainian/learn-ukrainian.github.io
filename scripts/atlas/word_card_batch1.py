"""Assemble the 150 frozen batch-1 pilot cards and a content-free receipt (#9402).

Use for mechanics-only pilot replay, never linguistic certification or publication.
Card bodies and verification details remain host-only; the receipt contains only
identities, counts and canonical content hashes.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import yaml

from scripts.atlas import word_card_assembly as assembly
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_verify as verifier
from scripts.common.repo_root import main_checkout_root
from scripts.common.scratch import ensure_scratch_root

ROOT = Path(__file__).resolve().parents[2]
PILOT = Path("registry/atlas/pilot/pilot-v1.json")
REGISTRY = Path("registry/atlas/identity/registry.json")
REGISTER = Path("docs/sources/permissions-register.yaml")
RECEIPT = Path("registry/atlas/pilot/batch1_manifest.json")
BATCH_SIZE = 150


def assemble(inputs: assembly.Inputs) -> tuple[dict, dict, dict]:
    """Build and independently check the complete frozen batch before any output."""
    assembly.need(len(inputs.units) == BATCH_SIZE, "Batch 1 requires exactly 150 frozen units")
    result = assembly.build(inputs)
    assembly.need(len(result["cards"]) == BATCH_SIZE, "Batch 1 requires exactly 150 cards")
    report = verifier.verify(inputs, result, assembly.build(inputs))
    assembly.need(report["passed"], "Batch 1 integrity verification failed; no output written")
    cards = []
    for card_id, card in sorted(result["cards"].items()):
        # Count distinct source/snapshot/locator citations, not assertion multiplicity.
        locators = {(a["source_id"], a["snapshot_id"], a["locator"]) for a in card["assertions"]}
        cards.append({"card_id": card_id, "locator_count": len(locators),
                      "content_sha256": foundation.digest(card)})
    receipt = {
        "schema_version": "1", "batch": "batch1", "status": "mechanics_only_uncertified",
        "pilot_manifest_sha256": inputs.manifest["manifest_sha256"],
        "build_id": result["build_id"], "card_count": len(cards),
        "locator_count": sum(c["locator_count"] for c in cards),
        "content_hash_basis": "sha256 canonical UTF-8 JSON of complete card (sorted keys, no whitespace)",
        "cards": cards, "cards_sha256": foundation.digest(cards),
    }
    return result, report, receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.atlas.word_card_batch1 --output data/word_cards/batch1
  .venv/bin/python -m scripts.atlas.word_card_batch1 --output data/word_cards/batch1 --check

Outputs: host-only cards/, ledger.json, build-manifest.json and report.json under
--output; a content-free deterministic --receipt, or comparison only with --check.
Exit codes: 0 verified build and receipt; 1 refused input or receipt mismatch;
2 invalid arguments. No source database is modified.
Related: #9402; scripts/atlas/word_card_assembly.py; docs/atlas/word-cards/schema.md
""")
    parser.add_argument("--output", required=True, type=Path,
                        help="Host-only ignored output directory, e.g. data/word_cards/batch1")
    parser.add_argument("--receipt", type=Path, default=ROOT / RECEIPT,
                        help=f"Content-free JSON receipt path (default: {RECEIPT})")
    parser.add_argument("--check", action="store_true",
                        help="Compare rebuilt receipt bytes to --receipt without writing any output (default: off)")
    parser.add_argument("--heldout-manifest", type=Path,
                        help="Optional private held-out manifest for isolation checking (default: unverified)")
    # The dispatch contract binds database reads to the primary checkout. Resolve
    # from this module, never relative to the worker's cwd or a worktree-local DB.
    primary = main_checkout_root(ROOT)
    for name in ("sources", "vesum", "atlas"):
        parser.add_argument(f"--{name}-db", type=Path, default=primary / "data" / f"{name}.db",
                            help=f"Read-only {name} database (default: primary data/{name}.db); "
                                 f"example: /path/to/{name}.db")
    args = parser.parse_args(argv)
    try:
        # Refuse protected card destinations before opening the databases.
        assembly.require_host_only([args.output])
        assembly.need(not args.receipt.resolve().is_relative_to(args.output.resolve()),
                      "The receipt must be separate from host-only card output")
        protected = [ROOT / PILOT, ROOT / REGISTRY, ROOT / REGISTER,
                     args.sources_db, args.vesum_db, args.atlas_db]
        assembly.need(args.receipt.resolve() not in {p.resolve() for p in protected},
                      "The receipt must not overwrite an assembly input")
        with ExitStack() as stack:
            scratch = Path(stack.enter_context(tempfile.TemporaryDirectory(
                prefix="word-card-batch1-", dir=ensure_scratch_root())))
            inputs = assembly.load_inputs(
                ROOT / PILOT, ROOT / REGISTRY, ROOT / REGISTER,
                args.sources_db, args.vesum_db, args.atlas_db, stack, scratch, args.heldout_manifest)
            result, report, receipt = assemble(inputs)
            # Use the same deterministic serializer for comparison and publication.
            candidate = scratch / "receipt.json"
            foundation.write(candidate, receipt)
            if args.check:
                assembly.need(args.receipt.read_bytes() == candidate.read_bytes(),
                              "Batch 1 receipt differs from the verified rebuild")
            else:
                assembly.write_output(args.output, result, report)
                foundation.write(args.receipt, receipt)
        print(json.dumps({"passed": True, "cards": receipt["card_count"],
                          "locators": receipt["locator_count"], "cards_sha256": receipt["cards_sha256"],
                          "heldout_isolation": inputs.heldout, "certified": False}, sort_keys=True))
        return 0
    except (foundation.Refusal, ValueError, KeyError, OSError, yaml.YAMLError) as error:
        message = str(error) if isinstance(error, foundation.Refusal) else "Invalid or inaccessible batch input"
        print("REFUSED: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
