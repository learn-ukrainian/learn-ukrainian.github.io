#!/usr/bin/env python3
"""Cryptographic SHA-256 integrity and drift canary for published curriculum.

Maintains a deterministic inventory of all learner-facing curriculum artifacts:
- Published MDX lessons in site/src/content/docs/
- Published readings in site/src/content/readings/
- Curriculum manifest and module mapping in curriculum/l2-uk-en/
- Lesson plans in curriculum/l2-uk-en/lesson-plans/
- Module plans in curriculum/l2-uk-en/plans/
- Module prose in curriculum/l2-uk-en/**/module.md
- Vocabulary, activities, and resources datasets:
  curriculum/l2-uk-en/**/{vocabulary,activities,resources}.yaml
- Vocabulary database: curriculum/l2-uk-en/vocabulary.db

Provides an integrity and drift detection boundary for curriculum content:
any modified, added, or deleted curriculum file without a corresponding
manifest update will cause the canary gate to fail in CI Checks.

Reference: learn-ukrainian-infra-private#705
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = ROOT / "curriculum" / "l2-uk-en" / "curriculum_manifest.sha256.json"

SCHEMA_VERSION = 1
SCOPE = (
    "Learner-facing published MDX lessons and readings, curriculum lesson plans, "
    "module plans, module prose, and vocabulary/activities/resources datasets"
)

CURRICULUM_PATTERNS = (
    "site/src/content/docs/**/*.mdx",
    "site/src/content/readings/**/*.mdx",
    "curriculum/l2-uk-en/curriculum.yaml",
    "curriculum/l2-uk-en/module-mapping.json",
    "curriculum/l2-uk-en/lesson-plans/**/*.yaml",
    "curriculum/l2-uk-en/plans/**/*.yaml",
    "curriculum/l2-uk-en/**/module.md",
    "curriculum/l2-uk-en/**/vocabulary.yaml",
    "curriculum/l2-uk-en/**/activities.yaml",
    "curriculum/l2-uk-en/**/resources.yaml",
    "curriculum/l2-uk-en/vocabulary.db",
)

EXCLUDED_DIR_NAMES = frozenset(
    {
        "orchestration",
        "status",
        "audit",
        "review",
        "reviews",
        "_archive",
        ".backup",
        "stuck",
    }
)


def _sha256_bytes(data: bytes) -> str:
    """Compute hex SHA-256 digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def _is_path_included(rel_path: str) -> bool:
    """Check whether a repository-relative path should be included in the manifest.

    Matches directory segments exactly to prevent false exclusions of module slugs
    that contain substrings like 'review' (e.g. 'motion-base-review').
    """
    parts = Path(rel_path).parts
    return not any(part in EXCLUDED_DIR_NAMES for part in parts[:-1])


def collect_curriculum_files(repo_root: Path = ROOT) -> list[dict[str, str]]:
    """Scan and compute SHA-256 for all learner-facing curriculum files in deterministic order."""
    repo_root = repo_root.resolve()
    included_files: dict[str, str] = {}

    for pattern in CURRICULUM_PATTERNS:
        for file_path in repo_root.glob(pattern):
            if not file_path.is_file():
                continue
            rel_posix = file_path.relative_to(repo_root).as_posix()
            if not _is_path_included(rel_posix):
                continue
            try:
                digest = _sha256_bytes(file_path.read_bytes())
                included_files[rel_posix] = digest
            except (OSError, PermissionError) as exc:
                print(f"[curriculum_manifest_canary] Error reading {rel_posix}: {exc}", file=sys.stderr)
                raise

    sorted_entries = [
        {"path": path, "sha256": included_files[path]}
        for path in sorted(included_files.keys())
    ]
    return sorted_entries


def build_manifest_payload(repo_root: Path = ROOT) -> dict[str, Any]:
    """Build the complete deterministic manifest dictionary."""
    files = collect_curriculum_files(repo_root)
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": SCOPE,
        "files": files,
    }


def write_manifest(manifest_path: Path = DEFAULT_MANIFEST_PATH, repo_root: Path = ROOT) -> dict[str, Any]:
    """Generate and write the manifest to disk in canonical JSON format."""
    payload = build_manifest_payload(repo_root)
    manifest_path = manifest_path.resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    manifest_path.write_text(content, encoding="utf-8")
    return payload


def update_manifest_entries(
    paths: list[str | Path],
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    repo_root: Path = ROOT,
) -> dict[str, Any]:
    """Update only the specified paths in the manifest, leaving all other entries untouched."""
    manifest_path = manifest_path.resolve()
    repo_root = repo_root.resolve()
    if not manifest_path.exists():
        return write_manifest(manifest_path, repo_root)

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to parse existing manifest: {exc}") from exc

    file_dict = {
        entry["path"]: entry["sha256"]
        for entry in data.get("files", [])
        if isinstance(entry, dict) and "path" in entry and "sha256" in entry
    }

    for p in paths:
        target = Path(p)
        if not target.is_absolute():
            target = (repo_root / target).resolve()
        try:
            rel_posix = target.relative_to(repo_root).as_posix()
        except ValueError:
            continue
        if not _is_path_included(rel_posix):
            continue
        if target.is_file():
            file_dict[rel_posix] = _sha256_bytes(target.read_bytes())
        elif not target.exists() and rel_posix in file_dict:
            del file_dict[rel_posix]

    data["schema_version"] = SCHEMA_VERSION
    data["scope"] = SCOPE
    data["files"] = [{"path": path, "sha256": file_dict[path]} for path in sorted(file_dict.keys())]

    content = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    manifest_path.write_text(content, encoding="utf-8")
    return data


def verify_manifest(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    repo_root: Path = ROOT,
    allow_sparse: bool = False,
) -> dict[str, Any]:
    """Verify live filesystem state against the stored cryptographic manifest."""
    manifest_path = manifest_path.resolve()
    repo_root = repo_root.resolve()

    if not manifest_path.exists():
        if allow_sparse and not (repo_root / "curriculum" / "l2-uk-en").exists():
            return {
                "valid": True,
                "sparse_skipped": True,
                "reason": "Sparse checkout without curriculum tree; check skipped.",
            }
        return {
            "valid": False,
            "error": f"Manifest file missing at {manifest_path}. Run with --write to generate.",
        }

    try:
        stored_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "valid": False,
            "error": f"Failed to parse manifest JSON at {manifest_path}: {exc}",
        }

    if not isinstance(stored_payload, dict):
        return {
            "valid": False,
            "error": f"Malformed manifest JSON at {manifest_path}: root must be a JSON object.",
        }

    raw_files = stored_payload.get("files")
    if not isinstance(raw_files, list):
        return {
            "valid": False,
            "error": f"Malformed manifest JSON at {manifest_path}: 'files' field must be a list.",
        }

    stored_files: dict[str, str] = {}
    for idx, item in enumerate(raw_files):
        if not isinstance(item, dict) or "path" not in item or "sha256" not in item:
            return {
                "valid": False,
                "error": f"Malformed manifest entry at index {idx} in {manifest_path}: missing required 'path' or 'sha256' field.",
            }
        stored_files[item["path"]] = item["sha256"]

    live_entries = collect_curriculum_files(repo_root)
    live_files: dict[str, str] = {f["path"]: f["sha256"] for f in live_entries}

    if allow_sparse and len(live_files) == 0 and len(stored_files) > 0:
        return {
            "valid": True,
            "sparse_skipped": True,
            "reason": "Sparse checkout detected (zero curriculum files present); check skipped.",
        }

    modified: list[dict[str, str]] = []
    added: list[str] = []
    deleted: list[str] = []

    for path, live_hash in live_files.items():
        if path not in stored_files:
            added.append(path)
        elif stored_files[path] != live_hash:
            modified.append({
                "path": path,
                "expected": stored_files[path],
                "actual": live_hash,
            })

    for path in stored_files:
        if path not in live_files:
            deleted.append(path)

    is_valid = (len(modified) == 0 and len(added) == 0 and len(deleted) == 0)

    return {
        "valid": is_valid,
        "total_files": len(live_files),
        "expected_files": len(stored_files),
        "modified": modified,
        "added": added,
        "deleted": deleted,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cryptographic SHA-256 integrity and drift canary for curriculum files."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--check",
        action="store_true",
        help="Verify on-disk curriculum files against the cryptographic manifest (default).",
    )
    group.add_argument(
        "--write",
        action="store_true",
        help="Compute hashes and write updated manifest to disk.",
    )
    group.add_argument(
        "--update",
        nargs="+",
        metavar="PATH",
        help="Update SHA-256 hashes for only the specified changed files in the manifest.",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help=f"Path to manifest JSON file (default: {DEFAULT_MANIFEST_PATH}).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help=f"Repository root directory (default: {ROOT}).",
    )
    parser.add_argument(
        "--allow-sparse",
        action="store_true",
        help="Allow check to pass if running in a sparse worktree lacking curriculum files.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output check result in JSON format.",
    )

    args = parser.parse_args(argv)

    if args.write:
        payload = write_manifest(args.manifest_path, args.repo_root)
        print(
            f"[curriculum_manifest_canary] Manifest written successfully: {len(payload['files'])} files"
        )
        return 0

    if args.update:
        payload = update_manifest_entries(args.update, args.manifest_path, args.repo_root)
        print(
            f"[curriculum_manifest_canary] Manifest updated for {len(args.update)} path(s) successfully"
        )
        return 0

    result = verify_manifest(args.manifest_path, args.repo_root, allow_sparse=args.allow_sparse)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result.get("valid") else 1

    if result.get("sparse_skipped"):
        print(f"[curriculum_manifest_canary] {result['reason']}")
        return 0

    if not result.get("valid"):
        print("[curriculum_manifest_canary] ❌ DRIFT DETECTED IN CURRICULUM MANIFEST CANARY!", file=sys.stderr)
        if "error" in result:
            print(f"  Error: {result['error']}", file=sys.stderr)
        if result.get("modified"):
            print(f"  Modified files ({len(result['modified'])}):", file=sys.stderr)
            for m in result["modified"]:
                print(f"    - {m['path']} (expected: {m['expected'][:12]}..., actual: {m['actual'][:12]}...)", file=sys.stderr)
        if result.get("added"):
            print(f"  Uncommitted/untracked new files ({len(result['added'])}):", file=sys.stderr)
            for a in result["added"]:
                print(f"    + {a}", file=sys.stderr)
        if result.get("deleted"):
            print(f"  Missing files ({len(result['deleted'])}):", file=sys.stderr)
            for d in result["deleted"]:
                print(f"    - {d}", file=sys.stderr)
        print(
            "\n  Run '.venv/bin/python scripts/audit/curriculum_manifest_canary.py --write' to regenerate manifest "
            "after authorized content changes with cross-family review approval.",
            file=sys.stderr,
        )
        return 1

    print(
        f"[curriculum_manifest_canary] ✓ All {result['total_files']} curriculum files match cryptographic manifest"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
