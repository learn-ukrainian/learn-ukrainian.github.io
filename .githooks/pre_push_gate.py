"""Validate the exact outgoing commit before any push leaves the checkout (#10033).

Git calls ``.githooks/pre-push`` for a worker's own ``git push`` and for the
auto-finalize push alike, so this gate sits on the one path both share.  For
each pushed branch it checks, in order:

1. the pre-commit ``pre-push`` stage over the explicit committed range;
2. the deduplicated registry of repository-wide invariant tests
   (``KNOWN_REPO_WIDE_*`` in ``tests/test_repo_wide_marker_invariant.py``);
3. the test files the outgoing range adds or changes.

A red result refuses the push with a typed reason and the failing node ids.
A run that cannot finish (admission wait, time budget, tooling error) is
``validation_incomplete``: the push is refused, the branch is preserved, the
driver decides, and nothing is retried or reported green.  Importer-closure
selection runs afterwards in shadow only; it is recorded and never blocks.

Receipts are bound to the commit, its tree, the range, the registry digest and
the gate version, and are ignored once the tree is dirty or any of those
change.  ``git push --no-verify`` remains the explicit operator bypass.

Stdlib only: the hook must run before any project import is trustworthy.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import errno
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

GATE_VERSION = 5  # 5: per-stage execution allowances (#10642)
REGISTRY_FILE = "tests/test_repo_wide_marker_invariant.py"
REGISTRY_NAMES = ("KNOWN_REPO_WIDE_MODULES", "KNOWN_REPO_WIDE_FUNCTIONS")
MAX_TEST_PROCESSES_ENV = "LU_PRE_PUSH_GATE_MAX_TEST_PROCESSES"
MAX_CONCURRENT_RUNS_ENV = "LU_PRE_PUSH_GATE_MAX_CONCURRENT_RUNS"
MEASUREMENT_SCHEMA = "pre-push-measurement.v1"
SCOPE_MEMORY_MAX = 6 * 1024**3
CGROUP_ROOT = Path("/sys/fs/cgroup")
# Each blocking stage (pre-commit, pytest) gets its own allowance from its own start, so time one
# stage spends never shortens the next (#10642). The run budget caps their sum for the whole push.
STAGE_BUDGET_S = 600.0
RUN_BUDGET_S = 2 * STAGE_BUDGET_S
SHADOW_BUDGET_S = 120.0
CLEANUP_BUDGET_S = 10.0  # after a kill: reaping and the sweep for leftover descendants
ADMISSION_WAIT_S = RUN_BUDGET_S + SHADOW_BUDGET_S + 2 * CLEANUP_BUDGET_S
# Each predecessor gets one complete gate allowance. The ceiling of ten allowances covers a burst of
# ten predecessors, while bounding overload or a stuck holder. Environment overrides only shorten it.
ADMISSION_MAX_WAIT_S = 10 * ADMISSION_WAIT_S
MAX_QUEUE_ENTRIES = 256  # cap live tickets after reaping abandoned entries
RUN_TOKEN_ENV = "LU_PRE_PUSH_GATE_RUN_TOKEN"
RECEIPT_TTL_S = 3600.0
OUTPUT_TAIL_BYTES = 8192
# Registered modules exceeding the cost threshold are explicitly deferred to CI
# and recorded on every run. Function entries always run.
HEAVY_MODULE_S = 60.0
DURATIONS_FILE = "scripts/ci/pytest-file-durations.json"
# Keep existing CI deferrals until the tracked durations table supplies a row.
CI_DEFERRED_MODULES = frozenset({"tests/test_source_ingest_entrypoints.py"})
# Registry entries that read a tree a sparse dispatch worktree omits.  They fail there for want of the
# tree, not for a defect. Deferred to CI only while the worktree is sparse and the tree is absent.
SPARSE_TREE_NODES = {
    "curriculum": (
        "tests/audit/test_track_deterministic_audit.py::test_config_consumer_file_launches_without_pythonpath",
        "tests/curriculum/evidence/test_lessons_lock.py::test_committed_lesson_lock_is_fresh",
        "tests/test_ohoiko_source_inventory_scope.py::test_ohoiko_abetka_inventory_covers_all_committed_key_words",
    ),
}
ZERO_SHA = "0" * 40
EXIT_REFUSED = 1
EXIT_INCOMPLETE = 75  # EX_TEMPFAIL: the push was not validated, not judged bad
NO_TESTS_COLLECTED = 5  # pytest.ExitCode.NO_TESTS_COLLECTED
FAILURE_RE = re.compile(r"^(?:FAILED|ERROR) (\S+?)(?: - .*)?$", re.MULTILINE)
SUMMARY_RE = re.compile(r"^=+ .*\bin \d+(?:\.\d+)?s.*=+$|^\d+ \w+.* in \d+(?:\.\d+)?s", re.MULTILINE)
PRE_COMMIT_FAILED_RE = re.compile(r"^(.+?)\.{3,}.*Failed$", re.MULTILINE)
TEST_FILE_RE = re.compile(r"^tests/(?:.+/)?test_[^/]+\.py$")
# Files outside the commit that can change what pytest imports or how it is configured.  The receipt
# binds only committed inputs, so any such file, untracked or ignored, makes the run unrepeatable.
OVERLAY_PATHSPECS = (
    "*.py",
    "*.pth",
    ":(glob)**/pytest.ini",
    ":(glob)**/tox.ini",
    ":(glob)**/setup.cfg",
    ":(glob)**/pyproject.toml",
)
# Pytest base temps live outside every Git checkout and Git directory (#10654), under the fleet scratch
# root of scripts/common/scratch.py. The hook imports no project code, so it restates that convention.
SCRATCH_ROOT_ENV = "LU_SCRATCH_ROOT"
DEFAULT_SCRATCH_ROOT = Path("/var/tmp/lu")
FALLBACK_SCRATCH_DIRNAME = "lu-scratch"


class GateOutcome(Exception):
    """A typed refusal: ``reason`` names the cause, ``failing`` the node ids."""

    def __init__(self, reason: str, detail: str, *, failing: tuple[str, ...] = (), incomplete: bool = False):
        super().__init__(detail)
        self.reason = reason
        self.detail = detail
        self.failing = failing
        self.incomplete = incomplete


@dataclass(frozen=True)
class Update:
    local_ref: str
    local_sha: str
    remote_ref: str
    remote_sha: str


@dataclass
class Plan:
    head: str
    tree: str
    base: str
    registry_version: str
    registry_nodes: tuple[str, ...]
    changed_tests: tuple[str, ...]
    changed_paths: tuple[str, ...]
    deferred_to_ci: tuple[str, ...] = ()
    node_ids: tuple[str, ...] = field(init=False)

    def __post_init__(self) -> None:
        self.node_ids = dedupe_node_ids((*self.registry_nodes, *self.changed_tests))


def clean_environment() -> dict[str, str]:
    """Drop caller-provided Git state and pytest option injection, as the stamp guard does."""
    environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    environment.pop("PYTEST_ADDOPTS", None)
    return environment


def git(*args: str, cwd: Path, timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], capture_output=True, check=False, cwd=cwd, env=clean_environment(), text=True, timeout=timeout
    )


def git_ok(*args: str, cwd: Path) -> str | None:
    try:
        result = git(*args, cwd=cwd)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


def parse_updates(text: str) -> list[Update]:
    updates = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 4:
            raise GateOutcome("invalid_ref_updates", f"could not read a valid ref update from Git: {line!r}")
        updates.append(Update(*fields))
    return updates


def dedupe_node_ids(node_ids: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Sorted unique ids; a function or class id is dropped when its whole file is selected."""
    unique = set(node_ids)
    files = {node for node in unique if "::" not in node}
    return tuple(sorted(node for node in unique if "::" not in node or node.split("::", 1)[0] not in files))


def pytest_node_id(registered: str) -> str:
    """The registry writes a class method as ``file::Class.method``; pytest wants ``file::Class::method``."""
    path, separator, rest = registered.partition("::")
    return f"{path}{separator}{rest.replace('.', '::')}"


def load_registry(root: Path) -> tuple[tuple[str, ...], str]:
    """Read the registry literals by AST (no import) and return ``(node_ids, version)``.

    The version is the digest of the gate version and the sorted, deduplicated
    ids, so any registry edit changes it and voids earlier receipts.
    """
    path = root / REGISTRY_FILE
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeError) as exc:
        raise GateOutcome("registry_unavailable", f"cannot read {REGISTRY_FILE}: {exc}", incomplete=True) from exc
    found: dict[str, tuple[str, ...]] = {}
    for statement in tree.body:
        if not isinstance(statement, ast.Assign | ast.AnnAssign):
            continue
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id in REGISTRY_NAMES and statement.value is not None:
                value = statement.value
                if isinstance(value, ast.Call) and len(value.args) <= 1:  # frozenset() / frozenset({...})
                    value = value.args[0] if value.args else ast.Tuple(elts=[], ctx=ast.Load())
                try:
                    found[target.id] = tuple(str(item) for item in ast.literal_eval(value))
                except (ValueError, TypeError) as exc:
                    raise GateOutcome(
                        "registry_unavailable", f"{target.id} in {REGISTRY_FILE} is not a literal", incomplete=True
                    ) from exc
    missing = [name for name in REGISTRY_NAMES if name not in found]
    if missing:
        raise GateOutcome("registry_unavailable", f"{REGISTRY_FILE} lacks {', '.join(missing)}", incomplete=True)
    nodes = dedupe_node_ids([pytest_node_id(node) for name in REGISTRY_NAMES for node in found[name]])
    digest = hashlib.sha256(json.dumps([GATE_VERSION, nodes]).encode()).hexdigest()[:16]
    return nodes, f"v{GATE_VERSION}-{digest}"


def tree_is_partial(root: Path, tree: str) -> bool:
    """True when sparse-checkout left some tracked file under ``tree`` unmaterialized (skip-worktree)."""
    listing = git_ok("ls-files", "-v", "--", tree, cwd=root)
    return listing is not None and any(line.startswith("S ") for line in listing.splitlines())


def defer_to_ci(nodes: tuple[str, ...], root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Split ``nodes`` into ``(run_here, deferred_to_ci)``; every deferral is recorded by the caller.

    Two reasons defer an entry.  A whole module whose tracked CI duration exceeds ``HEAVY_MODULE_S``
    cannot fit the budget (function entries and unknown durations run).  An entry that reads a tree
    a sparse worktree omits cannot pass here; it defers only while sparse-checkout has left part of
    the tree unmaterialized, so a full checkout runs it.
    """
    try:
        durations = json.loads((root / DURATIONS_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        durations = {}
    durations = durations if isinstance(durations, dict) else {}
    absent = {
        node for tree, tree_nodes in SPARSE_TREE_NODES.items() if tree_is_partial(root, tree) for node in tree_nodes
    }

    def deferred(node: str) -> bool:
        cost = durations.get(node)
        heavy = "::" not in node and (
            (isinstance(cost, int | float) and cost > HEAVY_MODULE_S)
            or (node not in durations and node in CI_DEFERRED_MODULES)
        )
        return heavy or node in absent

    return tuple(n for n in nodes if not deferred(n)), tuple(n for n in nodes if deferred(n))


def outgoing_base(update: Update, root: Path) -> str:
    """The commit below the outgoing range; never inferred from HEAD or shell arguments."""
    if (
        update.remote_sha != ZERO_SHA
        and git_ok("merge-base", "--is-ancestor", update.remote_sha, update.local_sha, cwd=root) is not None
    ):
        return update.remote_sha
    base = (git_ok("merge-base", "origin/main", update.local_sha, cwd=root) or "").strip()
    if not base:
        raise GateOutcome(
            "range_unresolved",
            f"cannot resolve the outgoing range for {update.local_ref}: no merge-base with origin/main",
        )
    return base


def reject_untracked_inputs(root: Path) -> None:
    """Refuse when untracked or ignored Python/config files could change the run but not the receipt."""
    listing = git_ok("ls-files", "-z", "--others", "--", *OVERLAY_PATHSPECS, cwd=root)
    if listing is None:
        raise GateOutcome("state_unavailable", "cannot list untracked validation inputs", incomplete=True)
    overlays = sorted(path for path in listing.split("\0") if path)
    if overlays:
        shown = ", ".join(overlays[:10]) + (f" (+{len(overlays) - 10} more)" if len(overlays) > 10 else "")
        raise GateOutcome(
            "untracked_inputs",
            f"untracked or ignored files outside the outgoing commit could change the test run: {shown}; "
            "commit them or remove them first",
        )


def build_plan(update: Update, root: Path) -> Plan | None:
    head = (git_ok("rev-parse", "HEAD", cwd=root) or "").strip()
    if head != update.local_sha:
        raise GateOutcome(
            "tree_mismatch",
            f"{update.local_ref} ({update.local_sha[:12]}) is not the checked-out HEAD ({head[:12] or 'unknown'}); "
            "push from the worktree that has the commit checked out so the exact commit is the one validated",
        )
    dirty = git_ok("status", "--porcelain", "--untracked-files=no", cwd=root)
    if dirty is None or dirty.strip():
        raise GateOutcome("dirty_tree", "tracked files differ from the outgoing commit; commit or restore them first")
    reject_untracked_inputs(root)
    base = outgoing_base(update, root)
    if base == head:
        return None
    names = git_ok("diff", "--name-only", "--diff-filter=ACMR", f"{base}..{head}", cwd=root)
    if names is None:
        raise GateOutcome("range_unresolved", f"cannot list changed paths for {base[:12]}..{head[:12]}")
    changed = tuple(sorted(path for path in names.splitlines() if path))
    changed_tests = tuple(path for path in changed if TEST_FILE_RE.match(path))
    unmaterialized = tuple(path for path in changed_tests if not (root / path).is_file())
    if unmaterialized:
        raise GateOutcome(
            "changed_tests_unmaterialized",
            "the outgoing range changes test files this worktree has not materialized (sparse-checkout): "
            f"{', '.join(unmaterialized)}; run `git sparse-checkout add tests` and push again",
            incomplete=True,
        )
    registry, version = load_registry(root)
    runnable, deferred = defer_to_ci(registry, root)
    absent = tuple(
        dict.fromkeys(node.split("::", 1)[0] for node in runnable if not (root / node.split("::", 1)[0]).is_file())
    )
    if absent:  # only the recorded deferrals above may skip a registered invariant; an absent file may not
        raise GateOutcome(
            "registry_entries_unmaterialized",
            "registered invariant files are missing from this worktree (sparse-checkout or a stale registry): "
            f"{', '.join(absent)}; run `git sparse-checkout add tests` and push again",
            incomplete=True,
        )
    tree = (git_ok("rev-parse", f"{head}^{{tree}}", cwd=root) or "").strip()
    return Plan(head, tree, base, version, runnable, changed_tests, changed, deferred)


# ---- receipts -------------------------------------------------------------


def state_dir(root: Path) -> Path:
    common = git_ok("rev-parse", "--git-common-dir", cwd=root)
    if common is None:
        raise GateOutcome("state_unavailable", "cannot resolve the Git common directory", incomplete=True)
    path = Path(common.strip())
    return (path if path.is_absolute() else root / path) / "lu-pre-push-gate"


def receipt_key(plan: Plan) -> dict[str, object]:
    return {
        "gate_version": GATE_VERSION,
        "head": plan.head,
        "tree": plan.tree,
        "base": plan.base,
        "registry_version": plan.registry_version,
        "deferred_to_ci": list(plan.deferred_to_ci),
        "node_ids": list(plan.node_ids),
        "changed_paths": list(plan.changed_paths),
    }


def receipt_path(state: Path, plan: Plan) -> Path:
    return state / "receipts" / f"{plan.head}-{plan.base}.json"


def receipt_is_fresh(state: Path, plan: Plan, now: float) -> bool:
    try:
        receipt = json.loads(receipt_path(state, plan).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return (
        isinstance(receipt, dict)
        and receipt.get("key") == receipt_key(plan)
        and receipt.get("outcome") == "green"
        and isinstance(receipt.get("at"), int | float)
        and 0 <= now - receipt["at"] <= RECEIPT_TTL_S
    )


def write_receipt(state: Path, plan: Plan, now: float) -> None:
    path = receipt_path(state, plan)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"key": receipt_key(plan), "outcome": "green", "at": now}), encoding="utf-8")
    temporary.replace(path)


def record(state: Path, event: dict[str, object]) -> bool:
    """Serialize complete rows and fsync both the journal and its directory."""
    try:
        row = (json.dumps(event, sort_keys=True) + "\n").encode("utf-8")
        state.mkdir(parents=True, exist_ok=True)
        fd = os.open(
            state / "measurements.jsonl", os.O_CREAT | os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600
        )
        original_handlers = {}
        pending_signals = []

        def defer_signal(number, frame):
            pending_signals.append((number, frame))

        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise OSError("measurement journal is not a regular file")
            fcntl.flock(fd, fcntl.LOCK_EX)
            original_handlers = {number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)}
            for number in original_handlers:
                signal.signal(number, defer_signal)
            view = memoryview(row)
            while view:
                written = os.write(fd, view)
                if written == 0:
                    raise OSError("measurement write made no progress")
                view = view[written:]
            os.fsync(fd)
            directory = os.open(state, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            os.close(fd)
            for number, handler in original_handlers.items():
                signal.signal(number, handler)
            if pending_signals:
                number, frame = pending_signals[0]
                handler = original_handlers[number]
                if callable(handler):
                    handler(number, frame)
                elif handler == signal.SIG_DFL:
                    os.kill(os.getpid(), number)
        return True
    except (OSError, TypeError, ValueError, UnicodeError):
        print("PRE-PUSH GATE: measurement_unavailable; durable evidence is unknown", file=sys.stderr)
        return False


# ---- bounded execution ----------------------------------------------------


def reap_stale_node(path: Path) -> None:
    """Unlink nodes; remove directory contents through a verified, non-following fd."""
    try:
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
        except OSError as error:
            if error.errno not in (errno.ELOOP, errno.ENOTDIR):
                raise
            path.unlink(missing_ok=True)
            return
        try:
            info = os.fstat(fd)
            if not os.path.samestat(info, path.lstat()):
                raise GateOutcome("validation_incomplete", "stale directory was replaced", incomplete=True)
            if not shutil.rmtree.avoids_symlink_attacks:
                raise GateOutcome("validation_incomplete", "safe directory removal is unavailable", incomplete=True)
            for name in os.listdir(fd):
                try:
                    os.unlink(name, dir_fd=fd)
                except IsADirectoryError:
                    shutil.rmtree(name, dir_fd=fd)
            if not os.path.samestat(info, path.lstat()):
                raise GateOutcome("validation_incomplete", "stale directory was replaced", incomplete=True)
            path.rmdir()
        finally:
            os.close(fd)
    except FileNotFoundError:  # another reaper already removed it
        return
    except OSError as error:
        raise GateOutcome("validation_incomplete", f"stale node cleanup failed: {error}", incomplete=True) from None


def ticket_identity(update: Update, root: Path | None = None) -> dict[str, str]:
    """Allow only the frozen Git update and the explicit dispatch task label."""
    branch = update.local_ref
    if branch == "HEAD":
        branch = "unknown"
        if root is not None:
            candidate = (git_ok("symbolic-ref", "--quiet", "HEAD", cwd=root) or "").strip()
            if candidate.startswith("refs/heads/"):
                sha = (git_ok("show-ref", "--verify", "--hash", candidate, cwd=root) or "").strip()
                if sha and sha == update.local_sha:
                    branch = candidate
    owner = os.environ.get("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "")
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", owner) is None:
        owner = "unknown"
    return {"head": update.local_sha, "branch": branch, "task_owner": owner}


def coalescing_state(state: Path, plan: Plan) -> Path:
    """The head groups serialization only; the existing full key still decides reuse."""
    if any(re.fullmatch(r"[0-9a-f]{40}", value) is None for value in (plan.head, plan.tree, plan.base)):
        raise GateOutcome("validation_incomplete", "immutable validation identity is unavailable", incomplete=True)
    if not plan.registry_version or any(not node for node in plan.node_ids):
        raise GateOutcome("validation_incomplete", "immutable validation identity is unavailable", incomplete=True)
    heads = state / "heads"
    path = heads / plan.head
    try:
        for directory in (heads, path):
            directory.mkdir(parents=True, exist_ok=True)
            if not stat.S_ISDIR(directory.lstat().st_mode):
                raise GateOutcome("validation_incomplete", "coalescing directory is unsafe", incomplete=True)
    except OSError as error:
        raise GateOutcome("validation_incomplete", "coalescing directory is unavailable", incomplete=True) from error
    return path


def concurrent_run_limit() -> int:
    """Only the explicitly supported experiment grants a second reservation."""
    value = os.environ.get(MAX_CONCURRENT_RUNS_ENV, "1")
    if value not in ("1", "2"):
        raise GateOutcome("invalid_configuration", f"{MAX_CONCURRENT_RUNS_ENV} must be 1 or 2", incomplete=True)
    return int(value)


def admission_resources() -> dict[str, object]:
    """Unknown host observations cannot qualify parallel admission."""
    result: dict[str, object] = {"load_1m": None, "mem_available_bytes": None, "qualified": False}
    try:
        load = os.getloadavg()[0]
        memory = re.search(r"^MemAvailable:\s+([0-9]+) kB$", Path("/proc/meminfo").read_text(), re.MULTILINE)
        if memory is not None and 0 <= load < float("inf"):
            available = int(memory[1]) * 1024
            result.update(load_1m=load, mem_available_bytes=available, qualified=load < 12 and available >= 8 * 1024**3)
    except (OSError, ValueError, OverflowError):
        pass
    return result


def scope_cgroup(relative: str) -> Path:
    """Accept a canonical cgroup-v2 path, never caller-controlled traversal."""
    path = Path(relative)
    if not path.is_absolute() or ".." in path.parts or relative != path.as_posix() or relative == "/":
        raise ValueError("invalid cgroup path")
    return CGROUP_ROOT / relative.lstrip("/")


def scope_supported(relative: str, unit: str) -> bool:
    try:
        group = scope_cgroup(relative)
        return (
            group.name == unit
            and int((group / "memory.max").read_text()) == SCOPE_MEMORY_MAX
            and int((group / "memory.peak").read_text()) >= 0
            and "populated 1" in (group / "cgroup.events").read_text().splitlines()
        )
    except (OSError, ValueError, TypeError):
        return False


def scoped_holder(ticket: Path) -> bool:
    """Ticket text alone is insufficient: require a flock-live scope proof and live cgroup."""
    try:
        launcher = os.open(ticket.with_suffix(".launcher.lock"), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            if not stat.S_ISREG(os.fstat(launcher).st_mode):
                return False
            try:
                fcntl.flock(launcher, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                return False  # Orphaned scoped work retains its reservation but cannot permit sharing.
        finally:
            os.close(launcher)
        fd = os.open(ticket, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                proof_fd = os.open(ticket.with_suffix(".scope.json"), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                try:
                    if not stat.S_ISREG(os.fstat(proof_fd).st_mode):
                        return False
                    proof = json.loads(os.read(proof_fd, 65536))
                finally:
                    os.close(proof_fd)
                return (
                    proof.get("mode") == "optin_scope"
                    and proof.get("max_concurrent_runs") == 2
                    and type(proof.get("effective_workers")) is int
                    and 1 <= proof["effective_workers"] <= 4
                    and proof.get("ticket_inode") == os.fstat(fd).st_ino
                    and scope_supported(proof["cgroup"], proof["unit"])
                )
            return False
        finally:
            os.close(fd)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return False


def sharing_lock_inventory(fd: int, expected_mode: str) -> bool:
    """Require the expected kernel flock and no earlier ticketless blocked caller.

    This is inode-backed lock evidence, not a PID liveness inference. Missing, partial or
    incompatible kernel evidence keeps exclusive admission.
    """
    try:
        info = os.fstat(fd)
        target = (os.major(info.st_dev), os.minor(info.st_dev), info.st_ino)
        with Path("/proc/locks").open("rb") as stream:
            data = stream.read(2 * 1024**2 + 1)
        if len(data) > 2 * 1024**2:
            return False
        modes = []
        for line in data.decode("ascii").splitlines():
            fields = line.split()
            waiting = "->" in fields
            fields = [field for field in fields if field != "->"]
            if len(fields) != 8:
                return False
            major, minor, inode = fields[5].split(":")
            if (int(major, 16), int(minor, 16), int(inode)) != target:
                continue
            if waiting or fields[1:3] != ["FLOCK", "ADVISORY"] or fields[6:] != ["0", "EOF"]:
                return False
            modes.append(fields[3])
        return modes == [expected_mode]
    except (OSError, ValueError, UnicodeError):
        return False


class ResourceScope:
    """Gate-owned scoped stage execution, retaining inherited reservations until cleanup.

    The scoped executor is idle until its real cgroup and inherited descriptors are verified.
    Setup failure therefore precedes every check. It remains the lock owner if its launcher dies.
    """

    def __init__(self, root: Path, launcher: str, head_admission: Admission):
        self.root = root
        self.launcher = launcher
        self.head_admission = head_admission
        self.unit = f"lu-pre-push-{uuid.uuid4().hex}.scope"
        self.process: subprocess.Popen | None = None
        self.channel: socket.socket | None = None
        self.stream = None
        self.group: str | None = None
        self.reason: str | None = None
        self.resources: dict[str, object] = {}
        self.setup_s = 0.0
        self.completed = False
        self.admission: Admission | None = None

    def start(self, admission: Admission) -> bool:
        started = time.monotonic()
        self.admission = admission
        parent, child = socket.socketpair()
        self.channel = parent
        parent.settimeout(5.0)
        self.stream = parent.makefile("rwb", buffering=0)
        descriptors = [admission._fd, admission._ticket_fd, self.head_admission._fd, self.head_admission._ticket_fd]
        try:
            self.process = subprocess.Popen(
                [
                    "systemd-run",
                    "--user",
                    "--scope",
                    "--quiet",
                    "--unit",
                    self.unit,
                    "--property=MemoryMax=6G",
                    "--property=MemoryAccounting=yes",
                    "--description=Protected push validation",
                    "bash",
                    self.launcher,
                    str(Path(__file__).resolve()),
                    "--scope-child",
                    str(child.fileno()),
                    self.unit,
                    *(str(fd) for fd in descriptors),
                ],
                cwd=self.root,
                env=clean_environment(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                pass_fds=(child.fileno(), *descriptors),
                start_new_session=True,
            )
            child.close()
            ready = json.loads(self.stream.readline(65536))
            self.group = ready.get("cgroup")
            if ready.get("ready") is not True or not scope_supported(self.group, self.unit):
                self.reason = "scope_support_unknown"
                self.close()
                return False
            proof = {
                "mode": "optin_scope",
                "max_concurrent_runs": 2,
                "unit": self.unit,
                "cgroup": self.group,
                "effective_workers": int(parallel_options()[1]) if parallel_options() else 1,
                "ticket_inode": os.fstat(admission._ticket_fd).st_ino,
            }
            path = admission._ticket.with_suffix(".scope.json")
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(proof), encoding="utf-8")
            temporary.replace(path)
            return True
        except (OSError, ValueError, TypeError, AttributeError) as error:
            self.reason = f"scope_setup_{type(error).__name__}"
            self.close()
            return False
        finally:
            child.close()
            self.setup_s = time.monotonic() - started

    def execute(
        self, plan: Plan, config: str, deadline: float, event: dict[str, object], *, stage_budget_s: float
    ) -> None:
        assert self.stream is not None and self.channel is not None
        self.channel.settimeout(max(0.01, deadline - time.monotonic()) + SHADOW_BUDGET_S + 2 * CLEANUP_BUDGET_S)
        packet = {
            "plan": {name: value for name, value in vars(plan).items() if name != "node_ids"},
            "root": str(self.root),
            "launcher": self.launcher,
            "config": config,
            "deadline": deadline,
            "stage_budget_s": stage_budget_s,
        }
        try:
            self.channel.sendall((json.dumps(packet) + "\n").encode())
            result = json.loads(self.stream.readline(16 * 1024 * 1024))
            event.update(result["event"])
            self.completed = result["settled"]
            if result["error"] is not None:
                raise GateOutcome(**result["error"])
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise GateOutcome(
                "validation_incomplete", "scoped executor did not return a complete verdict", incomplete=True
            ) from error
        finally:
            self.close()

    def close(self) -> None:
        """Release only this scope, and only after its children have gone."""
        if self.admission is not None:
            self.admission.withdraw_sharing()
        if self.stream is not None:
            self.stream.close()
            self.stream = None
        if self.channel is not None:
            self.channel.close()
            self.channel = None
        if self.process is None:
            return
        deadline = time.monotonic() + CLEANUP_BUDGET_S
        try:
            if not self.completed and (self.process.poll() is None or self.group is not None):
                subprocess.run(
                    ["systemctl", "--user", "kill", "--signal=SIGKILL", "--kill-whom=all", self.unit],
                    capture_output=True,
                    timeout=max(0.01, deadline - time.monotonic()),
                    check=False,
                    env=clean_environment(),
                )
            self.process.wait(timeout=max(0.01, deadline - time.monotonic()))
            if self.group is not None:
                group = scope_cgroup(self.group)
                while True:
                    try:
                        populated = "populated 1" in (group / "cgroup.events").read_text().splitlines()
                    except FileNotFoundError:
                        populated = False
                    if not populated:
                        break
                    if time.monotonic() >= deadline:
                        raise OSError("scope still contains descendants")
                    time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            raise GateOutcome(
                "validation_incomplete", "own scope cleanup is unverified; stop", incomplete=True
            ) from error
        finally:
            self.process = None


class Admission:
    """FIFO reservations across worktrees; the scoped experiment can share two.

    A ticket's flock is its liveness proof, including after a crash; no PID inference. Publication
    uses rename after locking, so observers cannot mistake a registering caller for a dead one.
    The allowance grows with the most predecessors observed, never shrinks as they finish, and
    never exceeds ``ADMISSION_MAX_WAIT_S``. Older gates without tickets still hold admission.lock.
    """

    def __init__(
        self,
        state: Path,
        wait_s: float,
        *,
        update: Update | None = None,
        prior: Admission | None = None,
        root: Path | None = None,
        global_state: Path | None = None,
        scope: ResourceScope | None = None,
    ):
        self.state = state
        self.global_state = global_state
        self.wait_s = wait_s
        self.identity = (
            prior.identity if prior is not None else ticket_identity(update, root) if update is not None else None
        )
        self._started = prior._started if prior is not None else None
        self.waited = 0.0
        self.queue_depth = 0
        self.queue_position = 0
        self.wait_limit = prior.wait_limit if prior is not None else 0.0
        self._fd: int | None = None
        self._ticket_fd: int | None = None
        self._ticket: Path | None = None
        self._launcher_fd: int | None = None
        self._exclusive = False
        self.scope = scope

    def withdraw_sharing(self) -> None:
        if self._launcher_fd is not None:
            os.close(self._launcher_fd)
            self._launcher_fd = None

    def _parallel_slot(self, position: int) -> bool:
        if self.scope is None or position > 2:
            return False
        mutex = os.open(self.state / "sharing.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(mutex, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return False
            # Recheck under the shared-mode transition lock. A serial waiter always blocks followers.
            live = self._live_tickets()
            position = live.index(self._ticket) + 1
            if position > 2 or (position == 2 and not scoped_holder(live[0])):
                return False
            self.scope.resources = admission_resources()
            if not self.scope.resources["qualified"]:
                self.scope.reason = "resources_unqualified_or_unknown"
                self.scope = None
                return False
            try:
                if position == 1:
                    fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                if not sharing_lock_inventory(self._fd, "WRITE" if position == 1 else "READ"):
                    self.scope.reason = "kernel_lock_inventory_unknown_or_blocked"
                    self.scope = None
                    if position == 1:
                        fcntl.flock(self._fd, fcntl.LOCK_UN)
                    return False
                fcntl.flock(self._fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError:
                return False
            self._launcher_fd = os.open(
                self._ticket.with_suffix(".launcher.lock"), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
            )
            fcntl.flock(self._launcher_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if self.scope.start(self):
                return True
            self.scope = None
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            return False
        finally:
            os.close(mutex)

    def _register(self) -> None:
        queue = self.state / "queue"
        queue.mkdir(parents=True, exist_ok=True)
        pending = queue / f".{uuid.uuid4().hex}.pending"
        self._ticket = pending
        self._ticket_fd = os.open(pending, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
        fcntl.flock(self._ticket_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if self.identity is not None:
            with os.fdopen(os.dup(self._ticket_fd), "w", encoding="utf-8") as stream:
                json.dump(self.identity, stream, sort_keys=True)
                stream.write("\n")
        ticket = queue / f"{time.monotonic_ns():020d}-{uuid.uuid4().hex}.ticket"
        pending.rename(ticket)
        self._ticket = ticket

    def _live_tickets(self, queue: Path | None = None) -> list[Path]:
        assert self._ticket is not None
        live = []
        for ticket in sorted((queue if queue is not None else self._ticket.parent).glob("*.ticket")):
            try:
                fd = os.open(ticket, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            except FileNotFoundError:  # a holder finished between listing and opening
                continue
            except OSError as error:
                if ticket != self._ticket:
                    try:
                        regular = stat.S_ISREG(ticket.lstat().st_mode)
                    except FileNotFoundError:
                        continue
                    if not regular:
                        reap_stale_node(ticket)
                        continue
                if error.errno != errno.ELOOP:
                    raise
                raise GateOutcome("validation_incomplete", "admission ticket is a symlink", incomplete=True) from None
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode):
                    if ticket != self._ticket:
                        reap_stale_node(ticket)
                        continue
                    raise GateOutcome(
                        "validation_incomplete", "admission ticket is not a regular file", incomplete=True
                    )
                if ticket == self._ticket:
                    assert self._ticket_fd is not None
                    own = os.fstat(self._ticket_fd)
                    if (info.st_dev, info.st_ino) != (own.st_dev, own.st_ino):
                        raise GateOutcome("validation_incomplete", "own admission ticket was replaced", incomplete=True)
                    live.append(ticket)
                    continue
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    live.append(ticket)
                else:  # no live owner: an interrupted caller left this ticket behind
                    ticket.unlink(missing_ok=True)
            finally:
                os.close(fd)
        if len(live) > MAX_QUEUE_ENTRIES:
            raise GateOutcome("validation_incomplete", "admission queue scan limit exceeded", incomplete=True)
        return live

    def __enter__(self) -> Admission:
        stage_started = time.monotonic()
        started = stage_started if self._started is None else self._started
        self._started = started
        last_report: tuple[int, int] | None = None
        reported_at = started
        try:
            self.state.mkdir(parents=True, exist_ok=True)
            self._fd = os.open(self.state / "admission.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            self._register()
            while True:
                live = self._live_tickets()
                try:
                    position, depth = live.index(self._ticket) + 1, len(live)
                except ValueError:
                    raise GateOutcome(
                        "validation_incomplete", "own admission ticket is missing", incomplete=True
                    ) from None
                if position == 1:
                    if self._parallel_slot(position):
                        self.queue_depth = max(self.queue_depth, depth)
                        self.queue_position = self.queue_position or position
                        return self
                    try:
                        fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:  # includes an older gate with no ticket
                        position, depth = 2, depth + 1
                    else:
                        self._exclusive = True
                        self.queue_depth = max(self.queue_depth, depth)
                        self.queue_position = self.queue_position or 1
                        return self
                elif self._parallel_slot(position):
                    self.queue_depth = max(self.queue_depth, depth)
                    self.queue_position = self.queue_position or position
                    return self
                self.queue_depth = max(self.queue_depth, depth)
                self.queue_position = self.queue_position or position
                global_depth = len(self._live_tickets(self.global_state / "queue")) if self.global_state else 0
                allowance = max(1, position - 1 + global_depth) * self.wait_s
                self.wait_limit = max(self.wait_limit, min(ADMISSION_MAX_WAIT_S, stage_started - started + allowance))
                self.waited = time.monotonic() - started
                report = (position, depth)
                if report != last_report or time.monotonic() - reported_at >= 30.0:
                    print(
                        f"PRE-PUSH GATE: waiting for admission; queue position {position}/{depth}; "
                        f"waited {self.waited:.1f}s, limit {self.wait_limit:.0f}s "
                        f"(hard ceiling {ADMISSION_MAX_WAIT_S:.0f}s)",
                        file=sys.stderr,
                        flush=True,
                    )
                    last_report, reported_at = report, time.monotonic()
                if self.waited >= self.wait_limit:
                    raise GateOutcome(
                        "validation_incomplete",
                        f"admission_timeout: waited {self.waited:.1f}s at queue position {position}/{depth} "
                        f"(limit {self.wait_limit:.0f}s)",
                        incomplete=True,
                    )
                time.sleep(min(0.2, self.wait_limit - self.waited))
        except BaseException:
            self.__exit__()
            raise
        finally:
            self.waited = time.monotonic() - started

    def __exit__(self, *exc: object) -> None:
        self._exclusive = False
        self.withdraw_sharing()
        if self.scope is not None:
            self.scope.close()
        if self._ticket is not None:
            with contextlib.suppress(OSError):
                self._ticket.with_suffix(".scope.json").unlink(missing_ok=True)
                self._ticket.with_suffix(".launcher.lock").unlink(missing_ok=True)
                self._ticket.unlink(missing_ok=True)
            self._ticket = None
        if self._ticket_fd is not None:
            os.close(self._ticket_fd)
            self._ticket_fd = None
        if self._fd is not None:
            os.close(self._fd)  # closing the descriptor releases the flock
            self._fd = None


def sweep_descendants(token: str, deadline: float) -> None:
    """SIGKILL every process that inherited ``token``, wherever it moved (setsid, double fork).

    Linux ``/proc`` only; elsewhere the process-group kill is the whole containment.  Repeats until
    a pass finds nothing, so a descendant that forks during the sweep is caught too.
    """
    needle = f"{RUN_TOKEN_ENV}={token}".encode()
    proc = Path("/proc")
    if not proc.is_dir():
        return
    while time.monotonic() < deadline:
        found = False
        for entry in proc.iterdir():
            if not entry.name.isdigit() or int(entry.name) == os.getpid():
                continue
            try:
                environment = (entry / "environ").read_bytes()
            except OSError:
                continue
            if needle in environment.split(b"\0"):
                found = True
                with contextlib.suppress(ProcessLookupError, PermissionError):
                    os.kill(int(entry.name), signal.SIGKILL)
        if not found:
            return
        time.sleep(0.05)


def terminate_run(process: subprocess.Popen[str], token: str) -> bool:
    """Kill the process group, sweep the token's descendants and reap, all within ``CLEANUP_BUDGET_S``.

    Returns whether the process was reaped; never raises, so it is safe on every cleanup path.
    """
    deadline = time.monotonic() + CLEANUP_BUDGET_S
    if process.poll() is None:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(process.pid, signal.SIGKILL)
    sweep_descendants(token, deadline)
    try:
        process.wait(timeout=max(0.0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        return False
    return True


def run_bounded(
    command: list[str], *, cwd: Path, deadline: float, label: str, diagnostics: dict[str, object] | None = None
) -> tuple[int, str]:
    """Run in its own process group; on budget exhaustion kill the group and report incomplete.

    Output goes to a file, never a pipe, so a descendant that outlives the command cannot block the
    gate on a pipe it still holds.  Every exit path then kills the run's leftover descendants.
    """
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        if diagnostics is not None:
            diagnostics["child_unavailable_reason"] = "budget_exhausted_before_start"
        raise GateOutcome(
            "validation_incomplete", f"{label}: time budget exhausted before start (timeout)", incomplete=True
        )
    token = uuid.uuid4().hex
    environment = {**clean_environment(), RUN_TOKEN_ENV: token}
    if diagnostics is not None:
        diagnostics["child_unavailable_reason"] = "output_file_unavailable"
    with tempfile.TemporaryFile() as sink:
        process = None
        try:
            if diagnostics is not None:
                diagnostics["child_unavailable_reason"] = "spawn_error"
            try:
                process = subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=environment,
                    stdin=subprocess.DEVNULL,
                    stdout=sink,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            except OSError as exc:
                raise GateOutcome("validation_incomplete", f"{label}: cannot start ({exc})", incomplete=True) from exc
            timed_out = False
            try:
                process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                timed_out = True
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
            except BaseException:
                terminate_run(process, token)
                raise
            finally:
                sweep_descendants(token, time.monotonic() + CLEANUP_BUDGET_S)
            if timed_out:
                try:
                    process.wait(timeout=CLEANUP_BUDGET_S)
                except subprocess.TimeoutExpired:
                    raise GateOutcome(
                        "validation_incomplete", f"{label}: could not reap the timed-out process", incomplete=True
                    ) from None
                raise GateOutcome(
                    "validation_incomplete", f"{label}: exceeded the time budget (timeout)", incomplete=True
                )
            sink.seek(0)
            return process.returncode, sink.read().decode("utf-8", errors="replace")
        finally:
            if diagnostics is not None:
                if process is not None:
                    code = process.returncode
                    diagnostics.update(
                        returncode=code,
                        signal=-code if code is not None and code < 0 else None,
                        child_unavailable_reason="exit_unobserved" if code is None else None,
                    )
                try:
                    size = sink.seek(0, os.SEEK_END)
                    sink.seek(max(0, size - OUTPUT_TAIL_BYTES))
                    diagnostics["output_tail"] = tail(sink.read(OUTPUT_TAIL_BYTES).decode("utf-8", errors="replace"))
                except OSError:
                    diagnostics["output_unavailable_reason"] = "output_read_error"


def failing_node_ids(output: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(FAILURE_RE.findall(output)))


def run_pre_commit_stage(
    plan: Plan, root: Path, launcher: str, config: str, deadline: float, *, diagnostics: dict[str, object] | None = None
) -> None:
    code, output = run_bounded(
        [
            "bash",
            launcher,
            "-m",
            "pre_commit",
            "run",
            "--hook-stage",
            "pre-push",
            "-c",
            config,
            "--from-ref",
            plan.base,
            "--to-ref",
            plan.head,
        ],
        cwd=root,
        deadline=deadline,
        label="pre-commit pre-push stage",
        diagnostics=diagnostics,
    )
    if code != 0:
        hooks = tuple(dict.fromkeys(name.strip() for name in PRE_COMMIT_FAILED_RE.findall(output)))
        raise GateOutcome("pre_commit_failed", tail(output), failing=hooks)
    # pre-commit's net-diff filename selection may skip OPSEC entirely when
    # intermediate changes cancel out. Always inspect the outgoing history.
    code, output = run_bounded(
        ["bash", launcher, "scripts/audit/lint_opsec_leaks.py", "--commit-range", f"{plan.base}..{plan.head}"],
        cwd=root,
        deadline=deadline,
        label="per-commit OPSEC scan",
        diagnostics=diagnostics,
    )
    if code != 0:
        raise GateOutcome("pre_commit_failed", tail(output), failing=("lint-opsec-leaks",))
    # Select the existing hook explicitly at its installed stage so its exact
    # learner-surface filter and scanner remain the source of truth.
    code, output = run_bounded(
        [
            "bash", launcher, "-m", "pre_commit", "run", "check-no-internal-ids",
            "--hook-stage", "pre-commit", "-c", config, "--from-ref", plan.base, "--to-ref", plan.head,
        ],
        cwd=root,
        deadline=deadline,
        label="learner-surface internal-ID scan",
        diagnostics=diagnostics,
    )
    if code != 0:
        raise GateOutcome("pre_commit_failed", tail(output), failing=("check-no-internal-ids",))


def test_process_limit() -> int:
    """Read the configured process ceiling; invalid configuration refuses validation."""
    value = os.environ.get(MAX_TEST_PROCESSES_ENV, "4")
    try:
        if re.fullmatch(r"[0-9]+", value) is None or int(value) < 1:
            raise ValueError
        return int(value)
    except ValueError:
        raise GateOutcome(
            "invalid_configuration", f"{MAX_TEST_PROCESSES_ENV} must be a positive integer", incomplete=True
        ) from None


def parallel_options(dist: str = "loadfile") -> list[str]:
    """Use configured parallelism when available, scheduled by xdist mode ``dist``."""
    limit = test_process_limit()
    if limit == 1 or importlib.util.find_spec("xdist") is None:
        return []
    if os.environ.get("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "").strip():
        limit = min(limit, 2)  # Match ci.pytest_dispatch_cap before recording the invocation.
    return ["-n", str(limit), "--dist", dist]


def pytest_invocations(plan: Plan) -> tuple[tuple[tuple[str, ...], str], ...]:
    """Split the plan's node ids into ``(node_ids, xdist mode)`` runs that together cover every id once.

    Changed test files are distributed per test (``worksteal``, as CI runs them) so one slow
    changed file cannot pin a single worker for the whole stage (#10610); they run first, as the
    likeliest to fail. Registered invariant nodes keep whole files on one worker (``loadfile``).
    """
    changed = set(plan.changed_tests)
    distributed = tuple(node for node in plan.node_ids if node.split("::", 1)[0] in changed)
    grouped = tuple(node for node in plan.node_ids if node.split("::", 1)[0] not in changed)
    return tuple((nodes, dist) for nodes, dist in ((distributed, "worksteal"), (grouped, "loadfile")) if nodes)


def inside_git_tree(path: Path) -> bool:
    """Whether ``path`` or an ancestor is a Git checkout or a Git directory, as Git discovery finds them.

    A checkout has a ``.git`` entry (directory or gitfile). A Git directory, bare or not, holds
    ``HEAD``, ``objects`` and ``refs``. An ancestor that cannot be inspected counts as inside.
    """

    def present(entry: Path) -> bool:
        try:
            entry.lstat()
        except (FileNotFoundError, NotADirectoryError):
            return False
        return True

    try:
        return any(
            present(directory / ".git") or all(present(directory / name) for name in ("HEAD", "objects", "refs"))
            for directory in (path, *path.parents)
        )
    except OSError:
        return True


def private_directory(path: Path) -> int:
    """Create ``path`` with mode 0700 if missing and open it without following a link.

    Requires a real directory owned by this user, closed to others, and returns its descriptor for the
    caller to close.
    """
    try:
        path.mkdir(mode=0o700, exist_ok=True)
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as error:
        raise GateOutcome(
            "pytest_temp_unavailable",
            f"cannot create a private pytest base temp directory ({errno.errorcode.get(error.errno, 'error')}); "
            f"set {SCRATCH_ROOT_ENV} to a writable directory outside every Git checkout",
            incomplete=True,
        ) from None
    info = os.fstat(fd)
    if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077:
        os.close(fd)
        raise GateOutcome(
            "pytest_temp_unavailable",
            "the pytest base temp directory is not private to this user (owner or mode); remove it and push again",
            incomplete=True,
        )
    return fd


def pytest_temp_parent(state: Path) -> Path:
    """Return this repository's private parent for pytest base temps, outside every Git tree (#10654).

    The root follows the fleet scratch convention: ``LU_SCRATCH_ROOT`` when set (strictly), else
    ``/var/tmp/lu``, else ``<system temp>/lu-scratch`` when the default cannot be created. Below it a
    per-user 0700 directory holds one 0700 directory per Git common dir. Nothing sweeps them: each run
    removes only its own base (``own_base_temp``) and the host's scratch aging owns what a killed run
    leaves. An unsafe or uncreatable location refuses the push as incomplete; it never falls back into Git.
    """

    def unsafe() -> GateOutcome:
        return GateOutcome(
            "pytest_temp_unavailable",
            f"the pytest base temp root is inside a Git checkout or Git directory; set {SCRATCH_ROOT_ENV} "
            "to a directory outside every Git checkout",
            incomplete=True,
        )

    override = os.environ.get(SCRATCH_ROOT_ENV, "").strip()
    candidates = (
        [Path(override)] if override else [DEFAULT_SCRATCH_ROOT, Path(tempfile.gettempdir()) / FALLBACK_SCRATCH_DIRNAME]
    )
    scratch, failure = None, "error"
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
            if inside_git_tree(resolved):
                raise unsafe()
            resolved.mkdir(parents=True, exist_ok=True)
        except (OSError, RuntimeError) as error:  # RuntimeError: a symlink loop before Python 3.13
            failure = errno.errorcode.get(getattr(error, "errno", None), "error")
            continue
        scratch = resolved
        break
    if scratch is None:
        raise GateOutcome(
            "pytest_temp_unavailable",
            f"cannot create the pytest base temp root ({failure}); "
            f"set {SCRATCH_ROOT_ENV} to a writable directory outside every Git checkout",
            incomplete=True,
        )
    user = scratch / f"pre-push-gate-{os.geteuid()}"
    parent = user / hashlib.sha256(os.fsencode(state.resolve())).hexdigest()[:32]
    for directory in (user, parent):
        os.close(private_directory(directory))
    if inside_git_tree(parent):
        raise unsafe()
    return parent


def remove_own_base_temp(parent_fd: int, name: str) -> None:
    """Remove ``name`` below ``parent_fd`` and everything in it, never following a link.

    Every directory is opened relative to its parent's descriptor with ``O_NOFOLLOW``, so a rename or
    link above or inside the base cannot redirect the removal. A directory a test left without owner
    access is first given 0700, as ``tempfile.TemporaryDirectory`` does, without following a link.
    """
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        if not stat.S_ISDIR(os.stat(name, dir_fd=parent_fd, follow_symlinks=False).st_mode):
            os.unlink(name, dir_fd=parent_fd)
            return
        try:
            fd = os.open(name, flags, dir_fd=parent_fd)
        except PermissionError:
            os.chmod(name, 0o700, dir_fd=parent_fd, follow_symlinks=False)
            fd = os.open(name, flags, dir_fd=parent_fd)
        try:
            os.fchmod(fd, 0o700)
            for entry in os.listdir(fd):
                remove_own_base_temp(fd, entry)
        finally:
            os.close(fd)
        os.rmdir(name, dir_fd=parent_fd)
    except FileNotFoundError:
        return


@contextlib.contextmanager
def own_base_temp(parent: Path):
    """Create this run's own pytest base temp below ``parent`` and remove only it afterwards (#10654).

    The private parent is opened once without following a link, and the base is created and removed
    relative to that descriptor, so replacing any ancestor after validation cannot redirect either step
    into another run's base. Pytest deletes and recreates a given ``--basetemp``, so the base is held by
    name inside the anchored parent, not by its own descriptor. No other run's base is ever removed.
    """
    parent_fd = private_directory(parent)
    try:
        name = f"pytest-{uuid.uuid4().hex}"
        try:
            os.mkdir(name, 0o700, dir_fd=parent_fd)
        except OSError as error:
            raise GateOutcome(
                "pytest_temp_unavailable",
                f"cannot create the pytest base temp ({errno.errorcode.get(error.errno, 'error')})",
                incomplete=True,
            ) from None
        try:
            yield str(parent / name)
        except BaseException:
            with contextlib.suppress(OSError):  # the run's own outcome outranks a cleanup failure
                remove_own_base_temp(parent_fd, name)
            raise
        try:
            remove_own_base_temp(parent_fd, name)
        except OSError as error:
            raise GateOutcome(
                "validation_incomplete",
                f"pytest base temp cleanup failed ({errno.errorcode.get(error.errno, 'error')})",
                incomplete=True,
            ) from None
    finally:
        os.close(parent_fd)


def run_pytest_stage(
    plan: Plan,
    root: Path,
    launcher: str,
    deadline: float,
    *,
    diagnostics: dict[str, object] | None = None,
    admission: Admission | None = None,
) -> str:
    state = state_dir(root)
    state.mkdir(parents=True, exist_ok=True)
    temp_parent = pytest_temp_parent(state)
    # Only the actual exclusive global holder can prove that no other gate owns these bases.
    exclusive = (
        admission is not None
        and admission._exclusive
        and admission._fd is not None
        and admission.scope is None
        and admission.state == state
    )
    if diagnostics is not None:
        diagnostics["stale_pytest_cleanup"] = "exclusive_sweep" if exclusive else "skipped_shared_or_unknown"
    if exclusive:
        for stale in state.glob("pytest-*"):
            reap_stale_node(stale)
    if not plan.node_ids:
        return "no tests selected"
    invocations = pytest_invocations(plan)
    options = parallel_options()
    if diagnostics is not None:
        diagnostics.update(
            requested_test_processes=test_process_limit(),
            effective_test_processes=int(options[1]) if options else 1,
            pytest_invocations=[{"dist": dist, "nodes": len(nodes)} for nodes, dist in invocations],
        )
    # The runs share the stage deadline and stop at the first refusal; a green stage means every run passed.
    summaries = []
    for nodes, dist in invocations:
        with own_base_temp(temp_parent) as base_temp:
            code, output = run_bounded(
                [
                    "bash",
                    launcher,
                    "-m",
                    "pytest",
                    *nodes,
                    "-rfE",
                    "-q",
                    "--tb=short",
                    "-p",
                    "no:cacheprovider",
                    "--basetemp",
                    base_temp,
                    *parallel_options(dist),
                ],
                cwd=root,
                deadline=deadline,
                label="pytest stage",
                diagnostics=diagnostics,
            )
        failing = failing_node_ids(output)
        if code == 0:
            match = SUMMARY_RE.findall(output)
            summaries.append(match[-1].strip("= ") if match else "pytest passed")
        elif code == 1 or failing:
            raise GateOutcome("tests_failed", tail(output), failing=failing)
        elif code != NO_TESTS_COLLECTED:
            break
    # One run collecting nothing is fine while the selection as a whole ran tests.
    if summaries and code in (0, NO_TESTS_COLLECTED):
        return "; ".join(summaries)
    raise GateOutcome("pytest_error", f"pytest exited {code} without a verdict\n{tail(output)}", incomplete=True)


class Shadow:
    """Importer-closure selection started beside the blocking stages and only recorded.

    It never gates: every failure, including a timeout, becomes data in the
    measurement row.  Output goes to a file so a large selection cannot fill a pipe.
    """

    def __init__(self, plan: Plan, root: Path, launcher: str):
        self.output = tempfile.TemporaryFile(mode="w+")  # noqa: SIM115 - closed in finish()
        self.deadline = time.monotonic() + SHADOW_BUDGET_S
        self.token = uuid.uuid4().hex
        try:
            self.process: subprocess.Popen[str] | None = subprocess.Popen(
                ["bash", launcher, "-m", "scripts.ci.pre_push_shadow", "--paths", *plan.changed_paths],
                cwd=root,
                env={**clean_environment(), RUN_TOKEN_ENV: self.token},
                stdin=subprocess.DEVNULL,
                stdout=self.output,
                stderr=subprocess.DEVNULL,
                text=True,
                start_new_session=True,
            )
        except OSError:
            self.process = None

    def finish(self) -> dict[str, object]:
        try:
            if self.process is None:
                return {"status": "unavailable", "detail": "could not start"}
            try:
                self.process.wait(timeout=max(0.0, self.deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                terminate_run(self.process, self.token)
                return {"status": "unavailable", "detail": "shadow time budget exhausted"}
            terminate_run(self.process, self.token)  # the selector exited; its detached descendants must not outlive it
            if self.process.returncode != 0:
                return {"status": "unavailable", "detail": f"exit {self.process.returncode}"}
            try:
                self.output.seek(0)
                selection = json.loads(self.output.read().strip().splitlines()[-1])
            except (OSError, ValueError, IndexError):
                return {"status": "unavailable", "detail": "unparseable output"}
            if not isinstance(selection, dict):
                return {"status": "unavailable", "detail": "unexpected result shape"}
            selected = selection.get("selected_tests")
            if not isinstance(selected, list) or not all(isinstance(test, str) for test in selected):
                return {"status": "unavailable", "detail": "unexpected selected_tests shape"}
            selected = sorted(selected)
            try:
                digest = hashlib.sha256("\n".join(selected).encode()).hexdigest()[:16]
            except UnicodeEncodeError:  # e.g. a lone surrogate from a JSON "\ud800" escape
                return {"status": "unavailable", "detail": "cannot encode selected_tests"}
            return {
                "status": "recorded",
                "selected_count": len(selected),
                "components": selection.get("components", []),
                "fallback_reasons": selection.get("fallback_reasons", []),
                "selected_digest": digest,
            }
        finally:
            self.output.close()

    def abandon(self) -> None:
        if self.process is not None:
            terminate_run(self.process, self.token)
        self.output.close()


def bounded(name: str, ceiling: float) -> float:
    """An environment override may only shorten a bound, never lengthen it."""
    try:
        return max(0.0, min(ceiling, float(os.environ.get(name, ceiling))))
    except ValueError:
        return ceiling


def tail(output: str, lines: int = 40) -> str:
    return "\n".join(output.rstrip().splitlines()[-lines:])


# ---- entry point ----------------------------------------------------------


class Budget:
    """Push execution budget: a total shared by every ref update, plus each stage's own allowance.

    The total starts at admission and excludes later admission waits. Each blocking stage's allowance
    starts when that stage starts and stays inside the total (#10642).
    """

    def __init__(self, seconds: float, stage_seconds: float = STAGE_BUDGET_S):
        self.seconds = seconds
        self.stage_seconds = stage_seconds
        self._deadline: float | None = None

    @classmethod
    def configured(cls) -> Budget:
        return cls(
            bounded("LU_PRE_PUSH_GATE_RUN_BUDGET_S", RUN_BUDGET_S),
            bounded("LU_PRE_PUSH_GATE_STAGE_BUDGET_S", STAGE_BUDGET_S),
        )

    @property
    def deadline(self) -> float:
        if self._deadline is None:
            self._deadline = time.monotonic() + self.seconds
        return self._deadline

    def after_admission(self, waited: float) -> float:
        if self._deadline is not None:
            self._deadline += waited
        return self.deadline


@contextlib.contextmanager
def stage_measurement(event: dict[str, object], name: str):
    """Observe only entered stages; preserve diagnostics when the stage raises."""
    started = time.monotonic()
    diagnostics: dict[str, object] = {
        "outcome": "validation_incomplete",
        "reason": "stage_interrupted",
        "returncode": None,
        "signal": None,
        "child_unavailable_reason": "stage_did_not_start_child",
        "output_tail": None,
        "allowance_s": None,
        "allowance_limited_by": None,
    }
    event.setdefault("stages", {})[name] = diagnostics
    try:
        yield diagnostics
    except GateOutcome as error:
        diagnostics.update(outcome="validation_incomplete" if error.incomplete else "refused", reason=error.reason)
        raise
    except OSError:
        diagnostics["reason"] = "validation_error"
        raise
    else:
        diagnostics.update(outcome="green", reason=None)
    finally:
        diagnostics["elapsed_s"] = time.monotonic() - started


def stage_deadline(deadline: float, stage_budget_s: float, diagnostics: dict[str, object]) -> float:
    """Start a stage's own allowance now, inside the push's total deadline, and record which one binds."""
    now = time.monotonic()
    own = now + stage_budget_s
    diagnostics.update(
        allowance_s=max(0.0, min(own, deadline) - now),
        allowance_limited_by="stage_budget" if own <= deadline else "run_budget",
    )
    return min(own, deadline)


def execute_stages(
    plan: Plan,
    root: Path,
    launcher: str,
    config: str,
    deadline: float,
    event: dict[str, object],
    *,
    stage_budget_s: float,
    persist_receipt: bool = True,
    admission: Admission | None = None,
) -> None:
    state = state_dir(root)
    shadow: Shadow | None = None
    settled = False
    try:
        shadow = Shadow(plan, root, launcher)
        with stage_measurement(event, "pre_commit") as diagnostics:
            run_pre_commit_stage(
                plan,
                root,
                launcher,
                config,
                stage_deadline(deadline, stage_budget_s, diagnostics),
                diagnostics=diagnostics,
            )
        with stage_measurement(event, "pytest") as diagnostics:
            event["pytest"] = run_pytest_stage(
                plan,
                root,
                launcher,
                stage_deadline(deadline, stage_budget_s, diagnostics),
                diagnostics=diagnostics,
                admission=admission,
            )
        if persist_receipt:
            try:
                write_receipt(state, plan, time.time())
            except OSError as error:
                raise GateOutcome(
                    "receipt_unwritable", f"cannot persist the green receipt: {error}", incomplete=True
                ) from error
        event["shadow"] = shadow.finish()
        settled = True
        event["outcome"] = "green"
    finally:
        if not settled and shadow is not None:  # whatever escapes, the shadow must not outlive the hook
            shadow.abandon()


def validate(
    update: Update, root: Path, launcher: str, config: str, event: dict[str, object], budget: Budget | None = None
) -> None:
    event["local_ref"] = update.local_ref
    event.update(admission_wait_s=0.0, queue_depth=0, queue_position=0)
    plan = build_plan(update, root)
    if plan is None:
        event["outcome"] = "green"
        event["detail"] = "no outgoing commits"
        return
    event.update(
        head=plan.head,
        base=plan.base,
        nodes=len(plan.node_ids),
        registry_version=plan.registry_version,
        deferred_to_ci=list(plan.deferred_to_ci),
    )
    state = state_dir(root)
    head_state = coalescing_state(state, plan)
    frozen_key = receipt_key(plan)
    event["validation_fingerprint"] = hashlib.sha256(json.dumps(frozen_key, sort_keys=True).encode()).hexdigest()
    if receipt_is_fresh(state, plan, time.time()):
        event["outcome"] = "green"
        event["detail"] = "valid receipt"
        return
    wait_s = bounded("LU_PRE_PUSH_GATE_ADMISSION_WAIT_S", ADMISSION_WAIT_S)
    head_admission = Admission(head_state, wait_s, update=update, root=root, global_state=state)
    admission = head_admission
    scope = None
    try:
        with contextlib.ExitStack() as locks:
            locks.enter_context(head_admission)
            # Followers have no global ticket. A head is only a serialization group,
            # so rebuild inputs and compare the entire frozen key before receipt reuse.
            refreshed = build_plan(update, root)
            if refreshed is None or receipt_key(refreshed) != frozen_key:
                raise GateOutcome("tree_mismatch", "validation inputs changed while waiting for coalescing")
            if receipt_is_fresh(state, plan, time.time()):
                event.update(outcome="green", detail="valid receipt after coalescing")
                if budget is not None and budget._deadline is not None:
                    budget.after_admission(head_admission.waited)
                return
            options = parallel_options()
            effective = int(options[1]) if options else 1
            if concurrent_run_limit() == 2 and effective <= 4:
                scope = ResourceScope(root, launcher, head_admission)
            scope_kwargs = {"scope": scope} if scope is not None else {}
            admission = Admission(state, wait_s, update=update, prior=head_admission, **scope_kwargs)
            admitted = locks.enter_context(admission)
            budget = budget or Budget.configured()
            deadline = budget.after_admission(admitted.waited)
            resources = scope.resources if getattr(admitted, "scope", None) is not None else admission_resources()
            event["resources_at_admission"] = resources
            event["scope"] = {
                "status": "supported" if getattr(admitted, "scope", None) is not None else "serial",
                "reason": scope.reason if scope is not None else "default_or_worker_bound",
            }
            # A matching gate may have finished while this caller was queued. Rebuild the plan
            # first to preserve the dirty-tree/untracked-input checks after the wait.
            refreshed = build_plan(update, root)
            if refreshed is None or receipt_key(refreshed) != frozen_key:
                raise GateOutcome("tree_mismatch", "validation inputs changed while waiting for admission")
            if receipt_is_fresh(state, plan, time.time()):
                event.update(outcome="green", detail="valid receipt after admission")
                return
            # Name both bounds, so each stage's elapsed_s reads against its own allowance.
            event.update(run_budget_s=budget.seconds, stage_budget_s=budget.stage_seconds)
            active_scope = getattr(admitted, "scope", None)
            if active_scope is not None:
                event["scope"] = {"status": "supported", "unit": active_scope.unit}
                event["peak_memory_unknown_reason"] = "scope_result_unavailable"
                active_scope.execute(plan, config, deadline, event, stage_budget_s=budget.stage_seconds)
                try:
                    write_receipt(state, plan, time.time())
                except OSError as error:
                    raise GateOutcome(
                        "receipt_unwritable", "cannot persist the green receipt", incomplete=True
                    ) from error
            else:
                execute_stages(
                    plan,
                    root,
                    launcher,
                    config,
                    deadline,
                    event,
                    stage_budget_s=budget.stage_seconds,
                    admission=admitted,
                )
    except GateOutcome:
        raise
    except OSError as error:  # e.g. the admission lock or a stage's output file could not be created
        raise GateOutcome("validation_error", f"validation I/O failed: {error}", incomplete=True) from error
    finally:
        event.update(
            admission_wait_s=round(admission.waited, 2),
            coalescing_wait_s=round(head_admission.waited, 2),
            queue_depth=admission.queue_depth if admission is not head_admission else 0,
            queue_position=admission.queue_position if admission is not head_admission else 0,
            admission_wait_limit_s=admission.wait_limit,
            scope_setup_s=scope.setup_s if scope is not None else 0.0,
            queue_wait_s=max(0.0, admission.waited - (scope.setup_s if scope is not None else 0.0)),
        )


def refuse(error: GateOutcome) -> int:
    kind = "validation_incomplete" if error.incomplete else "refused"
    reason = error.reason
    print(f"PRE-PUSH GATE: push {kind} (reason: {reason})", file=sys.stderr)
    if error.failing:
        print("Failing:", file=sys.stderr)
        for node in error.failing:
            print(f"  {node}", file=sys.stderr)
    if error.incomplete:
        print(
            "\nThe push was NOT validated and is NOT green. The branch is preserved; return to the driver.\n"
            "Do not retry blindly.",
            file=sys.stderr,
        )
    print(
        json.dumps({"pre_push_gate": {"outcome": kind, "reason": reason, "failing": list(error.failing)}}),
        file=sys.stderr,
    )
    print("To intentionally bypass this gate, use: git push --no-verify", file=sys.stderr)
    print(error.detail, file=sys.stderr)
    return EXIT_INCOMPLETE if error.incomplete else EXIT_REFUSED


@contextlib.contextmanager
def catch_interruptions():
    def interrupted(signum: int, _frame: object) -> None:
        raise GateOutcome("interrupted", f"received signal {signum}", incomplete=True)

    original = {number: signal.signal(number, interrupted) for number in (signal.SIGINT, signal.SIGTERM)}
    try:
        yield
    finally:
        for number, handler in original.items():
            signal.signal(number, handler)


def scope_child(arguments: list[str]) -> int:
    """Run the unchanged stages in the verified scope, with the parent's inherited flocks."""
    channel = socket.socket(fileno=int(arguments[0]))
    unit = arguments[1]
    for value in arguments[2:]:
        os.fstat(int(value))  # Missing inherited reservations prohibit readiness and validation.
    with channel, channel.makefile("rwb", buffering=0) as stream, catch_interruptions():
        group = next(
            (line[3:] for line in Path("/proc/self/cgroup").read_text().splitlines() if line.startswith("0::")), ""
        )
        ready = scope_supported(group, unit)
        channel.sendall((json.dumps({"ready": ready, "cgroup": group}) + "\n").encode())
        if not ready:
            return EXIT_INCOMPLETE
        # EOF when the launcher dies before dispatch releases the idle scope without any check.
        text = stream.readline(16 * 1024 * 1024)
        if not text:
            return EXIT_INCOMPLETE
        packet = json.loads(text)
        event: dict[str, object] = {}
        error = None
        try:
            execute_stages(
                Plan(**packet["plan"]),
                Path(packet["root"]),
                packet["launcher"],
                packet["config"],
                packet["deadline"],
                event,
                stage_budget_s=packet["stage_budget_s"],
                persist_receipt=False,
            )
        except GateOutcome as caught:
            error = {
                "reason": caught.reason,
                "detail": caught.detail,
                "failing": caught.failing,
                "incomplete": caught.incomplete,
            }
        except OSError:
            error = {"reason": "validation_error", "detail": "scoped validation I/O failed", "incomplete": True}
        # Keep the inherited reservations until every scoped descendant has exited. If cleanup
        # cannot be verified, retain the executor for the caller's own-unit kill and driver disposition.
        settled = False
        try:
            group_path = scope_cgroup(group)
            members = {int(pid) for path in group_path.rglob("cgroup.procs") for pid in path.read_text().splitlines()}
            settled = members == {os.getpid()}
        except (OSError, ValueError):
            pass
        if not settled:
            error = {
                "reason": "scope_cleanup_unverified",
                "detail": "own scoped descendants are not settled",
                "incomplete": True,
            }
        # Read before this executor exits and systemd can garbage-collect its cgroup.
        try:
            peak = int((scope_cgroup(group) / "memory.peak").read_text())
            if peak < 0:
                raise ValueError
            event.update(peak_memory_bytes=peak, peak_memory_unknown_reason=None)
            if peak > SCOPE_MEMORY_MAX:
                error = {
                    "reason": "resource_bound_exceeded",
                    "detail": "scope peak exceeded its approved memory limit",
                    "incomplete": True,
                }
        except (OSError, ValueError):
            event.update(peak_memory_bytes=None, peak_memory_unknown_reason="cgroup_peak_unavailable")
        with contextlib.suppress(BrokenPipeError):
            channel.sendall((json.dumps({"event": event, "error": error, "settled": settled}) + "\n").encode())
        if not settled:
            while True:
                signal.pause()  # Retain the existing reservation, never promote an orphaned owner.
        return 0 if error is None else EXIT_INCOMPLETE


def attempt_fingerprints(root: Path, launcher: str, config: str, text: str) -> dict[str, str | None]:
    inputs = {
        "source": Path(__file__),
        "registry": root / REGISTRY_FILE,
        "selector": root / "scripts/ci/pre_push_shadow.py",
        "launcher": Path(launcher),
        "config": Path(config),
    }
    result: dict[str, str | None] = {"input": hashlib.sha256(text.encode()).hexdigest()}
    for name, path in inputs.items():
        try:
            result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            result[name] = None
    return result


def main(argv: list[str] | None = None, stdin: str | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] + "\nInvoked by the tracked pre-push hook, with Git ref updates on stdin.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  pre_push_gate.py --launcher scripts/pre_commit/project_python.sh "
        "--config .pre-commit-config.yaml < ref-updates.txt\n"
        "Outputs: private gate receipts and measurements; refusal diagnostics on stderr.\n"
        "Exit codes: 0 green; 1 refused; 75 validation incomplete.\n"
        "Related: docs/runbooks/pre-push-gate.md.",
    )
    parser.add_argument("--launcher", required=True, help="project_python.sh path")
    parser.add_argument("--config", required=True, help=".pre-commit-config.yaml path")
    parser.add_argument("remote", nargs="*", help="Git-supplied remote arguments; default: none")
    arguments = parser.parse_args(argv)

    started = time.monotonic()
    root_text = git_ok("rev-parse", "--show-toplevel", cwd=Path.cwd())
    if root_text is None:
        return refuse(GateOutcome("tree_mismatch", "cannot resolve the worktree root", incomplete=True))
    root = Path(root_text.strip())
    events: list[dict[str, object]] = []
    event_times: dict[str, list[float]] = {}
    measurement_state: Path | None = None
    status = 0
    text = sys.stdin.read() if stdin is None else stdin
    fingerprints = attempt_fingerprints(root, arguments.launcher, arguments.config, text)

    def new_event() -> dict[str, object]:
        nonlocal measurement_state
        event: dict[str, object] = {
            "gate_version": GATE_VERSION,
            "measurement_schema": MEASUREMENT_SCHEMA,
            "at": time.time(),
            "attempt_id": uuid.uuid4().hex,
            "fingerprints": fingerprints,
            "requested_test_processes": None,
            "effective_test_processes": None,
            "peak_memory_bytes": None,
            "peak_memory_unknown_reason": "no_supported_scope",
            "admission_wait_s": 0.0,
            "queue_wait_s": 0.0,
            "scope_setup_s": 0.0,
            "resources_at_admission": None,
            "begin_durable": False,
            "task_owner": ticket_identity(Update("unknown", "unknown", "unknown", ZERO_SHA))["task_owner"],
        }
        events.append(event)
        event_times[event["attempt_id"]] = [time.monotonic()]
        measurement_state = state_dir(root)
        event["begin_durable"] = record(measurement_state, {**event, "phase": "BEGIN"})
        if not event["begin_durable"]:
            raise GateOutcome(
                "measurement_unavailable", "cannot durably begin validation; evidence is unknown", incomplete=True
            )
        return event

    def mark(event: dict[str, object], error: GateOutcome) -> None:
        event.update(
            outcome="validation_incomplete" if error.incomplete else "refused",
            reason=error.reason,
            failing=list(error.failing),
            detail=error.detail,
        )

    def publish_terminal(state: Path, event: dict[str, object]) -> bool:
        event["duration_s"] = round(time.monotonic() - started, 2)
        times = event_times[event["attempt_id"]]
        elapsed = (times[1] if len(times) > 1 else time.monotonic()) - times[0]
        event["execution_s"] = max(0.0, elapsed - event.get("admission_wait_s", 0.0))
        event["phase"] = "TERMINAL"
        pytest_stage = event.get("stages", {}).get("pytest", {})
        event["effective_test_processes"] = pytest_stage.get("effective_test_processes")
        return record(state, event)

    with catch_interruptions():
        try:
            event = new_event()
            event["requested_test_processes"] = test_process_limit()
            concurrent_run_limit()
            updates = [
                u for u in parse_updates(text) if u.local_sha != ZERO_SHA and not u.remote_ref.startswith("refs/tags/")
            ]
            if len({u.local_sha for u in updates}) > 1:
                raise GateOutcome(
                    "tree_mismatch", "one push carries several different commits; push them one at a time"
                )
            budget = Budget.configured()
            for index, update in enumerate(
                updates
            ):  # equal commits can still have different outgoing ranges: validate each
                if index:
                    event = new_event()
                    event["requested_test_processes"] = test_process_limit()
                try:
                    with catch_interruptions():
                        validate(update, root, arguments.launcher, arguments.config, event, budget)
                except GateOutcome as error:
                    mark(event, error)
                    raise
                finally:
                    event_times[event["attempt_id"]].append(time.monotonic())
            if not updates:
                event.update(outcome="green", detail="no branch updates")
        except GateOutcome as error:
            mark(events[-1] if events else new_event(), error)
            status = refuse(error)
        finally:
            try:
                state = state_dir(root)
                for event in events:
                    if "outcome" in event:
                        try:
                            if not publish_terminal(state, event) and status == 0:
                                status = refuse(
                                    GateOutcome(
                                        "measurement_unavailable",
                                        "cannot durably finish validation; evidence is unknown",
                                        incomplete=True,
                                    )
                                )
                        except GateOutcome as error:
                            # A signal deferred through fsync may follow a committed terminal row.
                            # Preserve it and append the interruption, so the attempt is never a
                            # valid green benchmark sample even at this publication boundary.
                            mark(event, error)
                            event["measurement_unknown_reason"] = "interrupted_terminal_append"
                            status = refuse(error)
                            publish_terminal(state, event)
            except GateOutcome as error:
                status = refuse(error)
                for event in events:
                    mark(event, error)
                    event["measurement_unknown_reason"] = "interrupted_terminal_publication"
                    if measurement_state is not None:
                        publish_terminal(measurement_state, event)
    return status


if __name__ == "__main__":
    sys.exit(scope_child(sys.argv[2:]) if sys.argv[1:2] == ["--scope-child"] else main())
