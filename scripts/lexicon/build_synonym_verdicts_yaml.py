#!/usr/bin/env python3
"""
Generate synonym pair verdicts YAML from final verdicts JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def _plain(value: str) -> str:
    return (
        value.casefold()
        .replace("\u0301", "")
        .replace("́", "")
        .replace("’", "'")
        .replace("ʼ", "'")
        .strip()
    )

def main() -> int:
    parser = argparse.ArgumentParser(description="Convert synonym verdicts JSON to YAML")
    parser.add_argument("--source", type=Path, required=True, help="Path to 4504_final_verdicts.json")
    parser.add_argument("--out", type=Path, required=True, help="Path to write synonym_pair_verdicts.yaml")
    args = parser.parse_args()

    if not args.source.exists():
        print(f"Error: source file {args.source} does not exist", file=sys.stderr)
        return 1

    try:
        with open(args.source, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: failed to parse source JSON: {e}", file=sys.stderr)
        return 1

    # Keep track of unique approved and rejected pairs
    approved_pairs = {}
    rejected_pairs = {}

    for pair in data.get("pairs", []):
        a_p = _plain(pair["a"])
        b_p = _plain(pair["b"])
        polarity = pair.get("polarity", "synonym")

        # Sort so that a <= b
        if a_p > b_p:
            a_p, b_p = b_p, a_p

        key = (a_p, b_p, polarity)
        emit = pair.get("emit", False)

        if emit:
            # Source of truth says this pair is emitted (approved)
            # Since emitted normalized pairs are unique, we just store it
            approved_pairs[key] = {
                "a": a_p,
                "b": b_p,
                "polarity": polarity,
                "sources": sorted(list(set(pair.get("attest_sources", []))))
            }
        else:
            # Rejected pair
            reason = pair.get("llm_reason") or ""
            if not isinstance(reason, str):
                reason = str(reason)
            reason_sliced = reason[:120].strip()
            # If we already have this pair, keep the first one
            if key not in rejected_pairs:
                rejected_pairs[key] = {
                    "a": a_p,
                    "b": b_p,
                    "polarity": polarity,
                    "reason": reason_sliced
                }

    # Remove any rejected pair that is also approved (i.e. overlap cleanup)
    for key in list(rejected_pairs.keys()):
        if key in approved_pairs:
            del rejected_pairs[key]

    # Convert to lists and sort deterministically by (a, b, polarity)
    approved_list = [approved_pairs[k] for k in sorted(approved_pairs.keys())]
    rejected_list = [rejected_pairs[k] for k in sorted(rejected_pairs.keys())]

    # Prepare YAML structure
    yaml_data = {
        "schema_version": 1,
        "policy": "emit = deterministically-attested AND llm-approved",
        "judged_at": "2026-07-06",
        "issue": 4504,
        "approved": approved_list,
        "rejected": rejected_list,
    }

    # Ensure output directory exists
    args.out.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Write to yaml file
        with open(args.out, "w", encoding="utf-8") as f:
            yaml.dump(yaml_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print(f"Successfully wrote {len(approved_list)} approved and {len(rejected_list)} rejected pairs to {args.out}")
    except Exception as e:
        print(f"Error: failed to write output YAML: {e}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
