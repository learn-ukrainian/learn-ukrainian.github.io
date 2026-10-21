"""Remove exactly the untracked primary-checkout files a session's audit record proves it created (#11253).

``audit-primary-checkout-dirt.py`` writes an attribution record outside the
repository whenever a shell call leaves new dirt in the protected primary
checkout. This command reads only the records of the named session and
removes a file only when every check holds:

* the record exists, parses, belongs to ``--session`` and names a primary root
  that is still a protected primary checkout;
* the entry was untracked when recorded and is untracked (not ignored, not
  tracked) now;
* its path stays below the root: relative, no ``..`` or ``.git`` component,
  and no symlinked directory on the way (opened with ``O_NOFOLLOW``);
* it is a regular file whose device, inode, size, mtime and SHA-256 still
  match the record (nobody modified it after creation);
* no record of another session claims the same file.

Everything else is refused and reported; nothing is ever removed without a
record. Tracked changes are never touched. Directories are never removed (Git
does not report empty directories, so they do not dirty the checkout).
"""

from __future__ import annotations

import argparse
import errno
import json
import os
import stat
import sys
from pathlib import Path

from scripts.guardrails import primary_dirt_audit as audit
from scripts.guardrails import worktree_containment as wc

EXIT_OK = 0
EXIT_NO_RECORD = 1
EXIT_REFUSED = 2


def _claim(root: str, entry: dict) -> tuple | None:
    fp = entry.get("fingerprint")
    if not isinstance(fp, dict):
        return None
    return (root, entry.get("path"), fp.get("dev"), fp.get("ino"), fp.get("sha256"))


def _other_session_claims(state: Path, session_id: str) -> set[tuple]:
    claims: set[tuple] = set()
    for _, record in audit.iter_records(state):
        if record.get("session_id") == session_id:
            continue
        for entry in record.get("entries") or []:
            if isinstance(entry, dict) and (claim := _claim(str(record.get("primary_root")), entry)) is not None:
                claims.add(claim)
    return claims


def _valid_primary_root(value: object) -> Path | None:
    if not isinstance(value, str) or not os.path.isabs(value):
        return None
    root = Path(value)
    try:
        if os.path.realpath(root) != value or not root.is_dir():
            return None
        if wc.resolve_main_root(root) != root or not wc.is_primary_checkout(root) or not wc.is_protected_branch(root):
            return None
    except Exception:
        return None
    return root


def _same_file(info: os.stat_result, fp: dict) -> bool:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) == (
        fp.get("dev"),
        fp.get("ino"),
        fp.get("size"),
        fp.get("mtime_ns"),
    )


def evaluate_entry(root: Path, entry: dict, other_claims: set[tuple], *, apply: bool) -> str:
    """Return the outcome for one record entry, removing the file when ``apply`` and every check holds."""
    relpath = entry.get("path")
    fp = entry.get("fingerprint")
    if entry.get("kind") != "untracked":
        return "refused:tracked_entry"
    parts = audit.split_relpath(relpath)
    if parts is None:
        return "refused:invalid_path"
    if not isinstance(fp, dict) or fp.get("kind") != "file" or not fp.get("sha256"):
        return "refused:not_a_fingerprinted_regular_file"
    if _claim(str(root), entry) in other_claims:
        return "refused:claimed_by_other_session"
    if audit.is_tracked(root, relpath):
        return "refused:tracked"
    try:
        dir_fd = audit.open_parent(root, parts)
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            return "absent"
        return "refused:symlink_or_non_directory_in_path"
    try:
        try:
            info = os.stat(parts[-1], dir_fd=dir_fd, follow_symlinks=False)
        except FileNotFoundError:
            return "absent"
        if stat.S_ISLNK(info.st_mode):
            return "refused:symlink"
        if not stat.S_ISREG(info.st_mode):
            return "refused:not_regular_file"
        if audit.status_entries(root, relpath).get(relpath) != "??":
            return "refused:not_untracked"
        current = audit.fingerprint(root, relpath)
        if not _same_file(info, fp) or current is None or current.get("sha256") != fp.get("sha256"):
            return "refused:modified_since_attribution"
        if not apply:
            return "removable"
        os.unlink(parts[-1], dir_fd=dir_fd)
        return "removed"
    finally:
        os.close(dir_fd)


def run(state: Path, session_id: str, record_ids: list[str], *, apply: bool) -> tuple[int, dict]:
    session_dir = audit.session_records_dir(state, session_id)
    records: list[tuple[Path, dict]] = []
    if session_dir.is_dir() and not session_dir.is_symlink():
        for path in sorted(session_dir.glob("*.json")):
            record = None if path.is_symlink() else audit.load_record(path)
            if record is not None and (not record_ids or record.get("record_id") in record_ids):
                records.append((path, record))
    found = {record.get("record_id") for _, record in records}
    missing = [rid for rid in record_ids if rid not in found]
    if not records or missing:
        return EXIT_NO_RECORD, {
            "session_id": session_id,
            "apply": apply,
            "error": "no_attribution_record",
            "missing_records": missing,
            "results": [],
        }

    other_claims = _other_session_claims(state, session_id)
    results: list[dict] = []
    for _, record in records:
        root = _valid_primary_root(record.get("primary_root"))
        for entry in record.get("entries") or []:
            if not isinstance(entry, dict):
                continue
            if record.get("session_id") != session_id:
                outcome = "refused:session_mismatch"
            elif root is None:
                outcome = "refused:primary_root_invalid"
            else:
                try:
                    outcome = evaluate_entry(root, entry, other_claims, apply=apply)
                except (OSError, audit.AuditError) as exc:
                    outcome = f"refused:error:{type(exc).__name__}"
            result = {
                "record_id": record.get("record_id"),
                "primary_root": record.get("primary_root"),
                "path": entry.get("path"),
                "outcome": outcome,
            }
            results.append(result)
            if apply:
                audit.append_jsonl(
                    state / "cleanup.jsonl",
                    {"event": "primary_dirt_cleanup", "session_id": session_id, "at": audit.utc_now(), **result},
                )
    refused = [r for r in results if r["outcome"].startswith("refused:")]
    return (EXIT_REFUSED if refused else EXIT_OK), {
        "session_id": session_id,
        "apply": apply,
        "results": results,
        "refused_count": len(refused),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scripts.hygiene.primary_dirt_cleanup",
        description=(
            "Remove untracked files in the protected primary checkout that an audit record proves your session "
            "created (#11253).\nUse it when audit-primary-checkout-dirt reported dirt from your own shell call; "
            "it never touches tracked files, other sessions' files or anything without a record."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.hygiene.primary_dirt_cleanup --session SESSION --record RECORD\n"
            "  .venv/bin/python -m scripts.hygiene.primary_dirt_cleanup --session SESSION --record RECORD --apply\n"
            "  .venv/bin/python -m scripts.hygiene.primary_dirt_cleanup --session SESSION   # all records, dry run\n"
            "\n"
            "Outputs: a JSON report on stdout. With --apply, removes the eligible files and appends one receipt\n"
            "per entry to $XDG_STATE_HOME/learn-ukrainian/primary-dirt-audit/cleanup.jsonl.\n"
            "\n"
            "Exit codes: 0 every entry is removable/removed/already absent; 1 no matching attribution record\n"
            "(nothing done); 2 at least one entry was refused (the rest were processed).\n"
            "\n"
            "Related: agents_extensions/shared/hooks/audit-primary-checkout-dirt.py, "
            "docs/runbooks/primary-checkout-dirt.md, issue #11253."
        ),
    )
    parser.add_argument(
        "--session",
        required=True,
        help="Session id printed in the audit message (the hook payload session_id). Required.",
    )
    parser.add_argument(
        "--record",
        action="append",
        default=[],
        help="Attribution record id printed in the audit message; repeatable. Default: every record of the session.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Remove the eligible files. Default: dry run that reports what would be removed.",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="Audit state directory. Default: $XDG_STATE_HOME/learn-ukrainian/primary-dirt-audit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    state = args.state_dir if args.state_dir is not None else audit.state_dir()
    code, report = run(state, args.session, list(args.record), apply=args.apply)
    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
