#!/usr/bin/env python3
"""Offline local TruffleHog scan with safe fixed flags and redacted console output.

Runbook: docs/runbooks/secret-scanning.md (#9416).

Safety properties, each covered by tests/audit/test_secret_scan_local.py:

* verification is never enabled: ``--no-verification`` is always passed and any
  verification-style option on the wrapper's command line is refused;
* the full TruffleHog JSON (which carries raw secret values) goes only to a new
  owner-only (0600) file outside the repository; TruffleHog's own stderr goes to
  a sibling owner-only log, never to the console. Both are created relative to
  one opened directory whose identity (device and inode of it and every
  ancestor) was checked against the repository roots, so swapping a path
  component for a symlink after the check cannot redirect the write;
* console output is allowlist-only: counts, plus detector, file, short commit
  and line when each matches a conservative pattern and holds none of the
  finding's secret values, else a fixed placeholder. Every diagnostic is a
  fixed message that never repeats an option value, a path, a remote URL or
  tool output;
* ``history`` mirror-clones only a plain ``https://`` remote (validated, passed
  after ``--``, transport restricted to https) into a temporary directory
  outside the repository and removes it afterwards; a failed removal is an error.
"""

from __future__ import annotations

import argparse
import errno
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.parse
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

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

# Console allowlist. A field that does not fully match, or that contains one of
# the finding's secret values, is replaced by its placeholder.
SAFE_DETECTOR = re.compile(r"[A-Za-z0-9_-]{1,64}")
SAFE_PATH = re.compile(r"[A-Za-z0-9._/+@=-]{1,240}")
SAFE_COMMIT = re.compile(r"[0-9a-f]{7,64}")
SAFE_LINE = re.compile(r"[0-9]{1,9}")
DETECTOR_WITHHELD = "<detector withheld>"
PATH_WITHHELD = "<path withheld>"
COMMIT_WITHHELD = "<commit withheld>"
LINE_WITHHELD = "<line withheld>"
# Finding fields that carry secret material; shorter strings are too generic to match on.
SECRET_FIELDS = ("Raw", "RawV2", "Redacted", "ExtraData", "StructuredData", "SecretParts")
MIN_SECRET_MATCH = 6

# history: the remote must be a plain https URL, and git may use no other transport
# (also after url.<base>.insteadOf rewrites or redirects).
SAFE_REMOTE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
MAX_REMOTE_URL = 2048
CLONE_PROTOCOLS = "https"

NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | NOFOLLOW
FILE_FLAGS = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | NOFOLLOW
MAX_ANCESTORS = 4096

MSG_VERIFICATION = (
    "refused a verification-style option: verified mode sends candidate secrets "
    "to provider APIs and needs an operator decision; this wrapper is offline only"
)
MSG_USAGE = "usage error: unknown option, missing argument or invalid value; see --help"
MSG_OUTPUT_INSIDE = "refused --output inside the repository: raw secrets must stay outside it"
MSG_TEMP_INSIDE = "the system temp directory is inside the repository; pass --output"
MSG_MIRROR_INSIDE = "refused mirror directory inside the repository"
MSG_REMOTE_NAME = "refused --remote: not a plain remote name"
MSG_REMOTE_URL = "refused the configured remote URL: only a plain https:// URL without credentials is allowed"
MSG_MIRROR_REMOVAL = "could not remove the temporary mirror (secret-scan-mirror-*); remove it by hand"


class ScanError(Exception):
    """A refusal or tool failure; the message is built only from fixed text and integers."""


@dataclass(frozen=True)
class Finding:
    """Console-safe display values of one finding."""

    detector: str
    file: str
    commit: str
    line: str

    @property
    def withheld(self) -> bool:
        return any(
            value in {DETECTOR_WITHHELD, PATH_WITHHELD, COMMIT_WITHHELD, LINE_WITHHELD}
            for value in (self.detector, self.file, self.commit, self.line)
        )


@dataclass(frozen=True)
class Outputs:
    report_fd: int
    log_fd: int
    # Wrapper-generated file name of a default report, or None for --output.
    default_name: str | None


def _errno_name(exc: OSError) -> str:
    return errno.errorcode.get(exc.errno or 0, "unknown error")


def refuse_verification_options(argv: Sequence[str]) -> None:
    """Reject any option that could turn verification on or widen result types."""
    for token in argv:
        name = token.split("=", 1)[0].lower()
        if name.startswith("-") and any(marker in name for marker in FORBIDDEN_FLAG_MARKERS):
            raise ScanError(MSG_VERIFICATION)


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


def _identity(info: os.stat_result) -> tuple[int, int]:
    return (info.st_dev, info.st_ino)


def root_identities(roots: Iterable[Path]) -> frozenset[tuple[int, int]]:
    return frozenset(_identity(os.stat(root)) for root in roots)


def dir_is_inside(dir_fd: int, root_ids: frozenset[tuple[int, int]]) -> bool:
    """Whether an open directory is a protected root or below one.

    Walks ``..`` handles from the open directory itself, so the answer is about
    the directory that will be written to, not about a path that may change.
    """
    current = os.dup(dir_fd)
    try:
        for _ in range(MAX_ANCESTORS):
            info = os.fstat(current)
            if _identity(info) in root_ids:
                return True
            parent = os.open("..", DIR_FLAGS, dir_fd=current)
            if _identity(os.fstat(parent)) == _identity(info):
                os.close(parent)
                return False  # reached the filesystem root
            os.close(current)
            current = parent
        return True  # fail closed on an absurd depth
    finally:
        os.close(current)


def open_checked_dir(path: Path, root_ids: frozenset[tuple[int, int]], refusal: str) -> int:
    """Open a directory once, refusing it when it is inside a protected root."""
    try:
        fd = os.open(path.resolve(strict=True), DIR_FLAGS)
    except (OSError, RuntimeError) as exc:
        reason = _errno_name(exc) if isinstance(exc, OSError) else "symlink loop"
        raise ScanError(f"cannot open the target directory ({reason})") from exc
    if dir_is_inside(fd, root_ids):
        os.close(fd)
        raise ScanError(refusal)
    return fd


def _create_private(dir_fd: int, name: str) -> int:
    """Create a new owner-only file in an open directory; never follow a symlink or reuse a file."""
    try:
        fd = os.open(name, FILE_FLAGS, 0o600, dir_fd=dir_fd)
    except FileExistsError as exc:
        raise ScanError("output path already exists; choose a new file") from exc
    except OSError as exc:
        raise ScanError(f"cannot create output file ({_errno_name(exc)})") from exc
    os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
    return fd


def open_outputs(output: Path | None, mode: str, root_ids: frozenset[tuple[int, int]]) -> Outputs:
    """Open the JSON report and TruffleHog log, both 0600 and outside the repository."""
    if output is None:
        directory, name = Path(tempfile.gettempdir()), f"secret-scan-{mode}-{secrets.token_hex(8)}.jsonl"
        refusal = MSG_TEMP_INSIDE
    else:
        directory, name = output.parent, output.name
        refusal = MSG_OUTPUT_INSIDE
        if name in {"", ".", ".."}:
            raise ScanError("--output must name a new file")
    dir_fd = open_checked_dir(directory, root_ids, refusal)
    try:
        report_fd = _create_private(dir_fd, name)
        try:
            log_fd = _create_private(dir_fd, name + ".log")
        except ScanError:
            os.close(report_fd)
            os.unlink(name, dir_fd=dir_fd)
            raise
    finally:
        os.close(dir_fd)
    return Outputs(report_fd, log_fd, name if output is None else None)


def _denied(rel: str) -> bool:
    parts = rel.split("/")
    if DENIED_DIR_PARTS.intersection(parts[:-1]) or parts[-1] in DENIED_DIR_PARTS:
        return True
    return parts[0] == "data" and rel.lower().endswith(DATABASE_SUFFIXES)


def tree_candidates(repo: Path) -> list[str]:
    """Tracked plus untracked-not-ignored regular files, minus denied areas and symlinked paths."""
    listing = _git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    seen: set[str] = set()
    files: list[str] = []
    for rel in listing.split("\0"):
        if not rel or rel in seen or _denied(rel):
            continue
        seen.add(rel)
        path = repo / rel
        # A symlink anywhere on the way (file or parent) could lead outside the tree.
        if os.path.realpath(path) != str(path):
            continue
        try:
            info = path.lstat()
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


def _run_trufflehog(cmd: list[str], cwd: str | Path, out_fd: int, log_fd: int, timeout: int) -> None:
    assert_safe_command(cmd)
    try:
        result = subprocess.run(cmd, cwd=cwd, stdout=out_fd, stderr=log_fd, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ScanError("trufflehog timed out (see --timeout-seconds)") from exc
    except OSError as exc:
        raise ScanError(f"cannot run trufflehog ({_errno_name(exc)})") from exc
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


def validate_remote_url(url: str) -> None:
    """Allow only a plain ``https://host/...`` URL: no option, transport helper or credentials."""
    if not url or len(url) > MAX_REMOTE_URL or not url.startswith("https://"):
        raise ScanError(MSG_REMOTE_URL)
    # Printable ASCII only: no whitespace, control, format or bidi characters.
    if not all("!" <= char <= "~" for char in url):
        raise ScanError(MSG_REMOTE_URL)
    try:
        parts = urllib.parse.urlsplit(url)
        _ = parts.port  # raises ValueError on a malformed port
    except ValueError as exc:
        raise ScanError(MSG_REMOTE_URL) from exc
    if not parts.hostname or "@" in parts.netloc:
        raise ScanError(MSG_REMOTE_URL)


def configured_remote_url(repo: Path, remote: str) -> str:
    """The raw configured URL of ``remote`` (the operand git clone will receive), validated."""
    if not SAFE_REMOTE_NAME.fullmatch(remote):
        raise ScanError(MSG_REMOTE_NAME)
    # NUL-terminated so a newline or other whitespace in the value is validated, not stripped.
    url = _git(repo, "config", "--null", "--get", f"remote.{remote}.url").removesuffix("\0")
    validate_remote_url(url)
    return url


def clone_command(url: str, dest: str) -> list[str]:
    # Public remote: no credential helper may contribute a token. ``--`` ends option parsing.
    return ["git", "-c", "credential.helper=", "clone", "--quiet", "--mirror", "--", url, dest]


def _dir_cwd(fd: int, fallback: Path) -> tuple[str, tuple[int, ...]]:
    """A cwd naming exactly the open directory where /proc allows it, else its path."""
    proc = f"/proc/self/fd/{fd}"
    if os.path.isdir(proc):
        return proc, (fd,)
    return str(fallback), ()


def _remove_mirror(parent_fd: int, name: str, prior: ScanError | None) -> None:
    try:
        shutil.rmtree(name, dir_fd=parent_fd)
    except OSError as exc:
        message = f"{prior}; {MSG_MIRROR_REMOVAL}" if prior is not None else MSG_MIRROR_REMOVAL
        raise ScanError(message) from exc


def _clone_and_scan(
    binary: str, url: str, work_fd: int, work_path: Path, repo: Path, out_fd: int, log_fd: int, timeout: int
) -> None:
    cwd, pass_fds = _dir_cwd(work_fd, work_path)
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ALLOW_PROTOCOL": CLONE_PROTOCOLS}
    try:
        clone = subprocess.run(
            clone_command(url, "mirror.git"),
            cwd=cwd,
            pass_fds=pass_fds,
            stdout=subprocess.DEVNULL,
            stderr=log_fd,
            env=env,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ScanError("mirror clone timed out (see --timeout-seconds)") from exc
    if clone.returncode != 0:
        raise ScanError(f"mirror clone of the configured remote failed (exit {clone.returncode})")
    real = Path(os.readlink(cwd)) if pass_fds else work_path
    cmd = [binary, "git", f"file://{real / 'mirror.git'}", "--bare", *SAFE_FLAGS, *_exclude_args(repo)]
    _run_trufflehog(cmd, real, out_fd, log_fd, timeout)


def scan_history(
    binary: str,
    repo: Path,
    url: str,
    mirror_parent: Path | None,
    root_ids: frozenset[tuple[int, int]],
    out_fd: int,
    log_fd: int,
    timeout: int,
) -> None:
    parent = mirror_parent if mirror_parent is not None else Path(tempfile.gettempdir())
    parent_fd = open_checked_dir(parent, root_ids, MSG_MIRROR_INSIDE)
    try:
        name = f"secret-scan-mirror-{secrets.token_hex(8)}"
        try:
            os.mkdir(name, 0o700, dir_fd=parent_fd)
        except OSError as exc:
            raise ScanError(f"cannot create the mirror directory ({_errno_name(exc)})") from exc
        try:
            work_fd = os.open(name, DIR_FLAGS, dir_fd=parent_fd)
            try:
                _clone_and_scan(binary, url, work_fd, parent / name, repo, out_fd, log_fd, timeout)
            finally:
                os.close(work_fd)
        except BaseException as exc:
            _remove_mirror(parent_fd, name, exc if isinstance(exc, ScanError) else None)
            raise
        _remove_mirror(parent_fd, name, None)
    finally:
        os.close(parent_fd)


def _secret_values(record: dict) -> set[str]:
    values: set[str] = set()
    stack: list[object] = [record.get(field) for field in SECRET_FIELDS]
    while stack:
        item = stack.pop()
        if isinstance(item, str) and len(item) >= MIN_SECRET_MATCH:
            values.add(item)
        elif isinstance(item, dict):
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return values


def _shown(value: str, pattern: re.Pattern[str], hidden: set[str], placeholder: str) -> str:
    if pattern.fullmatch(value) and not any(secret in value for secret in hidden):
        return value
    return placeholder


def _location(record: object, number: int) -> dict:
    """The single source-location object of a finding; any other shape is a typed error."""
    error = ScanError(f"unexpected report structure at line {number}")
    if not isinstance(record, dict) or not isinstance(record.get("DetectorName"), str):
        raise error
    metadata = record.get("SourceMetadata")
    data = metadata.get("Data") if isinstance(metadata, dict) else None
    if not isinstance(data, dict) or len(data) != 1:
        raise error
    (location,) = data.values()
    if not isinstance(location, dict):
        raise error
    return location


def _field(value: object, pattern: re.Pattern[str], hidden: set[str], placeholder: str) -> str:
    if value is None:
        return "-"
    if isinstance(value, int) and not isinstance(value, bool):
        value = str(value)
    if not isinstance(value, str):
        return placeholder
    return _shown(value, pattern, hidden, placeholder)


def to_finding(record: dict, location: dict) -> Finding:
    """Console-safe display values; anything outside the allowlist becomes a placeholder."""
    hidden = _secret_values(record)
    commit = _field(location.get("commit"), SAFE_COMMIT, hidden, COMMIT_WITHHELD)
    return Finding(
        detector=_shown(record["DetectorName"], SAFE_DETECTOR, hidden, DETECTOR_WITHHELD),
        file=_field(location.get("file"), SAFE_PATH, hidden, PATH_WITHHELD),
        commit=commit[:10] if SAFE_COMMIT.fullmatch(commit) else commit,
        line=_field(location.get("line"), SAFE_LINE, hidden, LINE_WITHHELD),
    )


def read_findings(report_fd: int) -> list[Finding]:
    """Parse the report through its open descriptor, keeping only console-safe location fields."""
    findings: list[Finding] = []
    os.lseek(report_fd, 0, os.SEEK_SET)
    with os.fdopen(os.dup(report_fd), encoding="utf-8", errors="strict") as fh:
        try:
            for number, raw_line in enumerate(fh, start=1):
                if not raw_line.strip():
                    continue
                try:
                    record = json.loads(raw_line)
                except (ValueError, RecursionError) as exc:
                    # Never echo the line: it may hold a secret.
                    raise ScanError(f"unparseable JSON at report line {number}") from exc
                findings.append(to_finding(record, _location(record, number)))
        except UnicodeDecodeError as exc:
            raise ScanError("the report is not valid UTF-8") from exc
    return findings


def render(findings: Sequence[Finding], max_rows: int) -> list[str]:
    lines = [f"findings: {len(findings)}"]
    for detector, count in sorted(Counter(f.detector for f in findings).items()):
        lines.append(f"  {detector}: {count}")
    withheld = sum(1 for f in findings if f.withheld)
    if withheld:
        lines.append(f"findings with withheld fields: {withheld} (see the JSON report)")
    rows = sorted(set(findings), key=lambda f: (f.detector, f.file, f.commit, f.line))
    if rows:
        lines.append("detector\tfile\tcommit\tline")
        lines.extend(f"{f.detector}\t{f.file}\t{f.commit}\t{f.line}" for f in rows[:max_rows])
        if len(rows) > max_rows:
            lines.append(f"... {len(rows) - max_rows} more rows in the JSON report")
    return lines


class _FixedErrorParser(argparse.ArgumentParser):
    """argparse whose usage errors never repeat the offending option or value."""

    def error(self, message: str) -> NoReturn:
        del message  # may contain a supplied value
        print(f"secret_scan_local: {MSG_USAGE}", file=sys.stderr)
        raise SystemExit(EXIT_ERROR)


def _int_at_least(minimum: int):
    def parse(text: str) -> int:
        value = int(text)
        if value < minimum:
            raise ValueError
        return value

    return parse


def build_parser() -> argparse.ArgumentParser:
    parser = _FixedErrorParser(
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
            "  as <report>.log (0600). Never paste either anywhere. stdout: counts and rows only;\n"
            "  a field outside the safe pattern is shown as a placeholder. The report location is\n"
            "  printed only as the generated default file name, never as a path.\n"
            "  history: a temporary bare mirror outside the repository, removed afterwards; only a\n"
            "  plain https:// remote without credentials is mirrored.\n"
            "\n"
            "Exit codes:\n"
            "  0  no findings\n"
            "  1  findings (triage per the runbook)\n"
            "  2  refusal, missing trufflehog, git or TruffleHog error, timeout, usage error,\n"
            "     unexpected report structure, mirror removal failure\n"
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
        type=_int_at_least(1),
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Limit per clone or TruffleHog call, in seconds (default: {DEFAULT_TIMEOUT_SECONDS}).",
    )
    parser.add_argument(
        "--max-rows",
        type=_int_at_least(0),
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
        help="Mirror-clone the configured https remote (all refs) and scan every commit with --bare.",
    )
    history.add_argument(
        "--remote",
        default="origin",
        help="Name of the configured public https remote to mirror (default: origin).",
    )
    history.add_argument(
        "--mirror-parent",
        type=Path,
        default=None,
        help="Directory to hold the temporary mirror; must be outside the repository "
        "(default: the system temp directory). Needs room for a full clone.",
    )
    return parser


def _report_line(outputs: Outputs) -> str:
    label = "full report (owner-only, contains raw values, never paste)"
    if outputs.default_name is not None and SAFE_PATH.fullmatch(outputs.default_name):
        return f"{label}: {outputs.default_name} in the system temp directory, log beside it with .log appended"
    return f"{label}: written to the --output path, log beside it with .log appended"


def _scan(args: argparse.Namespace, binary: str) -> int:
    repo = work_tree_top(args.repo)
    root_ids = root_identities(protected_roots(repo))
    # Refusals come before any output file exists.
    url = configured_remote_url(repo, args.remote) if args.mode == "history" else ""
    outputs = open_outputs(args.output, args.mode, root_ids)
    try:
        try:
            if args.mode == "tree":
                scanned = scan_tree(binary, repo, outputs.report_fd, outputs.log_fd, args.timeout_seconds)
                print(f"mode: tree, files scanned: {scanned}")
            else:
                scan_history(
                    binary,
                    repo,
                    url,
                    args.mirror_parent,
                    root_ids,
                    outputs.report_fd,
                    outputs.log_fd,
                    args.timeout_seconds,
                )
                print("mode: history")
        except ScanError as exc:
            raise ScanError(f"{exc}; details in the owner-only log beside the report") from exc
        findings = read_findings(outputs.report_fd)
    finally:
        os.close(outputs.report_fd)
        os.close(outputs.log_fd)
    for line in render(findings, args.max_rows):
        print(line)
    print(_report_line(outputs))
    return EXIT_FINDINGS if findings else EXIT_CLEAN


def main(argv: Sequence[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    try:
        refuse_verification_options(args_list)
        args = build_parser().parse_args(args_list)
    except ScanError as exc:
        print(f"secret_scan_local: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else EXIT_ERROR
    binary = shutil.which(TRUFFLEHOG)
    if binary is None:
        print(
            "secret_scan_local: trufflehog not found on PATH; see docs/runbooks/secret-scanning.md",
            file=sys.stderr,
        )
        return EXIT_ERROR
    try:
        return _scan(args, binary)
    except ScanError as exc:
        print(f"secret_scan_local: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as exc:  # a traceback could carry report contents or paths
        print(f"secret_scan_local: internal error ({type(exc).__name__})", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
