"""Prepare a verified immutable Atlas runtime before the credential-free site build."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.deploy.vendor_atlas_tree import VendorError, vendor_atlas_tree


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download and verify the configured immutable Atlas runtime for search and browse.\n"
            "Use before a pinned site build; unpinned local DB builds do not need this preparation."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Example:
  .venv/bin/python site/scripts/prepare-atlas-search.py --dest "$TMPDIR/atlas-search-runtime"

Inputs: ATLAS_TREE_ASSET_ID and ATLAS_TREE_SHA256; ATLAS_TREE_ARCHIVE_PATH may supply a local ZIP.
Outputs: verified atlas/ tree and search projection under --dest. No release or pointer changes.
Exit codes: 0 on success; 1 on verification failure; 2 on missing pin or invalid arguments.
Related: scripts/deploy/vendor_atlas_tree.py; docs/runbooks/word-atlas-static-api.md; #10453.
""",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        required=True,
        help="Private preparation directory, e.g. $TMPDIR/atlas-search-runtime (required).",
    )
    parser.add_argument(
        "--archive",
        type=Path,
        help="Local immutable runtime ZIP, e.g. ./atlas.zip (default: configured release asset).",
    )
    parser.add_argument(
        "--sha256",
        help="Expected 64-character ZIP SHA-256 (default: $ATLAS_TREE_SHA256).",
    )
    args = parser.parse_args()
    if not (args.sha256 or os.environ.get("ATLAS_TREE_SHA256", "")).strip() or not (
        args.archive
        or os.environ.get("ATLAS_TREE_ASSET_ID", "").strip()
        or os.environ.get("ATLAS_TREE_ARCHIVE_PATH", "").strip()
    ):
        parser.error("a runtime source and ATLAS_TREE_SHA256 are required")
    try:
        vendor_atlas_tree(args.dest, archive_path=args.archive, sha256=args.sha256)
    except VendorError as exc:
        print(f"Atlas search preparation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
