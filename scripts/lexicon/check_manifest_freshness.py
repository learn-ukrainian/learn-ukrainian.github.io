#!/usr/bin/env python3
"""DB-free Word Atlas manifest freshness gate."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lexicon.manifest_fingerprint import DEFAULT_FINGERPRINT, build_fingerprint, sidecar_payload

LEXICON_PATH_PREFIX = "scripts/lexicon/"
FINGERPRINT_SIDECAR_PATH = "site/src/data/lexicon-manifest.fingerprint.json"
GIT_SCOPE_ENV_VARS = ("GIT_COMMON_DIR", "GIT_DIR", "GIT_INDEX_FILE", "GIT_PREFIX", "GIT_WORK_TREE")


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
        if not isinstance(path, str) or not isinstance(digest, str) or path in by_path:
            return None
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


def _git_env() -> dict[str, str]:
    """Return an environment that lets Git resolve the requested repository."""
    env = os.environ.copy()
    for name in GIT_SCOPE_ENV_VARS:
        env.pop(name, None)
    return env


def pr_touches_manifest_scope(*, root: Path, base_ref: str, head_ref: str = "HEAD") -> bool:
    """Return whether a PR changes lexicon code or the fingerprint sidecar."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", base_ref, head_ref, "--"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        env=_git_env(),
    )
    return any(
        path.startswith(LEXICON_PATH_PREFIX) or path == FINGERPRINT_SIDECAR_PATH
        for path in result.stdout.splitlines()
    )


def check_freshness(
    *,
    root: Path = ROOT,
    fingerprint_path: Path = DEFAULT_FINGERPRINT,
    pr_scoped: bool = False,
    base_ref: str = "origin/main",
    head_ref: str = "HEAD",
) -> int:
    current = build_fingerprint(root)
    if not fingerprint_path.exists():
        print(
            "::error::Atlas manifest freshness sidecar is missing; "
            "run `make atlas` locally and commit site/src/data/lexicon-manifest.fingerprint.json."
        )
        print("# TODO(#3150): dictionary DB/cache version drift is out of scope until CI can access #2928 data.")
        return 2

    try:
        committed = _normalized_sidecar(_load_json(fingerprint_path))
    except (json.JSONDecodeError, ValueError):
        committed = None
    if committed != sidecar_payload(current):
        if pr_scoped:
            try:
                touches_manifest_scope = pr_touches_manifest_scope(
                    root=root,
                    base_ref=base_ref,
                    head_ref=head_ref,
                )
            except subprocess.CalledProcessError as error:
                print(
                    "::error::Atlas manifest freshness could not determine PR-scoped "
                    f"changes against {base_ref!r}: {error.stderr.strip()}"
                )
                return 2
            if not touches_manifest_scope:
                print(
                    "::notice::Atlas manifest freshness sidecar differs, but this PR "
                    "does not modify lexicon code or the fingerprint sidecar "
                    f"relative to {base_ref}; "
                    "allowing unrelated drift."
                )
                return 0
        print(
            "::error::Atlas manifest stale vs lexicon code; "
            "run `make atlas` locally and commit the updated manifest + fingerprint."
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
    parser.add_argument(
        "--pr-scoped",
        action="store_true",
        help="Allow stale sidecars only when this PR did not change scripts/lexicon/.",
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Git base ref used by --pr-scoped (default: origin/main).",
    )
    parser.add_argument(
        "--head-ref",
        default="HEAD",
        help="Git head ref used by --pr-scoped (default: HEAD).",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    fingerprint = args.fingerprint
    if not fingerprint.is_absolute():
        fingerprint = root / fingerprint
    return check_freshness(
        root=root,
        fingerprint_path=fingerprint,
        pr_scoped=args.pr_scoped,
        base_ref=args.base_ref,
        head_ref=args.head_ref,
    )


if __name__ == "__main__":
    raise SystemExit(main())
