#!/usr/bin/env python3
"""Prove that an extracted machinery repository is exactly the approved one, before its first push.

Step 6 of the machinery move rewrites a clone of the product repository with git-filter-repo,
then adds one transformation commit (the ``scripts`` -> ``lu_machinery`` rename, the approved
additions). This tool checks the result against frozen inputs and never writes to any of them:
every git call and every child process runs in a bubblewrap sandbox whose only writable path is the
tool's scratch directory.

* V1 the final tree is exactly the tree manifest;
* V2 excluded paths appear nowhere, history-only paths are absent from the final tree;
* V3 every manifest Python module imports from the extracted root alone;
* V4 no extracted Python file still references ``scripts`` modules, machinery ``scripts/`` paths
  or product packages;
* V5 the evaluator's held-out rename expectations hold and the rename tools are idempotent;
* V6 every source commit of ``scripts/dispatch.py`` survives in ``lu_machinery/dispatch.py``'s history;
* V7 every check inspected the expected, nonzero number of items;
* V8 (``--run-tests``) the ported machinery tests pass against the extracted code;
* V9 HEAD is the single transformation commit on top of the rewrite tip, with the frozen tree;
* HP (``--history-policy``) ``history_policy.py verify`` passes up to the rewrite tip.

Run ``verify_extraction.py --help`` for inputs, formats and exit codes.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

EXIT_PASS = 0
EXIT_FINDING = 1
EXIT_UNUSABLE = 2

OLD_PREFIX = "scripts/"
NEW_PREFIX = "lu_machinery/"
PATH_RENAME = f"{OLD_PREFIX}:{NEW_PREFIX}"
DISPATCH_SOURCE = "scripts/dispatch.py"
DISPATCH_DEST = "lu_machinery/dispatch.py"
DISPATCH_MODULE = "lu_machinery.dispatch"
ADDITION = "-"
CLASSES = ("imports", "module-strings", "non-python", "resource-paths")
PYTHON_CLASSES = frozenset({"imports", "module-strings"})
MACHINERY = "machinery"
PRODUCT = "product"
MIXED = "mixed"

HERE = Path(__file__).resolve().parent
RENAME_TOOLS = ("rename_python.py", "rename_nonpython.py", "rename_structured.py")
HISTORY_POLICY_TOOL = "history_policy.py"
TESTS_LIST = "machinery_tests.txt"

HEX_OID = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")
ZERO_OID = re.compile(r"0{40}(?:0{24})?")
# A ``scripts.<name>`` module reference; ``scripts.py`` and other file names are not modules.
MODULE_REF = re.compile(r"(?<![\w.\-/])scripts(?:\.[A-Za-z_]\w*)+")
FILE_SUFFIXES = frozenset({"py", "pyc", "sh", "md", "json", "yaml", "yml", "txt", "toml", "cfg", "ini", "log"})
# Calls whose literal first argument (or name=/mod_name=) names a module that gets imported, with its
# parent packages: importlib.import_module and importlib.util.find_spec (relative with a package),
# __import__ (level and fromlist), runpy.run_module and pkgutil.resolve_name ("module:attribute").
LOADERS = frozenset({"import_module", "find_spec", "__import__", "run_module", "resolve_name"})
PATH_REF = re.compile(r"(?<![\w.\-])(?:\./)?scripts/([\w.\-/]*)")
# Environment variables that would let a source checkout or another repository leak in.
STRIPPED_ENV_PREFIXES = ("PYTHON", "GIT_", "PYTEST_")
GIT_TIMEOUT = 1800
LISTED_SHOWN = 20
NOT_EXTRACTED = "not-extracted"
UNKNOWN = "unknown"


class Unusable(Exception):
    """An input is missing, unreadable or malformed: exit 2."""


@dataclass
class CheckResult:
    """What one check inspected and found."""

    check: str
    title: str
    status: str = "pass"  # pass | fail | skipped
    inspected: dict[str, int] = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    listed: list[str] = field(default_factory=list)  # allowed references reported in full (V4 product references)

    def fail(self, message: str) -> None:
        self.findings.append(message)
        self.status = "fail"

    def as_dict(self) -> dict[str, object]:
        return {
            "check": self.check,
            "title": self.title,
            "status": self.status,
            "inspected": self.inspected,
            "findings": self.findings,
            "notes": self.notes,
            "listed": self.listed,
        }


@dataclass(frozen=True)
class Expectation:
    line: int
    klass: str
    dest: str
    present: bool
    literal: str


@dataclass
class Inputs:
    repo: Path
    source_repo: Path
    source: str
    commit_map: dict[str, str]
    manifest: list[tuple[str, str]]
    history_paths: list[str]
    exclude: list[str]
    expectations: list[Expectation]
    rewrite_tip: str
    final_tree: str
    ownership: dict[str, str]
    map_path: Path
    history_policy: Path | None
    policy_sha256: str | None
    commit_map_path: Path
    run_tests: bool
    tests_run: list[str]
    tests_support: list[str]
    python: str
    tool_python: str
    external_names: Path | None
    jobs: int
    import_timeout: int
    test_timeout: int
    tools_dir: Path
    head: str = ""

    @property
    def dests(self) -> list[str]:
        return [dest for _source, dest in self.manifest]

    @property
    def python_dests(self) -> list[str]:
        return sorted(dest for dest in self.dests if dest.endswith(".py"))


# --------------------------------------------------------------------------- helpers


def renamed(path: str) -> str:
    """The filter-repo destination of a source path under --path-rename scripts/:lu_machinery/."""
    return NEW_PREFIX + path[len(OLD_PREFIX) :] if path.startswith(OLD_PREFIX) else path


def clean_env(**extra: str) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith(STRIPPED_ENV_PREFIXES)}
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.update(extra)
    return env


class Sandbox:
    """Runs every git call and child process with the whole filesystem read-only except the scratch directory.

    bubblewrap binds / read-only, gives a private /dev (with a private /dev/shm) and /proc, unshares every
    namespace (no network) and binds only the scratch directory writable. Inputs that live under /dev are
    bound back read-only. Imported machinery code, ported tests, rename tools, history_policy.py, git and
    any repository-configured git helper therefore cannot write to an input.
    """

    def __init__(self, scratch: Path, visible: Iterable[Path]) -> None:
        executable = shutil.which("bwrap")
        if executable is None:
            raise Unusable("bubblewrap (bwrap) is required: every git call and child process runs read-only in it")
        self.scratch = scratch
        self.home = scratch / "home"
        self.tmp = scratch / "tmp"
        self.home.mkdir(exist_ok=True)
        self.tmp.mkdir(exist_ok=True)
        anchors: list[str] = []
        for path in visible:
            real = os.path.realpath(path)
            if real != "/dev" and not real.startswith("/dev/"):
                continue
            anchor = "/".join(real.split("/")[:4]) if real.startswith("/dev/shm/") else real
            if os.path.exists(anchor) and anchor not in anchors:
                anchors.append(anchor)
        binds = [arg for anchor in sorted(anchors) for arg in ("--ro-bind", anchor, anchor)]
        self.prefix = [
            executable,
            "--die-with-parent",
            "--new-session",
            "--unshare-all",
            "--ro-bind",
            "/",
            "/",
            "--dev",
            "/dev",
            "--proc",
            "/proc",
            *binds,
            "--bind",
            str(scratch),
            str(scratch),
        ]
        try:
            probe = self.run(["true"], cwd=scratch, env=self.env(), timeout=60)
        except subprocess.TimeoutExpired as exc:
            raise Unusable("bubblewrap did not start a sandbox within 60s") from exc
        if probe.returncode != 0:
            detail = probe.stderr.decode("utf-8", "replace").strip()
            raise Unusable(f"bubblewrap cannot start the read-only sandbox here: {detail}")

    def env(self, **extra: str) -> dict[str, str]:
        """The cleaned environment with HOME, TMPDIR and XDG directories inside the scratch directory."""
        return clean_env(
            HOME=str(self.home),
            TMPDIR=str(self.tmp),
            XDG_CONFIG_HOME=str(self.home / ".config"),
            XDG_CACHE_HOME=str(self.home / ".cache"),
            **extra,
        )

    def run(
        self, cmd: Sequence[str], *, cwd: Path, env: dict[str, str], timeout: int, stdin: bytes | None = None
    ) -> subprocess.CompletedProcess[bytes]:
        argv = [*self.prefix, "--chdir", str(cwd), "--", *cmd]
        if stdin is None:
            return subprocess.run(
                argv,
                cwd=self.scratch,
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        return subprocess.run(
            argv, cwd=self.scratch, env=env, input=stdin, capture_output=True, timeout=timeout, check=False
        )


_SANDBOX: list[Sandbox] = []


def sandbox() -> Sandbox:
    if not _SANDBOX:
        raise RuntimeError("the sandbox is not set up")
    return _SANDBOX[-1]


def git(repo: Path, *args: str, check: bool = True, stdin: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    """Run a read-only git command in the sandbox; replace refs, signatures and fsmonitor are off."""
    executable = shutil.which("git")
    if executable is None:
        raise Unusable("git is not on PATH")
    box = sandbox()
    cmd = [
        executable,
        "--no-pager",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "log.showSignature=false",
        "-C",
        str(repo),
        *args,
    ]
    env = box.env(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    try:
        proc = box.run(cmd, cwd=box.scratch, env=env, timeout=GIT_TIMEOUT, stdin=stdin)
    except subprocess.TimeoutExpired as exc:
        raise Unusable(f"git {' '.join(args)} in {repo} timed out after {GIT_TIMEOUT}s") from exc
    if check and proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", "replace").strip()
        raise Unusable(f"git {' '.join(args)} in {repo} failed: {detail}")
    return proc


def git_text(repo: Path, *args: str) -> str:
    return git(repo, *args).stdout.decode("utf-8", "surrogateescape")


def git_z(repo: Path, *args: str) -> list[str]:
    out = git(repo, *args).stdout.decode("utf-8", "surrogateescape")
    return [item for item in out.split("\0") if item]


def resolve_commit(repo: Path, rev: str, what: str) -> str:
    proc = git(repo, "rev-parse", "--verify", "--quiet", "--end-of-options", f"{rev}^{{commit}}", check=False)
    if proc.returncode != 0:
        raise Unusable(f"{what} {rev!r} is not a commit in {repo}")
    return proc.stdout.decode().strip()


def tree_paths(repo: Path, rev: str) -> list[str]:
    return git_z(repo, "ls-tree", "-r", "-z", "--name-only", "--full-tree", rev)


def valid_path(path: str, *, allow_dir: bool = False) -> bool:
    if not path or path.startswith("/") or "\\" in path or "\0" in path:
        return False
    body = path[:-1] if allow_dir and path.endswith("/") else path
    parts = body.split("/")
    return bool(body) and all(part not in ("", ".", "..") for part in parts) and parts[0] != ".git"


def read_text(path: Path, what: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Unusable(f"cannot read {what} {path}: {exc}") from exc


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


# --------------------------------------------------------------------------- input loading


def load_manifest(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    seen_dest: dict[str, int] = {}
    seen_source: dict[str, int] = {}
    for number, line in enumerate(read_text(path, "--tree-manifest").splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != 2:
            raise Unusable(f"--tree-manifest line {number}: expected source_path<TAB>dest_path, got {line!r}")
        source, dest = fields
        if source != ADDITION and not valid_path(source):
            raise Unusable(f"--tree-manifest line {number}: invalid source path {source!r}")
        if not valid_path(dest):
            raise Unusable(f"--tree-manifest line {number}: invalid dest path {dest!r}")
        if dest in seen_dest:
            raise Unusable(f"--tree-manifest line {number}: dest {dest!r} repeats line {seen_dest[dest]}")
        if source != ADDITION and source in seen_source:
            raise Unusable(f"--tree-manifest line {number}: source {source!r} repeats line {seen_source[source]}")
        seen_dest[dest] = number
        if source != ADDITION:
            seen_source[source] = number
        rows.append((source, dest))
    if not rows:
        raise Unusable(f"--tree-manifest {path} has no rows")
    return rows


def load_path_list(path: Path, flag: str) -> list[str]:
    entries: list[str] = []
    for number, line in enumerate(read_text(path, flag).splitlines(), 1):
        entry = line.strip()
        if not entry:
            continue
        if not valid_path(entry, allow_dir=True):
            raise Unusable(f"{flag} line {number}: invalid path {entry!r}")
        entries.append(entry)
    return entries


def load_commit_map(path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    lines = read_text(path, "--commit-map").splitlines()
    for number, line in enumerate(lines, 1):
        fields = line.split()
        if not fields:
            continue
        if number == 1 and fields == ["old", "new"]:
            continue  # git-filter-repo's header line
        if len(fields) != 2 or not all(HEX_OID.fullmatch(item) for item in fields):
            raise Unusable(f"--commit-map line {number}: expected '<old-oid> <new-oid>', got {line!r}")
        old, new = fields
        if old in mapping and mapping[old] != new:
            raise Unusable(f"--commit-map line {number}: {old} is mapped twice")
        mapping[old] = new
    if not mapping:
        raise Unusable(f"--commit-map {path} has no entries")
    return mapping


def load_expectations(path: Path) -> list[Expectation]:
    rows: list[Expectation] = []
    for number, line in enumerate(read_text(path, "--expectations").splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split("\t", 3)
        if len(fields) != 4:
            raise Unusable(f"--expectations line {number}: expected class<TAB>dest_path<TAB>present|absent<TAB>literal")
        klass, dest, mode, literal = fields
        if klass not in CLASSES:
            raise Unusable(f"--expectations line {number}: class {klass!r} is not one of {', '.join(CLASSES)}")
        if not valid_path(dest):
            raise Unusable(f"--expectations line {number}: invalid dest path {dest!r}")
        if mode not in ("present", "absent"):
            raise Unusable(f"--expectations line {number}: expected present or absent, got {mode!r}")
        if not literal:
            raise Unusable(f"--expectations line {number}: empty literal")
        is_python = dest.endswith(".py")
        if klass in PYTHON_CLASSES and not is_python:
            raise Unusable(f"--expectations line {number}: class {klass} needs a .py file, got {dest!r}")
        if klass == "non-python" and is_python:
            raise Unusable(f"--expectations line {number}: class non-python needs a non-.py file, got {dest!r}")
        rows.append(Expectation(number, klass, dest, mode == "present", literal))
    missing = [klass for klass in CLASSES if not any(row.klass == klass for row in rows)]
    if missing:
        raise Unusable(f"--expectations has no row for class(es): {', '.join(missing)}; every class needs one")
    return rows


def load_ownership(path: Path) -> dict[str, str]:
    try:
        data = json.loads(read_text(path, "--map"))
    except json.JSONDecodeError as exc:
        raise Unusable(f"--map {path} is not JSON: {exc}") from exc
    if not isinstance(data, dict) or not data:
        raise Unusable(f"--map {path} must be a non-empty JSON object of path -> owner")
    for key, owner in data.items():
        if not isinstance(key, str) or not valid_path(key) or owner not in (MACHINERY, PRODUCT):
            raise Unusable(f"--map entry {key!r}: {owner!r} must map a repository path to machinery or product")
    return data


def load_tests_list(path: Path) -> tuple[list[str], list[str]]:
    """The [run] test files and their [support] closure, one repository path per line."""
    sections: dict[str, list[str]] = {"run": [], "support": []}
    current: str | None = None
    seen: set[str] = set()
    for number, line in enumerate(read_text(path, TESTS_LIST).splitlines(), 1):
        entry = line.strip()
        if not entry:
            continue
        if entry.startswith("#"):
            marker = entry.lstrip("#").strip()
            if marker in ("[run]", "[support]"):
                current = marker[1:-1]
            continue
        if current is None:
            raise Unusable(f"{path} line {number}: path before a '# [run]' or '# [support]' marker")
        if not valid_path(entry) or not entry.startswith("tests/"):
            raise Unusable(f"{path} line {number}: {entry!r} must be a repository path under tests/")
        if entry in seen:
            raise Unusable(f"{path} line {number}: {entry!r} is listed twice")
        if current == "run" and not PurePosixPath(entry).name.startswith("test_"):
            raise Unusable(f"{path} line {number}: run entry {entry!r} is not a test_*.py file")
        seen.add(entry)
        sections[current].append(entry)
    if not sections["run"]:
        raise Unusable(f"{path} lists no [run] test files")
    return sections["run"], sections["support"]


def require_file(path: Path | None, flag: str) -> Path:
    if path is None or not path.is_file():
        raise Unusable(f"{flag} {path} is missing or not a file")
    return path


def require_repo(path: Path, flag: str) -> Path:
    if not path.is_dir():
        raise Unusable(f"{flag} {path} is not a directory")
    proc = git(path, "rev-parse", "--show-toplevel", check=False)
    if proc.returncode != 0:
        raise Unusable(f"{flag} {path} is not a git repository")
    top = Path(proc.stdout.decode().strip())
    if top.resolve() != path.resolve():
        raise Unusable(f"{flag} {path} is not the top of its repository ({top})")
    if git_text(path, "rev-parse", "--is-shallow-repository").strip() != "false":
        raise Unusable(f"{flag} {path} is shallow; full history is required")
    grafts = Path(git_text(path, "rev-parse", "--git-path", "info/grafts").strip())
    if not grafts.is_absolute():
        grafts = path / grafts
    if grafts.exists():
        raise Unusable(f"{flag} {path} has an info/grafts file, which rewrites history views")
    return path


def worktree_mismatches(repo: Path) -> list[str]:
    """Every difference between the files on disk and HEAD's tree, by bytes and mode.

    The comparison reads the working tree directly and hashes each file as a git blob. It trusts no
    index entry, so assume-unchanged and skip-worktree flags cannot hide a change, and it runs no git
    filter. Any file or symlink on disk that HEAD does not track, ignored files included, is a mismatch;
    empty directories carry no bytes and are not.
    """
    object_format = git_text(repo, "rev-parse", "--show-object-format").strip()
    digest = {"sha1": hashlib.sha1, "sha256": hashlib.sha256}.get(object_format)
    if digest is None:
        raise Unusable(f"{repo} uses an unsupported object format {object_format!r}")
    expected: dict[str, tuple[str, str]] = {}
    for line in git_z(repo, "ls-tree", "-r", "-z", "--full-tree", "HEAD"):
        meta, path = line.split("\t", 1)
        mode, _kind, oid = meta.split()
        expected[path] = (mode, oid)
    problems = [f"{path}: submodules are not supported" for path, (mode, _oid) in expected.items() if mode == "160000"]
    seen: set[str] = set()
    pending: list[tuple[str, str]] = [(str(repo), "")]
    while pending:
        directory, rel = pending.pop()
        with os.scandir(directory) as entries:
            items = sorted(entries, key=lambda entry: entry.name)
        for entry in items:
            path = f"{rel}/{entry.name}" if rel else entry.name
            if not rel and entry.name == ".git":
                continue
            if entry.is_symlink():
                mode, data = "120000", os.fsencode(os.readlink(entry.path))
            elif entry.is_dir(follow_symlinks=False):
                if path in expected:
                    problems.append(f"{path}: a directory where HEAD has a file")
                else:
                    pending.append((entry.path, path))  # git tracks no directories; their files are judged
                continue
            elif entry.is_file(follow_symlinks=False):
                executable = entry.stat(follow_symlinks=False).st_mode & stat.S_IXUSR
                mode = "100755" if executable else "100644"
                with open(entry.path, "rb") as handle:
                    data = handle.read()
            else:
                problems.append(f"{path}: not a regular file, directory or symlink")
                continue
            seen.add(path)
            want = expected.get(path)
            oid = digest(b"blob %d\0" % len(data) + data).hexdigest()
            if want is None:
                problems.append(f"{path}: not tracked at HEAD")
            elif want != (mode, oid):
                problems.append(f"{path}: {mode} {oid} on disk, {want[0]} {want[1]} at HEAD")
    for path in sorted(set(expected) - seen):
        if expected[path][0] != "160000":
            problems.append(f"{path}: missing from the working tree")
    return problems


def require_worktree_equals_head(repo: Path, why: str) -> None:
    problems = worktree_mismatches(repo)
    if problems:
        raise Unusable(
            f"{repo} {why}: the working tree must equal HEAD byte for byte, with nothing untracked or ignored "
            f"(index flags are not trusted); {len(problems)} difference(s): {problems[:10]}"
        )


def pointer_value(path: Path, text: str, what: str) -> str:
    """A git pointer value, spelled exactly as git reads it, or exit 2 for a spelling git might read otherwise.

    Git strips only line terminators from a .git file, commondir and an alternates line; every other
    character, a trailing blank included, is part of the path. Any value with surrounding whitespace, a
    carriage return, a control character or a quote is refused, so the path protected here is the one git
    uses.
    """
    value = text.rstrip("\n")
    if (
        not value
        or value != value.strip()
        or value.startswith('"')
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise Unusable(f"{path}: unsupported {what} spelling {value!r} (surrounding blanks, controls or quotes)")
    return value


def read_pointer_file(path: Path) -> str:
    try:
        return path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Unusable(f"cannot read {path}: {exc}") from exc


def repo_storage(repo: Path) -> list[Path]:
    """The repository's git directory, common directory and every object store its alternates reach.

    Found by reading files, without running git, and spelled as git reads them (see pointer_value). A
    relative alternate is resolved against the object store that names it, as git does, and alternates of
    alternates are followed (git stops at depth 5). check_storage_against_git later compares this with
    git's own answer.
    """
    dot = repo / ".git"
    if dot.is_dir() and not dot.is_symlink():
        git_dir = dot
    elif dot.is_file() or dot.is_symlink():
        text = read_pointer_file(dot)
        if not text.startswith("gitdir: "):
            raise Unusable(f"{dot}: not a 'gitdir: ' pointer")
        named = Path(pointer_value(dot, text[len("gitdir: ") :], "gitdir"))
        git_dir = named if named.is_absolute() else repo / named
    else:
        return []
    common = git_dir
    pointer = git_dir / "commondir"
    if pointer.exists():
        named = Path(pointer_value(pointer, read_pointer_file(pointer), "commondir"))
        common = named if named.is_absolute() else git_dir / named
    found = [git_dir, common]
    seen: set[str] = set()
    queue: list[tuple[Path, int]] = [(common / "objects", 0)]
    while queue:
        objects, depth = queue.pop(0)
        real = os.path.realpath(objects)
        if real in seen or depth > 5:
            continue
        seen.add(real)
        found.append(Path(real))
        alternates = Path(real) / "info" / "alternates"
        if not alternates.exists():
            continue
        for line in read_pointer_file(alternates).split("\n"):
            if not line or line.startswith("#"):
                continue
            target = Path(pointer_value(alternates, line, "alternate"))
            queue.append((target if target.is_absolute() else Path(real) / target, depth + 1))
    return [Path(os.path.realpath(path)) for path in found]


def check_storage_against_git(repo: Path, protected: Sequence[Path]) -> None:
    """Exit 2 unless every git directory and object store git itself reports is protected."""
    reported = git_text(repo, "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir")
    paths = [Path(line) for line in reported.split("\n") if line]
    out = git(repo, "count-objects", "-v").stdout.decode("utf-8", "surrogateescape")
    paths += [Path(line[len("alternate: ") :]) for line in out.split("\n") if line.startswith("alternate: ")]
    for path in paths:
        real = Path(os.path.realpath(path))
        if not any(real == root or inside(real, root) for root in protected):
            raise Unusable(f"git uses {real} for {repo}, which the protected set misses; refusing to continue")


def protected_paths(args: argparse.Namespace) -> list[Path]:
    """Everything the verifier must never write: inputs, both repositories and their git storage, the tools."""
    paths = [args.repo, args.source_repo, HERE, *input_files(args)]
    if args.history_policy is not None:
        paths.append(args.history_policy.parent)  # its replacements/ directory
    for repo in (args.repo, args.source_repo):
        paths += repo_storage(Path(repo))
    return [Path(os.path.realpath(path)) for path in paths]


def check_report_path(report: Path, protected: Sequence[Path], files: Sequence[Path]) -> None:
    """--report may not alias an input file or lie inside a repository, its git storage or the tools."""
    if report.is_symlink():
        raise Unusable(f"--report {report} is a symlink")
    if report.exists() and not report.is_file():
        raise Unusable(f"--report {report} exists and is not a regular file")
    parent = Path(os.path.realpath(report.parent))
    if not parent.is_dir():
        raise Unusable(f"--report {report}: its directory does not exist")
    target = parent / report.name
    for path in files:
        real = Path(os.path.realpath(path))
        if target == real or (report.exists() and real.exists() and os.path.samefile(report, real)):
            raise Unusable(f"--report {report} is an input file")
    for root in protected:
        if target == root or inside(target, root):
            raise Unusable(f"--report {report} lies inside {root}, which is read-only")


def write_report(report: Path, payload: dict[str, Any]) -> None:
    """Write through a freshly created file in the report's directory, then rename it into place.

    The staging name is random and created exclusively without following links, and the rename replaces
    a directory entry, so neither a planted staging link nor a hard link can carry the write elsewhere.
    """
    data = (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    directory = os.open(os.path.realpath(report.parent), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        staging = f".{report.name}.{secrets.token_hex(8)}.tmp"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        descriptor = os.open(staging, flags, 0o644, dir_fd=directory)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(staging, report.name, src_dir_fd=directory, dst_dir_fd=directory)
        except BaseException:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(staging, dir_fd=directory)
            raise
    finally:
        os.close(directory)


def read_child_json(path: Path) -> Any:
    """Read a JSON file a sandboxed child wrote, refusing links and anything but a regular file."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError(f"{path} is not a regular file")
        return json.loads(handle.read().decode("utf-8"))


def require_python(executable: str, flag: str) -> str:
    resolved = shutil.which(executable)
    if resolved is None:
        raise Unusable(f"{flag} {executable!r} is not an executable")
    return resolved


def load_inputs(args: argparse.Namespace) -> Inputs:
    if (args.history_policy is None) != (args.policy_sha256 is None):
        raise Unusable("--history-policy and --policy-sha256 must be given together")
    if args.policy_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", args.policy_sha256):
        raise Unusable("--policy-sha256 must be 64 lowercase hex digits")
    if not re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", args.final_tree):
        raise Unusable("--final-tree must be a full lowercase tree id (40 or 64 hex digits)")
    if args.jobs < 1 or args.import_timeout < 1 or args.test_timeout < 1:
        raise Unusable("--jobs, --import-timeout and --test-timeout must be at least 1")
    repo = require_repo(args.repo.resolve(), "--repo")
    source_repo = require_repo(args.source_repo.resolve(), "--source-repo")
    if repo == source_repo:
        raise Unusable("--repo and --source-repo must be different repositories")
    tools_dir = HERE
    for tool in RENAME_TOOLS:
        if not (tools_dir / tool).is_file():
            raise Unusable(f"rename tool {tools_dir / tool} is absent (PR 12764)")
    history_policy = None
    if args.history_policy is not None:
        history_policy = require_file(args.history_policy.resolve(), "--history-policy")
        if not (tools_dir / HISTORY_POLICY_TOOL).is_file():
            raise Unusable(f"{tools_dir / HISTORY_POLICY_TOOL} is absent; it is needed for --history-policy")
    tests_run: list[str] = []
    tests_support: list[str] = []
    if args.run_tests:
        tests_run, tests_support = load_tests_list(require_file(tools_dir / TESTS_LIST, TESTS_LIST))
    external_names = None
    if args.external_names is not None:
        external_names = require_file(args.external_names.resolve(), "--external-names")
    inputs = Inputs(
        repo=repo,
        source_repo=source_repo,
        source=resolve_commit(source_repo, args.source, "--source"),
        commit_map=load_commit_map(require_file(args.commit_map, "--commit-map")),
        manifest=load_manifest(require_file(args.tree_manifest, "--tree-manifest")),
        history_paths=load_path_list(require_file(args.history_paths, "--history-paths"), "--history-paths"),
        exclude=load_path_list(require_file(args.exclude, "--exclude"), "--exclude"),
        expectations=load_expectations(require_file(args.expectations, "--expectations")),
        rewrite_tip=resolve_commit(repo, args.rewrite_tip, "--rewrite-tip"),
        final_tree=args.final_tree,
        ownership=load_ownership(require_file(args.map, "--map")),
        map_path=args.map.resolve(),
        history_policy=history_policy,
        policy_sha256=args.policy_sha256,
        commit_map_path=args.commit_map.resolve(),
        run_tests=args.run_tests,
        tests_run=tests_run,
        tests_support=tests_support,
        python=require_python(args.python, "--python"),
        tool_python=require_python(args.tool_python, "--tool-python"),
        external_names=external_names,
        jobs=args.jobs,
        import_timeout=args.import_timeout,
        test_timeout=args.test_timeout,
        tools_dir=tools_dir,
    )
    inputs.head = resolve_commit(repo, "HEAD", "--repo HEAD")
    protected = protected_paths(args)
    for checked in (repo, source_repo):
        check_storage_against_git(checked, protected)
    if git(source_repo, "cat-file", "-e", f"{inputs.source}:{DISPATCH_SOURCE}", check=False).returncode != 0:
        raise Unusable(f"--source {inputs.source} has no {DISPATCH_SOURCE}")
    if inputs.run_tests:
        present = set(git_z(source_repo, "ls-tree", "-r", "-z", "--name-only", inputs.source, "--", "tests/"))
        absent = [path for path in tests_run + tests_support if path not in present]
        if absent:
            raise Unusable(f"{TESTS_LIST} names files absent at --source {inputs.source}: {absent[:10]}")
    require_worktree_equals_head(repo, "is not usable")
    return inputs


def input_files(args: argparse.Namespace) -> list[Path]:
    files = [args.commit_map, args.tree_manifest, args.history_paths, args.exclude, args.expectations, args.map]
    files += [path for path in (args.history_policy, args.external_names) if path is not None]
    return files


def visible_roots(args: argparse.Namespace, protected: Sequence[Path]) -> list[Path]:
    """Paths the sandbox must show; only those under /dev need binding back (bwrap gives a private /dev)."""
    roots = list(protected)
    for executable in (args.python, args.tool_python):
        found = shutil.which(executable)
        if found:
            roots += [Path(found).parent.parent, Path(os.path.realpath(found)).parent.parent]
    return roots


# --------------------------------------------------------------------------- V1 final tree


def check_v1(inputs: Inputs) -> CheckResult:
    result = CheckResult("V1", "final tree equals the tree manifest")
    tree = set(tree_paths(inputs.repo, "HEAD"))
    dests = set(inputs.dests)
    for path in sorted(dests - tree):
        result.fail(f"missing from the final tree: {path}")
    for path in sorted(tree - dests):
        result.fail(f"extra in the final tree (not in the manifest): {path}")
    for source, dest in inputs.manifest:
        if source != ADDITION and renamed(source) != dest:
            result.fail(f"manifest row {source} -> {dest} is not the {PATH_RENAME} rename of its source")
    result.inspected = {"manifest_rows": len(inputs.manifest), "tree_paths": len(tree)}
    return result


# --------------------------------------------------------------------------- V2 exclusions


def _forms(entry: str) -> set[str]:
    return {entry, renamed(entry)}


def _matches(path: str, entry: str) -> bool:
    return path.startswith(entry) if entry.endswith("/") else path == entry


def history_paths_seen(repo: Path, rev: str = "HEAD") -> set[str]:
    """Every path that any commit reachable from rev adds, changes or deletes (merges against each parent)."""
    paths = git_z(
        repo,
        "log",
        "-z",
        "--format=",
        "--name-only",
        "--no-renames",
        "--root",
        "--diff-merges=separate",
        rev,
    )
    return {item.strip("\n") for item in paths if item.strip("\n")}


def check_v2(inputs: Inputs) -> CheckResult:
    result = CheckResult("V2", "excluded paths appear nowhere; history-only paths not in the final tree")
    tree = tree_paths(inputs.repo, "HEAD")
    history = history_paths_seen(inputs.repo)
    rewritten = history_paths_seen(inputs.repo, inputs.rewrite_tip)
    commits = int(git_text(inputs.repo, "rev-list", "--count", "HEAD").strip())
    additions = {dest for source, dest in inputs.manifest if source == ADDITION}
    for entry in inputs.exclude:
        for form in sorted(_forms(entry)):
            if form in additions:
                # An approved addition takes this destination (lu_machinery/__init__.py replaces the product's
                # scripts/__init__.py): only the transformation commit may hold it, never the rewritten history.
                result.notes.append(f"excluded {entry} renames onto approved addition {form}; checked up to the tip")
                for path in sorted(p for p in rewritten if _matches(p, form)):
                    result.fail(f"excluded {entry} is in the rewritten history as {path}")
                continue
            for path in sorted(p for p in tree if _matches(p, form)):
                result.fail(f"excluded {entry} is in the final tree as {path}")
            for path in sorted(p for p in history if _matches(p, form)):
                result.fail(f"excluded {entry} is in the extracted history as {path}")
    for entry in inputs.history_paths:
        for form in sorted(_forms(entry)):
            for path in sorted(p for p in tree if _matches(p, form)):
                result.fail(f"history-only {entry} is in the final tree as {path}")
    result.inspected = {
        "exclude_entries": len(inputs.exclude),
        "history_only_entries": len(inputs.history_paths),
        "history_commits": commits,
        "history_paths": len(history),
    }
    return result


# --------------------------------------------------------------------------- V3 import origin

_IMPORT_CHILD = r"""
import importlib, importlib.util, json, os, sys
root, mode, target, expected, out = sys.argv[1:6]
root = os.path.realpath(root)
sys.path.insert(0, root)
def inside(path):
    path = os.path.realpath(path)
    return path == root or path.startswith(root + os.sep)
try:
    if mode == "name":
        module = importlib.import_module(target)
    else:
        parent = target.rpartition(".")[0]
        if parent:
            importlib.import_module(parent)
        spec = importlib.util.spec_from_file_location(target, os.path.join(root, expected))
        module = importlib.util.module_from_spec(spec)
        sys.modules[target] = module
        spec.loader.exec_module(module)
    loaded = getattr(module, "__file__", None)
    result = {"ok": True, "file": os.path.realpath(loaded) if loaded else None}
except BaseException as exc:
    result = {"ok": False, "error": (type(exc).__name__ + ": " + str(exc))[:400]}
env_roots = {os.path.realpath(p) for p in (sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix)}
outside, product = [], []
for name, module in list(sys.modules.items()):
    if name == "scripts" or name.startswith("scripts."):
        product.append(name)
    loaded = getattr(module, "__file__", None)
    if not isinstance(loaded, str):
        continue
    real = os.path.realpath(loaded)
    if inside(real) or any(real.startswith(env + os.sep) for env in env_roots):
        continue
    outside.append(name + " from " + real)
result["scripts_modules"] = sorted(product)
result["outside"] = sorted(outside)
with open(out, "w", encoding="utf-8") as handle:
    json.dump(result, handle)
sys.stdout.flush()
os._exit(0)
"""

_DISPATCH_HELP_CHILD = r"""
import runpy, sys
sys.path.insert(0, sys.argv[1])
sys.argv = [sys.argv[2], "--help"]
runpy.run_module(sys.argv[0], run_name="__main__", alter_sys=True)
"""


def import_target(dest: str) -> tuple[str, str]:
    """How a manifest Python file is imported: by dotted name, or by path under a synthetic name."""
    parts = dest[: -len(".py")].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    if parts and all(part.isidentifier() for part in parts):
        return "name", ".".join(parts)
    dirs = dest.split("/")[:-1]
    stem = re.sub(r"\W", "_", PurePosixPath(dest).stem)
    synthetic = f"_lu_verify_{stem}"
    if dirs and all(part.isidentifier() for part in dirs):
        return "path", ".".join([*dirs, synthetic])
    return "path", synthetic


def isolated_env(box: Sandbox) -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(box.home),
        "TMPDIR": str(box.tmp),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "GIT_NO_REPLACE_OBJECTS": "1",
    }


def check_v3(inputs: Inputs, scratch: Path) -> CheckResult:
    result = CheckResult("V3", "every manifest Python module imports from the extracted root alone")
    cwd = scratch / "v3-cwd"
    cwd.mkdir()
    results_dir = scratch / "v3-results"
    results_dir.mkdir()
    box = sandbox()
    env = isolated_env(box)
    root = inputs.repo.resolve()
    dests = inputs.python_dests

    def run_one(index_dest: tuple[int, str]) -> tuple[str, dict[str, Any] | None, str]:
        index, dest = index_dest
        mode, target = import_target(dest)
        out = results_dir / f"{index}.json"
        cmd = [inputs.python, "-I", "-B", "-c", _IMPORT_CHILD, str(root), mode, target, dest, str(out)]
        try:
            proc = box.run(cmd, cwd=cwd, env=env, timeout=inputs.import_timeout)
        except subprocess.TimeoutExpired:
            return dest, None, f"timed out after {inputs.import_timeout}s"
        if not out.is_file():
            tail = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-1:]
            return dest, None, f"the import child exited {proc.returncode} without a result {tail}"
        try:
            return dest, read_child_json(out), ""
        except (OSError, ValueError) as exc:
            return dest, None, f"unreadable import result: {exc}"

    reported = 0
    with ThreadPoolExecutor(max_workers=inputs.jobs) as pool:
        for dest, data, error in pool.map(run_one, enumerate(dests)):
            if data is None:
                result.fail(f"{dest}: {error}")
                continue
            reported += 1
            _mode, target = import_target(dest)
            if not data.get("ok"):
                result.fail(f"{dest}: import of {target} failed: {data.get('error')}")
            else:
                loaded = data.get("file")
                expected = str((root / dest).resolve())
                if loaded != expected:
                    result.fail(f"{dest}: {target} resolved to {loaded}, not {expected}")
            for name in data.get("scripts_modules") or []:
                result.fail(f"{dest}: importing {target} loaded product module {name}")
            for item in data.get("outside") or []:
                result.fail(f"{dest}: importing {target} loaded {item}, outside the extracted root")
    help_cmd = [inputs.python, "-I", "-B", "-c", _DISPATCH_HELP_CHILD, str(root), DISPATCH_MODULE]
    try:
        proc = box.run(help_cmd, cwd=cwd, env=env, timeout=inputs.import_timeout)
        if proc.returncode != 0:
            tail = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-3:]
            result.fail(f"python -m {DISPATCH_MODULE} --help exited {proc.returncode}: {tail}")
        dispatch_ok = int(proc.returncode == 0)
    except subprocess.TimeoutExpired:
        result.fail(f"python -m {DISPATCH_MODULE} --help timed out after {inputs.import_timeout}s")
        dispatch_ok = 0
    result.inspected = {"python_modules": reported, "dispatch_help": dispatch_ok}
    return result


# --------------------------------------------------------------------------- V4 no product imports


def docstring_nodes(tree: ast.AST) -> set[int]:
    """Bare string expression statements: docstrings and other prose, which the rename keeps."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            ids.add(id(node.value))
    return ids


class OwnershipIndex:
    """Answers who owns a scripts/ module or path, from the frozen ownership map."""

    def __init__(self, ownership: dict[str, str], extracted_tops: set[str], extracted: Iterable[str] = ()) -> None:
        self.files = {key: owner for key, owner in ownership.items() if key.startswith(OLD_PREFIX)}
        self.extracted_tops = extracted_tops
        # Machinery per the tree manifest: the scripts/ source paths that are in the final tree.
        self.extracted = {path for path in extracted if path.startswith(OLD_PREFIX)}
        self.extracted_dirs = {
            "/".join(path.split("/")[:depth]) for path in self.extracted for depth in range(1, path.count("/") + 1)
        }
        self.dir_owners: dict[str, set[str]] = {}
        for key, owner in self.files.items():
            parts = key.split("/")
            for depth in range(1, len(parts)):
                self.dir_owners.setdefault("/".join(parts[:depth]), set()).add(owner)

    def module_owner(self, dotted: str) -> str | None:
        """The owner of the file Python binds for dotted (resolved under scripts/), or mixed, or None.

        Python prefers a regular package, then a module, then a namespace package (a directory without
        __init__.py); a namespace package belongs to its files' owner, or is mixed when they differ. The
        longest resolvable prefix decides, so an attribute import resolves to its module's owner.
        """
        parts = dotted.split(".")
        for depth in range(len(parts), 0, -1):
            base = OLD_PREFIX + "/".join(parts[:depth])
            for candidate in (base + "/__init__.py", base + ".py"):
                if candidate in self.files:
                    return self.files[candidate]
            owners = self.dir_owners.get(base)
            if owners:
                return next(iter(owners)) if len(owners) == 1 else MIXED
        return None

    def path_is_machinery(self, path: str) -> bool:
        path = path.rstrip("/")
        if path in self.files:
            return self.files[path] == MACHINERY
        return MACHINERY in self.dir_owners.get(path, set())

    def path_reference(self, path: str) -> str:
        """What a scripts/ path literal names: machinery (in the final tree), product, mixed, or other.

        A file is machinery when the tree manifest extracts it. A directory is machinery when it holds
        extracted files and no product file, mixed when it holds both (the scripts/ root does).
        """
        path = path.rstrip("/")
        if path in self.extracted:
            return MACHINERY
        if path in self.files:
            return PRODUCT if self.files[path] == PRODUCT else NOT_EXTRACTED
        if path in self.extracted_dirs:
            return MIXED if PRODUCT in self.dir_owners.get(path, set()) else MACHINERY
        owners = self.dir_owners.get(path)
        if owners:
            return PRODUCT if owners == {PRODUCT} else NOT_EXTRACTED
        return UNKNOWN

    def module_reference(self, dotted: str) -> str:
        """What a scripts.<dotted> module name names, by its longest resolvable prefix (see path_reference)."""
        parts = dotted.split(".")
        for depth in range(len(parts), 0, -1):
            base = OLD_PREFIX + "/".join(parts[:depth])
            for candidate in (base + "/__init__.py", base + ".py"):
                if candidate in self.extracted or candidate in self.files:
                    return self.path_reference(candidate)
            if base in self.extracted_dirs or base in self.dir_owners:
                return self.path_reference(base)
        return UNKNOWN

    def product_dependency(self, dotted: str, *, relative: bool = False) -> str | None:
        """Why importing dotted (a name under scripts/) needs product code, or None.

        Python initializes every parent package before the module, so a product-owned __init__.py on the
        way is a dependency even when the module itself is machinery. An absolute name whose top level is
        a standard-library module or a top-level name of the extracted tree is not resolved under scripts/;
        a relative import always is.
        """
        parts = dotted.split(".")
        if not relative and (parts[0] in sys.stdlib_module_names or parts[0] in self.extracted_tops):
            return None
        for depth in range(1, len(parts)):
            init = OLD_PREFIX + "/".join(parts[:depth]) + "/__init__.py"
            if self.files.get(init) == PRODUCT:
                return f"initializes product package {'.'.join(parts[:depth])} ({init})"
        owner = self.module_owner(dotted)
        if owner in (PRODUCT, MIXED):
            return f"is a {owner} package (scripts/{dotted.replace('.', '/')})"
        return None


def file_package(rel: str) -> list[str] | None:
    """The scripts/-relative package (__package__) of a file under lu_machinery/, or None elsewhere."""
    if not rel.startswith(NEW_PREFIX):
        return None
    return rel[len(NEW_PREFIX) :].split("/")[:-1]  # a module's and an __init__.py's package is its directory


def climb(package: list[str] | None, level: int) -> list[str] | None:
    """The package a relative import of this level starts from, or None when it leaves the tree."""
    if package is None or level - 1 > len(package):
        return None
    return package[: len(package) - (level - 1)]


def relative_base(rel: str, level: int) -> list[str] | None:
    """The scripts/-relative package a relative import of this level starts from, or None outside lu_machinery/."""
    return climb(file_package(rel), level)


def extracted_name(name: str) -> str | None:
    """The scripts/-relative name of a lu_machinery-qualified module name, or None for any other name."""
    root = NEW_PREFIX.rstrip("/")
    if name == root:
        return ""
    return name[len(root) + 1 :] if name.startswith(root + ".") else None


def package_argument(node: ast.expr | None, rel: str) -> list[str] | None:
    """The scripts/-relative package a loader's package argument names, when it is statically known."""
    if isinstance(node, ast.Name) and node.id == "__package__":
        return file_package(rel)
    if isinstance(node, ast.Attribute) and node.attr == "parent" and isinstance(node.value, ast.Name):
        return file_package(rel) if node.value.id == "__spec__" else None
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value:
        inner = extracted_name(node.value)
        if inner is not None:
            return inner.split(".") if inner else []
        if node.value == "scripts" or node.value.startswith("scripts."):
            return node.value.split(".")[1:]
        return node.value.split(".")
    return None


def call_argument(call: ast.Call, index: int, *names: str) -> ast.expr | None:
    found = call.args[index] if len(call.args) > index else None
    for keyword in call.keywords:
        if keyword.arg in names:
            found = keyword.value
    return found


def literal_strings(node: ast.expr | None) -> list[str]:
    if isinstance(node, ast.List | ast.Tuple | ast.Set):
        return [item.value for item in node.elts if isinstance(item, ast.Constant) and isinstance(item.value, str)]
    return []


def scan_python_source(
    rel: str,
    source: bytes,
    index: OwnershipIndex,
    unprefixed: list[str] | None = None,
    listed: list[str] | None = None,
) -> list[str]:
    """V4 findings for one file (brief amendment A1).

    Findings: (a) import statements of scripts or of product code, and loader targets inside the
    lu_machinery namespace that name product code; (b) scripts.<module> references and scripts/ path
    literals that name a machinery file of the tree manifest (a missed rename). References that name
    product code (for example a module passed to a subprocess under the product checkout) are appended
    to listed. Unprefixed machinery imports, which resolve only while scripts/ is on sys.path, are
    appended to unprefixed.
    """
    allowed: list[str] = listed if listed is not None else []
    try:
        tree = ast.parse(source, filename=rel)
    except (SyntaxError, ValueError) as exc:
        return [f"{rel}:{getattr(exc, 'lineno', 0) or 0}: cannot parse ({exc.__class__.__name__}: {exc})"]
    findings: list[str] = []
    prose = docstring_nodes(tree)

    def check_import(name: str, line: int, *, relative: bool = False, shown: str = "") -> bool:
        """Report an import that needs product code. relative: name is already scripts/-relative."""
        if not relative:
            if name == "scripts" or name.startswith("scripts."):
                findings.append(f"{rel}:{line}: import of {name}")
                return True
            inner = extracted_name(name)
            if inner is not None:  # lu_machinery.<x> is scripts/<x> in the ownership map
                return bool(inner) and check_import(inner, line, relative=True, shown=f"import of {name}")
        reason = index.product_dependency(name, relative=relative)
        if reason is None:
            top = name.split(".")[0]
            plain = top not in sys.stdlib_module_names and top not in index.extracted_tops
            if unprefixed is not None and not relative and plain and index.module_owner(name) == MACHINERY:
                unprefixed.append(f"{rel}:{line}: {name}")
            return False
        label = shown or (f"relative import of scripts.{name}" if relative else f"import of {name}")
        findings.append(f"{rel}:{line}: {label} {reason}")
        return True

    def check_from(module: str, names: Sequence[str], line: int, *, relative: bool, shown: str = "") -> None:
        if module and check_import(module, line, relative=relative, shown=shown):
            return
        for name in names:
            if name != "*":  # a submodule can have another owner than its package
                child = f"{module}.{name}" if module else name
                check_import(child, line, relative=relative, shown=f"{shown}.{name}" if shown else "")

    def check_relative(base: list[str] | None, rest: str, names: Sequence[str], line: int, what: str) -> None:
        if base is None:
            findings.append(f"{rel}:{line}: {what} cannot be resolved statically; its owner is unknown")
            return
        module = ".".join([*base, *(rest.split(".") if rest else [])])
        check_from(module, names, line, relative=True)

    def check_reference(target: str, line: int) -> None:
        """An absolute loader target: scripts.<x> is judged by the string scan; a lu_machinery-qualified
        target must not name product code; an unprefixed product target is an allowed, listed reference."""
        if target == "scripts" or target.startswith("scripts."):
            return
        if extracted_name(target) is not None:
            check_import(target, line)
            return
        reason = index.product_dependency(target)
        if reason is not None:
            allowed.append(f"{rel}:{line}: loader target {target} {reason}")
        else:
            check_import(target, line)  # records an unprefixed machinery target in unprefixed

    def check_loader(call: ast.Call, called: str) -> None:
        line = call.lineno
        target_node = call_argument(call, 0, "name", "mod_name")
        target = target_node.value if isinstance(target_node, ast.Constant) else None
        if not isinstance(target, str) or not target:
            return  # computed targets are beyond a static scan (the rename tools report them)
        if called in ("import_module", "find_spec"):
            if target.startswith("."):
                level = len(target) - len(target.lstrip("."))
                base = climb(package_argument(call_argument(call, 1, "package"), rel), level)
                check_relative(base, target.lstrip("."), [], line, f"relative loader target {target!r}")
            else:
                check_reference(target, line)
        elif called == "__import__":
            level_node = call_argument(call, 4, "level")
            raw_level = 0 if level_node is None else level_node.value if isinstance(level_node, ast.Constant) else None
            fromlist = literal_strings(call_argument(call, 3, "fromlist"))
            if not isinstance(raw_level, int) or isinstance(raw_level, bool) or raw_level < 0:
                findings.append(f"{rel}:{line}: __import__ level is not a literal integer; its owner is unknown")
            elif raw_level > 0:
                what = f"__import__({target!r}, level={raw_level})"
                check_relative(relative_base(rel, raw_level), target, fromlist, line, what)
            elif extracted_name(target) is not None:
                check_from(target, fromlist, line, relative=False)
            else:
                check_reference(target, line)
                for name in fromlist:
                    check_reference(f"{target}.{name}", line)
        elif called == "resolve_name":
            check_reference(target.split(":", 1)[0], line)
        else:
            check_reference(target, line)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                check_import(alias.name, node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == "scripts":
            for alias in node.names:
                findings.append(f"{rel}:{node.lineno}: import of scripts.{alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            check_from(node.module, [alias.name for alias in node.names], node.lineno, relative=False)
        elif isinstance(node, ast.ImportFrom) and node.level > 0:
            base = relative_base(rel, node.level)
            if base is not None:  # outside lu_machinery/ a relative import cannot reach scripts/
                names = [alias.name for alias in node.names]
                check_relative(base, node.module or "", names, node.lineno, "relative import")
        elif isinstance(node, ast.Call):
            func = node.func
            called = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
            if called in LOADERS:
                check_loader(node, called)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str | bytes) and id(node) not in prose:
            text = node.value if isinstance(node.value, str) else node.value.decode("latin-1")
            for match in MODULE_REF.finditer(text):
                ref = match.group(0)
                last = ref.rsplit(".", 1)[-1]
                if ref.count(".") == 1 and last in FILE_SUFFIXES:
                    continue
                owner = index.module_reference(ref[len("scripts.") :])
                if owner == MACHINERY:
                    findings.append(f"{rel}:{node.lineno}: string references machinery module {ref} (missed rename)")
                else:
                    allowed.append(f"{rel}:{node.lineno}: {owner} module reference {ref}")
            for match in PATH_REF.finditer(text):
                rest = match.group(1).rstrip("/")
                shown = f"scripts/{rest}" if rest else "scripts/"
                owner = index.path_reference((OLD_PREFIX + rest).rstrip("/"))
                if owner == MACHINERY:
                    findings.append(f"{rel}:{node.lineno}: string holds machinery path {shown} (missed rename)")
                else:
                    allowed.append(f"{rel}:{node.lineno}: {owner} path reference {shown}")
    return findings


def check_v4(inputs: Inputs) -> CheckResult:
    result = CheckResult("V4", "no scripts or product imports, no missed machinery renames (A1)")
    tree = tree_paths(inputs.repo, "HEAD")
    tops = {path.split("/")[0].removesuffix(".py") for path in tree}
    index = OwnershipIndex(inputs.ownership, tops, (source for source, _dest in inputs.manifest))
    scanned = 0
    unprefixed: list[str] = []
    for rel in sorted(path for path in tree if path.endswith(".py")):
        path = inputs.repo / rel
        if path.is_symlink() or not path.is_file():
            result.fail(f"{rel}: not a regular file in the working tree")
            continue
        scanned += 1
        for finding in scan_python_source(rel, path.read_bytes(), index, unprefixed, result.listed):
            result.fail(finding)
    if unprefixed:
        result.notes.append(
            f"{len(unprefixed)} unprefixed import(s) of machinery modules resolve only while scripts/ is on "
            f"sys.path (not product coupling; V3 proves the module-level ones): {unprefixed[:20]}"
        )
    result.inspected = {"python_files": scanned}
    return result


# --------------------------------------------------------------------------- tool runner


def run_tool(inputs: Inputs, tool: str, args: Sequence[str], report: Path, cwd: Path) -> dict[str, Any]:
    """Run one packaging/machinery-move tool; exit 2 (Unusable) unless it ran and wrote its report."""
    script = inputs.tools_dir / tool
    if not script.is_file():
        raise Unusable(f"{script} is absent")
    cmd = [inputs.tool_python, "-B", str(script), *args]
    timeout = inputs.test_timeout
    box = sandbox()
    try:
        proc = box.run(cmd, cwd=cwd, env=box.env(), timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise Unusable(f"{tool} timed out after {timeout}s") from exc
    stderr = proc.stderr.decode("utf-8", "replace").strip()
    if proc.returncode not in (0, 1) or not report.is_file():
        raise Unusable(f"{tool} could not run (exit {proc.returncode}): {stderr.splitlines()[-3:]}")
    try:
        data = read_child_json(report)
    except (OSError, ValueError) as exc:
        raise Unusable(f"{tool} wrote an unreadable report: {exc}") from exc
    if not isinstance(data, dict):
        raise Unusable(f"{tool} wrote a report that is not a JSON object")
    if data.get("map_sha256") != sha256_file(inputs.map_path):
        raise Unusable(f"{tool} report map_sha256 {data.get('map_sha256')!r} does not match --map")
    return data


def rename_args(inputs: Inputs, tool: str, mode: str, root: Path, report: Path, paths: Sequence[str]) -> list[str]:
    args = [mode, "--map", str(inputs.map_path), "--root", str(root), "--report", str(report)]
    if tool == "rename_python.py":
        args += ["--jobs", str(inputs.jobs)]
        if inputs.external_names is not None:
            args += ["--external-names", str(inputs.external_names)]
    return [*args, *paths]


# --------------------------------------------------------------------------- V5 renames


def check_v5(inputs: Inputs, scratch: Path) -> CheckResult:
    result = CheckResult("V5", "held-out rename expectations hold; rename tools find nothing left to rewrite")
    blob_ids: dict[str, str] = {}
    for line in git_z(inputs.repo, "ls-tree", "-r", "-z", "--full-tree", "HEAD"):
        meta, path = line.split("\t", 1)
        mode, kind, oid = meta.split()
        if kind == "blob" and mode in ("100644", "100755"):
            blob_ids[path] = oid
    wanted = sorted({blob_ids[row.dest] for row in inputs.expectations if row.dest in blob_ids})
    contents = read_blobs(inputs.repo, wanted)  # the final-tree bytes, never a file reached through a link
    per_class = dict.fromkeys(CLASSES, 0)
    for row in inputs.expectations:
        per_class[row.klass] += 1
        where = f"expectation line {row.line} ({row.klass} {row.dest})"
        if row.dest not in blob_ids:
            result.fail(f"{where}: no regular file at this path in the final tree")
            continue
        found = row.literal.encode("utf-8") in contents[blob_ids[row.dest]]
        if row.present and not found:
            result.fail(f"{where}: expected literal {row.literal!r} is missing")
        elif not row.present and found:
            result.fail(f"{where}: forbidden literal {row.literal!r} is present")
    tool_files = 0
    for tool in RENAME_TOOLS:
        report = scratch / f"v5-{tool}.json"
        args = rename_args(inputs, tool, "--check", inputs.repo, report, [])
        data = run_tool(inputs, tool, args, report, scratch)
        rewrites = data.get("rewrites") or []
        changed = data.get("files_changed") or []
        if not isinstance(rewrites, list) or not isinstance(changed, list):
            raise Unusable(f"{tool} report lacks rewrites/files_changed lists")
        scanned = data.get("files_scanned")
        tool_files += scanned if isinstance(scanned, int) else 0
        for item in rewrites[:50]:
            if isinstance(item, dict):
                where = f"{item.get('path')}:{item.get('line')}"
                result.fail(f"{tool} --check would still rewrite {where}: {item.get('before')} -> {item.get('after')}")
            else:
                result.fail(f"{tool} --check would still rewrite {item!r}")
        if len(rewrites) > 50:
            result.fail(f"{tool} --check: {len(rewrites) - 50} more pending rewrites (see the tool's report)")
        if changed and not rewrites:
            result.fail(f"{tool} --check would change {len(changed)} file(s): {changed[:10]}")
        unresolved = data.get("unresolved") or []
        result.notes.append(
            f"{tool}: {len(rewrites)} pending rewrites, {len(unresolved) if isinstance(unresolved, list) else '?'} "
            "unresolved references (reported by the tool; V4 judges what remains)"
        )
    result.inspected = {"expectation_rows": len(inputs.expectations), "tool_files_scanned": tool_files}
    result.inspected.update({f"class_{klass}": count for klass, count in per_class.items()})
    return result


# --------------------------------------------------------------------------- V6 dispatch history


def follow_log(repo: Path, rev: str, path: str) -> list[str]:
    out = git_text(repo, "log", "--follow", "--format=%H", rev, "--", path)
    return [line for line in out.splitlines() if line]


def check_v6(inputs: Inputs) -> CheckResult:
    result = CheckResult("V6", f"source history of {DISPATCH_SOURCE} survives in {DISPATCH_DEST}")
    source_commits = follow_log(inputs.source_repo, inputs.source, DISPATCH_SOURCE)
    extracted = set(follow_log(inputs.repo, "HEAD", DISPATCH_DEST))
    for commit in source_commits:
        mapped = inputs.commit_map.get(commit)
        if mapped is None:
            result.fail(f"source commit {commit} is not in the commit map")
        elif ZERO_OID.fullmatch(mapped):
            result.fail(f"source commit {commit} was pruned by the rewrite (maps to {mapped})")
        elif mapped not in extracted:
            result.fail(f"source commit {commit} maps to {mapped}, which is not in the {DISPATCH_DEST} history")
    result.inspected = {"source_commits": len(source_commits), "extracted_commits": len(extracted)}
    return result


# --------------------------------------------------------------------------- V9 transformation commit


def check_v9(inputs: Inputs) -> CheckResult:
    result = CheckResult("V9", "HEAD is the single transformation commit on the rewrite tip, with the frozen tree")
    parents = git_text(inputs.repo, "rev-list", "--parents", "-n", "1", "HEAD").split()[1:]
    after_tip = int(git_text(inputs.repo, "rev-list", "--count", f"{inputs.rewrite_tip}..HEAD").strip())
    if len(parents) != 1:
        result.fail(f"HEAD {inputs.head} has {len(parents)} parents; exactly one (the rewrite tip) is required")
    elif parents[0] != inputs.rewrite_tip:
        result.fail(f"HEAD's parent is {parents[0]}, not the rewrite tip {inputs.rewrite_tip}")
    if after_tip != 1:
        result.fail(f"{after_tip} commits follow the rewrite tip; exactly one transformation commit is required")
    tree = git_text(inputs.repo, "rev-parse", "HEAD^{tree}").strip()
    if tree != inputs.final_tree:
        result.fail(f"HEAD's tree is {tree}, not the frozen --final-tree {inputs.final_tree}")
    dests = set(inputs.dests)
    additions = {dest for source, dest in inputs.manifest if source == ADDITION}
    at_tip = set(tree_paths(inputs.repo, inputs.rewrite_tip))
    for dest in sorted(additions & at_tip):
        result.fail(f"addition row {dest} already exists at the rewrite tip; an addition must be new")
    entries = git_z(
        inputs.repo,
        "diff-tree",
        "-r",
        "-z",
        "--no-renames",
        "--no-commit-id",
        "--name-status",
        inputs.rewrite_tip,
        "HEAD",
    )
    changes = 0
    for status, path in zip(entries[0::2], entries[1::2], strict=False):
        changes += 1
        kind = status[:1]
        if kind == "A" and path not in additions:
            result.fail(f"the transformation adds {path}, which is not a manifest addition row")
        elif kind in ("M", "T") and path not in dests:
            result.fail(f"the transformation modifies {path}, which is not a manifest path")
        elif kind == "D" and path in dests:
            result.fail(f"the transformation deletes {path}, which the manifest keeps")
        elif kind not in ("A", "M", "T", "D"):
            result.fail(f"the transformation has an unexpected change {status} {path}")
    result.inspected = {"commits_after_tip": after_tip, "diff_entries": changes}
    return result


# --------------------------------------------------------------------------- HP history policy


def check_history_policy(inputs: Inputs, scratch: Path) -> CheckResult:
    result = CheckResult("HP", "history_policy.py verify passes up to the rewrite tip")
    if inputs.history_policy is None or inputs.policy_sha256 is None:
        result.status = "skipped"
        result.notes.append("not requested (--history-policy and --policy-sha256 absent)")
        return result
    script = inputs.tools_dir / HISTORY_POLICY_TOOL
    if not script.is_file():
        raise Unusable(f"{script} is absent")
    cmd = [
        inputs.tool_python,
        "-B",
        str(script),
        "verify",
        "--repo",
        str(inputs.repo),
        "--rev",
        inputs.rewrite_tip,
        "--policy",
        str(inputs.history_policy),
        "--policy-sha256",
        inputs.policy_sha256,
        "--commit-map",
        str(inputs.commit_map_path),
        "--path-rename",
        PATH_RENAME,
    ]
    box = sandbox()
    try:
        proc = box.run(cmd, cwd=scratch, env=box.env(), timeout=inputs.test_timeout)
    except subprocess.TimeoutExpired as exc:
        raise Unusable(f"{HISTORY_POLICY_TOOL} verify timed out after {inputs.test_timeout}s") from exc
    output = (proc.stdout + proc.stderr).decode("utf-8", "replace").strip().splitlines()
    result.notes.extend(output[-20:])
    if proc.returncode == 1:
        result.fail(f"{HISTORY_POLICY_TOOL} verify reported findings (exit 1)")
    elif proc.returncode != 0:
        raise Unusable(f"{HISTORY_POLICY_TOOL} verify could not run (exit {proc.returncode}): {output[-3:]}")
    result.inspected = {"policy_runs": 1}
    return result


# --------------------------------------------------------------------------- V8 harness

# Runs pytest on the whole [run] files and records every collected node id before any filtering and the
# terminal outcome of each, so no configuration (for example addopts = --collect-only or -k) and no conftest
# (deselecting, or silently dropping items) can shrink the run unnoticed.
_PYTEST_CHILD = r"""
import json, sys
harness, root, out, *files = sys.argv[1:]
sys.path[:0] = [harness, root]
import pytest


class Recorder:
    def __init__(self):
        self.collected = []  # every item as collected, before any hook filters, deselects or reorders it
        self.deselected = 0
        self.collect_errors = 0
        self.results = {}  # node id -> terminal outcome

    def pytest_itemcollected(self, item):
        self.collected.append(item.nodeid)

    def pytest_collectreport(self, report):
        if report.failed:
            self.collect_errors += 1

    def pytest_deselected(self, items):
        self.deselected += len(items)

    def pytest_runtest_logreport(self, report):
        node = report.nodeid
        xfail = hasattr(report, "wasxfail")
        if report.when == "setup":
            if report.failed:
                self.results[node] = "errors"
            elif report.skipped:
                self.results[node] = "xfailed" if xfail else "skipped"
        elif report.when == "call":
            if xfail:
                self.results[node] = "xfailed" if report.skipped else "xpassed"
            else:
                self.results[node] = report.outcome
        elif report.failed:
            self.results[node] = "errors"


recorder = Recorder()
code = int(pytest.main(["-p", "no:cacheprovider", "--rootdir", harness, *files], plugins=[recorder]))
with open(out, "w", encoding="utf-8") as handle:
    json.dump(
        {
            "exit": code,
            "collected": recorder.collected,
            "deselected": recorder.deselected,
            "collect_errors": recorder.collect_errors,
            "results": recorder.results,
        },
        handle,
    )
sys.exit(code)
"""


class HarnessPathError(Exception):
    """A harness path would be written through a symlink or over a non-file."""


def harness_target(root: Path, rel: str) -> Path:
    """The path to write rel at under root, refusing any symlinked or non-directory component."""
    current = root
    parts = rel.split("/")
    for part in parts[:-1]:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            raise HarnessPathError(f"{rel}: harness component {current.relative_to(root)} is a symlink or a file")
    target = current / parts[-1]
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise HarnessPathError(f"{rel}: harness path is a symlink or not a regular file")
    return target


def read_blobs(repo: Path, oids: Sequence[str]) -> dict[str, bytes]:
    """Blob contents by id, through one git cat-file --batch call."""
    out = git(repo, "cat-file", "--batch", stdin="".join(f"{oid}\n" for oid in oids).encode()).stdout
    blobs: dict[str, bytes] = {}
    position = 0
    for oid in oids:
        header_end = out.index(b"\n", position)
        header = out[position:header_end].decode().split()
        if len(header) != 3 or header[1] != "blob":
            raise Unusable(f"git cat-file returned {header} for {oid}")
        size = int(header[2])
        start = header_end + 1
        blobs[oid] = out[start : start + size]
        position = start + size + 1
    return blobs


def copy_from_source(inputs: Inputs, paths: Iterable[str], dest_root: Path) -> int:
    """Write the listed files from --source into the harness; never through a symlink."""
    wanted = set(paths)
    entries = []
    for line in git_z(inputs.source_repo, "ls-tree", "-r", "-z", inputs.source, "--", *sorted(wanted)):
        meta, path = line.split("\t", 1)
        mode, kind, oid = meta.split()
        if path in wanted and kind == "blob" and mode in ("100644", "100755"):
            entries.append((path, mode, oid))
    blobs = read_blobs(inputs.source_repo, [oid for _path, _mode, oid in entries])
    targets = [(harness_target(dest_root, path), mode, oid) for path, mode, oid in entries]
    for target, mode, oid in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.parent.is_symlink() or not inside(target.parent, dest_root):
            raise HarnessPathError(f"{target}: harness directory escapes the harness")
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW
        descriptor = os.open(target, flags, 0o755 if mode == "100755" else 0o644)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(blobs[oid])
        target.chmod(0o755 if mode == "100755" else 0o644)
    return len(targets)


def check_v8(inputs: Inputs, scratch: Path) -> CheckResult:
    result = CheckResult("V8", "ported machinery tests pass against the extracted code")
    if not inputs.run_tests:
        result.status = "skipped"
        result.notes.append("not requested (--run-tests absent)")
        return result
    harness = scratch / "harness"
    if inside(harness, inputs.repo):
        raise Unusable(f"the temporary harness {harness} would be inside --repo; set TMPDIR elsewhere")
    clone = git(scratch, "clone", "--quiet", "--shared", "--no-checkout", str(inputs.repo), str(harness), check=False)
    if clone.returncode != 0:
        raise Unusable(f"cannot clone --repo into the harness: {clone.stderr.decode('utf-8', 'replace').strip()}")
    git(harness, "checkout", "--quiet", "--detach", inputs.head)
    listed = inputs.tests_run + inputs.tests_support
    overlaid = sorted(path for path in listed if (harness / path).exists() or (harness / path).is_symlink())
    if overlaid:
        result.notes.append(f"{len(overlaid)} listed test file(s) replace extracted copies: {overlaid[:10]}")
    try:
        copied = copy_from_source(inputs, listed, harness)
    except HarnessPathError as exc:
        result.fail(f"the extracted tree blocks the harness: {exc}")
        result.inspected = {"files_copied": 0, "tests_collected": 0}
        return result
    if copied != len(listed):
        raise Unusable(f"copied {copied} of {len(listed)} {TESTS_LIST} files (regular files) from --source")
    for tool in RENAME_TOOLS:
        report = scratch / f"v8-{tool}.json"
        args = rename_args(inputs, tool, "--apply", harness, report, listed)
        data = run_tool(inputs, tool, args, report, scratch)
        rewrites = data.get("rewrites") or []
        unresolved = data.get("unresolved") or []
        result.notes.append(
            f"{tool} --apply on the test copies: {len(rewrites) if isinstance(rewrites, list) else '?'} rewrites, "
            f"{len(unresolved) if isinstance(unresolved, list) else '?'} unresolved"
        )
    record = scratch / "v8-pytest.json"
    cmd = [inputs.python, "-I", "-B", "-c", _PYTEST_CHILD, str(harness), str(inputs.repo), str(record)]
    cmd += inputs.tests_run
    box = sandbox()
    try:
        proc = box.run(cmd, cwd=harness, env=box.env(), timeout=inputs.test_timeout)
    except subprocess.TimeoutExpired:
        result.fail(f"the harness pytest run timed out after {inputs.test_timeout}s")
        result.inspected = {"files_copied": copied, "tests_collected": 0}
        return result
    output = (proc.stdout + proc.stderr).decode("utf-8", "replace").strip().splitlines()
    run_record: dict[str, Any] = {}
    try:
        run_record = read_child_json(record)
    except (OSError, ValueError) as exc:
        result.fail(f"pytest wrote no readable run record (exit {proc.returncode}, {exc}): {output[-15:]}")
    collected = [str(item) for item in run_record.get("collected") or []]
    results: dict[str, str] = {str(k): str(v) for k, v in dict(run_record.get("results") or {}).items()}
    deselected = int(run_record.get("deselected") or 0)
    collect_errors = int(run_record.get("collect_errors") or 0)
    outcomes = {key: 0 for key in ("passed", "failed", "errors", "skipped", "xfailed", "xpassed")}
    for node in collected:
        if node in results:
            outcomes[results[node]] = outcomes.get(results[node], 0) + 1
    not_run = [node for node in dict.fromkeys(collected) if node not in results]
    result.notes.append(
        f"pytest exit {proc.returncode}; collected {len(collected)}; not run {len(not_run)}; {outcomes}"
    )
    if proc.returncode != 0 and run_record:
        result.fail(f"pytest exited {proc.returncode}: {output[-15:]}")
    if not collected:
        result.fail("pytest collected zero tests")
    if not_run:
        result.fail(f"{len(not_run)} collected test(s) never ran (deselected, dropped or collect-only): {not_run[:10]}")
    if deselected:
        result.fail(f"{deselected} test(s) were deselected; every test of the listed files must run")
    if collect_errors:
        result.fail(f"{collect_errors} collection error(s)")
    for path in inputs.tests_run:
        nodes = [node for node in collected if node == path or node.startswith(path + "::")]
        if not nodes:
            result.fail(f"{path}: no test collected from this listed file")
        elif not any(results.get(node) == "passed" for node in nodes):
            result.fail(f"{path}: no test of this listed file passed (all skipped, xfailed, failed or not run)")
    failed, errored = outcomes["failed"], outcomes["errors"]
    if failed or errored or outcomes["xpassed"]:
        result.fail(f"{failed} test(s) failed, {errored} errored, {outcomes['xpassed']} unexpectedly passed")
    problems = worktree_mismatches(inputs.repo)
    if problems:
        result.fail(f"--repo changed while the tests ran: {problems[:10]}")
    result.inspected = {
        "files_copied": copied,
        "tests_collected": len(collected),
        "tests_passed": outcomes.get("passed", 0),
        "tests_failed": failed,
        "tests_errored": errored,
        "tests_skipped": outcomes.get("skipped", 0),
        "tests_xfailed": outcomes.get("xfailed", 0),
        "tests_deselected": deselected,
        "tests_not_run": len(not_run),
    }
    return result


# --------------------------------------------------------------------------- V7 denominators

# The count that proves each check looked at something; zero always fails.
PRIMARY = {
    "V1": "tree_paths",
    "V2": "history_commits",
    "V3": "python_modules",
    "V4": "python_files",
    "V5": "expectation_rows",
    "V6": "source_commits",
    "V8": "tests_collected",
    "V9": "commits_after_tip",
    "HP": "policy_runs",
}


def check_v7(inputs: Inputs, results: Sequence[CheckResult]) -> CheckResult:
    result = CheckResult("V7", "every check inspected the expected, nonzero number of items")
    by_check = {item.check: item for item in results}
    rows = len(inputs.manifest)
    python = len(inputs.python_dests)
    expected = {
        ("V1", "tree_paths"): rows,
        ("V1", "manifest_rows"): rows,
        ("V3", "python_modules"): python,
        ("V4", "python_files"): python,
        ("V3", "dispatch_help"): 1,
    }
    for (check, key), want in expected.items():
        got = by_check[check].inspected.get(key)
        if got != want:
            result.fail(f"{check} inspected {key}={got}, expected {want} (tree-manifest denominator)")
    for item in results:
        if item.status == "skipped":
            continue
        key = PRIMARY[item.check]
        if not item.inspected.get(key):
            result.fail(f"{item.check} inspected zero {key}")
        for name, count in item.inspected.items():
            if count == 0 and name != key and not name.startswith("tests_") and name != "history_only_entries":
                result.fail(f"{item.check} inspected zero {name}")
    if python == 0:
        result.fail("the tree manifest lists no Python files")
    result.inspected = {"checks": len(results), "manifest_rows": rows, "manifest_python_files": python}
    return result


# --------------------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="verify_extraction.py",
        description=(
            "Prove, before the first public push, that an extracted machinery repository has exactly the approved\n"
            "final tree, imports only from itself, carries the expected renames, keeps the full dispatch history and\n"
            "passes the ported machinery tests. Read-only on every input. Use it on the disposable extraction clone\n"
            "after git-filter-repo and the transformation commit; it does not extract, rewrite or publish anything."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""\
Examples:
  .venv/bin/python packaging/machinery-move/verify_extraction.py \\
      --repo "$EXTRACT" --source-repo "$SRC" --source "$S" --commit-map "$EXTRACT/.git/filter-repo/commit-map" \\
      --tree-manifest tree.tsv --history-paths history.txt --exclude exclude.txt --expectations heldout.tsv \\
      --rewrite-tip "$TIP" --final-tree "$TREE" --map ownership.json \\
      --tool-python "$TOOL_ENV/bin/python" --external-names external-names.txt \\
      --history-policy policy.tsv --policy-sha256 "$POLICY_SHA" --run-tests --report verify.json
  .venv/bin/python packaging/machinery-move/verify_extraction.py ... (same required inputs, no --run-tests) --jobs 16

Input formats:
  --tree-manifest  TSV source_path<TAB>dest_path, one row per file of the final tree. An approved addition
                   (lu_machinery/__init__.py, an approved workflow destination) is written -<TAB>dest_path.
                   A source row's dest must be its {PATH_RENAME} rename. Historical aliases are not rows.
  --history-paths  one source path per line: accepted aliases that may exist only in history.
  --exclude        one source path per line (a trailing / excludes a directory): must appear nowhere.
  --expectations   evaluator-owned TSV class<TAB>dest_path<TAB>present|absent<TAB>literal; class is one of
                   {", ".join(CLASSES)}; imports/module-strings rows name .py files,
                   non-python rows other files. The literal is matched byte for byte in the final-tree file.
  --commit-map     git-filter-repo's commit-map: optional 'old new' header, then '<old-oid> <new-oid>' lines;
                   an all-zero new id means the commit was pruned.
  --map            ownership JSON {{"scripts/<path>": "machinery"|"product", ...}} (PR 12764 tools' --map).
  {TESTS_LIST} (next to this tool, used by --run-tests): '# [run]' test files and '# [support]' fixture/
                   helper closure, one repository path per line, read from --source in --source-repo.

Checks (every finding is printed; nothing stops at the first one):
  V1  HEAD's tracked paths equal the manifest dest paths; missing and extra paths are both reported.
  V2  no --exclude path, as written or renamed {PATH_RENAME}, is in the final tree or in any commit reachable
      from HEAD (every added, changed or deleted path, merges diffed against each parent); no --history-paths
      entry is in the final tree. A form that is a manifest addition row (scripts/__init__.py renames onto
      lu_machinery/__init__.py) may exist only after the rewrite tip, which V9 binds to the frozen tree.
  V3  each manifest .py file imports in its own `python -I -B` child (--python), cwd an empty temp dir, HOME and
      TMPDIR temporary, only --repo prepended to sys.path. Dotted names import by name (the resolved __file__
      must be that file); other files load from their path under a synthetic name. A loaded `scripts` module or
      any module file outside --repo and the interpreter's own prefixes is a finding. Then
      `python -m {DISPATCH_MODULE} --help` must exit 0.
  V4  static AST scan of every .py file at HEAD (brief amendment A1). Fails only on:
      (a) an import statement of scripts, or of product code per --map: a product module or namespace
          package, a product __init__.py that Python initializes on the way to a machinery module, a
          from-import's product submodule, a relative import resolved under scripts/, or a
          lu_machinery-qualified name mapped back to scripts/. Loader targets inside the lu_machinery
          namespace count too: relative import_module/find_spec targets (through a literal package or
          __package__), __import__ with a level, and lu_machinery-qualified targets. A relative target
          that cannot be resolved statically is a finding.
      (b) a `scripts.<module>` reference or `scripts/<path>` literal that names a machinery file of the tree
          manifest, or a directory holding only such files (a missed rename).
      References that name product code (for example a module passed to a subprocess that runs under the
      product checkout), mixed directories such as the scripts/ root, and other unextracted names are
      allowed: they are listed with file:line and a count (all of them in --report). Unprefixed imports of
      machinery modules (resolved only while scripts/ is on sys.path) are a note. Docstrings and comments
      are prose and are not scanned; paths split into components are not literals.
  V5  every --expectations row holds; then {", ".join(RENAME_TOOLS)} --check on --repo report zero pending
      rewrites (idempotence). Their unresolved counts are printed as notes.
  V6  every commit of `git -C SRC log --follow SOURCE -- {DISPATCH_SOURCE}` maps through --commit-map to a commit of
      `git -C EXTRACT log --follow -- {DISPATCH_DEST}`; unmapped and pruned commits are findings.
  V7  denominators: V1 must inspect the manifest row count, V3 and V4 the manifest .py count; any check that ran
      with a zero count fails.
  V8  (--run-tests) clone --repo (--shared) into a temp harness outside it, copy the {TESTS_LIST} files
      from --source over it (never through a symlink), apply the rename tools to those copies with --map, run
      pytest on the whole [run] files with the harness and --repo on sys.path (--python -I, no extra pytest
      arguments). A plugin records every collected node id before any filtering and each one's outcome. Fails
      on a nonzero pytest exit, zero collected tests, any collected test that never ran (deselected, dropped by
      a hook, or a collect-only configuration), a collection error, a [run] file with no collected test or with
      no passing test, any failed, errored or unexpectedly passing test, or --repo changing during the run.
      Skips and expected failures are allowed and counted when the file also has a passing test.
  V9  HEAD has exactly one parent, the --rewrite-tip, and is the only commit after it; HEAD^{{tree}} equals
      --final-tree; its diff against the tip only adds manifest addition rows (new at the tip), modifies manifest
      paths and deletes nothing the manifest keeps.
  HP  (--history-policy) runs {HISTORY_POLICY_TOOL} verify --repo EXTRACT --rev REWRITE_TIP --policy FILE
      --policy-sha256 HEX --commit-map FILE --path-rename {PATH_RENAME}; its nonzero exit fails.

Read-only enforcement: every git call, V3 import child, rename tool, {HISTORY_POLICY_TOOL} run and the V8
pytest run executes in bubblewrap (bwrap): / read-only, private /dev and /proc, every namespace unshared (no
network), HOME and TMPDIR in the scratch directory, which is the only writable path. Replace refs are ignored
(GIT_NO_REPLACE_OBJECTS=1), signatures are not checked, no global or system git config is read.

Preconditions (exit 2 otherwise): bwrap can start that sandbox; every input exists and parses; both
repositories are full (not shallow, no grafts) top-level clones; every file in --repo's working tree equals
HEAD by bytes and mode, with nothing untracked or ignored (hashed directly; index flags such as
assume-unchanged or skip-worktree are not trusted); --source holds {DISPATCH_SOURCE}; the rename tools (and
{HISTORY_POLICY_TOOL} for --history-policy) sit next to this tool; --report is not a symlink, an input file,
or inside either repository, its git storage or the tools directory.

Outputs:
  stdout: one block per check with PASS/FAIL/SKIPPED, its inspected counts, findings and notes, then a verdict.
  --report writes the same as JSON (atomic replace). The scratch directory lives under $TMPDIR and is removed.
  Nothing else is written.

Exit codes:
  0  every check that ran passed
  1  at least one finding
  2  an input is missing, unreadable or malformed, a required tool is absent or could not run

Related:
  packaging/machinery-move/README.md and the rename tools (PR 12764); {HISTORY_POLICY_TOOL}; step-6 plan
  (STEP6-PLAN C-4674, plan-v1 section 4 step 5); machinery move contract v3 section 4 (the ported tests).
""",
    )
    req = parser.add_argument_group("required inputs")
    req.add_argument("--repo", type=Path, required=True, metavar="EXTRACT", help="The extracted repository root.")
    req.add_argument(
        "--source-repo", type=Path, required=True, metavar="SRC", help="A full clone that contains --source."
    )
    req.add_argument("--source", required=True, metavar="SHA", help="The frozen source commit that was extracted.")
    req.add_argument(
        "--commit-map", type=Path, required=True, metavar="FILE", help="git-filter-repo's commit-map (old new)."
    )
    req.add_argument(
        "--tree-manifest",
        type=Path,
        required=True,
        metavar="FILE",
        help="TSV source_path<TAB>dest_path of the final tree.",
    )
    req.add_argument(
        "--history-paths", type=Path, required=True, metavar="FILE", help="Source paths allowed only in history."
    )
    req.add_argument(
        "--exclude", type=Path, required=True, metavar="FILE", help="Source paths that must appear nowhere."
    )
    req.add_argument(
        "--expectations", type=Path, required=True, metavar="FILE", help="Evaluator-owned held-out rename TSV."
    )
    req.add_argument(
        "--rewrite-tip",
        required=True,
        metavar="SHA",
        help="The commit git-filter-repo produced, before the transformation commit.",
    )
    req.add_argument(
        "--final-tree", required=True, metavar="HEX", help="The frozen, reviewed tree id of the final HEAD (full hex)."
    )
    req.add_argument(
        "--map", type=Path, required=True, metavar="FILE", help="Frozen ownership map JSON (the rename tools' --map)."
    )
    opt = parser.add_argument_group("optional")
    opt.add_argument(
        "--history-policy",
        type=Path,
        metavar="FILE",
        help="Frozen history policy TSV; runs history_policy.py verify (needs --policy-sha256). Default: not run.",
    )
    opt.add_argument("--policy-sha256", metavar="HEX", help="The policy's frozen SHA-256 (with --history-policy).")
    opt.add_argument("--run-tests", action="store_true", help="Run the V8 ported-test harness. Default: off.")
    opt.add_argument(
        "--python",
        default=sys.executable,
        help="Interpreter with the machinery dependencies and pytest, for V3 and V8 (default: this interpreter).",
    )
    opt.add_argument(
        "--tool-python",
        default=sys.executable,
        help="Interpreter with libcst==1.8.6 for the rename tools and history_policy.py (default: this interpreter).",
    )
    opt.add_argument(
        "--external-names",
        type=Path,
        metavar="FILE",
        help="Passed to rename_python.py (top-level importable names, one per line). Default: not passed.",
    )
    opt.add_argument("--jobs", type=int, default=os.cpu_count() or 1, help="Parallel V3 imports (default: CPU count).")
    opt.add_argument("--import-timeout", type=int, default=120, help="Seconds per V3 import child (default: 120).")
    opt.add_argument(
        "--test-timeout",
        type=int,
        default=3600,
        help="Seconds for each tool run and the V8 pytest run (default: 3600).",
    )
    opt.add_argument("--report", type=Path, metavar="OUT.json", help="Also write the results as JSON. Default: none.")
    return parser


def print_result(result: CheckResult) -> None:
    counts = ", ".join(f"{key}={value}" for key, value in result.inspected.items()) or "-"
    print(f"{result.check} {result.status.upper()}: {result.title} [inspected: {counts}]")
    for finding in result.findings:
        print(f"  - {finding}")
    for note in result.notes:
        print(f"  note: {note}")
    if result.listed:
        print(f"  listed ({len(result.listed)}, allowed; all in --report):")
        for item in result.listed[:LISTED_SHOWN]:
            print(f"    {item}")
        if len(result.listed) > LISTED_SHOWN:
            print(f"    ... {len(result.listed) - LISTED_SHOWN} more")


def run_checks(inputs: Inputs, scratch: Path) -> list[CheckResult]:
    for root in (inputs.repo, inputs.source_repo):
        if inside(scratch, root):
            raise Unusable(f"the scratch directory {scratch} is inside {root}; set TMPDIR elsewhere")
    results = [
        check_v1(inputs),
        check_v2(inputs),
        check_v3(inputs, scratch),
        check_v4(inputs),
        check_v5(inputs, scratch),
        check_v6(inputs),
        check_v8(inputs, scratch),
        check_v9(inputs),
        check_history_policy(inputs, scratch),
    ]
    results.append(check_v7(inputs, results))
    order = ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "HP"]
    return sorted(results, key=lambda item: order.index(item.check))


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        protected = protected_paths(args)
        temp_root = Path(os.path.realpath(tempfile.gettempdir()))
        for root in protected:
            if temp_root == root or inside(temp_root, root):
                raise Unusable(f"the temporary directory {temp_root} lies inside {root}; set TMPDIR elsewhere")
        if args.report is not None:
            check_report_path(args.report, protected, input_files(args))
        with tempfile.TemporaryDirectory(prefix="lu-verify-extraction-") as tmp:
            scratch = Path(os.path.realpath(tmp))
            _SANDBOX.append(Sandbox(scratch, visible_roots(args, protected)))
            try:
                inputs = load_inputs(args)
                results = run_checks(inputs, scratch)
            finally:
                _SANDBOX.pop()
    except Unusable as exc:
        print(f"error: {exc}", file=sys.stderr)
        print("verdict: UNUSABLE INPUT (exit 2)")
        return EXIT_UNUSABLE
    for result in results:
        print_result(result)
    failed = [result.check for result in results if result.status == "fail"]
    code = EXIT_FINDING if failed else EXIT_PASS
    verdict = f"FAIL ({', '.join(failed)})" if failed else "PASS"
    print(f"verdict: {verdict} (exit {code})")
    if args.report is not None:
        payload = {
            "verdict": "fail" if failed else "pass",
            "exit": code,
            "repo": str(inputs.repo),
            "head": inputs.head,
            "source": inputs.source,
            "rewrite_tip": inputs.rewrite_tip,
            "checks": [result.as_dict() for result in results],
        }
        write_report(args.report, payload)
    return code


if __name__ == "__main__":
    sys.exit(main())
