#!/usr/bin/env python3
"""DB-free Word Atlas manifest freshness gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lexicon.manifest_fingerprint import DEFAULT_FINGERPRINT, build_fingerprint, sidecar_payload

FINGERPRINT_REFRESH_COMMAND = "python -m scripts.lexicon.manifest_fingerprint --write"


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    """Build a JSON object while refusing ambiguous duplicate keys."""
    payload: dict = {}
    for key, value in pairs:
        if key in payload:
            raise ValueError(f"duplicate JSON key: {key}")
        payload[key] = value
    return payload


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)


def _normalized_sidecar(payload: object) -> dict | None:
    """Validate and canonicalize a sidecar without requiring its line order.

    ``merge=union`` may retain concurrently added records in a different order.
    The gate therefore compares the complete path-to-digest mapping while still
    rejecting duplicate or malformed records rather than silently accepting a
    conflicted merge result.
    """
    if not isinstance(payload, dict):
        return None
    if set(payload) != {"schema_version", "scope", "inputs"}:
        return None
    inputs = payload.get("inputs")
    if not isinstance(inputs, dict) or set(inputs) != {"lexicon_code"}:
        return None
    records = inputs["lexicon_code"]
    if not isinstance(records, list):
        return None

    by_path: dict[str, str] = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
            return None
        path = record["path"]
        digest = record["sha256"]
        if not isinstance(path, str) or not isinstance(digest, str):
            return None
        previous_digest = by_path.get(path)
        if previous_digest is not None:
            # Git's union driver may retain an unchanged record from both
            # parents.  Identical records carry the same source-of-truth
            # assertion, so collapse them.  Different hashes for one path
            # remain an ambiguous concurrent edit and must fail closed.
            if previous_digest != digest:
                return None
            continue
        by_path[path] = digest

    return {
        "schema_version": payload["schema_version"],
        "scope": payload["scope"],
        "inputs": {
            "lexicon_code": [
                {"path": path, "sha256": by_path[path]}
                for path in sorted(by_path)
            ],
        },
    }


def check_freshness(
    *,
    root: Path = ROOT,
    fingerprint_path: Path = DEFAULT_FINGERPRINT,
) -> int:
    current = build_fingerprint(root)
    if not fingerprint_path.exists():
        print(
            "::error::Atlas manifest freshness sidecar is missing; "
            f"run `{FINGERPRINT_REFRESH_COMMAND}` locally and commit "
            "site/src/data/lexicon-manifest.fingerprint.json. "
            "Use `make atlas` when the Atlas manifest content itself changed."
        )
        print("# TODO(#3150): dictionary DB/cache version drift is out of scope until CI can access #2928 data.")
        return 2

    try:
        committed = _normalized_sidecar(_load_json(fingerprint_path))
    except (json.JSONDecodeError, ValueError):
        committed = None
    if committed != sidecar_payload(current):
        print(
            "::error::Atlas manifest stale vs lexicon code (fingerprint sidecar); "
            f"run `{FINGERPRINT_REFRESH_COMMAND}` locally and commit the updated sidecar. "
            "Use `make atlas` when the Atlas manifest content itself changed."
        )
        print("committed: <invalid or stale sidecar>")
        print(f"current:   {current['fingerprint']}")
        print("# TODO(#3150): dictionary DB/cache version drift is out of scope until CI can access #2928 data.")
        return 2

    stats = current["stats"]
    print(
        "Atlas manifest freshness OK: "
        f"{stats['lexicon_code_files']} lexicon code files."
    )
    print("# TODO(#3150): dictionary DB/cache version drift is out of scope until CI can access #2928 data.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check DB-free Atlas manifest freshness.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root.")
    parser.add_argument(
        "--fingerprint",
        type=Path,
        default=DEFAULT_FINGERPRINT,
        help="Committed fingerprint sidecar.",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    fingerprint = args.fingerprint
    if not fingerprint.is_absolute():
        fingerprint = root / fingerprint
    return check_freshness(
        root=root,
        fingerprint_path=fingerprint,
    )


if __name__ == "__main__":
    raise SystemExit(main())
