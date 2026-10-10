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
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

GATE_VERSION = 3
REGISTRY_FILE = "tests/test_repo_wide_marker_invariant.py"
REGISTRY_NAMES = ("KNOWN_REPO_WIDE_MODULES", "KNOWN_REPO_WIDE_FUNCTIONS")
MAX_TEST_PROCESSES_ENV = "LU_PRE_PUSH_GATE_MAX_TEST_PROCESSES"
RUN_BUDGET_S = 600.0
SHADOW_BUDGET_S = 120.0
CLEANUP_BUDGET_S = 10.0  # after a kill: reaping and the sweep for leftover descendants
ADMISSION_WAIT_S = RUN_BUDGET_S + SHADOW_BUDGET_S + 2 * CLEANUP_BUDGET_S
# Each predecessor gets one complete gate allowance. The 7,400 second ceiling covers a burst of
# ten predecessors, while bounding overload or a stuck holder. Environment overrides only shorten it.
ADMISSION_MAX_WAIT_S = 10 * ADMISSION_WAIT_S
MAX_QUEUE_ENTRIES = 256  # cap live tickets after reaping abandoned entries
RUN_TOKEN_ENV = "LU_PRE_PUSH_GATE_RUN_TOKEN"
RECEIPT_TTL_S = 3600.0
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


def record(state: Path, event: dict[str, object]) -> None:
    """Append one measurement row (AC-05); a write failure never changes the verdict."""
    try:
        state.mkdir(parents=True, exist_ok=True)
        with (state / "measurements.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")
    except OSError:
        pass


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


class Admission:
    """One gate per repository, ordered by live local tickets across all worktrees.

    A ticket's flock is its liveness proof, including after a crash; no PID inference. Publication
    uses rename after locking, so observers cannot mistake a registering caller for a dead one.
    The allowance grows with the most predecessors observed, never shrinks as they finish, and
    never exceeds ``ADMISSION_MAX_WAIT_S``. Older gates without tickets still hold admission.lock.
    """

    def __init__(self, state: Path, wait_s: float):
        self.state = state
        self.wait_s = wait_s
        self.waited = 0.0
        self.queue_depth = 0
        self.queue_position = 0
        self.wait_limit = 0.0
        self._fd: int | None = None
        self._ticket_fd: int | None = None
        self._ticket: Path | None = None

    def _register(self) -> None:
        queue = self.state / "queue"
        queue.mkdir(parents=True, exist_ok=True)
        pending = queue / f".{uuid.uuid4().hex}.pending"
        self._ticket = pending
        self._ticket_fd = os.open(pending, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
        fcntl.flock(self._ticket_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ticket = queue / f"{time.monotonic_ns():020d}-{uuid.uuid4().hex}.ticket"
        pending.rename(ticket)
        self._ticket = ticket

    def _live_tickets(self) -> list[Path]:
        assert self._ticket is not None
        live = []
        for ticket in sorted(self._ticket.parent.glob("*.ticket")):
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
        started = time.monotonic()
        last_report: tuple[int, int] | None = None
        reported_at = started
        try:
            self.state.mkdir(parents=True, exist_ok=True)
            self._fd = os.open(self.state / "admission.lock", os.O_CREAT | os.O_RDWR, 0o600)
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
                    try:
                        fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:  # includes an older gate with no ticket
                        position, depth = 2, depth + 1
                    else:
                        self.queue_depth = max(self.queue_depth, depth)
                        self.queue_position = self.queue_position or 1
                        return self
                self.queue_depth = max(self.queue_depth, depth)
                self.queue_position = self.queue_position or position
                self.wait_limit = max(self.wait_limit, min(ADMISSION_MAX_WAIT_S, max(1, position - 1) * self.wait_s))
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
        if self._ticket is not None:
            with contextlib.suppress(OSError):
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


def run_bounded(command: list[str], *, cwd: Path, deadline: float, label: str) -> tuple[int, str]:
    """Run in its own process group; on budget exhaustion kill the group and report incomplete.

    Output goes to a file, never a pipe, so a descendant that outlives the command cannot block the
    gate on a pipe it still holds.  Every exit path then kills the run's leftover descendants.
    """
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise GateOutcome(
            "validation_incomplete", f"{label}: time budget exhausted before start (timeout)", incomplete=True
        )
    token = uuid.uuid4().hex
    environment = {**clean_environment(), RUN_TOKEN_ENV: token}
    with tempfile.TemporaryFile() as sink:
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
        finally:
            sweep_descendants(token, time.monotonic() + CLEANUP_BUDGET_S)
        if timed_out:
            try:
                process.wait(timeout=CLEANUP_BUDGET_S)
            except subprocess.TimeoutExpired:
                raise GateOutcome(
                    "validation_incomplete", f"{label}: could not reap the timed-out process", incomplete=True
                ) from None
            raise GateOutcome("validation_incomplete", f"{label}: exceeded the time budget (timeout)", incomplete=True)
        sink.seek(0)
        return process.returncode, sink.read().decode("utf-8", errors="replace")


def failing_node_ids(output: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(FAILURE_RE.findall(output)))


def run_pre_commit_stage(plan: Plan, root: Path, launcher: str, config: str, deadline: float) -> None:
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
    )
    if code != 0:
        hooks = tuple(dict.fromkeys(name.strip() for name in PRE_COMMIT_FAILED_RE.findall(output)))
        raise GateOutcome("pre_commit_failed", tail(output), failing=hooks)


def test_process_limit() -> int:
    """Read the configured process ceiling; invalid configuration refuses validation."""
    value = os.environ.get(MAX_TEST_PROCESSES_ENV, "1")
    try:
        if re.fullmatch(r"[0-9]+", value) is None or int(value) < 1:
            raise ValueError
        return int(value)
    except ValueError:
        raise GateOutcome(
            "invalid_configuration", f"{MAX_TEST_PROCESSES_ENV} must be a positive integer", incomplete=True
        ) from None


def parallel_options() -> list[str]:
    """Use configured parallelism when available; keep whole files together."""
    limit = test_process_limit()
    if limit == 1 or importlib.util.find_spec("xdist") is None:
        return []
    return ["-n", str(limit), "--dist", "loadfile"]


def run_pytest_stage(plan: Plan, root: Path, launcher: str, deadline: float) -> str:
    # Admission serializes these directories. A killed gate leaves no live owner, so the next
    # admitted stage can reap its base without touching another pytest session's shared temp.
    state = state_dir(root)
    state.mkdir(parents=True, exist_ok=True)
    for stale in state.glob("pytest-*"):
        reap_stale_node(stale)
    if not plan.node_ids:
        return "no tests selected"
    with tempfile.TemporaryDirectory(prefix="pytest-", dir=state) as base_temp:
        code, output = run_bounded(
            [
                "bash",
                launcher,
                "-m",
                "pytest",
                *plan.node_ids,
                "-rfE",
                "-q",
                "--tb=short",
                "-p",
                "no:cacheprovider",
                "--basetemp",
                base_temp,
                *parallel_options(),
            ],
            cwd=root,
            deadline=deadline,
            label="pytest stage",
        )
    failing = failing_node_ids(output)
    if code == 0:
        match = SUMMARY_RE.findall(output)
        return match[-1].strip("= ") if match else "pytest passed"
    if code == 1 or failing:
        raise GateOutcome("tests_failed", tail(output), failing=failing)
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
    """Shared push execution budget, starting at admission and excluding later admission waits."""

    def __init__(self, seconds: float):
        self.seconds = seconds
        self._deadline: float | None = None

    @property
    def deadline(self) -> float:
        if self._deadline is None:
            self._deadline = time.monotonic() + self.seconds
        return self._deadline

    def after_admission(self, waited: float) -> float:
        if self._deadline is not None:
            self._deadline += waited
        return self.deadline


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
    if receipt_is_fresh(state, plan, time.time()):
        event["outcome"] = "green"
        event["detail"] = "valid receipt"
        return
    admission = Admission(state, bounded("LU_PRE_PUSH_GATE_ADMISSION_WAIT_S", ADMISSION_WAIT_S))
    try:
        with admission as admitted:
            deadline = (budget or Budget(bounded("LU_PRE_PUSH_GATE_RUN_BUDGET_S", RUN_BUDGET_S))).after_admission(
                admitted.waited
            )
            # A matching gate may have finished while this caller was queued. Rebuild the plan
            # first to preserve the dirty-tree/untracked-input checks after the wait.
            if build_plan(update, root) != plan:
                raise GateOutcome("tree_mismatch", "validation inputs changed while waiting for admission")
            if receipt_is_fresh(state, plan, time.time()):
                event.update(outcome="green", detail="valid receipt after admission")
                return
            shadow: Shadow | None = None
            settled = False
            try:
                shadow = Shadow(plan, root, launcher)
                run_pre_commit_stage(plan, root, launcher, config, deadline)
                event["pytest"] = run_pytest_stage(plan, root, launcher, deadline)
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
    except GateOutcome:
        raise
    except OSError as error:  # e.g. the admission lock or a stage's output file could not be created
        raise GateOutcome("validation_error", f"validation I/O failed: {error}", incomplete=True) from error
    finally:
        event.update(
            admission_wait_s=round(admission.waited, 2),
            queue_depth=admission.queue_depth,
            queue_position=admission.queue_position,
            admission_wait_limit_s=admission.wait_limit,
        )


def refuse(error: GateOutcome) -> int:
    kind = "validation_incomplete" if error.incomplete else "refused"
    reason = error.reason
    print(f"PRE-PUSH GATE: push {kind} (reason: {reason})", file=sys.stderr)
    if error.failing:
        print("Failing:", file=sys.stderr)
        for node in error.failing:
            print(f"  {node}", file=sys.stderr)
    print(error.detail, file=sys.stderr)
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
    return EXIT_INCOMPLETE if error.incomplete else EXIT_REFUSED


def main(argv: list[str] | None = None, stdin: str | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--launcher", required=True, help="project_python.sh path")
    parser.add_argument("--config", required=True, help=".pre-commit-config.yaml path")
    parser.add_argument("remote", nargs="*")
    arguments = parser.parse_args(argv)

    started = time.monotonic()
    root_text = git_ok("rev-parse", "--show-toplevel", cwd=Path.cwd())
    if root_text is None:
        return refuse(GateOutcome("tree_mismatch", "cannot resolve the worktree root", incomplete=True))
    root = Path(root_text.strip())
    events: list[dict[str, object]] = []
    status = 0

    def new_event() -> dict[str, object]:
        event: dict[str, object] = {"gate_version": GATE_VERSION, "at": time.time()}
        events.append(event)
        return event

    def mark(event: dict[str, object], error: GateOutcome) -> None:
        event.update(
            outcome="validation_incomplete" if error.incomplete else "refused",
            reason=error.reason,
            failing=list(error.failing),
        )

    try:
        test_process_limit()  # refuse invalid configuration even when a receipt would skip testing
        updates = [
            u
            for u in parse_updates(sys.stdin.read() if stdin is None else stdin)
            if u.local_sha != ZERO_SHA and not u.remote_ref.startswith("refs/tags/")
        ]
        if len({u.local_sha for u in updates}) > 1:
            raise GateOutcome("tree_mismatch", "one push carries several different commits; push them one at a time")
        budget = Budget(bounded("LU_PRE_PUSH_GATE_RUN_BUDGET_S", RUN_BUDGET_S))
        for update in updates:  # equal commits can still have different outgoing ranges: validate each
            event = new_event()
            try:
                validate(update, root, arguments.launcher, arguments.config, event, budget)
            except GateOutcome as error:
                mark(event, error)
                raise
    except GateOutcome as error:
        if not events:
            mark(new_event(), error)
        status = refuse(error)
    finally:
        with contextlib.suppress(GateOutcome):
            state = state_dir(root)
            for event in events:
                if "outcome" in event:
                    event["duration_s"] = round(time.monotonic() - started, 2)
                    record(state, event)
    return status


if __name__ == "__main__":
    sys.exit(main())
