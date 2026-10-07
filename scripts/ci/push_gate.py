"""Exact-commit, bounded dispatch push validation (#10033).

The harness-installed git wrapper intercepts push before invoking Git, so
--no-verify cannot disable this gate. This is a supported-command boundary,
not a sandbox against workers deliberately replacing PATH or the executable.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from contextlib import suppress
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

MAX_SECONDS = 600
SHADOW_SECONDS = 30
NETWORK_SECONDS = 180
REGISTRY = "scripts/ci/push_invariants.json"
REPOSITORY_ENV = {"GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX",
                  "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"}


def unavailable_shadow() -> dict:
    """Unknown coverage is explicit and never a blocking selector verdict."""
    return {"schema_version": 1, "mode": "shadow", "status": "unavailable", "closure_tests": [],
            "selected_tests": [], "unresolved_dependencies": [{"reason": "shadow_unavailable"}],
            "full_fallback": True}


class GateFailure(RuntimeError):
    """Typed refusal; local receipt retains details, public reason stays bounded."""

    def __init__(self, reason: str, receipt: dict | None = None):
        super().__init__(reason)
        self.reason = reason
        self.receipt = receipt or {}


@dataclass(frozen=True)
class Context:
    root: Path
    git: str
    python: str
    state: Path
    lock: Path
    deadline: float | None = None


def git_env(source: dict | None = None) -> dict:
    """Keep credentials/config, but never let inherited repository overrides select another tree."""
    return {key: value for key, value in (os.environ if source is None else source).items()
            if key not in REPOSITORY_ENV}


def git(ctx: Context, *args: str, timeout: float = 30) -> str:
    """Use the real executable, never recurse into the wrapper."""
    if ctx.deadline is not None:
        timeout = min(timeout, ctx.deadline - time.monotonic())
        if timeout <= 0:
            raise GateFailure("validation_incomplete")
    return subprocess.run([ctx.git, *args], cwd=ctx.root, env=git_env(), text=True, capture_output=True,
                          check=True, timeout=timeout).stdout.strip()


def real_binary(env: dict[str, str]) -> str:
    """Resolve Git behind runtime and push-gate shims; retain the runtime shim on transmission."""
    for entry in env.get("PATH", os.defpath).split(os.pathsep):
        candidate = Path(entry) / "git"
        if entry.endswith("/agent_runtime/shims") or entry.endswith("/push-gate/bin"):
            continue
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise GateFailure("validation_incomplete")


def context(root: Path, *, real_git: str | None = None, interpreter: str | None = None) -> Context:
    """Place receipts and wrapper in per-worktree admin state, lock in shared state."""
    real_git = real_git or real_binary(dict(os.environ))
    if not real_git:
        raise GateFailure("validation_incomplete")
    # Match delegate._git_common_dir's established filesystem-only dispatch
    # lookup; provisioning must not spawn another process ahead of the worker.
    dot_git = root / ".git"
    if dot_git.is_dir():
        admin = dot_git.resolve()
    else:
        raw = dot_git.read_text().strip()
        if not raw.startswith("gitdir:"):
            raise GateFailure("validation_incomplete")
        admin = (root / raw.split(":", 1)[1].strip()).resolve()
    common_file = admin / "commondir"
    common = (admin / common_file.read_text().strip()).resolve() if common_file.is_file() else admin
    python = interpreter or str(common.parent / ".venv/bin/python")
    return Context(root.resolve(), real_git, python, admin / "push-gate", common / "push-gate.lock")


def install(root: Path, env: dict[str, str], *, interpreter: str) -> dict[str, str]:
    """Freeze the validator outside owned paths and prepend its git shim to PATH."""
    ctx = context(root, real_git=real_binary(env), interpreter=interpreter)
    ctx.state.mkdir(mode=0o700, parents=True, exist_ok=True)
    config = ctx.state / "context.json"
    # Nested launches retain the original executable rather than snapshotting our shim.
    if config.exists():
        previous = json.loads(config.read_text())
        ctx = Context(ctx.root, previous["git"], interpreter, ctx.state, ctx.lock)
    snapshot = ctx.state / "validator.py"
    shutil.copyfile(__file__, snapshot)
    config.write_text(json.dumps({"root": str(ctx.root), "git": ctx.git, "python": ctx.python,
                                  "state": str(ctx.state), "lock": str(ctx.lock)}))
    bin_dir = ctx.state / "bin"
    bin_dir.mkdir(mode=0o700, exist_ok=True)
    shim = bin_dir / "git"
    shim.write_text("#!/bin/sh\nexec " + shlex.join([interpreter, str(snapshot), str(config)]) + ' "$@"\n')
    shim.chmod(0o700)
    return {**env, "PATH": str(bin_dir) + os.pathsep + env.get("PATH", os.defpath)}


def invariant_targets(root: Path, changed: list[str]) -> tuple[list[str], str]:
    """One versioned authority, deduplicating whole modules against individual IDs."""
    raw = (root / REGISTRY).read_bytes()
    registry = json.loads(raw)
    if registry["schema_version"] != 1:
        raise ValueError("unsupported invariant registry")
    modules = set(registry["modules"])
    modules.update(p for p in changed if p.startswith("tests/") and Path(p).name.startswith("test_")
                   and p.endswith(".py") and (root / p).is_file())
    nodes = {n for n in registry["node_ids"] if n.split("::", 1)[0] not in modules}
    targets = sorted(modules | nodes)
    if not targets or any(not p.startswith("tests/") or ".." in Path(p.split("::", 1)[0]).parts for p in targets):
        raise ValueError("invalid invariant registry")
    return targets, hashlib.sha256(raw).hexdigest()


def run(ctx: Context, command: list[str], deadline: float, *, env: dict | None = None,
        input_text: str | None = None) -> tuple[int, str]:
    """Kill the complete subprocess group on timeout, including nested test runners."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise GateFailure("validation_incomplete")
    with subprocess.Popen(command, cwd=ctx.root, env=env, stdin=subprocess.PIPE if input_text else None,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                          start_new_session=True) as proc:
        try:
            output, _ = proc.communicate(input_text, timeout=remaining)
        except BaseException:
            # A timeout or cancellation must not leave paid/resource-bearing children behind.
            with suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            raise
    return proc.returncode, output


def failed_nodes(root: Path, junit: Path) -> list[str]:
    """Recover assertion and collection identities from JUnit, not log guessing."""
    if not junit.is_file():
        return []
    nodes = []
    for case in ET.parse(junit).iter("testcase"):
        if case.find("failure") is not None or case.find("error") is not None:
            parts = case.get("classname", "").split(".")
            name = case.get("name", "")
            # Match the collection-error convention in ci.junit_results:
            # an empty classname can carry the dotted module path in name.
            collection_name = name.removesuffix(".py").replace(".", "/") if not case.get("classname") else name
            collection_file = "/".join(filter(None, ["/".join(parts), collection_name])).removesuffix(".py") + ".py"
            if case.find("error") is not None and (root / collection_file).is_file():
                nodes.append(collection_file)
                continue
            for index in range(len(parts), 0, -1):
                path = "/".join(parts[:index]) + ".py"
                if (root / path).is_file():
                    nodes.append("::".join([path, *parts[index:], name]))
                    break
            else:
                nodes.append(case.get("file", "/".join(parts)) + "::" + name)
    return sorted(set(nodes))


def merge_records(ctx: Context, base: str, head: str) -> list[dict]:
    """Every outgoing merge needs evidence bound to that merge, never a loose env string."""
    merges = git(ctx, "rev-list", "--first-parent", "--merges", f"{base}..{head}").splitlines()
    if not merges:
        return []
    records = json.loads((ctx.state / "merge-reasons.json").read_text())
    result = []
    for sha in merges:
        record = records[sha]
        if record["reason"] in {"driver_order", "driver_disposition"}:
            required = ("evidence",) if record["reason"] == "driver_order" else ("base", "head", "combined_tree", "evidence")
            if not all(record.get(key) for key in required):
                raise ValueError("missing driver merge evidence")
        elif record["reason"] == "conflict":
            # Fetch now and check that the cited, freshly observed main is a merge parent.
            git(ctx, "fetch", "origin", "main", timeout=60)
            main = git(ctx, "rev-parse", "FETCH_HEAD")
            parents = git(ctx, "rev-list", "--parents", "-n", "1", sha).split()[1:]
            if len(parents) != 2 or parents[1] != main or record.get("base") != main:
                raise ValueError("stale conflict evidence")
            probe = subprocess.run([ctx.git, "merge-tree", "--write-tree", parents[0], main], cwd=ctx.root,
                                   env=git_env(), capture_output=True, text=True,
                                   timeout=min(30, max(0.001, (ctx.deadline or time.monotonic() + 30) - time.monotonic())))
            if probe.returncode != 1:
                raise ValueError("merge-tree clean or unknown")
            record = {**record, "head": parents[0], "merge_tree_exit": 1}
        else:
            raise ValueError("invalid merge reason")
        result.append({**record, "merge_sha": sha})
    return result


def receipt_current(ctx: Context, receipt: dict, base: str, head: str) -> bool:
    """Only this clean outgoing commit/range and registry can consume a green receipt."""
    return (receipt.get("status") == "passed" and receipt.get("head") == head
            and receipt.get("base") == base and git(ctx, "rev-parse", "HEAD") == head
            and not git(ctx, "status", "--porcelain", "--untracked-files=all")
            and receipt.get("registry_sha256") == hashlib.sha256((ctx.root / REGISTRY).read_bytes()).hexdigest())


def validate(ctx: Context, base: str, head: str, *, budget: float = MAX_SECONDS, merge_base: str | None = None) -> dict:
    """One attempt, no retries; retain red/incomplete receipts and the local commit."""
    ctx.state.mkdir(mode=0o700, parents=True, exist_ok=True)
    receipt = {"schema_version": 1, "head": head, "base": base, "status": "validation_incomplete",
               "outgoing_base": merge_base or base, "failing_node_ids": [], "max_test_processes": 2,
               "budget_seconds": min(budget, MAX_SECONDS), "attempted_at": datetime.now(UTC).isoformat()}
    start = time.monotonic()
    admitted = False
    try:
        with ctx.lock.open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                receipt["detail"] = "admission_busy"
                raise GateFailure("validation_incomplete", receipt) from exc
            admitted = True
            receipt["admission_wait_seconds"] = time.monotonic() - start
            deadline = time.monotonic() + min(budget, MAX_SECONDS)
            ctx = replace(ctx, deadline=deadline)
            if git(ctx, "rev-parse", "HEAD") != head or git(ctx, "status", "--porcelain", "--untracked-files=all"):
                receipt["detail"] = "outgoing_tree_not_clean_head"
                raise GateFailure("validation_incomplete", receipt)
            changed = git(ctx, "diff", "--name-only", "--diff-filter=ACMRT", "-z", base, head).split("\0")
            changed = [p for p in changed if p]
            targets, digest = invariant_targets(ctx.root, changed)
            receipt.update(changed_files=changed, selected_tests=targets, registry_sha256=digest,
                           merge_records=merge_records(ctx, merge_base or base, head))
            env = git_env()
            # Ambient pytest/pre-commit skip options never weaken harness checks.
            for key in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "SKIP"):
                env.pop(key, None)
            env["PRE_COMMIT_FROM_REF"] = base
            env["PRE_COMMIT_TO_REF"] = head
            # Serial execution: at most the test runner and one nested collector.
            command = [ctx.python, "-m", "pre_commit", "run", "--hook-stage", "pre-push",
                       "--from-ref", base, "--to-ref", head]
            code, output = run(ctx, command, deadline, env=env)
            (ctx.state / "pre-push.log").write_text(output)
            receipt["pre_push_exit"] = code
            if code:
                reason = "validation_failed" if code == 1 else "validation_incomplete"
                receipt.update(status=reason, detail="pre_push_failed",
                               failing_node_ids=sorted(set(re.findall(r"(?m)^\s*FAILED (tests/.+?)(?: - |$)", output))))
                raise GateFailure(reason, receipt)
            junit = ctx.state / "pytest.xml"
            junit.unlink(missing_ok=True)
            command = [ctx.python, "-m", "pytest", *targets, "--override-ini", "addopts=-q",
                       "-n", "0", "--junitxml", str(junit)]
            code, output = run(ctx, command, deadline, env=env)
            (ctx.state / "pytest.log").write_text(output)
            receipt.update(pytest_exit=code, failing_node_ids=failed_nodes(ctx.root, junit))
            if code:
                assertion_failure = code == 1 or (code == 2 and bool(receipt["failing_node_ids"]))
                reason = "validation_failed" if assertion_failure else "validation_incomplete"
                receipt.update(status=reason, detail="pytest_failed")
                raise GateFailure(reason, receipt)
            receipt["status"] = "passed"
            if not receipt_current(ctx, receipt, base, head):
                receipt.update(status="validation_incomplete", detail="stale_receipt")
                raise GateFailure("validation_incomplete", receipt)
    except GateFailure as exc:
        receipt["status"] = exc.reason
        exc.receipt = receipt
        raise
    except (OSError, ValueError, KeyError, ET.ParseError, subprocess.SubprocessError) as exc:
        receipt.update(status="validation_incomplete", detail=type(exc).__name__)
        raise GateFailure("validation_incomplete", receipt) from exc
    finally:
        receipt["execution_seconds"] = time.monotonic() - start
        receipt.setdefault("admission_wait_seconds", receipt["execution_seconds"] if not admitted else 0)
        # Shadow failures, unresolved dependencies and timeouts never decide push eligibility.
        try:
            code, output = run(ctx, [ctx.python, "-m", "scripts.ci.push_shadow"],
                               time.monotonic() + SHADOW_SECONDS,
                               env=git_env(), input_text=json.dumps(receipt.get("changed_files", [])))
            receipt["shadow"] = json.loads(output) if code == 0 else unavailable_shadow()
        except (OSError, ValueError, subprocess.SubprocessError):
            receipt["shadow"] = unavailable_shadow()
        (ctx.state / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        with (ctx.state / "attempts.jsonl").open("a") as ledger:
            ledger.write(json.dumps(receipt) + "\n")
    return receipt


def push(ctx: Context, branch: str, *, options: tuple[str, ...] = ()) -> subprocess.CompletedProcess:
    """Validate and transmit a literal object ID; a moving branch cannot replace it."""
    head = git(ctx, "rev-parse", "HEAD")
    current = git(ctx, "branch", "--show-current")
    if branch != current or branch in {"main", "master"} or not branch:
        raise GateFailure("validation_incomplete")
    # The complete branch delta, including changes already published by a previous attempt.
    base = git(ctx, "merge-base", "origin/main", head)
    remote = git(ctx, "ls-remote", "origin", f"refs/heads/{branch}", timeout=NETWORK_SECONDS)
    outgoing_base = remote.split()[0] if remote else base
    if remote:
        git(ctx, "fetch", "origin", f"refs/heads/{branch}", timeout=NETWORK_SECONDS)
        if git(ctx, "rev-parse", "FETCH_HEAD") != outgoing_base:
            raise GateFailure("validation_incomplete")
    receipt = validate(ctx, base, head, merge_base=outgoing_base)
    if not receipt_current(ctx, receipt, base, head):
        raise GateFailure("validation_incomplete")
    # Retain the harness's existing OPSEC/main protection shim when present.
    # Pin its underlying executable to real Git, so nested shims cannot recurse.
    env = git_env()
    env["PATH"] = os.pathsep.join(p for p in env.get("PATH", os.defpath).split(os.pathsep)
                                 if not p.endswith("/push-gate/bin"))
    env["AGENT_REAL_GIT"] = ctx.git
    transport = shutil.which("git", path=env["PATH"]) or ctx.git
    options = tuple(f"--force-with-lease=refs/heads/{branch}:{outgoing_base if remote else ''}"
                    if item == "--force-with-lease" else item for item in options)
    result = subprocess.run([transport, "push", *options, "origin", f"{head}:refs/heads/{branch}"], cwd=ctx.root,
                            env=env, text=True, capture_output=True, timeout=NETWORK_SECONDS)
    if result.returncode == 0 and ("-u" in options or "--set-upstream" in options):
        git(ctx, "branch", f"--set-upstream-to=origin/{branch}", branch)
    return result


def wrapper_main(ctx: Context, argv: list[str]) -> int:
    """Support ordinary worker push forms; fail closed on ambiguous/multi-ref pushes."""
    if "push" not in argv:
        os.execv(ctx.git, [ctx.git, *argv])
    try:
        # The runtime OPSEC shim chains its pre-push hooks with a process-local
        # core.hooksPath argument. That hook config never replaces this validator.
        invocation_dir = Path.cwd()
        while len(argv) >= 3 and argv[0] in {"-c", "-C"}:
            if argv[0] == "-C":
                invocation_dir = (invocation_dir / argv[1]).resolve()
            elif not argv[1].startswith("core.hooksPath="):
                raise GateFailure("validation_incomplete")
            argv = argv[2:]
        actual_root = subprocess.run([ctx.git, "rev-parse", "--show-toplevel"], cwd=invocation_dir,
                                     env=git_env(), text=True, capture_output=True, check=True, timeout=30).stdout.strip()
        if Path(actual_root).resolve() != ctx.root:
            raise GateFailure("validation_incomplete")
        # Globals/config overrides and aliases cannot redirect an admitted push to another tree.
        if not argv or argv[0] != "push":
            raise GateFailure("validation_incomplete")
        options, positional = [], []
        for arg in argv[1:]:
            if arg in {"-u", "--set-upstream", "--no-verify", "--porcelain", "--quiet", "--force-with-lease"}:
                options.append(arg)
            elif arg.startswith("-"):
                raise GateFailure("validation_incomplete")
            else:
                positional.append(arg)
        branch = git(ctx, "branch", "--show-current")
        if positional not in (["origin", "HEAD"], ["origin", branch], ["origin"], []):
            raise GateFailure("validation_incomplete")
        result = push(ctx, branch, options=tuple(options))
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        return result.returncode
    except (GateFailure, OSError, subprocess.SubprocessError) as exc:
        receipt = exc.receipt if isinstance(exc, GateFailure) else {}
        print(json.dumps({"reason": exc.reason if isinstance(exc, GateFailure) else "validation_incomplete",
                          "failing_node_ids": receipt.get("failing_node_ids", [])}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    configuration = json.loads(Path(sys.argv[1]).read_text())
    sys.exit(wrapper_main(Context(Path(configuration["root"]), configuration["git"], configuration["python"],
                                  Path(configuration["state"]), Path(configuration["lock"])), sys.argv[2:]))
