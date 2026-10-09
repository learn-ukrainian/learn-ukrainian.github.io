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
import fcntl
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

GATE_VERSION = 1
REGISTRY_FILE = "tests/test_repo_wide_marker_invariant.py"
REGISTRY_NAMES = ("KNOWN_REPO_WIDE_MODULES", "KNOWN_REPO_WIDE_FUNCTIONS")
MAX_TEST_PROCESSES = 2  # the gate runs one pytest process; this is the ceiling, not a target
ADMISSION_WAIT_S = 300.0
RUN_BUDGET_S = 600.0
SHADOW_BUDGET_S = 120.0
RECEIPT_TTL_S = 3600.0
ZERO_SHA = "0" * 40
EXIT_REFUSED = 1
EXIT_INCOMPLETE = 75  # EX_TEMPFAIL: the push was not validated, not judged bad
FAILURE_RE = re.compile(r"^(?:FAILED|ERROR) (\S+?)(?: - .*)?$", re.MULTILINE)
SUMMARY_RE = re.compile(r"^=+ .*\bin \d+(?:\.\d+)?s.*=+$|^\d+ \w+.* in \d+(?:\.\d+)?s", re.MULTILINE)
PRE_COMMIT_FAILED_RE = re.compile(r"^(.+?)\.{3,}.*Failed$", re.MULTILINE)
TEST_FILE_RE = re.compile(r"^tests/(?:.+/)?test_[^/]+\.py$")


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
    missing_registry_entries: tuple[str, ...] = ()
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
    base = outgoing_base(update, root)
    if base == head:
        return None
    names = git_ok("diff", "--name-only", "--diff-filter=ACMR", f"{base}..{head}", cwd=root)
    if names is None:
        raise GateOutcome("range_unresolved", f"cannot list changed paths for {base[:12]}..{head[:12]}")
    changed = tuple(sorted(path for path in names.splitlines() if path))
    changed_tests = tuple(path for path in changed if TEST_FILE_RE.match(path) and (root / path).is_file())
    registry, version = load_registry(root)
    present = tuple(node for node in registry if (root / node.split("::", 1)[0]).is_file())
    missing = tuple(node for node in registry if node not in present)
    tree = (git_ok("rev-parse", f"{head}^{{tree}}", cwd=root) or "").strip()
    return Plan(head, tree, base, version, present, changed_tests, changed, missing)


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
        "node_ids": list(plan.node_ids),
    }


def receipt_path(state: Path, plan: Plan) -> Path:
    return state / "receipts" / f"{plan.head}.json"


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


class Admission:
    """One admitted gate at a time per repository, across every worktree."""

    def __init__(self, state: Path, wait_s: float):
        self.state = state
        self.wait_s = wait_s
        self.waited = 0.0
        self._fd: int | None = None

    def __enter__(self) -> Admission:
        self.state.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.state / "admission.lock", os.O_CREAT | os.O_RDWR, 0o644)
        started = time.monotonic()
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                self.waited = time.monotonic() - started
                if self.waited >= self.wait_s:
                    os.close(fd)
                    raise GateOutcome(
                        "validation_incomplete",
                        f"another pre-push gate held the admission lock for {self.wait_s:.0f}s (admission_timeout)",
                        incomplete=True,
                    ) from None
                time.sleep(0.2)
        self.waited = time.monotonic() - started
        self._fd = fd
        return self

    def __exit__(self, *exc: object) -> None:
        if self._fd is not None:
            os.close(self._fd)  # closing the descriptor releases the flock
            self._fd = None


def run_bounded(command: list[str], *, cwd: Path, deadline: float, label: str) -> tuple[int, str]:
    """Run in its own process group; on budget exhaustion kill the group and report incomplete."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise GateOutcome(
            "validation_incomplete", f"{label}: time budget exhausted before start (timeout)", incomplete=True
        )
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=clean_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
    except OSError as exc:
        raise GateOutcome("validation_incomplete", f"{label}: cannot start ({exc})", incomplete=True) from exc
    try:
        output, _ = process.communicate(timeout=remaining)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise GateOutcome(
            "validation_incomplete", f"{label}: exceeded the time budget (timeout)", incomplete=True
        ) from None
    return process.returncode, output or ""


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


def run_pytest_stage(plan: Plan, root: Path, launcher: str, deadline: float) -> str:
    if not plan.node_ids:
        return "no tests selected"
    code, output = run_bounded(
        ["bash", launcher, "-m", "pytest", *plan.node_ids, "-rfE", "-q", "--tb=short", "-p", "no:cacheprovider"],
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
        try:
            self.process: subprocess.Popen[str] | None = subprocess.Popen(
                ["bash", launcher, "-m", "scripts.ci.pre_push_shadow", "--paths", *plan.changed_paths],
                cwd=root,
                env=clean_environment(),
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
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait()
                return {"status": "unavailable", "detail": "shadow time budget exhausted"}
            if self.process.returncode != 0:
                return {"status": "unavailable", "detail": f"exit {self.process.returncode}"}
            self.output.seek(0)
            try:
                selection = json.loads(self.output.read().strip().splitlines()[-1])
            except (ValueError, IndexError):
                return {"status": "unavailable", "detail": "unparseable output"}
            selected = sorted(selection.get("selected_tests", ()))
            return {
                "status": "recorded",
                "selected_count": len(selected),
                "components": selection.get("components", []),
                "fallback_reasons": selection.get("fallback_reasons", []),
                "selected_digest": hashlib.sha256("\n".join(selected).encode()).hexdigest()[:16],
            }
        finally:
            self.output.close()

    def abandon(self) -> None:
        if self.process is not None and self.process.poll() is None:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait()
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


def validate(update: Update, root: Path, launcher: str, config: str, event: dict[str, object]) -> None:
    now = time.time()
    plan = build_plan(update, root)
    event["local_ref"] = update.local_ref
    if plan is None:
        event["outcome"] = "green"
        event["detail"] = "no outgoing commits"
        return
    event.update(
        head=plan.head,
        base=plan.base,
        nodes=len(plan.node_ids),
        registry_version=plan.registry_version,
        missing_registry_entries=list(plan.missing_registry_entries),
    )
    state = state_dir(root)
    if receipt_is_fresh(state, plan, now):
        event["outcome"] = "green"
        event["detail"] = "valid receipt"
        return
    with Admission(state, bounded("LU_PRE_PUSH_GATE_ADMISSION_WAIT_S", ADMISSION_WAIT_S)) as admitted:
        event["admission_wait_s"] = round(admitted.waited, 2)
        deadline = time.monotonic() + bounded("LU_PRE_PUSH_GATE_RUN_BUDGET_S", RUN_BUDGET_S)
        shadow = Shadow(plan, root, launcher)
        try:
            run_pre_commit_stage(plan, root, launcher, config, deadline)
            event["pytest"] = run_pytest_stage(plan, root, launcher, deadline)
        except GateOutcome:
            shadow.abandon()
            raise
        write_receipt(state, plan, time.time())
        event["outcome"] = "green"
        event["shadow"] = shadow.finish()


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
    event: dict[str, object] = {"gate_version": GATE_VERSION, "at": time.time()}
    status = 0
    try:
        updates = [
            u
            for u in parse_updates(sys.stdin.read() if stdin is None else stdin)
            if u.local_sha != ZERO_SHA and not u.remote_ref.startswith("refs/tags/")
        ]
        if len({u.local_sha for u in updates}) > 1:
            raise GateOutcome("tree_mismatch", "one push carries several different commits; push them one at a time")
        for update in updates[:1]:
            validate(update, root, arguments.launcher, arguments.config, event)
    except GateOutcome as error:
        event.update(
            outcome="validation_incomplete" if error.incomplete else "refused",
            reason=error.reason,
            failing=list(error.failing),
        )
        status = refuse(error)
    finally:
        event["duration_s"] = round(time.monotonic() - started, 2)
        if "outcome" in event:
            with contextlib.suppress(GateOutcome):
                record(state_dir(root), event)
    return status


if __name__ == "__main__":
    sys.exit(main())
