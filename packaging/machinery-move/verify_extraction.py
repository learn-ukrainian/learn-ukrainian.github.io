#!/usr/bin/env python3
"""Prove that an extracted machinery repository is exactly the approved one, before its first push.

Step 6 of the machinery move rewrites a clone of the product repository with git-filter-repo,
then adds one transformation commit (the ``scripts`` -> ``lu_machinery`` rename, the approved
additions). This tool checks the result against frozen inputs and never writes to any of them:
every git call and every child process runs in a bubblewrap sandbox whose only writable path is the
tool's scratch directory.

* V1 the final tree is exactly the tree manifest;
* V2 HEAD is refs/heads/main and no other ref exists; excluded paths appear nowhere in its history,
  history-only paths are absent from the final tree;
* V3 every manifest Python module imports from the extracted root alone;
* V4 no extracted Python file still references ``scripts`` modules, machinery ``scripts/`` paths
  or product packages;
* V5 the evaluator's held-out rename expectations hold and the rename tools are idempotent;
* V6 every source commit of ``scripts/dispatch.py`` survives in ``lu_machinery/dispatch.py``'s history;
* V7 every check inspected the expected, nonzero number of items;
* V8 (``--run-tests``) the ported machinery tests pass against the extracted code;
* V9 HEAD is the single transformation commit on top of the rewrite tip, with the frozen tree;
* HP (``--history-policy``) ``history_policy.py verify`` passes up to the rewrite tip;
* PR (``--product-root-cases``) the product marker is absent and the evaluator's held-out product-root
  cases hold for the migrated consumers in the extracted tree (C-4746).

V4 is fail-closed: whatever it cannot classify exactly is reported (failed or listed), never treated as
safe or as prose. Its two invariants:

1. Every lu_machinery-qualified name (in an import statement, an attribute chain on the name
   ``lu_machinery``, a loader target or any string value) and every relative name in a file under lu_machinery/ resolves by its LONGEST prefix that exists in the
   final tree: an extracted module file, a package or a directory (a namespace package); the bare
   ``lu_machinery`` is the package. The name is clean when that prefix is the whole name or a module
   file (the rest is an attribute). Otherwise the next component is a finding when the ownership map
   lists it (product code, or source the tree manifest does not extract) and an attribute of the
   package when the map does not list it.
2. Every string value passes one evaluator once, in its outermost composition. An exact value is judged
   exactly (invariant 1, and amendment A1 for ``scripts.`` and ``scripts/`` references). A composition
   with an unknown part is LISTED (file:line, counted in a note) when one of its known literal parts
   holds ``scripts``, ``lu_machinery``, a manifest path or a component-wise prefix of one; the complete
   references inside its known parts are still judged. Listed items do not fail the run; the listing is
   the evaluator's to review. A loader target or fromlist that is not statically known is listed too.

Residual (severity MINOR under C-4715: no instance in the frozen tree; recorded, not implemented):

* a module component that is not an ASCII identifier (a non-ASCII letter, a dash, a leading digit) in a
  literal ``lu_machinery`` name: the token pattern ends the name before it, so ``lu_machinery.продукт``
  reads as the bare package;
* ``PureWindowsPath`` and ``WindowsPath`` values are evaluated with POSIX semantics (a backslash is no
  separator).

Loaders: the import statement, ``import_module``/``find_spec``, ``__import__``, ``pkgutil.resolve_name``,
``runpy`` and ``-m`` (their literal targets are string values, so invariant 1 judges them; targets
assembled from a package, a level or a fromlist are judged by invariant 1 directly). Out of scope: a value
bound to a variable, attribute or alias is unknown (no constant propagation); docstrings and comments are
prose.

Run ``verify_extraction.py --help`` for inputs, formats and exit codes.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import json
import os
import posixpath
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
PUBLISHED_REF = "refs/heads/main"  # the only ref the first push publishes (step-6 plan, steps 6 and 7)
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
REPORT_MAX_BYTES = 64 * 1024 * 1024
STATIC_MAX = 4096
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
    product_root_cases: list[ProductRootCase] | None = None

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
        if not stat.S_ISREG(path.stat().st_mode):  # follows a link: the file git reads must be regular
            raise Unusable(f"{path} is not a regular file")
        return path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Unusable(f"cannot read {path}: {exc}") from exc


def repo_storage(repo: Path) -> list[Path]:
    """The repository's git directory, common directory and every object store its alternates reach.

    Found by reading files, without running git, and spelled as git reads them (see pointer_value). A
    relative alternate is resolved against the object store that names it, as git does, and alternates of
    alternates are followed (git stops at depth 5). The pointer files themselves (.git, commondir and each
    alternates file) are included by their resolved paths, so a pointer reached through a symlink is
    protected too. check_storage_against_git later compares this with git's own answer.
    """
    dot = repo / ".git"
    pointers: list[Path] = []
    if dot.is_dir() and not dot.is_symlink():
        git_dir = dot
    elif dot.is_file() or dot.is_symlink():
        pointers.append(dot)
        text = read_pointer_file(dot)
        if not text.startswith("gitdir: "):
            raise Unusable(f"{dot}: not a 'gitdir: ' pointer")
        named = Path(pointer_value(dot, text[len("gitdir: ") :], "gitdir"))
        git_dir = named if named.is_absolute() else repo / named
    else:
        return []
    common = git_dir
    pointer = git_dir / "commondir"
    if pointer.exists() or pointer.is_symlink():
        pointers.append(pointer)
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
        if not alternates.exists() and not alternates.is_symlink():
            continue
        pointers.append(alternates)
        for line in read_pointer_file(alternates).split("\n"):
            if not line or line.startswith("#"):
                continue
            target = Path(pointer_value(alternates, line, "alternate"))
            queue.append((target if target.is_absolute() else Path(real) / target, depth + 1))
    found += pointers
    return [Path(os.path.realpath(path)) for path in found]


def storage_link_targets(roots: Iterable[Path]) -> list[Path]:
    """The resolved targets of every symlink inside the given git storage directories.

    A file git reads for a repository (config, a ref, a pack) can be a link to a file elsewhere; that
    file is repository storage too, so it joins the protected set.
    """
    targets: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for directory, dirs, files in os.walk(root, followlinks=False):
            for name in [*dirs, *files]:
                entry = os.path.join(directory, name)
                if os.path.islink(entry):
                    targets.append(Path(os.path.realpath(entry)))
    return targets


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
        storage = repo_storage(Path(repo))
        paths += storage + storage_link_targets(path for path in storage if path.is_dir())
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
    if report.exists():
        # Overwrite only a report this tool wrote: whatever path an input or git file hides behind, its
        # bytes are never replaced.
        try:
            size = report.stat().st_size
            earlier = json.loads(report.read_bytes()) if size <= REPORT_MAX_BYTES else None
        except (OSError, ValueError):
            earlier = None
        if not (isinstance(earlier, dict) and {"verdict", "exit", "checks"} <= set(earlier)):
            raise Unusable(f"--report {report} exists and is not an earlier verify_extraction report; not overwriting")


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
    if args.product_root_cases is not None:
        inputs.product_root_cases = load_product_root_cases(
            require_file(args.product_root_cases, "--product-root-cases")
        )
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
    files += [path for path in (args.history_policy, args.external_names, args.product_root_cases) if path is not None]
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
    """Every path that any commit reachable from rev adds, changes or deletes (merges against each parent,
    so content only a merge introduces is seen)."""
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
    # The first push publishes exactly PUBLISHED_REF (step-6 plan: no tags, mirror push or other refs), so
    # the history checked below, everything reachable from HEAD, must be that ref and the only one there is.
    symbolic = git(inputs.repo, "symbolic-ref", "--quiet", "HEAD", check=False).stdout.decode().strip()
    if symbolic != PUBLISHED_REF:
        result.fail(f"HEAD is {symbolic or 'detached'}, not {PUBLISHED_REF} (the only ref the first push publishes)")
    refs = git_text(inputs.repo, "for-each-ref", "--format=%(refname)").splitlines()
    for ref in refs:
        if ref != PUBLISHED_REF:
            result.fail(f"ref {ref} exists; the extraction may hold only {PUBLISHED_REF}, the ref V2, V9 and HP verify")
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
        "refs": len(refs),
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


def _parent_dirs(paths: Iterable[str]) -> set[str]:
    return {"/".join(path.split("/")[:depth]) for path in paths for depth in range(1, path.count("/") + 1)}


class OwnershipIndex:
    """Answers who owns a scripts/ module or path (the frozen ownership map) and what the final tree holds."""

    def __init__(
        self,
        ownership: dict[str, str],
        extracted_tops: set[str],
        extracted: Iterable[str] = (),
        final_tree: Iterable[str] | None = None,
        manifest_paths: Iterable[str] = (),
    ) -> None:
        self.files = {key: owner for key, owner in ownership.items() if key.startswith(OLD_PREFIX)}
        self.extracted_tops = extracted_tops
        # Machinery per the tree manifest: the scripts/ source paths that are in the final tree.
        self.extracted = {path for path in extracted if path.startswith(OLD_PREFIX)}
        self.extracted_dirs = _parent_dirs(self.extracted)
        self.dir_owners: dict[str, set[str]] = {}
        for key, owner in self.files.items():
            parts = key.split("/")
            for depth in range(1, len(parts)):
                self.dir_owners.setdefault("/".join(parts[:depth]), set()).add(owner)
        # The final tree's lu_machinery/ files, written in scripts/ form (the namespace of the map). Without
        # an explicit final tree the extracted sources' renamed destinations stand for it.
        tree = list(final_tree) if final_tree is not None else [renamed(path) for path in self.extracted]
        self.final = {OLD_PREFIX + path[len(NEW_PREFIX) :] for path in tree if path.startswith(NEW_PREFIX)}
        self.final_dirs = _parent_dirs(self.final)
        known = {*self.extracted, *(renamed(path) for path in self.extracted), *tree, *manifest_paths} - {ADDITION}
        self.path_prefixes = {
            tuple(parts[:depth]) for parts in (path.split("/") for path in known) for depth in range(1, len(parts) + 1)
        }
        self.module_prefixes: set[tuple[str, ...]] = set()
        for path in known:
            if path.endswith(".py"):
                parts = path[: -len(".py")].split("/")
                parts = parts[:-1] if parts[-1] == "__init__" else parts
                self.module_prefixes.update(tuple(parts[:depth]) for depth in range(1, len(parts) + 1))

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

    def _final_kind(self, parts: Sequence[str], path: bool) -> str | None:
        """'file' or 'package' when lu_machinery/<parts> exists in the final tree, else None.

        For a module name Python's order applies: a regular package, a module file, then a directory (a
        namespace package, also when the source's __init__.py was not extracted).
        """
        base = OLD_PREFIX + "/".join(parts)
        if path:
            return "file" if base in self.final else "package" if base in self.final_dirs else None
        if base + "/__init__.py" in self.final:
            return "package"
        if base + ".py" in self.final:
            return "file"
        return "package" if base in self.final_dirs else None

    def _map_entry(self, parts: Sequence[str], path: bool) -> str | None:
        """Why lu_machinery/<parts>, absent from the final tree, is a dependency: the map lists it, or None."""
        base = OLD_PREFIX + "/".join(parts)
        for candidate in (base,) if path else (base + "/__init__.py", base + ".py"):
            if candidate in self.files:
                if self.files[candidate] == PRODUCT:
                    return f"names product code absent from the machinery tree ({candidate})"
                return f"names {candidate}, which the tree manifest does not extract"
        owners = self.dir_owners.get(base)
        if owners == {PRODUCT}:
            return f"names a product package absent from the machinery tree ({base}/)"
        if owners:
            return f"names {base}/, which the machinery tree does not contain"
        return None

    def extracted_dependency(self, name: str, *, path: bool = False) -> str | None:
        """Invariant (1): why a name inside the lu_machinery namespace needs code the final tree lacks, or None.

        name is scripts/-relative: dotted for a module, slash-separated for a path; empty for lu_machinery
        itself. It resolves by its longest prefix that exists in the final tree; the bare lu_machinery is
        the package. The name is clean when that prefix is the whole name or a module file (the rest is an
        attribute). Otherwise the next component is a finding when the ownership map lists it (product
        code, or source the tree manifest does not extract), and an attribute of the package when the map
        does not list it (the map lists every scripts/ file of the source, so it names no source code).
        """
        parts = [part for part in name.split("/" if path else ".") if part]
        depth = len(parts)
        while depth and self._final_kind(parts[:depth], path) is None:
            depth -= 1
        if depth == len(parts) or (depth and self._final_kind(parts[:depth], path) == "file"):
            return None
        return self._map_entry(parts[: depth + 1], path)

    def names_known_location(self, text: str) -> bool:
        """Invariant (2): text holds scripts, lu_machinery, a manifest path or a component-wise prefix of one.

        Each path-like token is split into path components ("/") and each of those into dotted components
        ("."); it qualifies when a component is scripts or lu_machinery, or when some trailing run of its
        path components, or of one path component's dotted components, is a manifest path or a
        component-wise prefix of one (source or destination; path or dotted module form).
        """
        for token in KNOWN_TOKEN.findall(text):
            segments = [part for part in token.split("/") if part not in ("", ".")]
            forms = [(tuple(segments), self.path_prefixes)]
            forms += [
                (tuple(part for part in segment.split(".") if part), self.module_prefixes) for segment in segments
            ]
            for parts, prefixes in forms:
                if ROOT_NAMES.intersection(parts) or any(parts[start:] in prefixes for start in range(len(parts))):
                    return True
        return False


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


def package_argument(node: ast.expr | None, rel: str) -> tuple[str, list[str]] | None:
    """A loader's package argument when statically known: its namespace and its scripts/-relative parts.

    "extracted" is the lu_machinery namespace (a lu_machinery-qualified name, __package__ or
    __spec__.parent of a file under lu_machinery/); "scripts" is a scripts.-anchored name, resolved under
    the product checkout; "plain" is an unprefixed name, resolved through scripts/ on sys.path.
    """
    if isinstance(node, ast.Name) and node.id == "__package__":
        package = file_package(rel)
        return ("extracted", package) if package is not None else None
    if isinstance(node, ast.Attribute) and node.attr == "parent" and isinstance(node.value, ast.Name):
        package = file_package(rel) if node.value.id == "__spec__" else None
        return ("extracted", package) if package is not None else None
    value = static_string(node)
    if not value:
        return None
    inner = extracted_name(value)
    if inner is not None:
        return "extracted", inner.split(".") if inner else []
    if value == "scripts" or value.startswith("scripts."):
        return "scripts", value.split(".")[1:]
    return "plain", value.split(".")


def call_argument(call: ast.Call, index: int, *names: str) -> ast.expr | None:
    found = call.args[index] if len(call.args) > index else None
    for keyword in call.keywords:
        if keyword.arg in names:
            found = keyword.value
    return found


def literal_strings(node: ast.expr | None) -> list[str] | None:
    """The exact strings of a literal sequence (an __import__ fromlist), or None when any is unknown."""
    if node is None or (isinstance(node, ast.Constant) and node.value is None):
        return []
    value = Evaluator().value(node)
    if isinstance(value, tuple) and all(isinstance(item, str) for item in value):
        return list(value)
    return None


# --------------------------------------------------------------------------- V4 string and path values

# Methods evaluated on an exact receiver; any other operation makes its result unknown.
STR_METHODS = frozenset(
    {
        "join", "format", "replace", "strip", "lstrip", "rstrip", "lower", "upper", "casefold", "title",
        "capitalize", "swapcase", "removeprefix", "removesuffix", "zfill", "center", "ljust", "rjust",
        "__add__", "__mod__", "__mul__", "__rmul__", "__format__", "__str__",
    }
)  # fmt: skip
TEMPLATE_METHODS = frozenset({"format", "__format__", "__mod__"})
PATH_METHODS = frozenset(
    {"joinpath", "with_name", "with_suffix", "with_stem", "as_posix", "__truediv__", "__rtruediv__"}
)
PATH_ATTRS = frozenset({"parent", "name", "stem", "suffix"})
PATH_CALLS = frozenset({"Path", "PurePath", "PurePosixPath", "PosixPath", "PureWindowsPath", "WindowsPath"})
PATH_MODULES = frozenset({"path", "posixpath", "ntpath"})
FUNCTIONS = frozenset({"str", "format", "fspath"})
ROOT_NAMES = frozenset({OLD_PREFIX.rstrip("/"), NEW_PREFIX.rstrip("/")})
KNOWN_TOKEN = re.compile(r"[\w.\-/]+")
LU_MODULE_REF = re.compile(r"(?<![\w.\-/])lu_machinery((?:\.[A-Za-z_]\w*)*)")
LU_PATH_REF = re.compile(r"(?<![\w.\-])(?:\./)?lu_machinery/([\w.\-/]*)")
DIGITS = re.compile(r"\d+")


@dataclass(frozen=True)
class Partial:
    """A composed value with unknown parts: its known text pieces in order, None for each unknown run."""

    parts: tuple[str | None, ...]


UNKNOWN_VALUE = Partial((None,))


def _parts(value: Any) -> tuple[str | None, ...]:
    if isinstance(value, Partial):
        return value.parts
    if isinstance(value, tuple):  # its items' order in the result is unknown: keep each one separate
        return (None, *(piece for item in value for piece in (*_parts(item), None)))
    return (str(value),)


def _pieces(pieces: Iterable[str | None]) -> Any:
    """Merge adjacent known text and adjacent unknown runs; the exact string when nothing is unknown."""
    merged: list[str | None] = []
    for piece in pieces:
        if piece == "":
            continue
        if merged and piece is not None and merged[-1] is not None:
            merged[-1] += piece
        elif not (merged and piece is None and merged[-1] is None):
            merged.append(piece)
    if None not in merged:  # literal text is bounded by the source; computed operations bound themselves
        return "".join(piece for piece in merged if piece is not None)
    return Partial(tuple(merged))


def _fallback(*values: Any) -> Partial:
    """An operation outside the evaluated set: its result is unknown, its known operands stay listed apart."""
    return Partial(_pieces([None, *(piece for value in values for piece in (*_parts(value), None))]).parts)


def _exact(value: Any) -> bool:
    if isinstance(value, tuple):
        return all(_exact(item) for item in value)
    return not isinstance(value, Partial)


def _bounded(*values: Any, template: bool = False) -> bool:
    """No operand can make an exact evaluation large: integers stay within STATIC_MAX, and so do the digit
    runs (field widths and precisions) of every string a format operation reads as a template."""
    for value in values:
        if isinstance(value, tuple) and not _bounded(*value, template=template):
            return False
        if isinstance(value, int) and abs(value) > STATIC_MAX:
            return False
        if template and isinstance(value, str) and any(int(run) > STATIC_MAX for run in DIGITS.findall(value)):
            return False
    return True


def _result(compute: Any, *operands: Any) -> Any:
    """compute() when it returns a string or path within STATIC_MAX; otherwise (it raises as Python would,
    or yields another type) the result is unknown and the operands stay listed apart."""
    try:
        value = compute()
    except Exception:
        return _fallback(*operands)
    if isinstance(value, str | PurePosixPath) and len(str(value)) <= STATIC_MAX:
        return value
    return _fallback(*operands)


def _path_join(values: Sequence[Any]) -> Any:
    """Join path operands with /; an exact absolute operand discards everything before it."""
    pieces: list[str | None] = []
    for value in values:
        if _exact(value) and isinstance(value, str | PurePosixPath) and str(value).startswith("/"):
            pieces = [str(value)]
            continue
        if pieces and not (isinstance(pieces[-1], str) and pieces[-1].endswith("/")):
            pieces.append("/")
        pieces.extend(_parts(value))
    return _pieces(pieces)


def composer(node: ast.AST) -> bool:
    """A node that composes a string or path value from its operands (the evaluated operations)."""
    if isinstance(node, ast.BinOp | ast.JoinedStr):
        return True
    if isinstance(node, ast.Attribute):
        return node.attr in PATH_ATTRS and (composer(node.value) or _literal(node.value))
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in PATH_CALLS or func.id in FUNCTIONS
    return isinstance(func, ast.Attribute) and (
        func.attr in PATH_CALLS or func.attr in FUNCTIONS or func.attr in STR_METHODS or func.attr in PATH_METHODS
    )


def _literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str | bytes)


def _path_module(node: ast.AST) -> bool:
    """os.path, posixpath, ntpath or a bare path module name: the receiver of a path join function."""
    if isinstance(node, ast.Name):
        return node.id in PATH_MODULES
    return isinstance(node, ast.Attribute) and node.attr in PATH_MODULES


class Evaluator:
    """The single reader of string and path values in V4 (invariant 2).

    value() returns an expression's exact value (str, int, tuple or PurePosixPath) or a Partial: known text
    pieces and unknown runs. Literals, the evaluated operations (BinOp, f-strings, Path(...) and the path
    module joins, str(), format(), os.fspath(), the methods in STR_METHODS and PATH_METHODS, PATH_ATTRS) and
    literal sequences are operands; anything else (a name, an attribute, another call, a subscript, a
    conditional) is an unknown run and is not read. Every operand node is recorded in consumed, so the scan
    judges each literal once, in the outermost composition that holds it.
    """

    def __init__(self) -> None:
        self.consumed: set[int] = set()

    def value(self, node: ast.AST | None, depth: int = 0) -> Any:
        if node is None or depth > 64:
            return UNKNOWN_VALUE
        if isinstance(node, ast.Constant):
            value = node.value.decode("latin-1") if isinstance(node.value, bytes) else node.value
            if isinstance(value, bool) or not isinstance(value, str | int):
                return UNKNOWN_VALUE
            self.consumed.add(id(node))
            return value
        if isinstance(node, ast.Tuple | ast.List | ast.Set):
            self.consumed.add(id(node))
            items: list[Any] = []
            for item in node.elts:
                if isinstance(item, ast.Starred):
                    inner = self.value(item.value, depth + 1)
                    items.extend(inner if isinstance(inner, tuple) else [_fallback(inner)])  # length unknown
                else:
                    items.append(self.value(item, depth + 1))
            if isinstance(node, ast.Set) and len(items) > 1:  # iteration order is unknown
                return (_fallback(*items),)
            return tuple(items)
        if not composer(node):
            return UNKNOWN_VALUE
        self.consumed.add(id(node))
        if isinstance(node, ast.BinOp):
            return self._binop(node.op, self.value(node.left, depth + 1), self.value(node.right, depth + 1))
        if isinstance(node, ast.JoinedStr):
            pieces: list[str | None] = []
            for item in node.values:
                part = (
                    self._field(item, depth + 1)
                    if isinstance(item, ast.FormattedValue)
                    else self.value(item, depth + 1)
                )
                pieces.extend(_parts(part))
            return _pieces(pieces)
        if isinstance(node, ast.Attribute):
            receiver = self.value(node.value, depth + 1)
            if isinstance(receiver, PurePosixPath):
                return _result(lambda: getattr(receiver, node.attr), receiver)
            return _fallback(receiver)
        assert isinstance(node, ast.Call)
        return self._call(node, depth + 1)

    def _field(self, item: ast.FormattedValue, depth: int) -> Any:
        value = self.value(item.value, depth)
        spec = self.value(item.format_spec, depth) if item.format_spec is not None else ""
        if _exact(value) and isinstance(spec, str) and _bounded(value) and _bounded(spec, template=True):
            conversions = {
                -1: lambda: value,
                115: lambda: str(value),
                114: lambda: repr(value),
                97: lambda: ascii(value),
            }
            convert = conversions.get(item.conversion, conversions[-1])
            return _result(lambda: format(convert(), spec), value, spec)
        if item.conversion == -1 and spec == "":
            return value
        return _fallback(value, spec)

    def _binop(self, op: ast.operator, left: Any, right: Any) -> Any:
        exact = _exact(left) and _exact(right) and _bounded(left, right)
        if isinstance(op, ast.Div):
            if not exact:
                return _path_join([left, right])
            if isinstance(left, PurePosixPath) or isinstance(right, PurePosixPath):
                return _result(lambda: PurePosixPath(left) / right, left, right)
            return _fallback(left, right)  # str / str raises TypeError
        if isinstance(op, ast.Add) and isinstance(left, tuple) and isinstance(right, tuple):
            return left + right
        if isinstance(op, ast.Add) and not isinstance(left, tuple | int) and not isinstance(right, tuple | int):
            if exact and type(left) is not type(right):
                return _fallback(left, right)  # str + Path raises TypeError
            return _pieces([*_parts(left), *_parts(right)])
        if exact and isinstance(op, ast.Mod) and isinstance(left, str) and _bounded(left, right, template=True):
            return _result(lambda: left % right, left, right)
        if exact and isinstance(op, ast.Mult) and {type(left), type(right)} == {str, int}:
            text, count = (left, right) if isinstance(left, str) else (right, left)
            if len(text) * max(count, 0) <= STATIC_MAX:
                return text * count
        return _fallback(left, right)

    def _call(self, node: ast.Call, depth: int) -> Any:
        func = node.func
        args: list[Any] = []
        for arg in node.args:
            if isinstance(arg, ast.Starred):
                inner = self.value(arg.value, depth)
                args.extend(inner if isinstance(inner, tuple) else [_fallback(inner)])  # length unknown
            else:
                args.append(self.value(arg, depth))
        kwargs = {keyword.arg: self.value(keyword.value, depth) for keyword in node.keywords if keyword.arg}
        if any(keyword.arg is None for keyword in node.keywords):
            kwargs["**"] = UNKNOWN_VALUE
        operands = [*args, *kwargs.values()]
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
        is_function = isinstance(func, ast.Name) or name in PATH_CALLS or name == "fspath"
        is_function = is_function or (name == "join" and isinstance(func, ast.Attribute) and _path_module(func.value))
        receiver = self.value(func.value, depth) if isinstance(func, ast.Attribute) and not is_function else None
        exact = all(_exact(value) for value in operands) and _bounded(*operands)
        if is_function:
            if name in PATH_CALLS or name == "join":
                if kwargs:
                    return _fallback(*operands)
                if not exact:
                    return _path_join(args)
                join = PurePosixPath if name in PATH_CALLS else posixpath.join
                return _result(lambda: join(*args), *operands)
            if len(args) == 1 and not kwargs and name in ("str", "fspath"):
                value = args[0]
                if not exact:
                    return value
                return _result(lambda: str(value) if isinstance(value, str | int | PurePosixPath) else None, value)
            if name == "format" and 1 <= len(args) <= 2 and not kwargs and exact and _bounded(*args, template=True):
                return _result(lambda: format(*args), *operands)
            return _fallback(*operands)
        template = name in TEMPLATE_METHODS
        evaluated = (isinstance(receiver, str) and name in STR_METHODS) or (
            isinstance(receiver, PurePosixPath) and name in PATH_METHODS
        )
        if evaluated and exact and _bounded(receiver, *operands, template=template) and "**" not in kwargs:
            return _result(lambda: getattr(receiver, name)(*args, **kwargs), receiver, *operands)
        if (
            name == "join"
            and isinstance(receiver, str)
            and len(args) == 1
            and not kwargs
            and isinstance(args[0], tuple)
        ):
            pieces: list[str | None] = []
            for index, item in enumerate(args[0]):
                pieces.extend(([receiver] if index else []) + list(_parts(item)))
            return _pieces(pieces)
        if name in ("joinpath", "__truediv__") and not kwargs:
            return _path_join([receiver, *args])
        if name == "__rtruediv__" and len(args) == 1 and not kwargs:
            return _path_join([args[0], receiver])
        if name == "__add__" and len(args) == 1 and not kwargs:
            return _pieces([*_parts(receiver), *_parts(args[0])])
        return _fallback(receiver, *operands)


def static_string(node: ast.AST | None) -> str | None:
    """The exact string value of an expression built only from literals by the evaluated operations, or None."""
    value = Evaluator().value(node)
    return value if isinstance(value, str) else None


def scan_python_source(
    rel: str,
    source: bytes,
    index: OwnershipIndex,
    unprefixed: list[str] | None = None,
    listed: list[str] | None = None,
) -> list[str]:
    """V4 findings for one file (brief amendment A1 and the module docstring's invariants 1 and 2).

    Findings: (a) import statements of scripts or of product code, and every name inside the lu_machinery
    namespace (import statement, attribute chain on the name lu_machinery, loader target, any string
    value) that invariant 1 resolves to code the final tree lacks; (b) scripts.<module> references and scripts/ path literals that name a machinery
    file of the tree manifest (a missed rename). References that name product code (for example a module
    passed to a subprocess under the product checkout), compositions with an unknown part (invariant 2)
    and loader targets that are not statically known are appended to listed. Unprefixed machinery imports,
    which resolve only while scripts/ is on sys.path, are appended to unprefixed.
    """
    allowed: list[str] = []
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
                what = "attribute reference" if shown == "attribute" else "import of"
                return check_import(inner, line, relative=True, shown=f"{what} {name}")
        reason = index.extracted_dependency(name) if relative else index.product_dependency(name)
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

    def judge_text(text: str, line: int, *, open_left: bool = False, open_right: bool = False) -> None:
        """Judge every complete reference in a known text; open_*: an unknown run touches that edge, so a
        reference touching it is incomplete and left to the composition listing."""

        def complete(match: re.Match[str]) -> bool:
            return not ((open_left and match.start() == 0) or (open_right and match.end() == len(text)))

        for match in filter(complete, MODULE_REF.finditer(text)):
            ref = match.group(0)
            last = ref.rsplit(".", 1)[-1]
            if ref.count(".") == 1 and last in FILE_SUFFIXES:
                continue
            owner = index.module_reference(ref[len("scripts.") :])
            if owner == MACHINERY:
                findings.append(f"{rel}:{line}: string references machinery module {ref} (missed rename)")
            else:
                allowed.append(f"{rel}:{line}: {owner} module reference {ref}")
        for match in filter(complete, PATH_REF.finditer(text)):
            rest = match.group(1).rstrip("/")
            shown = f"scripts/{rest}" if rest else "scripts/"
            owner = index.path_reference((OLD_PREFIX + rest).rstrip("/"))
            if owner == MACHINERY:
                findings.append(f"{rel}:{line}: string holds machinery path {shown} (missed rename)")
            else:
                allowed.append(f"{rel}:{line}: {owner} path reference {shown}")
        for match in filter(complete, LU_MODULE_REF.finditer(text)):
            reason = index.extracted_dependency(match.group(1).lstrip("."))
            if reason is not None:
                findings.append(f"{rel}:{line}: string reference {match.group(0)} {reason}")
        for match in filter(complete, LU_PATH_REF.finditer(text)):
            rest = posixpath.normpath(match.group(1)) if match.group(1) else "."
            if rest == ".." or rest.startswith("../"):
                continue  # it leaves lu_machinery/; the scripts/ scan reads what it names
            reason = index.extracted_dependency("" if rest == "." else rest, path=True)
            if reason is not None:
                findings.append(f"{rel}:{line}: string path {match.group(0)} {reason}")

    def judge(value: Any, line: int) -> None:
        """Invariant 2: an exact value is judged exactly; a composition with an unknown part judges its
        complete references and is listed when a known part names scripts, lu_machinery or a manifest path."""
        if isinstance(value, tuple):
            for item in value:
                judge(item, line)
        elif isinstance(value, Partial):
            pieces = value.parts
            for position, piece in enumerate(pieces):
                if piece is not None:
                    left = position > 0 and pieces[position - 1] is None
                    right = position + 1 < len(pieces) and pieces[position + 1] is None
                    judge_text(piece, line, open_left=left, open_right=right)
            if any(piece is not None and index.names_known_location(piece) for piece in pieces):
                shown = "".join("<?>" if piece is None else piece for piece in pieces)
                allowed.append(f"{rel}:{line}: composition with an unknown part {shown!r}")
        elif isinstance(value, str | PurePosixPath):
            judge_text(str(value), line)

    def check_reference(target: str, line: int, *, assembled: bool = False) -> None:
        """An absolute loader target. A literal target is judged with every other string value; a name
        assembled from a target and its fromlist or package is judged here the same way. An unprefixed
        product target is an allowed, listed reference (A1)."""
        if target == "scripts" or target.startswith("scripts."):
            if assembled and target != "scripts":
                owner = index.module_reference(target[len("scripts.") :])
                if owner == MACHINERY:
                    findings.append(f"{rel}:{line}: loader target {target} names machinery (missed rename)")
                else:
                    allowed.append(f"{rel}:{line}: {owner} loader target {target}")
            return
        if extracted_name(target) is not None:
            if assembled:
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
        if target_node is None:
            return
        target = static_string(target_node)
        if target is None:
            allowed.append(f"{rel}:{line}: {called} target is not statically known")
            return
        if not target and called != "__import__":
            return  # an empty name raises ValueError and imports nothing
        if called in ("import_module", "find_spec"):
            if target.startswith("."):
                level = len(target) - len(target.lstrip("."))
                package = package_argument(call_argument(call, 1, "package"), rel)
                base = climb(package[1], level) if package is not None else None
                rest = target.lstrip(".")
                if package is None or base is None or package[0] == "extracted":
                    check_relative(base, rest, [], line, f"relative loader target {target!r}")
                else:  # anchored on scripts. or an unprefixed package: a reference resolved outside lu_machinery
                    name = ".".join([*base, *(rest.split(".") if rest else [])])
                    if package[0] == "scripts":
                        check_reference(f"scripts.{name}" if name else "scripts", line, assembled=True)
                    elif name:
                        check_reference(name, line)
            else:
                check_reference(target, line)
        elif called == "__import__":
            level_node = call_argument(call, 4, "level")
            raw_level = 0 if level_node is None else level_node.value if isinstance(level_node, ast.Constant) else None
            fromlist = literal_strings(call_argument(call, 3, "fromlist"))
            if fromlist is None:
                allowed.append(f"{rel}:{line}: __import__ fromlist is not statically known")
                fromlist = []
            if not isinstance(raw_level, int) or isinstance(raw_level, bool) or raw_level < 0:
                findings.append(f"{rel}:{line}: __import__ level is not a literal integer; its owner is unknown")
            elif raw_level > 0:  # an empty name with a level imports the package itself, then the fromlist
                what = f"__import__({target!r}, level={raw_level})"
                check_relative(relative_base(rel, raw_level), target, fromlist, line, what)
            elif not target:
                return  # an empty absolute name raises ValueError and imports nothing
            else:
                check_reference(target, line)
                for name in fromlist:
                    if name != "*":
                        check_reference(f"{target}.{name}", line, assembled=True)
        elif called == "resolve_name":
            check_reference(target.split(":", 1)[0], line)
        else:
            check_reference(target, line)

    evaluator = Evaluator()
    chained: set[int] = set()
    for node in ast.walk(tree):  # breadth-first: a composition is read before the operands it holds
        if isinstance(node, ast.Import):
            for alias in node.names:
                check_import(alias.name, node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == "scripts":
            for alias in node.names:
                findings.append(f"{rel}:{node.lineno}: import of scripts.{alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            check_from(node.module, [alias.name for alias in node.names], node.lineno, relative=False)
        elif isinstance(node, ast.ImportFrom) and node.level > 0:
            if file_package(rel) is not None:  # outside lu_machinery/ a relative import cannot reach scripts/
                names = [alias.name for alias in node.names]
                base = relative_base(rel, node.level)  # None: the level climbs past lu_machinery, a finding
                check_relative(base, node.module or "", names, node.lineno, "relative import")
        elif isinstance(node, ast.Call):
            func = node.func
            called = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
            if called in LOADERS:
                check_loader(node, called)
        elif isinstance(node, ast.Attribute) and id(node) not in chained:
            attributes: list[str] = []
            inner: ast.expr = node
            while isinstance(inner, ast.Attribute):  # the outermost attribute of a chain comes first
                chained.add(id(inner))
                attributes.append(inner.attr)
                inner = inner.value
            if isinstance(inner, ast.Name) and inner.id == NEW_PREFIX.rstrip("/"):
                check_import(".".join(["lu_machinery", *reversed(attributes)]), node.lineno, shown="attribute")
        if id(node) in prose or id(node) in evaluator.consumed:
            continue
        if _literal(node) or composer(node):  # the single choke point: every string value passes here once
            judge(evaluator.value(node), getattr(node, "lineno", 0))
    if listed is not None:
        listed.extend(dict.fromkeys(allowed))
    return list(dict.fromkeys(findings))


def check_v4(inputs: Inputs) -> CheckResult:
    result = CheckResult("V4", "no scripts or product imports, no missed machinery renames (A1)")
    tree = tree_paths(inputs.repo, "HEAD")
    tops = {path.split("/")[0].removesuffix(".py") for path in tree}
    manifest_paths = [path for row in inputs.manifest for path in row]
    index = OwnershipIndex(inputs.ownership, tops, (source for source, _dest in inputs.manifest), tree, manifest_paths)
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
    unresolved = sum(1 for item in result.listed if ": composition with an unknown part " in item)
    unknown_targets = sum(1 for item in result.listed if "is not statically known" in item)
    if unresolved or unknown_targets:
        result.notes.append(
            f"{unresolved} composition(s) with an unknown part and {unknown_targets} loader argument(s) that are "
            "not statically known are listed, not failed (invariant 2); review them in the listing"
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


# --------------------------------------------------------------------------- PR product-root resolution

# C-4746: machinery finds the product checkout through ``product_root()`` or refuses. The marker below
# proves a product checkout's layout and must never be in the extracted tree; the evaluator-owned cases
# (--product-root-cases) exercise the migrated consumers in the extracted tree.
PRODUCT_MARKER = "curriculum/l2-uk-en/curriculum.yaml"
RESOLVER_DEST = f"{NEW_PREFIX}common/repo_root.py"
PRODUCT_ROOT_CASES_SCHEMA = "lu-machinery.product-root-cases"
_CASE_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
_CALL_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*:[A-Za-z_][A-Za-z0-9_]*")
_PLACEHOLDER_RE = re.compile(r"\{([a-z]+)\}")
_CASE_FIELDS = {"id", "layout", "sys_path", "env", "call", "attr", "args", "kwargs", "expect"}
_EXPECT_FIELDS = {"raises", "returns", "contains", "not_contains"}


@dataclass(frozen=True)
class ProductRootCase:
    """One evaluator-owned case: a layout in its own scratch directory, one consumer call and its outcome."""

    case_id: str
    layout: tuple[dict[str, str], ...]
    sys_path: str
    env: dict[str, str]
    target: str
    is_attr: bool
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    expect: dict[str, Any]


def _case_strings(value: Any, where: str) -> Any:
    """Arguments are strings, ``{"path": str}`` (a ``Path``), lists of those, or null/bool/int."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, dict) and set(value) == {"path"} and isinstance(value["path"], str):
        return value
    if isinstance(value, list):
        return [_case_strings(item, where) for item in value]
    raise Unusable(f'{where}: an argument must be a string, number, boolean, null, list or {{"path": str}}')


def load_product_root_cases(path: Path) -> list[ProductRootCase]:
    """Parse the evaluator's held-out product-root cases; any defect is unusable input."""
    try:
        document = json.loads(read_text(path, "--product-root-cases"))
    except json.JSONDecodeError as exc:
        raise Unusable(f"--product-root-cases is not JSON: {exc}") from exc
    if (
        not isinstance(document, dict)
        or set(document) != {"schema", "schema_version", "cases"}
        or document["schema"] != PRODUCT_ROOT_CASES_SCHEMA
        or document["schema_version"] != 1
        or type(document["schema_version"]) is not int
        or not isinstance(document["cases"], list)
        or not document["cases"]
    ):
        raise Unusable(
            f"--product-root-cases must be {{schema: {PRODUCT_ROOT_CASES_SCHEMA}, schema_version: 1, cases: [...]}}"
        )
    cases: list[ProductRootCase] = []
    seen: set[str] = set()
    for index, raw in enumerate(document["cases"]):
        where = f"--product-root-cases case {index}"
        if not isinstance(raw, dict) or not set(raw) <= _CASE_FIELDS or not {"id", "sys_path", "expect"} <= set(raw):
            raise Unusable(f"{where}: fields must be {sorted(_CASE_FIELDS)} with id, sys_path and expect")
        case_id = raw["id"]
        if not isinstance(case_id, str) or not _CASE_ID_RE.fullmatch(case_id) or case_id in seen:
            raise Unusable(f"{where}: id must be a unique lowercase slug")
        seen.add(case_id)
        where = f"--product-root-cases case {case_id}"
        if ("call" in raw) == ("attr" in raw):
            raise Unusable(f"{where}: give exactly one of call and attr")
        target = raw.get("call", raw.get("attr"))
        if not isinstance(target, str) or not _CALL_RE.fullmatch(target):
            raise Unusable(f"{where}: call/attr must be module.path:name")
        if "attr" in raw and ("args" in raw or "kwargs" in raw):
            raise Unusable(f"{where}: attr takes no args or kwargs")
        layout = raw.get("layout", [])
        if not isinstance(layout, list):
            raise Unusable(f"{where}: layout must be a list")
        entries = []
        for entry in layout:
            kind = entry.get("kind") if isinstance(entry, dict) else None
            keys = {
                "dir": {"kind", "path"},
                "file": {"kind", "path", "text"},
                "source": {"kind", "path", "source"},
                "symlink": {"kind", "path", "target"},
                "package": {"kind", "path"},
            }.get(kind)
            if keys is None or set(entry) != keys or not all(isinstance(entry[key], str) for key in keys):
                raise Unusable(f"{where}: layout entry {entry!r} is not a dir, file, source, symlink or package entry")
            if not valid_path(entry["path"], allow_dir=True):
                raise Unusable(f"{where}: layout path {entry['path']!r} is not a clean relative path")
            if kind == "source" and not valid_path(entry["source"]):
                raise Unusable(f"{where}: source path {entry['source']!r} is not a clean relative path")
            entries.append(dict(entry))
        env = raw.get("env", {})
        if not isinstance(env, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in env.items()):
            raise Unusable(f"{where}: env must map names to strings")
        args = raw.get("args", [])
        kwargs = raw.get("kwargs", {})
        if not isinstance(args, list) or not isinstance(kwargs, dict):
            raise Unusable(f"{where}: args must be a list and kwargs an object")
        expect = raw["expect"]
        if not isinstance(expect, dict) or not expect or not set(expect) <= _EXPECT_FIELDS:
            raise Unusable(f"{where}: expect must hold some of {sorted(_EXPECT_FIELDS)}")
        if "raises" in expect and set(expect) != {"raises"}:
            raise Unusable(f"{where}: expect.raises excludes the other expectations")
        for key in ("raises", "returns"):
            if key in expect and not isinstance(expect[key], str):
                raise Unusable(f"{where}: expect.{key} must be a string")
        for key in ("contains", "not_contains"):
            if key in expect and (
                not isinstance(expect[key], list) or not all(isinstance(x, str) for x in expect[key])
            ):
                raise Unusable(f"{where}: expect.{key} must be a list of strings")
        if not isinstance(raw["sys_path"], str):
            raise Unusable(f"{where}: sys_path must be a string")
        cases.append(
            ProductRootCase(
                case_id=case_id,
                layout=tuple(entries),
                sys_path=raw["sys_path"],
                env=dict(env),
                target=target,
                is_attr="attr" in raw,
                args=tuple(_case_strings(arg, where) for arg in args),
                kwargs={str(key): _case_strings(value, where) for key, value in kwargs.items()},
                expect=dict(expect),
            )
        )
    return cases


def _substitute(value: Any, places: dict[str, str], where: str) -> Any:
    """Replace ``{extracted}``, ``{case}`` and ``{python}`` in every string; any other placeholder is unusable input."""
    if isinstance(value, str):

        def replace(match: re.Match[str]) -> str:
            if match[1] not in places:
                raise Unusable(f"{where}: unknown placeholder {match[0]} (known: {sorted(places)})")
            return places[match[1]]

        return _PLACEHOLDER_RE.sub(replace, value)
    if isinstance(value, list):
        return [_substitute(item, places, where) for item in value]
    if isinstance(value, tuple):
        return tuple(_substitute(item, places, where) for item in value)
    if isinstance(value, dict):
        return {key: _substitute(item, places, where) for key, item in value.items()}
    return value


def _case_target(case_dir: Path, rel: str, case_id: str) -> Path:
    """``case_dir/rel`` with its missing parents created; refuse a symlinked parent or an existing target.

    The layout is built by this process, outside the sandbox, so nothing may be created through a link
    (a case links into the extracted tree, which must stay untouched).
    """
    current = case_dir
    for part in PurePosixPath(rel).parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise Unusable(f"--product-root-cases case {case_id}: {rel} would be created through the link {current}")
        current.mkdir(exist_ok=True)
    target = current / PurePosixPath(rel).name
    if os.path.lexists(target):
        raise Unusable(f"--product-root-cases case {case_id}: layout path {rel} is given twice")
    return target


def _build_layout(inputs: Inputs, case: ProductRootCase, case_dir: Path, places: dict[str, str]) -> None:
    """Create the case's files under ``case_dir`` (never through a symlink), sources from --source."""
    package = inputs.repo / NEW_PREFIX.rstrip("/")
    sources = [entry["source"] for entry in case.layout if entry["kind"] == "source"]
    blobs: dict[str, bytes] = {}
    if sources:
        oids = {}
        for line in git_z(inputs.source_repo, "ls-tree", "-r", "-z", inputs.source, "--", *sorted(set(sources))):
            meta, path = line.split("\t", 1)
            mode, kind, oid = meta.split()
            if kind == "blob" and mode in ("100644", "100755"):
                oids[path] = oid
        missing = sorted(set(sources) - set(oids))
        if missing:
            raise Unusable(f"--product-root-cases case {case.case_id}: --source has no file {missing}")
        content = read_blobs(inputs.source_repo, sorted(set(oids.values())))
        blobs = {path: content[oid] for path, oid in oids.items()}
    for entry in case.layout:
        target = _case_target(case_dir, entry["path"].rstrip("/"), case.case_id)
        kind = entry["kind"]
        if kind == "dir":
            target.mkdir()
        elif kind in ("file", "source"):
            data = (
                _substitute(entry["text"], places, case.case_id).encode() if kind == "file" else blobs[entry["source"]]
            )
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
        elif kind == "symlink":
            target.symlink_to(_substitute(entry["target"], places, case.case_id))
        else:  # package: a copy of the extracted machinery package, not a link to it
            shutil.copytree(package, target, symlinks=True, ignore=shutil.ignore_patterns("__pycache__"))


_PRODUCT_ROOT_CHILD = r"""
import importlib, json, os, sys
from pathlib import Path
spec = json.loads(sys.argv[1])
out = sys.argv[2]
sys.path.insert(0, spec["sys_path"])
os.environ.update(spec["env"])
def value(item):
    if isinstance(item, dict):
        return Path(item["path"])
    if isinstance(item, list):
        return [value(x) for x in item]
    return item
result = {}
try:
    module_name, _, name = spec["target"].partition(":")
    module = importlib.import_module(module_name)
    result["module_file"] = getattr(module, "__file__", None)
    got = getattr(module, name) if spec["is_attr"] else getattr(module, name)(
        *[value(x) for x in spec["args"]], **{k: value(v) for k, v in spec["kwargs"].items()})
    result["ok"] = True
    result["value"] = json.dumps(got, default=str, sort_keys=True) if isinstance(got, (dict, list, tuple)) else str(got)
except BaseException as exc:
    result["ok"] = False
    result["error_types"] = [cls.__name__ for cls in type(exc).__mro__]
    result["error"] = (type(exc).__name__ + ": " + str(exc))[:600]
with open(out, "w", encoding="utf-8") as handle:
    json.dump(result, handle)
sys.stdout.flush()
os._exit(0)
"""


def _resolver_marker(inputs: Inputs) -> str | None:
    """The ``PRODUCT_MARKER`` string the extracted resolver defines, read from its source (never imported)."""
    path = inputs.repo / RESOLVER_DEST
    try:
        tree = ast.parse(path.read_bytes())
    except (OSError, SyntaxError):
        return None
    for node in tree.body:
        named = isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "PRODUCT_MARKER" for target in node.targets
        )
        if named and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return node.value.value
    return None


def check_product_root(inputs: Inputs, scratch: Path) -> CheckResult:
    result = CheckResult("PR", "product-root resolution: no marker in the tree; held-out consumer cases hold")
    if inputs.product_root_cases is None:
        result.status = "skipped"
        result.notes.append("not requested (--product-root-cases absent)")
        return result
    if PRODUCT_MARKER in inputs.dests or os.path.lexists(inputs.repo / PRODUCT_MARKER):
        result.fail(f"the extracted tree carries the product marker {PRODUCT_MARKER}")
    declared = _resolver_marker(inputs)
    if declared != PRODUCT_MARKER:
        result.fail(f"{RESOLVER_DEST} declares PRODUCT_MARKER {declared!r}, not {PRODUCT_MARKER!r}")
    box = sandbox()
    env = isolated_env(box)
    base = scratch / "pr-cases"
    base.mkdir()
    cwd = scratch / "pr-cwd"
    cwd.mkdir()
    extracted = str(inputs.repo)
    passed = 0
    for case in inputs.product_root_cases:
        case_dir = base / case.case_id
        case_dir.mkdir()
        places = {"extracted": extracted, "case": str(case_dir), "python": inputs.python}
        _build_layout(inputs, case, case_dir, places)
        spec = {
            "sys_path": _substitute(case.sys_path, places, case.case_id),
            "env": _substitute(case.env, places, case.case_id),
            "target": case.target,
            "is_attr": case.is_attr,
            "args": _substitute(list(case.args), places, case.case_id),
            "kwargs": _substitute(case.kwargs, places, case.case_id),
        }
        expect = _substitute(case.expect, places, case.case_id)
        out = base / f"{case.case_id}.json"
        cmd = [inputs.python, "-I", "-B", "-c", _PRODUCT_ROOT_CHILD, json.dumps(spec), str(out)]
        try:
            proc = box.run(cmd, cwd=cwd, env=env, timeout=inputs.import_timeout)
        except subprocess.TimeoutExpired:
            result.fail(f"{case.case_id}: timed out after {inputs.import_timeout}s")
            continue
        if not out.is_file():
            tail = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-1:]
            result.fail(f"{case.case_id}: the child exited {proc.returncode} without a result {tail}")
            continue
        try:
            data = read_child_json(out)
        except (OSError, ValueError) as exc:
            result.fail(f"{case.case_id}: unreadable result: {exc}")
            continue
        module_file = data.get("module_file")
        if isinstance(module_file, str) and not (
            inside(Path(os.path.realpath(module_file)), inputs.repo) or inside(Path(module_file), case_dir)
        ):
            result.fail(f"{case.case_id}: {case.target} loaded from {module_file}, outside the extracted tree")
            continue
        problems = _case_problems(expect, data)
        for problem in problems:
            result.fail(f"{case.case_id}: {problem}")
        passed += not problems
    result.inspected = {"product_root_cases": len(inputs.product_root_cases)}
    result.notes.append(f"{passed} of {len(inputs.product_root_cases)} held-out cases hold")
    return result


def _case_problems(expect: dict[str, Any], data: dict[str, Any]) -> list[str]:
    if "raises" in expect:
        if data.get("ok"):
            return [f"expected {expect['raises']}, got the value {data.get('value')!r}"]
        if expect["raises"] not in (data.get("error_types") or []):
            return [f"expected {expect['raises']}, got {data.get('error')}"]
        return []
    if not data.get("ok"):
        return [f"expected a value, got {data.get('error')}"]
    got = str(data.get("value"))
    problems = []
    if "returns" in expect and got != expect["returns"]:
        problems.append(f"returned {got!r}, expected {expect['returns']!r}")
    problems += [f"result lacks {needle!r}: {got[:300]}" for needle in expect.get("contains", []) if needle not in got]
    problems += [f"result holds {needle!r}: {got[:300]}" for needle in expect.get("not_contains", []) if needle in got]
    return problems


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
    "PR": "product_root_cases",
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
  V2  the first push publishes only {PUBLISHED_REF}: HEAD must be that ref and no other ref may exist (no
      tag, branch, note, stash, replace or remote-tracking ref), so the history checked here is everything
      that can be published. No --exclude path, as written or renamed {PATH_RENAME}, is in the final tree or in
      any commit reachable from HEAD (every added, changed or deleted path, merges diffed against each
      parent); no --history-paths entry is in the final tree. A form that is a manifest addition row
      (scripts/__init__.py renames onto lu_machinery/__init__.py) may exist only after the rewrite tip, which
      V9 binds to the frozen tree.
  V3  each manifest .py file imports in its own `python -I -B` child (--python), cwd an empty temp dir, HOME and
      TMPDIR temporary, only --repo prepended to sys.path. Dotted names import by name (the resolved __file__
      must be that file); other files load from their path under a synthetic name. A loaded `scripts` module or
      any module file outside --repo and the interpreter's own prefixes is a finding. Then
      `python -m {DISPATCH_MODULE} --help` must exit 0.
  V4  static AST scan of every .py file at HEAD (brief amendment A1), fail-closed by two invariants (the
      module docstring states them in full). Fails only on:
      (a) an import statement of scripts, or one that needs product code per --map. For an absolute
          unprefixed name (resolved through scripts/ on sys.path): a product module or namespace package,
          a product __init__.py Python initializes on the way, or a from-import's product submodule.
          Invariant 1, for every name inside the lu_machinery namespace (an import statement, an attribute
          chain on the name lu_machinery, a loader target, -m arguments and any other string value;
          relative names in files under lu_machinery/):
          the name resolves by its longest prefix that exists in the final tree (a module file, a package
          or a directory; bare lu_machinery is the package). After a module file the rest is an
          attribute; otherwise the next component fails when --map lists it (product code, or source the
          tree manifest does not extract). Relative targets resolve through a literal package,
          __package__ or __spec__.parent; __import__ levels (an empty name included) and fromlists are
          followed. A relative target or level that cannot be resolved statically is a finding.
      (b) a `scripts.<module>` reference or `scripts/<path>` literal that names a machinery file of the tree
          manifest, or a directory holding only such files (a missed rename), in any string value.
      Invariant 2, string values: every string value is read once, in its outermost composition, by one
      evaluator (+, %, *, /, f-strings with conversions and format specs, Path(...) and the other pathlib
      classes, os.path/posixpath join, str(), format(), os.fspath() and str and path methods such as join,
      format, replace, strip, joinpath, with_name). An exact value is judged by (a) and (b). A composition
      with an unknown part is listed when a known literal part holds scripts, lu_machinery, a manifest
      path or a component-wise prefix of one; complete references inside its known parts are still judged.
      References that name product code (for example a module passed to a subprocess that runs under the
      product checkout), mixed directories such as the scripts/ root, other unextracted names, those
      compositions and loader targets or fromlists that are not statically known are allowed: they are
      listed with file:line and counted (all of them in --report); listed items never fail the run.
      Unprefixed imports of machinery modules (resolved only while scripts/ is on sys.path) are a note.
      Docstrings and comments are prose and are not scanned; a value bound to a variable, attribute or
      alias is unknown (no constant propagation).
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
  PR  (--product-root-cases) the product marker {PRODUCT_MARKER} is not in the tree and the extracted
      {RESOLVER_DEST} declares it; then each evaluator case builds its layout in its own scratch directory
      (dirs, files, --source files, symlinks, copies of the extracted package; never written through a link)
      and calls or reads one consumer in a sandboxed child (--python -I, sys.path[0] = the case's sys_path, the
      case's env only; placeholders {{extracted}}, {{case}} and {{python}}). The consumer must load from the extracted tree or
      the case directory, and the outcome must match: the named exception in the raised type's MRO, or the
      returned value (str, or JSON for containers) equal to "returns" and holding every "contains" and no
      "not_contains" string.
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
or inside either repository, its git storage or the tools directory, and an existing --report must be an earlier
report of this tool (anything else is never overwritten). Git storage is read as git reads it: the
.git file, commondir and every alternates file (relative entries against their object store, indirect ones
followed), each a regular file whose value has no surrounding blanks, controls or quotes; the pointer files
themselves and the targets of every symlink inside the storage are protected too; git's own git dir, common
dir and alternate list must agree. $TMPDIR may not lie inside any protected path.

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
        "--product-root-cases",
        type=Path,
        metavar="FILE",
        help="Evaluator-owned held-out product-root cases (JSON); runs PR (C-4746). Default: not run.",
    )
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
        check_product_root(inputs, scratch),
    ]
    results.append(check_v7(inputs, results))
    order = ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "HP", "PR"]
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
