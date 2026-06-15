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

from scripts.lexicon.manifest_fingerprint import DEFAULT_FINGERPRINT, build_fingerprint


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_freshness(
    *,
    root: Path = ROOT,
    fingerprint_path: Path = DEFAULT_FINGERPRINT,
) -> int:
    current = build_fingerprint(root)
    if not fingerprint_path.exists():
        print(
            "::error::Atlas manifest freshness sidecar is missing; "
            "run `make atlas` locally and commit site/src/data/lexicon-manifest.fingerprint.json."
        )
        print("# TODO(#3150): dictionary DB/cache version drift is out of scope until CI can access #2928 data.")
        return 2

    committed = _load_json(fingerprint_path)
    if committed.get("fingerprint") != current["fingerprint"]:
        print(
            "::error::Atlas manifest stale vs lexicon code; "
            "run `make atlas` locally and commit the updated manifest + fingerprint."
        )
        print(f"committed: {committed.get('fingerprint', '<missing>')}")
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
    return check_freshness(root=root, fingerprint_path=fingerprint)


if __name__ == "__main__":
    raise SystemExit(main())
