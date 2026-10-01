#!/usr/bin/env python3
"""Offline local TruffleHog scan with safe fixed flags and redacted console output.

Runbook: docs/runbooks/secret-scanning.md (#9416).

Safety properties, each covered by tests/audit/test_secret_scan_local.py:

* verification is never enabled: ``--no-verification`` is always passed and any
  verification-style option on the wrapper's command line is refused;
* the full TruffleHog JSON (which carries raw secret values) goes only to a new
  owner-only (0600) file outside the repository; TruffleHog's own stderr goes to
  a sibling owner-only log, never to the console;
* the console shows counts per detector and rows of detector, file, short commit
  and line, nothing else from a finding;
* ``history`` scans a full bare mirror built in a temporary directory outside the
  repository and removes it afterwards.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2

TRUFFLEHOG = "trufflehog"
IGNORE_FILE = ".trufflehogignore"
DEFAULT_TIMEOUT_SECONDS = 3600
DEFAULT_MAX_ROWS = 200
GIT_TIMEOUT_SECONDS = 60
# Bytes of path arguments per ``trufflehog filesystem`` call; well under ARG_MAX.
TREE_BATCH_BYTES = 100_000

# Fixed for every scan. Offline TruffleHog marks every candidate "unverified", so
# CI's ``--results=verified,unknown`` would hide everything; ``unverified`` is the
# offline superset of what CI reports. ``--no-update`` keeps the run offline.
SAFE_FLAGS: tuple[str, ...] = (
    "--json",
    "--no-verification",
    "--no-update",
    "--results=unverified",
    "--exclude-detectors=Lob",
    "--fail-on-scan-errors",
)
FORBIDDEN_FLAG_MARKERS: tuple[str, ...] = ("verif", "--results")

# Never handed to the filesystem scan, whatever .gitignore says.
DENIED_DIR_PARTS = frozenset({".git", ".venv", "node_modules", ".worktrees"})
DATABASE_SUFFIXES = (".db", ".sqlite", ".sqlite3", ".duckdb", ".db-wal", ".db-shm", ".db-journal")


class ScanError(Exception):
    """A refusal or tool failure; the message is safe to print."""


@dataclass(frozen=True)
class Finding:
    detector: str
    file: str
    commit: str
    line: str


def refuse_verification_options(argv: Sequence[str]) -> None:
    """Reject any option that could turn verification on or widen result types."""
    for token in argv:
        name = token.split("=", 1)[0].lower()
        if name.startswith("-") and any(marker in name for marker in FORBIDDEN_FLAG_MARKERS):
            raise ScanError(
                f"refused option {name!r}: verified mode sends candidate secrets "
                "to provider APIs and needs an operator decision; this wrapper is offline only"
            )


def assert_safe_command(cmd: Sequence[str]) -> None:
    """Last check before TruffleHog runs: offline flags present, no verifier options."""
    options = list(cmd[: cmd.index("--")] if "--" in cmd else cmd)
    missing = [flag for flag in SAFE_FLAGS if flag not in options]
    if missing:
        raise ScanError(f"internal error: unsafe TruffleHog command, missing {missing}")
    refuse_verification_options([part for part in options if part not in {"--no-verification", "--results=unverified"}])


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_SECONDS,
        check=False,
    )
    if result.returncode != 0:
        raise ScanError(f"git {args[0]} failed (exit {result.returncode})")
    return result.stdout


def work_tree_top(repo: Path) -> Path:
    return Path(_git(repo, "rev-parse", "--show-toplevel").strip()).resolve()


def protected_roots(top: Path) -> list[Path]:
    """The scanned work tree, its primary checkout, and this script's checkout."""
    common = Path(_git(top, "rev-parse", "--path-format=absolute", "--git-common-dir").strip())
    return sorted({top, common.resolve().parent, PROJECT_ROOT})


def _is_inside(path: Path, roots: Iterable[Path]) -> bool:
    resolved = path.resolve()
    return any(resolved == root or resolved.is_relative_to(root) for root in roots)


def _open_private(path: Path) -> int:
    """Create a new owner-only file; never follow a symlink or reuse a file."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise ScanError("output path already exists; choose a new file") from exc
    except OSError as exc:
        raise ScanError(f"cannot create output file ({exc.strerror})") from exc
    os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
    return fd


def open_outputs(output: Path | None, mode: str, roots: Sequence[Path]) -> tuple[Path, int, Path, int]:
    """Open the JSON report and TruffleHog log, both 0600 and outside the repository."""
    if output is None:
        fd, name = tempfile.mkstemp(prefix=f"secret-scan-{mode}-", suffix=".jsonl")
        output = Path(name)
        if _is_inside(output, roots):
            os.close(fd)
            output.unlink()
            raise ScanError("the system temp directory is inside the repository; pass --output")
        os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
    else:
        if _is_inside(output, roots):
            raise ScanError("refused --output inside the repository: raw secrets must stay outside it")
        fd = _open_private(output)
    log = output.with_name(output.name + ".log")
    try:
        log_fd = _open_private(log)
    except ScanError:
        os.close(fd)
        raise
    return output, fd, log, log_fd


def _denied(rel: str) -> bool:
    parts = rel.split("/")
    if DENIED_DIR_PARTS.intersection(parts[:-1]) or parts[-1] in DENIED_DIR_PARTS:
        return True
    return parts[0] == "data" and rel.lower().endswith(DATABASE_SUFFIXES)


def tree_candidates(repo: Path) -> list[str]:
    """Tracked plus untracked-not-ignored regular files, minus the denied areas."""
    listing = _git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    seen: set[str] = set()
    files: list[str] = []
    for rel in listing.split("\0"):
        if not rel or rel in seen or _denied(rel):
            continue
        seen.add(rel)
        try:
            info = (repo / rel).lstat()
        except FileNotFoundError:
            continue  # deleted or outside a sparse checkout
        if stat.S_ISREG(info.st_mode):
            files.append(rel)
    return files


def batches(paths: Sequence[str], budget: int = TREE_BATCH_BYTES) -> list[list[str]]:
    out: list[list[str]] = []
    current: list[str] = []
    size = 0
    for path in paths:
        cost = len(path.encode()) + 1
        if current and size + cost > budget:
            out.append(current)
            current, size = [], 0
        current.append(path)
        size += cost
    if current:
        out.append(current)
    return out


def _run_trufflehog(cmd: list[str], cwd: Path, out_fd: int, log_fd: int, timeout: int) -> None:
    assert_safe_command(cmd)
    try:
        result = subprocess.run(cmd, cwd=cwd, stdout=out_fd, stderr=log_fd, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ScanError(f"trufflehog timed out after {timeout}s") from exc
    if result.returncode != 0:
        raise ScanError(f"trufflehog exited {result.returncode} (scan error)")


def _exclude_args(repo: Path) -> list[str]:
    ignore = repo / IGNORE_FILE
    return [f"--exclude-paths={ignore}"] if ignore.is_file() else []


def scan_tree(binary: str, repo: Path, out_fd: int, log_fd: int, timeout: int) -> int:
    files = tree_candidates(repo)
    for chunk in batches(files):
        cmd = [binary, "filesystem", *SAFE_FLAGS, *_exclude_args(repo), "--", *chunk]
        _run_trufflehog(cmd, repo, out_fd, log_fd, timeout)
    return len(files)


def scan_history(
    binary: str,
    repo: Path,
    remote: str,
    mirror_parent: Path | None,
    roots: Sequence[Path],
    out_fd: int,
    log_fd: int,
    timeout: int,
) -> None:
    url = _git(repo, "remote", "get-url", remote).strip()
    parent = mirror_parent if mirror_parent is not None else Path(tempfile.gettempdir())
    if _is_inside(parent, roots):
        raise ScanError("refused mirror directory inside the repository")
    try:
        workdir = Path(tempfile.mkdtemp(prefix="secret-scan-mirror-", dir=parent))
    except OSError as exc:
        raise ScanError(f"cannot create the mirror directory ({exc.strerror})") from exc
    try:
        mirror = workdir / "mirror.git"
        env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        try:
            # Public remote: no credential helper may contribute a token.
            clone = subprocess.run(
                ["git", "-c", "credential.helper=", "clone", "--quiet", "--mirror", url, str(mirror)],
                stdout=subprocess.DEVNULL,
                stderr=log_fd,
                env=env,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ScanError(f"mirror clone timed out after {timeout}s") from exc
        if clone.returncode != 0:
            raise ScanError(f"mirror clone of remote {remote!r} failed (exit {clone.returncode})")
        cmd = [binary, "git", f"file://{mirror}", "--bare", *SAFE_FLAGS, *_exclude_args(repo)]
        _run_trufflehog(cmd, workdir, out_fd, log_fd, timeout)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def read_findings(output: Path) -> list[Finding]:
    """Parse the JSON report keeping only non-secret location fields."""
    findings: list[Finding] = []
    with output.open(encoding="utf-8") as fh:
        for number, raw_line in enumerate(fh, start=1):
            if not raw_line.strip():
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                # Never echo the line: it may hold a secret.
                raise ScanError(f"unparseable JSON at report line {number}") from exc
            data = (record.get("SourceMetadata") or {}).get("Data") or {}
            location = next(iter(data.values()), {}) if isinstance(data, dict) and data else {}
            if not isinstance(location, dict):
                location = {}
            findings.append(
                Finding(
                    detector=str(record.get("DetectorName") or "unknown"),
                    file=str(location.get("file") or "-"),
                    commit=str(location.get("commit") or "-")[:10],
                    line=str(location.get("line") if location.get("line") is not None else "-"),
                )
            )
    return findings


def render(findings: Sequence[Finding], max_rows: int) -> list[str]:
    lines = [f"findings: {len(findings)}"]
    for detector, count in sorted(Counter(f.detector for f in findings).items()):
        lines.append(f"  {detector}: {count}")
    rows = sorted(set(findings), key=lambda f: (f.detector, f.file, f.commit, f.line))
    if rows:
        lines.append("detector\tfile\tcommit\tline")
        lines.extend(f"{f.detector}\t{f.file}\t{f.commit}\t{f.line}" for f in rows[:max_rows])
        if len(rows) > max_rows:
            lines.append(f"... {len(rows) - max_rows} more rows in the JSON report")
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="secret_scan_local.py",
        description=(
            "Run the locally installed TruffleHog offline (no verification) over the working tree or\n"
            "the full public history, printing only counts and detector/file/commit/line rows.\n"
            "Use before a PR that changes credential, identity, transport or hook code and after a\n"
            "suspected leak. Not a CI replacement (CI scans every pushed range) and never verified mode."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/audit/secret_scan_local.py tree\n"
            "  .venv/bin/python scripts/audit/secret_scan_local.py history\n"
            "  .venv/bin/python scripts/audit/secret_scan_local.py --output /tmp/scan.jsonl tree\n"
            "\n"
            "Fixed TruffleHog flags: " + " ".join(SAFE_FLAGS) + "\n"
            "  plus --exclude-paths=.trufflehogignore when the file exists.\n"
            "\n"
            "Outputs:\n"
            "  Full JSON Lines report (contains RAW secret values) in a new 0600 file outside the\n"
            "  repository, default under the system temp directory; TruffleHog's log beside it\n"
            "  as <report>.log (0600). Never paste either anywhere. stdout: counts and rows only.\n"
            "  history: a temporary bare mirror outside the repository, removed afterwards.\n"
            "\n"
            "Exit codes:\n"
            "  0  no findings\n"
            "  1  findings (triage per the runbook)\n"
            "  2  refusal, missing trufflehog, git or TruffleHog error, timeout, usage error\n"
            "\n"
            "Related: docs/runbooks/secret-scanning.md, .github/workflows/ci.yml (Secret scan),\n"
            "  .trufflehogignore, issue #9416."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "New file for the full JSON report; must not exist and must be outside the repository "
            "(default: a fresh secret-scan-<mode>-*.jsonl in the system temp directory)."
        ),
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=PROJECT_ROOT,
        help="Git work tree to scan or whose remote to mirror (default: this script's checkout).",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Limit per clone or TruffleHog call, in seconds (default: {DEFAULT_TIMEOUT_SECONDS}).",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=DEFAULT_MAX_ROWS,
        help=f"Maximum finding rows printed; counts always cover all (default: {DEFAULT_MAX_ROWS}).",
    )
    sub = parser.add_subparsers(dest="mode", required=True, metavar="{tree,history}")
    sub.add_parser(
        "tree",
        help="Scan tracked and untracked-not-ignored files of the work tree "
        "(never .git, .venv, node_modules, .worktrees or data/ databases; symlinks skipped).",
    )
    history = sub.add_parser(
        "history",
        help="Mirror-clone the configured remote (all refs) and scan every commit with --bare.",
    )
    history.add_argument(
        "--remote",
        default="origin",
        help="Name of the configured public remote to mirror (default: origin).",
    )
    history.add_argument(
        "--mirror-parent",
        type=Path,
        default=None,
        help="Directory to hold the temporary mirror; must be outside the repository "
        "(default: the system temp directory). Needs room for a full clone.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    try:
        refuse_verification_options(args_list)
    except ScanError as exc:
        print(f"secret_scan_local: {exc}", file=sys.stderr)
        return EXIT_ERROR
    args = build_parser().parse_args(args_list)
    binary = shutil.which(TRUFFLEHOG)
    if binary is None:
        print(
            "secret_scan_local: trufflehog not found on PATH; see docs/runbooks/secret-scanning.md",
            file=sys.stderr,
        )
        return EXIT_ERROR
    try:
        repo = work_tree_top(args.repo)
        roots = protected_roots(repo)
        output, out_fd, log, log_fd = open_outputs(args.output, args.mode, roots)
        try:
            if args.mode == "tree":
                scanned = scan_tree(binary, repo, out_fd, log_fd, args.timeout_seconds)
                print(f"mode: tree, files scanned: {scanned}")
            else:
                scan_history(
                    binary,
                    repo,
                    args.remote,
                    args.mirror_parent,
                    roots,
                    out_fd,
                    log_fd,
                    args.timeout_seconds,
                )
                print(f"mode: history, remote: {args.remote}")
        except ScanError as exc:
            raise ScanError(f"{exc}; TruffleHog/git log (owner-only): {log}") from exc
        finally:
            os.close(out_fd)
            os.close(log_fd)
        findings = read_findings(output)
    except ScanError as exc:
        print(f"secret_scan_local: {exc}", file=sys.stderr)
        return EXIT_ERROR
    for line in render(findings, args.max_rows):
        print(line)
    print(f"full report (owner-only, contains raw values, never paste): {output}")
    return EXIT_FINDINGS if findings else EXIT_CLEAN


if __name__ == "__main__":
    raise SystemExit(main())
