#!/usr/bin/env python3
"""Prove that an extracted machinery repository is exactly the approved one, before its first push.

Step 6 of the machinery move rewrites a clone of the product repository with git-filter-repo,
then adds one transformation commit (the ``scripts`` -> ``lu_machinery`` rename, the approved
additions). This tool checks the result against frozen inputs and never writes to any of them:

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
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

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

HERE = Path(__file__).resolve().parent
RENAME_TOOLS = ("rename_python.py", "rename_nonpython.py", "rename_structured.py")
HISTORY_POLICY_TOOL = "history_policy.py"
TESTS_LIST = "machinery_tests.txt"

HEX_OID = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")
ZERO_OID = re.compile(r"0{40}(?:0{24})?")
# A ``scripts.<name>`` module reference; ``scripts.py`` and other file names are not modules.
MODULE_REF = re.compile(r"(?<![\w.\-/])scripts(?:\.[A-Za-z_]\w*)+")
FILE_SUFFIXES = frozenset({"py", "pyc", "sh", "md", "json", "yaml", "yml", "txt", "toml", "cfg", "ini", "log"})
PATH_REF = re.compile(r"(?<![\w.\-])(?:\./)?scripts/([\w.\-/]*)")
# Environment variables that would let a source checkout or another repository leak in.
STRIPPED_ENV_PREFIXES = ("PYTHON", "GIT_", "PYTEST_")
GIT_TIMEOUT = 1800


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
    pytest_args: list[str]
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


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    """Run a read-only git command; replace refs are ignored and no optional lock is taken."""
    executable = shutil.which("git")
    if executable is None:
        raise Unusable("git is not on PATH")
    cmd = [executable, "--no-pager", "-c", "core.fsmonitor=false", "-C", str(repo), *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, env=clean_env(), check=False, timeout=GIT_TIMEOUT)
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


def require_clean(repo: Path, why: str) -> None:
    status = git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored=matching").stdout
    if status:
        entries = [item for item in status.decode("utf-8", "replace").split("\0") if item][:10]
        raise Unusable(
            f"{repo} {why}: the working tree must equal HEAD with nothing untracked or ignored; got {entries}"
        )


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
        pytest_args=list(args.pytest_arg),
        tools_dir=tools_dir,
    )
    inputs.head = resolve_commit(repo, "HEAD", "--repo HEAD")
    if git(source_repo, "cat-file", "-e", f"{inputs.source}:{DISPATCH_SOURCE}", check=False).returncode != 0:
        raise Unusable(f"--source {inputs.source} has no {DISPATCH_SOURCE}")
    if inputs.run_tests:
        present = set(git_z(source_repo, "ls-tree", "-r", "-z", "--name-only", inputs.source, "--", "tests/"))
        absent = [path for path in tests_run + tests_support if path not in present]
        if absent:
            raise Unusable(f"{TESTS_LIST} names files absent at --source {inputs.source}: {absent[:10]}")
    if args.report is not None and inside(args.report.resolve().parent, repo):
        raise Unusable(f"--report {args.report} must be outside --repo, which is read-only")
    require_clean(repo, "is not clean")
    return inputs


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


def isolated_env(scratch: Path) -> dict[str, str]:
    home = scratch / "home"
    tmp = scratch / "tmp"
    home.mkdir(exist_ok=True)
    tmp.mkdir(exist_ok=True)
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "TMPDIR": str(tmp),
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
    env = isolated_env(scratch)
    root = inputs.repo.resolve()
    dests = inputs.python_dests

    def run_one(index_dest: tuple[int, str]) -> tuple[str, dict[str, object] | None, str]:
        index, dest = index_dest
        mode, target = import_target(dest)
        out = results_dir / f"{index}.json"
        cmd = [inputs.python, "-I", "-B", "-c", _IMPORT_CHILD, str(root), mode, target, dest, str(out)]
        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=inputs.import_timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return dest, None, f"timed out after {inputs.import_timeout}s"
        if not out.is_file():
            tail = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-1:]
            return dest, None, f"the import child exited {proc.returncode} without a result {tail}"
        return dest, json.loads(out.read_text(encoding="utf-8")), ""

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
            for name in data.get("scripts_modules") or []:  # type: ignore[union-attr]
                result.fail(f"{dest}: importing {target} loaded product module {name}")
            for item in data.get("outside") or []:  # type: ignore[union-attr]
                result.fail(f"{dest}: importing {target} loaded {item}, outside the extracted root")
    help_cmd = [inputs.python, "-I", "-B", "-c", _DISPATCH_HELP_CHILD, str(root), DISPATCH_MODULE]
    try:
        proc = subprocess.run(
            help_cmd,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=inputs.import_timeout,
            check=False,
        )
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

    def __init__(self, ownership: dict[str, str], extracted_tops: set[str]) -> None:
        self.files = {key: owner for key, owner in ownership.items() if key.startswith(OLD_PREFIX)}
        self.extracted_tops = extracted_tops
        self.dir_owners: dict[str, set[str]] = {}
        for key, owner in self.files.items():
            parts = key.split("/")
            for depth in range(2, len(parts)):
                self.dir_owners.setdefault("/".join(parts[:depth]), set()).add(owner)

    def module_owner(self, dotted: str) -> str | None:
        parts = dotted.split(".")
        for depth in range(len(parts), 0, -1):
            base = OLD_PREFIX + "/".join(parts[:depth])
            for candidate in (base + "/__init__.py", base + ".py"):
                if candidate in self.files:
                    return self.files[candidate]
        return None

    def path_is_machinery(self, path: str) -> bool:
        path = path.rstrip("/")
        if path in self.files:
            return self.files[path] == MACHINERY
        return MACHINERY in self.dir_owners.get(path, set())

    def is_product_import(self, dotted: str) -> bool:
        top = dotted.split(".")[0]
        if top in sys.stdlib_module_names or top in self.extracted_tops:
            return False
        return self.module_owner(dotted) == PRODUCT


def scan_python_source(rel: str, source: bytes, index: OwnershipIndex) -> list[str]:
    try:
        tree = ast.parse(source, filename=rel)
    except (SyntaxError, ValueError) as exc:
        return [f"{rel}:{getattr(exc, 'lineno', 0) or 0}: cannot parse ({exc.__class__.__name__}: {exc})"]
    findings: list[str] = []
    prose = docstring_nodes(tree)

    def check_import(name: str, line: int) -> None:
        if name == "scripts" or name.startswith("scripts."):
            findings.append(f"{rel}:{line}: import of {name}")
        elif index.is_product_import(name):
            findings.append(f"{rel}:{line}: import of product package {name} (scripts/{name.replace('.', '/')})")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                check_import(alias.name, node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == "scripts":
            for alias in node.names:
                findings.append(f"{rel}:{node.lineno}: import of scripts.{alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            check_import(node.module, node.lineno)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str | bytes) and id(node) not in prose:
            text = node.value if isinstance(node.value, str) else node.value.decode("latin-1")
            for match in MODULE_REF.finditer(text):
                ref = match.group(0)
                last = ref.rsplit(".", 1)[-1]
                if ref.count(".") == 1 and last in FILE_SUFFIXES:
                    continue
                findings.append(f"{rel}:{node.lineno}: string references module {ref}")
            for match in PATH_REF.finditer(text):
                rest = match.group(1).rstrip("/")
                if rest and index.path_is_machinery(OLD_PREFIX + rest):
                    findings.append(f"{rel}:{node.lineno}: string holds machinery path scripts/{rest}")
    return findings


def check_v4(inputs: Inputs) -> CheckResult:
    result = CheckResult("V4", "no scripts module references, machinery scripts/ paths or product imports")
    tree = tree_paths(inputs.repo, "HEAD")
    tops = {path.split("/")[0].removesuffix(".py") for path in tree}
    index = OwnershipIndex(inputs.ownership, tops)
    scanned = 0
    for rel in sorted(path for path in tree if path.endswith(".py")):
        path = inputs.repo / rel
        if path.is_symlink() or not path.is_file():
            result.fail(f"{rel}: not a regular file in the working tree")
            continue
        scanned += 1
        for finding in scan_python_source(rel, path.read_bytes(), index):
            result.fail(finding)
    result.inspected = {"python_files": scanned}
    return result


# --------------------------------------------------------------------------- tool runner


def run_tool(inputs: Inputs, tool: str, args: Sequence[str], report: Path, cwd: Path) -> dict[str, object]:
    """Run one packaging/machinery-move tool; exit 2 (Unusable) unless it ran and wrote its report."""
    script = inputs.tools_dir / tool
    if not script.is_file():
        raise Unusable(f"{script} is absent")
    cmd = [inputs.tool_python, "-B", str(script), *args]
    timeout = inputs.test_timeout
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=clean_env(), capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise Unusable(f"{tool} timed out after {timeout}s") from exc
    stderr = proc.stderr.decode("utf-8", "replace").strip()
    if proc.returncode not in (0, 1) or not report.is_file():
        raise Unusable(f"{tool} could not run (exit {proc.returncode}): {stderr.splitlines()[-3:]}")
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
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
    tree = set(tree_paths(inputs.repo, "HEAD"))
    per_class = dict.fromkeys(CLASSES, 0)
    for row in inputs.expectations:
        per_class[row.klass] += 1
        where = f"expectation line {row.line} ({row.klass} {row.dest})"
        if row.dest not in tree:
            result.fail(f"{where}: file is not in the final tree")
            continue
        data = (inputs.repo / row.dest).read_bytes()
        found = row.literal.encode("utf-8") in data
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
    try:
        proc = subprocess.run(
            cmd, cwd=scratch, env=clean_env(), capture_output=True, timeout=inputs.test_timeout, check=False
        )
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

_PYTEST_CHILD = r"""
import sys
harness, root, junit, *rest = sys.argv[1:]
sys.path[:0] = [harness, root]
import pytest
sys.exit(pytest.main(["-p", "no:cacheprovider", "--rootdir", harness, "--junitxml", junit, *rest]))
"""


def copy_from_source(inputs: Inputs, paths: Iterable[str], dest_root: Path) -> int:
    wanted = set(paths)
    copied = 0
    for line in git_z(inputs.source_repo, "ls-tree", "-r", "-z", inputs.source, "--", *sorted(wanted)):
        meta, path = line.split("\t", 1)
        mode, kind, oid = meta.split()
        if path not in wanted or kind != "blob" or mode == "120000":
            continue
        target = dest_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git(inputs.source_repo, "cat-file", "blob", oid).stdout)
        if mode == "100755":
            target.chmod(0o755)
        copied += 1
    return copied


def junit_counts(path: Path) -> dict[str, int]:
    counts = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    for suite in suites:
        for key in counts:
            counts[key] += int(suite.get(key, "0") or 0)
    counts["passed"] = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
    return counts


def check_v8(inputs: Inputs, scratch: Path) -> CheckResult:
    result = CheckResult("V8", "ported machinery tests pass against the extracted code")
    if not inputs.run_tests:
        result.status = "skipped"
        result.notes.append("not requested (--run-tests absent)")
        return result
    harness = scratch / "harness"
    if inside(harness, inputs.repo):
        raise Unusable(f"the temporary harness {harness} would be inside --repo; set TMPDIR elsewhere")
    clone = git(
        Path(scratch), "clone", "--quiet", "--shared", "--no-checkout", str(inputs.repo), str(harness), check=False
    )
    if clone.returncode != 0:
        raise Unusable(f"cannot clone --repo into the harness: {clone.stderr.decode('utf-8', 'replace').strip()}")
    git(harness, "checkout", "--quiet", "--detach", inputs.head)
    listed = inputs.tests_run + inputs.tests_support
    overlaid = sorted(path for path in listed if (harness / path).exists())
    if overlaid:
        result.notes.append(f"{len(overlaid)} listed test file(s) replace extracted copies: {overlaid[:10]}")
    copied = copy_from_source(inputs, listed, harness)
    if copied != len(listed):
        raise Unusable(f"copied {copied} of {len(listed)} {TESTS_LIST} files from --source")
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
    junit = scratch / "v8-junit.xml"
    cmd = [inputs.python, "-I", "-B", "-c", _PYTEST_CHILD, str(harness), str(inputs.repo), str(junit)]
    cmd += [*inputs.pytest_args, *inputs.tests_run]
    try:
        proc = subprocess.run(
            cmd,
            cwd=harness,
            env=clean_env(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=inputs.test_timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        result.fail(f"the harness pytest run timed out after {inputs.test_timeout}s")
        result.inspected = {"files_copied": copied, "tests_collected": 0}
        return result
    output = (proc.stdout + proc.stderr).decode("utf-8", "replace").strip().splitlines()
    counts = junit_counts(junit) if junit.is_file() else {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    result.notes.append(f"pytest exit {proc.returncode}; {counts}")
    if proc.returncode != 0:
        result.fail(f"pytest exited {proc.returncode}: {output[-15:]}")
    if counts["tests"] == 0:
        result.fail("pytest collected zero tests")
    if counts["failures"] or counts["errors"]:
        result.fail(f"{counts['failures']} test(s) failed and {counts['errors']} errored")
    try:
        require_clean(inputs.repo, "changed while the tests ran")
    except Unusable as exc:
        result.fail(str(exc))
    result.inspected = {
        "files_copied": copied,
        "tests_collected": counts["tests"],
        "tests_passed": counts.get("passed", 0),
        "tests_failed": counts["failures"],
        "tests_errored": counts["errors"],
        "tests_skipped": counts["skipped"],
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
  V4  static AST scan of every .py file at HEAD: imports of scripts or of product packages (per --map),
      `scripts.<module>` in string literals, and string literals naming machinery scripts/ files or directories.
      Docstrings and comments are prose and are not scanned; paths split into components are not literals.
      Each finding is file:line.
  V5  every --expectations row holds; then {", ".join(RENAME_TOOLS)} --check on --repo report zero pending
      rewrites (idempotence). Their unresolved counts are printed as notes.
  V6  every commit of `git -C SRC log --follow SOURCE -- {DISPATCH_SOURCE}` maps through --commit-map to a commit of
      `git -C EXTRACT log --follow -- {DISPATCH_DEST}`; unmapped and pruned commits are findings.
  V7  denominators: V1 must inspect the manifest row count, V3 and V4 the manifest .py count; any check that ran
      with a zero count fails.
  V8  (--run-tests) clone --repo (--shared, read-only) into a temp harness outside it, copy the
      {TESTS_LIST} files from --source over it, apply the rename tools to those copies with --map, run pytest
      on the [run] files with the harness and --repo on sys.path (--python -I). Fails on any failed or errored test,
      a nonzero pytest exit, zero collected tests, or --repo changing during the run; counts are reported.
  V9  HEAD has exactly one parent, the --rewrite-tip, and is the only commit after it; HEAD^{{tree}} equals
      --final-tree; its diff against the tip only adds manifest addition rows (new at the tip), modifies manifest
      paths and deletes nothing the manifest keeps.
  HP  (--history-policy) runs {HISTORY_POLICY_TOOL} verify --repo EXTRACT --rev REWRITE_TIP --policy FILE
      --policy-sha256 HEX --commit-map FILE --path-rename {PATH_RENAME}; its nonzero exit fails.

Preconditions (exit 2 otherwise): every input exists and parses; both repositories are full (not shallow,
no grafts) top-level clones; --repo's working tree equals HEAD with nothing untracked or ignored; --source holds
{DISPATCH_SOURCE}; the rename tools (and {HISTORY_POLICY_TOOL} for --history-policy) sit next to this tool.
Replace refs are ignored (GIT_NO_REPLACE_OBJECTS=1) and git takes no optional locks.

Outputs:
  stdout: one block per check with PASS/FAIL/SKIPPED, its inspected counts, findings and notes, then a verdict.
  --report writes the same as JSON. Temporary files live under $TMPDIR and are removed. Nothing else is written.

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
    opt.add_argument(
        "--pytest-arg",
        action="append",
        default=[],
        metavar="ARG",
        help="Extra argument for the V8 pytest run, repeatable, e.g. --pytest-arg=-n4. Default: none.",
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


def run_checks(inputs: Inputs) -> list[CheckResult]:
    with tempfile.TemporaryDirectory(prefix="lu-verify-extraction-") as tmp:
        scratch = Path(tmp)
        if inside(scratch, inputs.repo):
            raise Unusable(f"the temporary directory {scratch} is inside --repo; set TMPDIR elsewhere")
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
        inputs = load_inputs(args)
        results = run_checks(inputs)
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
        args.report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    sys.exit(main())
