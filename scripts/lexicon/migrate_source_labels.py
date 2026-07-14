#!/usr/bin/env python3
"""Remap learner-facing Atlas source labels away from mirror aggregators (#5163).

Targeted manifest migration: rewrites already-hydrated ``lexicon-manifest.json``
source strings and URLs to academic attribution without running full enrich.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_FINGERPRINT = ROOT / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lexicon import enrich_manifest
from scripts.lexicon.source_attribution import apply_entry_attribution, learner_facing_mirror_violations


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _refresh_manifest_fingerprint(manifest: dict[str, Any], fingerprint_path: Path) -> None:
    fingerprint_payload = enrich_manifest.write_fingerprint(fingerprint_path, root=ROOT)
    manifest["manifest_fingerprint"] = {
        "schema_version": fingerprint_payload["schema_version"],
        "fingerprint": fingerprint_payload["fingerprint"],
    }


def migrate_manifest(manifest: dict[str, Any]) -> tuple[int, int]:
    changed_entries = 0
    remaining = 0
    for entry in manifest.get("entries", []):
        if not isinstance(entry, dict):
            continue
        before = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        apply_entry_attribution(entry)
        after = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        if before != after:
            changed_entries += 1
        if learner_facing_mirror_violations(entry):
            remaining += 1
    return changed_entries, remaining


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate Atlas source labels to academic attribution (#5163).")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--fingerprint", type=Path, default=DEFAULT_FINGERPRINT)
    parser.add_argument("--write", action="store_true", help="Write the migrated manifest and refresh fingerprint.")
    args = parser.parse_args(argv)

    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    fingerprint_path = args.fingerprint if args.fingerprint.is_absolute() else ROOT / args.fingerprint
    manifest = _load_json(manifest_path)
    changed, remaining = migrate_manifest(manifest)
    print(f"migrated {changed} entries with learner-facing source label/url updates")
    print(f"remaining mirror-attribution violations: {remaining}")
    if args.write:
        _refresh_manifest_fingerprint(manifest, fingerprint_path)
        _write_json(manifest_path, manifest)
        print(f"wrote {manifest_path}")
        print(f"refreshed {fingerprint_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
