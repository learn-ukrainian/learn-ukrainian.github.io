"""Run the W1b mechanics rehearsal against the reviewed W1a pilot (#8981).

Reuses Atlas assembly, source verification and withdrawal/rollback checks.
Emits only a deterministic receipt; never mints IDs or certifies card content.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path
from typing import TYPE_CHECKING

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml

from scripts.common.scratch import ensure_scratch_root

if TYPE_CHECKING:
    from scripts.atlas import word_card_assembly as assembly

W1A_SHA = "c5d5909282c98dbb04fc8e71c7c59a7167b2ae2c"
# Canonical JSON digests of the two committed W1a inputs, independent of candidates and Git availability.
MANIFEST_SHA256 = "ffe7ff160ad9b08a97e0bd971d0577be654825b90cc40c2fc37aca7ae70a0b8b"
REGISTRY_SHA256 = "c1b33a0d498ab2365fb8690b483755c16cb7ca39d62b871fd90bc756dcf22ff5"
DENOMINATOR = {"cards": 150, "locators": 3163, "source_rows": 272}
SCENARIOS = frozenset({
    "source_record", "source", "overlap_source_then_record", "overlap_record_then_source",
    "content_stress_set", "content_paradigm_slot", "assertion_id_fallback",
})


def check_frozen_inputs(manifest: dict, registry: dict) -> None:
    """Refuse changed W1a inputs, including a coherently rehashed selection or identity swap."""
    from scripts.atlas import word_card_assembly as assembly
    from scripts.atlas import word_card_foundation as foundation

    foundation.require(foundation.digest(manifest) == MANIFEST_SHA256, "Manifest differs from frozen W1a baseline")
    foundation.require(foundation.digest(registry) == REGISTRY_SHA256, "Registry differs from frozen W1a baseline")
    assembly.audit_allocation(registry, manifest)


def run_rehearsal(inputs: assembly.Inputs) -> dict:
    """Build twice, verify every assertion and identity, then rehearse withdrawal and rollback."""
    from scripts.atlas import word_card_assembly as assembly
    from scripts.atlas import word_card_foundation as foundation
    from scripts.atlas import word_card_verify as verifier

    check_frozen_inputs(inputs.manifest, inputs.registry)
    baseline = assembly.build(inputs)
    repeated = assembly.build(inputs)
    verification = verifier.verify(inputs, baseline, repeated)
    observed = {
        "cards": len(baseline["cards"]),
        "locators": sum(len(card["assertions"]) for card in baseline["cards"].values()),
        "source_rows": inputs.hashes["frozen_rows_verified"],
    }
    complete = observed == DENOMINATOR and verification.get("locators", {}).get("checked") == DENOMINATOR["locators"]
    baseline_passed = complete and verification["passed"]
    withdrawal = verifier.rehearse(inputs) if baseline_passed else {
        "passed": False, "reason": "baseline_verification_failed", "scenarios": {},
    }
    scenario_coverage = set(withdrawal["scenarios"]) == SCENARIOS
    return {
        "schema_version": "word-cards-pilot-rehearsal.v1",
        "baseline_sha": W1A_SHA,
        "input_sha256": {"manifest": MANIFEST_SHA256, "registry": REGISTRY_SHA256},
        "denominator": dict(DENOMINATOR),
        "observed": observed,
        "denominator_passed": complete,
        "cards_sha256": foundation.digest(baseline["cards"]),
        "verification": verification,
        "withdrawal": withdrawal,
        "scenario_coverage_passed": scenario_coverage,
        "passed": baseline_passed and withdrawal["passed"] and scenario_coverage,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the frozen 150-card W1a pilot and rehearse withdrawal/rollback.\n"
        "Use for W1b mechanics proof, not content certification or identity allocation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.projects.open_model_data.word_cards.rehearsal --output "$TMPDIR/w1b"
  .venv/bin/python -m scripts.projects.open_model_data.word_cards.rehearsal --output batch_state/reports/w1b

Outputs: host-only pilot-rehearsal.json and the same JSON on stdout. Source databases and frozen inputs are read-only.
Exit codes: 0 all mechanics checks pass; 1 refusal or failed check; 2 usage error.
Related: #8981; docs/atlas/word-cards/pilot-findings.md; scripts/atlas/word_card_assembly.py
""",
    )
    parser.add_argument("--manifest", type=Path, default=ROOT / "registry/atlas/pilot/pilot-v1.json",
                        help="Frozen pilot JSON (default: registry/atlas/pilot/pilot-v1.json); must match W1a digest")
    parser.add_argument("--registry", type=Path, default=ROOT / "registry/atlas/identity/registry.json",
                        help="Identity JSON (default: registry/atlas/identity/registry.json); must match W1a digest")
    parser.add_argument("--register", type=Path, default=ROOT / "docs/sources/permissions-register.yaml",
                        help="Permissions YAML (default: docs/sources/permissions-register.yaml); referenced entries are pinned")
    parser.add_argument("--output", type=Path, required=True,
                        help="Host-only receipt directory, e.g. batch_state/reports/w1b (required; no default)")
    for store in ("sources", "vesum", "atlas"):
        parser.add_argument(f"--{store}-db", type=Path,
                            help=f"Read-only {store} SQLite file (default: configured primary store); use an absolute path. "
                            "The sources store must have its associated ULIF raw cache.")
    args = parser.parse_args(argv)
    from scripts.atlas import word_card_assembly as assembly
    from scripts.atlas import word_card_foundation as foundation

    try:
        # Refuse substituted inputs and unsafe output before opening any source store or creating scratch.
        check_frozen_inputs(foundation.load(args.manifest), foundation.load(args.registry))
        for path in (args.sources_db, args.vesum_db, args.atlas_db):
            foundation.require(path is None or path.is_absolute(), "Source database paths must be absolute")
        assembly.require_host_only([args.output, args.output / "pilot-rehearsal.json"])
        with ExitStack() as stack:
            scratch = Path(stack.enter_context(tempfile.TemporaryDirectory(
                prefix="word-cards-rehearsal-", dir=ensure_scratch_root())))
            inputs = assembly.load_inputs(
                args.manifest, args.registry, args.register,
                assembly.store_path("sources", args.sources_db), assembly.store_path("vesum", args.vesum_db),
                assembly.store_path("atlas", args.atlas_db), stack, scratch,
            )
            report = run_rehearsal(inputs)
            assembly.write_host_only(args.output, {"pilot-rehearsal.json": report})
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0 if report["passed"] else 1
    except (foundation.Refusal, ValueError, KeyError, TypeError, OSError, yaml.YAMLError) as error:
        message = str(error) if isinstance(error, foundation.Refusal) else "Invalid or inaccessible rehearsal input"
        print("REFUSED: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
