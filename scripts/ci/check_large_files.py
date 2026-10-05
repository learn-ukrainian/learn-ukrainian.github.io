"""Guard repository against untracked large blobs over 5 MB.

Use in CI checks and merge queue; do not use for historical scanning or working-tree file discovery.
"""

from __future__ import annotations

import argparse
import csv
import io
import string
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

THRESHOLD_BYTES = 5 * 1024 * 1024  # 5,242,880 bytes (5 MB)
DEFAULT_ALLOWLIST = "scripts/ci/large_files_allowlist.txt"
_HEX_DIGITS = set(string.hexdigits)


@dataclass(frozen=True)
class AllowlistEntry:
    path: str
    size: int
    reason: str


def load_allowlist(allowlist_path: Path) -> dict[str, AllowlistEntry]:
    """Load and validate the large files allowlist."""
    if not allowlist_path.exists():
        raise FileNotFoundError(f"Allowlist file not found: {allowlist_path}")
    entries: dict[str, AllowlistEntry] = {}
    for line_num, raw in enumerate(allowlist_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.rstrip("\r\n")
        if not line.strip() or line.strip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            raise ValueError(f"Malformed allowlist entry at {allowlist_path}:{line_num}: {line!r}")
        path, size_str, reason = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if not path or not reason:
            raise ValueError(f"Empty path or reason in allowlist at {allowlist_path}:{line_num}: {line!r}")
        try:
            size = int(size_str)
            if size <= 0:
                raise ValueError
        except ValueError:
            raise ValueError(f"Invalid size in allowlist at {allowlist_path}:{line_num}: {size_str!r}") from None
        entries[path] = AllowlistEntry(path=path, size=size, reason=reason)
    return entries


def _run_git(args: list[str], cwd: Path, timeout: int = 30) -> bytes:
    res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=False, timeout=timeout)
    if res.returncode != 0:
        err = res.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Git command failed ({' '.join(args)}): {err}")
    return res.stdout


def _is_valid_object_id(oid: str) -> bool:
    return len(oid) in (40, 64) and set(oid).issubset(_HEX_DIGITS)


def batch_check_blob_sizes(shas: list[str], cwd: Path, timeout: int = 30) -> dict[str, int]:
    """Query blob sizes for object SHAs using a single git cat-file --batch-check process."""
    if not shas:
        return {}
    for sha in shas:
        if not _is_valid_object_id(sha):
            raise RuntimeError(f"Invalid object ID: {sha!r}")

    input_data = "".join(f"{sha}\n" for sha in shas).encode("ascii")
    res = subprocess.run(
        ["git", "cat-file", "--batch-check"],
        input=input_data,
        cwd=cwd,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    if res.returncode != 0:
        err = res.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Git cat-file --batch-check failed: {err}")

    lines = res.stdout.decode("utf-8", errors="replace").splitlines()
    if len(lines) != len(shas):
        raise RuntimeError(
            f"git cat-file --batch-check response count mismatch: expected {len(shas)}, got {len(lines)}"
        )

    sizes: dict[str, int] = {}
    for expected_sha, line in zip(shas, lines, strict=True):
        parts = line.split()
        if len(parts) == 2 and parts[1] == "missing":
            raise RuntimeError(f"Git object missing in batch-check: {expected_sha}")
        if len(parts) != 3:
            raise RuntimeError(f"Malformed git cat-file --batch-check output for {expected_sha}: {line!r}")
        obj_name, obj_type, size_str = parts
        if obj_name != expected_sha:
            raise RuntimeError(f"Mismatched batch-check response object: expected {expected_sha}, got {obj_name}")
        if obj_type != "blob":
            raise RuntimeError(f"Expected blob object type for {expected_sha}, got {obj_type!r}")
        try:
            size = int(size_str)
            if size < 0:
                raise ValueError
        except ValueError:
            raise RuntimeError(f"Invalid blob size {size_str!r} for object {expected_sha}") from None
        sizes[expected_sha] = size
    return sizes


def resolve_commit(ref: str, cwd: Path) -> str:
    """Resolve a reference to a commit SHA."""
    try:
        sha = _run_git(["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], cwd=cwd).decode().strip()
        if not sha:
            raise RuntimeError(f"Cannot resolve {ref!r} to a commit")
        return sha
    except Exception as exc:
        raise RuntimeError(f"Cannot resolve base ref {ref!r} to a commit") from exc


def get_merge_base(base_commit: str, head_commit: str, cwd: Path) -> str:
    """Find the merge base between base and head."""
    try:
        mb = _run_git(["merge-base", base_commit, head_commit], cwd=cwd).decode().strip()
        if not mb:
            raise RuntimeError(f"No merge base found between {base_commit} and {head_commit}")
        return mb
    except Exception as exc:
        raise RuntimeError(f"Cannot find merge base between base commit {base_commit} and HEAD") from exc


def check_changed_vs_base(
    base_ref: str,
    allowlist_path: Path,
    repo_root: Path,
    threshold: int = THRESHOLD_BYTES,
) -> list[tuple[str, int]]:
    """Compare blobs added or modified between merge-base of base_ref and HEAD."""
    base_commit = resolve_commit(base_ref, cwd=repo_root)
    merge_base = get_merge_base(base_commit, "HEAD", cwd=repo_root)
    allowlist = load_allowlist(allowlist_path)

    raw_diff = _run_git(["diff", "--raw", "-z", "--no-renames", "--abbrev=40", merge_base, "HEAD"], cwd=repo_root)
    if not raw_diff:
        return []
    tokens = raw_diff.split(b"\0")
    if tokens and tokens[-1] == b"":
        tokens.pop()
    if len(tokens) % 2 != 0:
        raise RuntimeError("Corrupted git diff output: odd token count.")

    items_to_check: list[tuple[str, str]] = []
    for i in range(0, len(tokens), 2):
        meta, path_bytes = tokens[i], tokens[i + 1]
        path = path_bytes.decode("utf-8", errors="surrogateescape")
        parts = (meta[1:] if meta.startswith(b":") else meta).split()
        if len(parts) != 5:
            raise RuntimeError(f"Unexpected git diff meta token: {meta!r}")
        _src_mode, dst_mode, _src_sha, dst_sha, status = parts
        dst_mode_str, dst_sha_str, status_str = dst_mode.decode(), dst_sha.decode(), status.decode()
        if status_str == "D" or dst_mode_str in ("000000", "160000") or dst_sha_str.startswith("0000000"):
            continue
        items_to_check.append((path, dst_sha_str))

    if not items_to_check:
        return []

    unique_shas = list(dict.fromkeys(sha for _, sha in items_to_check))
    sizes_by_sha = batch_check_blob_sizes(unique_shas, cwd=repo_root)

    violations: list[tuple[str, int]] = []
    for path, sha in items_to_check:
        size = sizes_by_sha[sha]
        if size > threshold and path not in allowlist:
            violations.append((path, size))
    return violations


def parse_classification_table(tsv_content: str) -> dict[str, str]:
    """Parse registry/artifacts/classification-v1.tsv content into {path: class}."""
    if not tsv_content.strip():
        raise ValueError("Classification table content is empty")

    reader = csv.DictReader(io.StringIO(tsv_content), delimiter="\t")
    if reader.fieldnames is None:
        raise ValueError("Malformed classification table: missing header line")

    fieldnames = [f.strip() for f in reader.fieldnames if f is not None]
    if "path" not in fieldnames:
        raise ValueError("Classification table missing required 'path' column")
    if "class" not in fieldnames:
        raise ValueError("Classification table missing required 'class' column")
    if fieldnames.count("path") > 1 or fieldnames.count("class") > 1:
        raise ValueError("Classification table has duplicate 'path' or 'class' column")

    classes: dict[str, str] = {}
    valid_classes = {"A", "K", "S"}

    for row_num, row in enumerate(reader, start=2):
        if None in row or any(v is None for v in row.values()):
            raise ValueError(f"Malformed row {row_num} in classification table: column count mismatch")
        raw_path = row.get("path")
        raw_cls = row.get("class")
        if raw_path is None or raw_cls is None:
            raise ValueError(f"Malformed row {row_num} in classification table")
        path = raw_path.strip()
        cls = raw_cls.strip()
        if not path or not cls:
            raise ValueError(f"Empty path or class at row {row_num} in classification table")
        if cls not in valid_classes:
            raise ValueError(f"Unsupported class code {cls!r} at row {row_num} for path {path!r}")
        if path in classes:
            raise ValueError(f"Duplicate path classification for {path!r} at row {row_num}")
        classes[path] = cls

    return classes


def seed_allowlist(
    seed_ref: str,
    allowlist_path: Path,
    repo_root: Path,
    threshold: int = THRESHOLD_BYTES,
) -> list[AllowlistEntry]:
    """Seed allowlist from origin/main tree."""
    seed_commit = resolve_commit(seed_ref, cwd=repo_root)

    try:
        tsv_bytes = _run_git(["show", f"{seed_commit}:registry/artifacts/classification-v1.tsv"], cwd=repo_root)
        tsv_content = tsv_bytes.decode("utf-8")
        classification_table = parse_classification_table(tsv_content)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to read or parse classification table at {seed_commit}:registry/artifacts/classification-v1.tsv: {exc}"
        ) from exc

    out = _run_git(["ls-tree", "-r", "-l", "-z", seed_commit], cwd=repo_root)
    qualifying: list[tuple[str, int]] = []
    for entry in [e for e in out.split(b"\0") if e]:
        meta, path_raw = entry.split(b"\t", 1)
        parts = meta.split()
        if parts[1].decode() == "blob" and parts[3].decode() != "-":
            size = int(parts[3].decode())
            if size > threshold:
                qualifying.append((path_raw.decode("utf-8", errors="surrogateescape"), size))
    if len(qualifying) > 200:
        raise RuntimeError(f"Seed allowlist discovered {len(qualifying)} qualifying paths, exceeding 200 ceiling.")
    qualifying.sort(key=lambda x: x[0])
    entries: list[AllowlistEntry] = []
    for path, size in qualifying:
        if path.startswith("data/"):
            cls = classification_table.get(path)
            if cls == "A":
                reason = "existing tracked data; leaves git through the data/ split"
            elif cls == "K":
                reason = "existing tracked data; kept in git as class K under the data/ split"
            elif cls == "S":
                reason = "existing tracked data; class S placeholder/control under the data/ split (not class A)"
            else:
                reason = "existing tracked data; absent from classification-v1.tsv; no split migration established"
        elif path.startswith("registry/"):
            reason = "existing tracked data; kept in git as class K under the data/ split"
        elif path.startswith("site/src/data/"):
            reason = "existing tracked data; grandfathered site-input"
        elif "_archive" in path:
            reason = "existing tracked data; archived session record"
        else:
            reason = "existing tracked file, no migration planned"
        entries.append(AllowlistEntry(path=path, size=size, reason=reason))

    lines = ["# Large files allowlist", "# Format: <repository-relative-path> <tab> <size-in-bytes> <tab> <reason>"]
    lines.extend(f"{e.path}\t{e.size}\t{e.reason}" for e in entries)
    lines.append("")
    allowlist_path.parent.mkdir(parents=True, exist_ok=True)
    allowlist_path.write_text("\n".join(lines), encoding="utf-8")
    return entries


def build_parser() -> argparse.ArgumentParser:
    desc = (
        "Guard repository against untracked large blobs over 5 MB.\n"
        "Use in CI checks and merge queue; do not use for historical scanning or working-tree file discovery."
    )
    epilog = (
        "Examples:\n"
        "  .venv/bin/python scripts/ci/check_large_files.py --changed-vs-base origin/main\n"
        "  .venv/bin/python scripts/ci/check_large_files.py --seed-allowlist\n\n"
        "Outputs:\n"
        "  None during verification; updates scripts/ci/large_files_allowlist.txt when seeding.\n\n"
        "Exit codes:\n"
        "  0 = all checked blobs pass or are within threshold\n"
        "  1 = oversized unallowlisted blob, Git error, or missing ref\n"
        "  2 = invalid CLI arguments\n\n"
        "Related:\n"
        "  Issue #8510, scripts/storage/artifacts.py, docs/runbooks/bulk-artifacts.md."
    )
    p = argparse.ArgumentParser(description=desc, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--changed-vs-base", metavar="REF", help="Git ref to compute merge-base against HEAD.")
    g.add_argument("--seed-allowlist", action="store_true", help="Seed allowlist file from blobs in seed-ref tree.")
    p.add_argument(
        "--allowlist", type=Path, default=None, help=f"Path to allowlist file (default: {DEFAULT_ALLOWLIST})."
    )
    p.add_argument(
        "--threshold",
        type=int,
        default=THRESHOLD_BYTES,
        help=f"Threshold bytes (default: {THRESHOLD_BYTES} bytes, 5 MB).",
    )
    p.add_argument("--seed-ref", default="origin/main", help="Git ref to seed allowlist from (default: origin/main).")
    p.add_argument(
        "--repo-root", type=Path, default=None, help="Root path of Git repository (default: current directory)."
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root or Path.cwd()
    allowlist_path = args.allowlist or (repo_root / DEFAULT_ALLOWLIST)
    try:
        if args.seed_allowlist:
            seeded = seed_allowlist(args.seed_ref, allowlist_path, repo_root, args.threshold)
            print(
                f"Seeded {len(seeded)} entries ({sum(e.size for e in seeded)} bytes) to {allowlist_path} from {args.seed_ref}."
            )
            return 0
        violations = check_changed_vs_base(args.changed_vs_base, allowlist_path, repo_root, args.threshold)
        if violations:
            print(
                f"ERROR: Large file guard violation: {len(violations)} blob(s) exceed {args.threshold} bytes (5 MB):",
                file=sys.stderr,
            )
            for path, size in violations:
                print(f"  File: {path!r}\n  Size: {size} bytes (threshold: {args.threshold} bytes)", file=sys.stderr)
            print(
                "\nNewly added or modified blobs over 5242880 bytes cannot be tracked directly in Git.\n"
                "How to proceed:\n"
                "  1. Move the large file behind artifact storage using 'scripts/storage/artifacts.py'.\n"
                "  2. If the file must remain tracked in Git, add an entry to 'scripts/ci/large_files_allowlist.txt'\n"
                "     with the exact path, size in bytes, and an explicit reason.",
                file=sys.stderr,
            )
            return 1
        print(
            f"Large files check passed: no unallowlisted blobs over {args.threshold} bytes vs base '{args.changed_vs_base}'."
        )
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
