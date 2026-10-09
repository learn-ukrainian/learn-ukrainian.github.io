#!/usr/bin/env python3
"""Compare guard decisions and judged argv/cwd with real Bash (#9484/#9480).

Run with the project interpreter. Fake git/gh utilities only record; no GitHub
operation or branch mutation is performed. Corpus rows come from the approved
issues; accepted residuals are reported separately. Non-zero fails the CI gate.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from contextlib import nullcontext, redirect_stderr, redirect_stdout
from pathlib import Path
from typing import NamedTuple
from unittest.mock import patch
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "agents_extensions/shared/hooks"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HOOKS))
from shell_bash import PINS, ShellParseError, invoked_start, read_commands


def load_hook(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HOOKS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def guarded(argv, kind):
    start, _ = invoked_start(argv)
    args = argv[start:]
    if kind in {"merge", "admin"}:
        admin = False
        for arg in args[3:]:
            if arg in {"--admin", "--admin=true"}:
                admin = True
            elif arg == "--admin=false":
                admin = False
        return args[:3] == ["gh", "pr", "merge"] and (kind != "admin" or admin)
    return args[:3] == ["gh", "pr", "checkout"] or (
        len(args) > 1 and args[0] == "git" and any(word in args for word in ("checkout", "switch", "branch"))
    )


def target_identity(pr, repo=None):
    """Normalize a lookup's identity, independently of the hook argv parser.

    The caller supplies lookup arguments, never gold row metadata. URL selectors
    identify their host/base repository; ordinary selectors use the explicit
    repository, inherited GH_REPO, or the synthetic cwd-discovery default.
    """
    if str(pr).startswith("https://"):
        url = urlparse(str(pr))
        parts = url.path.strip("/").split("/")
        if len(parts) == 4 and parts[2] == "pull":
            url_repository = f"{url.netloc}/{parts[0]}/{parts[1]}"
            explicit = repo
            if explicit and explicit.count("/") == 1:
                explicit = "github.com/" + explicit
            # Conflicting selection must be refused by the hook, rather than
            # accidentally receiving red CI for the URL's unrelated repository.
            return {"repository": explicit or url_repository, "pr": parts[3]}
    repository = repo or os.environ.get("GH_REPO") or "fixture/default"
    if repository.count("/") == 1:
        repository = "github.com/" + repository
    return {"repository": repository, "pr": str(pr)}


def run_oracle(rows=None, traffic=None):
    """Return privacy-safe aggregate results and failing corpus IDs."""
    rows = (
        rows if rows is not None else json.loads((ROOT / "tests/fixtures/guard_bash_oracle.json").read_text())["rows"]
    )
    rows = resolve_active_rows(rows)
    traffic = (
        traffic if traffic is not None else json.loads((ROOT / "tests/fixtures/guard_bash_traffic.json").read_text())
    )
    merge, admin, branch = [load_hook("guard-" + name) for name in ("pr-merge", "admin-merge", "branch-switch-in-main")]
    counts = Counter()
    families = {}
    failures = []
    overblock_ids = []
    observations = []
    with tempfile.TemporaryDirectory(prefix="guard-bash-oracle-") as temporary:
        base = Path(temporary)
        primary = base / "primary"
        worktree = primary / ".worktrees" / "wt"
        worktree.mkdir(parents=True)
        (primary / "wt").symlink_to(worktree, target_is_directory=True)
        (primary / "a" / "b").mkdir(parents=True)
        (primary / "primary").symlink_to(primary, target_is_directory=True)
        (primary / "link").symlink_to(worktree, target_is_directory=True)
        (primary / "file").write_text("git checkout\ngh pr merge\nx\n")
        (primary / "script").write_text("gh pr merge 5\n")
        binaries = base / "bin"
        binaries.mkdir()
        # `source script` searches PATH before the current directory; do not
        # accidentally source the host's unrelated `script` executable.
        (binaries / "script").write_text("gh pr merge 5\n")
        records = base / "records"
        records.mkdir()
        # Keep recording utilities visible when the approved env -i row
        # clears PATH; only instrumentation visibility is restored.
        environment = binaries / "env"
        environment.write_text(
            '#!/bin/bash\nif [[ "$1" == -i ]]; then shift; exec /usr/bin/env -i '
            + shlex.quote("PATH=" + str(binaries) + ":/usr/bin:/bin")
            + ' "$@"; fi\n'
            # Canonical attached -S form also works on hosts whose env only
            # splits attached option values. The real utility performs splitting.
            + 'if [[ "$1" == -S || "$1" == --split-string ]]; then\n'
            + '  payload="$2"; shift 2; exec /usr/bin/env "-S$payload" "$@"; fi\n'
            + 'if [[ "$1" == --split-string=* ]]; then\n'
            + '  payload="${1#*=}"; shift; exec /usr/bin/env "-S$payload" "$@"; fi\n'
            + 'exec /usr/bin/env "$@"\n'
        )
        environment.chmod(0o755)
        for utility in ("git", "gh", "sudo", "jq", "cat", "touch"):
            recorder = binaries / utility
            recorder.write_text(
                "#!/bin/bash\n"
                "name=${0##*/}\n"
                'if [[ "$name" == sudo ]]; then\n'
                '  while [[ "$1" == -* ]]; do\n'
                '    case "$1" in -D|--chdir) cd "$2" || exit; shift 2;;\n'
                "      -u|-g|-p|--user|--group|--prompt) shift 2;;\n"
                "      --) shift; break;; *) shift;; esac\n"
                '  done; exec "$@"; fi\n'
                'if [[ "$name" == jq ]]; then /bin/cat "${@: -1}"; exit; fi\n'
                'if [[ "$name" == git ]]; then\n'
                '  while [[ "$1" == -C* ]]; do\n'
                '    if [[ "$1" == -C ]]; then cd -P "$2" || exit; shift 2;\n'
                '    else cd -P "${1:2}" || exit; shift; fi\n'
                "  done\n"
                '  if [[ "$1" == rev-parse ]]; then printf "%s\\n" "$PWD"; exit; fi\n'
                "fi\n"
                'printf "%s\\0" "$(pwd -P)" "$name" "$@" > ' + shlex.quote(str(records)) + "/$$-$RANDOM\n"
            )
            recorder.chmod(0o755)
        env = {
            **os.environ,
            "PATH": str(binaries) + os.pathsep + os.environ["PATH"],
            "ORACLE_RECORDS": str(records),
            "P": str(primary),
            "x": "gh pr merge 5",
            "GH_REPO": "fixture/default",
            "HOME": str(primary),
            "TERM": "xterm",
            "ORACLE_GIT": str(binaries / "git"),
            "ORACLE_GH": str(binaries / "gh"),
        }
        # Host shell options and GIT_DIR change discovery and must not change the score.
        for name in ("CDPATH", "SHELLOPTS", "BASHOPTS", "BASH_ENV", "GIT_DIR", "GIT_WORK_TREE"):
            env.pop(name, None)

        def protected(directory):
            path = Path(directory).resolve()
            return path.is_relative_to(primary) and not path.is_relative_to(worktree)

        def repository(directory):
            path = Path(directory).resolve()
            return primary if protected(directory) else worktree if path.is_relative_to(worktree) else path

        for row in rows:
            for path in records.iterdir():
                path.unlink()
            command, kind = row["command"].replace("{primary}", str(primary)), row["hook"]
            start_cwd = worktree if row.get("cwd") == "worktree" else primary
            # Await asynchronous/coprocess recorders before reading their files.
            subprocess.run(["bash", "-c", command + "\nwait"], cwd=start_cwd, env=env, capture_output=True, timeout=10)
            actual = []
            for path in records.iterdir():
                fields = path.read_bytes().decode().split("\0")[:-1]
                actual.append((fields[1:], fields[0]))
            executed = any(guarded(argv, kind) for argv, _ in actual) if kind != "argv" else bool(actual)
            # Prefix rows must actually observe their protected utility. An empty
            # recording set is missing oracle evidence, never an all([]) success.
            oracle_missing = kind == "argv" and not actual
            payload = {"cwd": str(start_cwd), "tool_input": {"command": command}}
            judged = []
            targets = []
            expected_target = row.get("expected", {}).get("target")

            def snapshot(pr, repo=None, cwd=None, seen=targets, gold=expected_target):
                identity = target_identity(pr, repo)
                seen.append({**identity, "cwd": cwd})
                red = identity == gold
                return (
                    {
                        "isDraft": False,
                        "baseRefName": "main",
                        "url": "https://" + identity["repository"] + "/pull/" + identity["pr"],
                    },
                    (["CI Gate"] if red else [], []),
                )

            def admin_checks(pr, cwd=None, repo=None, seen=targets, args_seen=judged, gold=expected_target):
                identity = target_identity(pr, repo)
                seen.append({**identity, "cwd": cwd})
                args_seen.append(([str(pr)], cwd))
                return ["CI Gate"] if identity == gold else []

            with (
                patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                redirect_stderr(io.StringIO()),
                patch.dict(os.environ, {**env, "CDPATH": ""}),
            ):
                for name in ("SHELLOPTS", "BASHOPTS", "BASH_ENV"):
                    os.environ.pop(name, None)
                if kind == "merge":
                    if expected_target:
                        with (
                            patch.object(merge, "_pr_snapshot", snapshot),
                            patch.object(merge, "_base_protected", return_value=True),
                        ):
                            blocked = merge.main() == 2
                    else:
                        with patch.object(
                            merge,
                            "_judge",
                            lambda args, cwd=None, seen=judged, **kwargs: seen.append((args, cwd)) or "oracle red PR",
                        ):
                            blocked = merge.main() == 2
                elif kind == "admin":
                    with patch.object(
                        admin,
                        "_failing_blocking_checks",
                        admin_checks
                        if expected_target
                        else lambda pr, cwd=None, repo=None, seen=judged: seen.append(([str(pr)], cwd)) or ["CI Gate"],
                    ):
                        blocked = admin.main() == 2
                elif kind == "branch":
                    with (
                        patch.object(branch, "PROTECTED_ROOTS", {primary}),
                        patch.object(branch, "_git_repo_root", repository),
                        patch.object(branch, "_in_main_worktree", lambda cwd: Path(cwd).resolve() == primary),
                        patch.object(branch, "_checked_out_branch", lambda cwd: "main"),
                    ):
                        # main() is the scored entry. The patches keep the recording
                        # git from answering repository discovery for this probe.
                        blocked = branch.main() == 2
                else:
                    try:
                        parsed = read_commands(command, cwd=str(start_cwd))
                        # #9490 policy changes are separate. Here prove actual argv survives.
                        blocked = all(
                            any(
                                inv.argv == argv and Path(inv.cwd).resolve() == Path(cwd).resolve()
                                for inv in parsed
                                if inv.cwd
                            )
                            for argv, cwd in actual
                        )
                    except ShellParseError:
                        blocked = True  # explicitly unreadable, never silently lost
            # A branch operation in a worktree is allowed by existing policy.
            if kind == "branch":
                executed = any(guarded(argv, kind) and protected(cwd) for argv, cwd in actual)
            # Required visible-operation cases must observe an operation. A
            # missing utility or invalid probe never satisfies acceptance.
            oracle_missing |= row["id"].startswith("9484-f-") and row["id"].endswith("-guarded") and not executed
            mismatch = False
            if kind == "merge" and judged:
                for argv, cwd in actual:
                    if guarded(argv, kind):
                        expected = argv[3:]
                        mismatch |= not any(
                            args == expected and Path(directory or primary).resolve() == Path(cwd).resolve()
                            for args, directory in judged
                        )
            if kind == "admin" and judged and not expected_target:
                # Targets are gold corpus metadata, not inferred by the helper
                # under test. The frozen admin corpus invokes PR 5.
                for argv, cwd in actual:
                    if guarded(argv, kind):
                        mismatch |= not any(
                            args == [row.get("oracle_pr")]
                            and Path(directory or primary).resolve() == Path(cwd).resolve()
                            for args, directory in judged
                        )
            operation_cwds = {Path(cwd).resolve() for argv, cwd in actual if guarded(argv, kind)}
            wrong_target = bool(expected_target) and any(
                {"repository": target["repository"], "pr": target["pr"]} != expected_target
                or Path(target["cwd"] or primary).resolve() not in (operation_cwds or {Path(start_cwd).resolve()})
                for target in targets
            )
            missing_target = bool(expected_target) and row["expected"]["disposition"] == "block" and not targets
            expected_disposition = row.get("expected", {}).get("disposition")
            # A safe branch invocation is still recorded by Bash. Conversely,
            # an intentional refusal can be correct without executing anything.
            unsafe_allow = (executed or expected_disposition in {"block", "refuse"}) and not blocked
            if expected_disposition == "allow":
                unsafe_allow = False
            miss = unsafe_allow or mismatch or oracle_missing or wrong_target or missing_target
            over = (
                blocked
                and kind != "argv"
                and (expected_disposition == "allow" if expected_disposition else not executed)
            )

            def relative(value):
                return str(value).replace(str(base), "<oracle>")

            observations.append(
                {
                    "id": row["id"],
                    "hook": kind,
                    "accepted": row["accepted"],
                    "executed": [{"argv": [relative(a) for a in argv], "cwd": relative(cwd)} for argv, cwd in actual],
                    "judged": [{"args": [relative(a) for a in args], "cwd": relative(cwd)} for args, cwd in judged],
                    "targets": [{**target, "cwd": relative(target["cwd"])} for target in targets],
                    "operation_executed": executed,
                    "wrong_target": wrong_target,
                    "missing_target": missing_target,
                    "blocked": blocked,
                    "miss": miss,
                    "overblock": over,
                }
            )
            if row["accepted"]:
                counts["accepted_residuals"] += 1
            else:
                counts["rows"] += 1
                counts["misses"] += int(miss)
                counts["overblocks"] += int(over)
                counts["argv_rows"] += int(kind == "argv")
                counts["observed_argv_rows"] += int(kind == "argv" and bool(actual))
                counts["executed_rows"] += int(executed)
                counts["wrong_target_judgments"] += int(wrong_target)
                counts["missing_target_judgments"] += int(missing_target)
                if "expected" in row:
                    expected_blocked = row["expected"]["disposition"] != "allow"
                    counts["expected_rows"] += 1
                    counts["expected_matches"] += int(
                        blocked == expected_blocked and not wrong_target and not missing_target
                    )
                    counts["expected_mismatches"] += int(blocked != expected_blocked or wrong_target or missing_target)
                if miss:
                    failures.append(row["id"])
            if over and not row["accepted"]:
                overblock_ids.append(row["id"])
            family = families.setdefault(row["family"], Counter())
            family["rows"] += 1
            family["executed_rows"] += int(executed)
            family["misses"] += int(miss and not row["accepted"])
            family["overblocks"] += int(over and not row["accepted"])
        traffic_blocks = 0
        for message in traffic:
            for command in (
                "git commit -m " + shlex.quote(message),
                "git commit -F - <<'EOF'\n" + message + "\nEOF",
                "gh pr create --body \"$(cat <<'EOF'\n" + message + '\nEOF\n)"',
            ):
                try:
                    invocations = read_commands(command, cwd=str(primary))
                    detected = any(
                        merge._merge_args(inv.argv) is not None
                        or admin._admin_merge_args(inv.argv) is not None
                        or branch._segment_is_dangerous(inv.argv) is not None
                        for inv in invocations
                    )
                    # Exercise the full raw gates and admission paths too.
                    # Unexpected lookups remain local: only quoted traffic is expected.
                    with (
                        redirect_stderr(io.StringIO()),
                        patch.object(branch, "_git_repo_root", lambda cwd: None),
                        patch.object(merge, "_judge", lambda *args, **kwargs: "unexpected traffic merge"),
                        patch.object(admin, "_failing_blocking_checks", lambda *args, **kwargs: ["CI Gate"]),
                    ):
                        decisions = []
                        for hook in (merge, admin, branch):
                            with patch.object(
                                sys,
                                "stdin",
                                io.StringIO(json.dumps({"cwd": str(primary), "tool_input": {"command": command}})),
                            ):
                                decisions.append(hook.main() == 2)
                    traffic_blocks += int(detected or any(decisions))
                except ShellParseError:
                    traffic_blocks += 1
        counts["traffic_rows"] = len(traffic) * 3
        counts["traffic_blocks"] = traffic_blocks
    return {
        "pins": PINS,
        "totals": dict(counts),
        "families": {key: dict(value) for key, value in sorted(families.items())},
        "failures": failures,
        "overblock_ids": overblock_ids,
        "observations": observations,
    }


# Refusals carry one of these classes. A block has no class. Allow has no class.
REASON_CLASSES = frozenset(
    {
        "UNKNOWN_EXECUTOR",
        "DYNAMIC_OPERATION",
        "DYNAMIC_COMMAND",
        "FORWARDED_ARGUMENTS",
        "ALIAS_EXECUTION",
        "VISIBLE_SOURCE",
        "EXECUTOR_OPTION",
        "INDIRECT_REFERENCE",
        "EXECUTED_REDIRECT",
        "DYNAMIC_REDIRECT",
        "UNKNOWN_CONTEXT",
        "UNKNOWN_REPOSITORY",
        "UNKNOWN_TARGET",
        "CREATION_COMPOUND",
        "UNACCOUNTED_OCCURRENCE",
        "PARSE_INCOMPLETE",
        "DECODE_FAILURE",
        "LIMIT_EXCEEDED",
        "RUNTIME_UNAVAILABLE",
    }
)
_TYPED_HOOKS = {"merge": "guard-pr-merge", "admin": "guard-admin-merge", "branch": "guard-branch-switch-in-main"}
# One stderr line. Prose, stdout, and the exit code cannot supply a reason class or a target.
_JUDGMENT_LINE = re.compile(r"(?m)^GUARD_JUDGMENT (\{.*\})\s*$")
_OVERBLOCK_BUDGET = 4
_SHELL_OPTION_NAMES = ("SHELLOPTS", "BASHOPTS", "BASH_ENV")
_GIT_ENV_NAMES = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_PREFIX",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
)
_JUDGMENT_KEYS = frozenset({"disposition", "reason_class"})


class DanglingSupersession(Exception):
    """A supersedes id is not an oracle row."""


class MultipleActiveSuccessors(Exception):
    """One row has two successors, so it has no single active expectation."""


class SupersessionCycle(Exception):
    """A supersedes chain returns to an earlier row."""


class TypedSupersededByUntyped(Exception):
    """A typed row's successor is untyped, so the typed expectation would be dropped."""


def _is_typed(row):
    return "expected" in row and row.get("hook") in _TYPED_HOOKS


class HookJudgment(NamedTuple):
    disposition: str | None
    reason_class: str | None
    exit_code: int
    consistent: bool
    source: str
    reported_targets: tuple | None


def resolve_active_rows(rows):
    """Return the single final successor of every supersession chain.

    A cycle, a supersedes id that is not a row, or two successors of one row
    fail the oracle before any hook is called.
    """
    by_id = {}
    for row in rows:
        row_id = row["id"]
        if row_id in by_id:
            raise ValueError(f"duplicate oracle row: {row_id}")
        by_id[row_id] = row
    successors = {}
    for row in rows:
        prior = row.get("supersedes")
        if not prior:
            continue
        if prior not in by_id:
            raise DanglingSupersession(f"dangling supersession: {row['id']} supersedes {prior}")
        successors.setdefault(prior, []).append(row["id"])
    for prior, follower_ids in successors.items():
        if len(follower_ids) > 1:
            joined = ", ".join(follower_ids)
            raise MultipleActiveSuccessors(f"multiple active successors: {prior} -> {joined}")

    def terminal(start):
        seen = []
        current = start
        while current in successors:
            if current in seen:
                cycle = [*seen[seen.index(current) :], current]
                raise SupersessionCycle("supersession cycle: " + " -> ".join(cycle))
            seen.append(current)
            current = successors[current][0]
        return current

    for row_id in by_id:
        terminal(row_id)
    for prior, follower_ids in successors.items():
        follower = by_id[follower_ids[0]]
        if _is_typed(by_id[prior]) and not _is_typed(follower):
            raise TypedSupersededByUntyped(f"typed row superseded by untyped row: {prior} -> {follower['id']}")
    superseded = set(successors)
    return [row for row in rows if row["id"] not in superseded]


def _json_object(text):
    """Parse one JSON object and reject duplicate keys."""

    def pairs(items):
        keys = [key for key, _value in items]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate key")
        return dict(items)

    payload = json.loads(text, object_pairs_hook=pairs)
    if not isinstance(payload, dict):
        raise ValueError("judgment payload is not an object")
    return payload


def _reported_targets(payload):
    """Targets carried on the judgment line, if the line has those keys.

    They are never lookup evidence. None means the line did not report any.
    """
    if "target" not in payload and "targets" not in payload:
        return None
    items = []
    listed = payload.get("targets")
    if isinstance(listed, list):
        items.extend(item for item in listed if isinstance(item, dict))
    single = payload.get("target")
    if isinstance(single, dict):
        items.append(single)
    return tuple(items)


def parse_hook_judgment(exit_code, stderr):
    """Read a typed judgment from main()'s exit code and stderr.

    The line is `GUARD_JUDGMENT` plus one JSON object with exactly
    `disposition` and `reason_class`. It is not a source of target evidence.
    Without the line, exit 0 is allow and exit 2 is block. That fallback
    cannot satisfy a refusal or a reason class. Any other exit, a duplicate
    line, or a malformed payload is an execution failure.
    """
    found = _JUDGMENT_LINE.findall(stderr or "")
    if len(found) != 1:
        if found:
            return HookJudgment(None, None, exit_code, False, "invalid", None)
        if exit_code == 0:
            return HookJudgment("allow", None, exit_code, True, "exit", None)
        if exit_code == 2:
            return HookJudgment("block", None, exit_code, True, "exit", None)
        return HookJudgment(None, None, exit_code, False, "invalid", None)
    try:
        payload = _json_object(found[0])
    except (json.JSONDecodeError, ValueError):
        return HookJudgment(None, None, exit_code, False, "invalid", None)
    reported = _reported_targets(payload)
    disposition = payload.get("disposition")
    reason = payload.get("reason_class")
    known = disposition in {"allow", "block", "refuse"}
    consistent = set(payload) == _JUDGMENT_KEYS and known and _reason_matches_disposition(disposition, reason)
    if disposition == "allow":
        consistent = consistent and exit_code == 0
    elif disposition in {"block", "refuse"}:
        consistent = consistent and exit_code == 2
    else:
        consistent = False
    stored_reason = reason if isinstance(reason, str) else None
    return HookJudgment(
        disposition if known else None,
        stored_reason,
        exit_code,
        consistent,
        "line",
        reported,
    )


def _reason_matches_disposition(disposition, reason):
    if disposition == "refuse":
        return reason in REASON_CLASSES
    if disposition in {"allow", "block"}:
        return reason is None
    return False


def invoke_hook_main(module, command, cwd):
    """Run the hook the way production does: JSON on stdin, then main().

    Helpers are not an entry point. Stdout and stderr stay separate so a
    judgment line on stdout cannot satisfy the contract.
    """
    payload = json.dumps({"cwd": cwd, "tool_input": {"command": command}})
    stdout, stderr = io.StringIO(), io.StringIO()
    code = 1
    with (
        patch.object(sys, "stdin", io.StringIO(payload)),
        redirect_stdout(stdout),
        redirect_stderr(stderr),
    ):
        try:
            code = module.main()
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 1
    if code is None:
        code = 0
    return int(code), stdout.getvalue(), stderr.getvalue()


def _same_directory(actual, expected):
    if not isinstance(actual, str) or actual == "":
        return False
    return Path(actual).expanduser().resolve() == Path(expected).expanduser().resolve()


def _one_target_matches(expected_target, actual_target, invocation_cwd):
    if not isinstance(actual_target, dict) or not isinstance(expected_target, dict):
        return False
    if actual_target.get("repository") != expected_target.get("repository"):
        return False
    if str(actual_target.get("pr")) != str(expected_target.get("pr")):
        return False
    gold_cwd = expected_target.get("cwd", invocation_cwd)
    return _same_directory(actual_target.get("cwd"), gold_cwd)


def _lists_match(expected_list, observed, invocation_cwd):
    if len(expected_list) != len(observed):
        return False
    remaining = list(observed)
    for gold in expected_list:
        matched = False
        for index, seen in enumerate(remaining):
            if _one_target_matches(gold, seen, invocation_cwd):
                del remaining[index]
                matched = True
                break
        if not matched:
            return False
    return not remaining


def _gh_pr_lookup(argv):
    """Return `(selector, repo)` for a recorded `gh pr view|checks` argv.

    The repo is None when the recorded command did not pass one. This parser
    reads the lookup argv only; it does not use the hook's own parser.
    """
    if not argv or argv[0] != "gh" or len(argv) < 4:
        return None
    repo = None
    positional = []
    index = 1
    valued = {"--json", "--jq", "-H", "--hostname", "--field", "-f", "--template", "-t"}
    while index < len(argv):
        arg = argv[index]
        if arg in {"-R", "--repo"}:
            if index + 1 >= len(argv):
                return None
            repo = argv[index + 1]
            index += 2
            continue
        if arg.startswith("--repo="):
            repo = arg.split("=", 1)[1]
            index += 1
            continue
        if arg.startswith("-R") and len(arg) > 2 and not arg.startswith("--"):
            repo = arg[2:]
            index += 1
            continue
        if arg in valued:
            index += 2
            continue
        if arg.startswith("--") and "=" in arg:
            index += 1
            continue
        if arg.startswith("-") and arg != "--":
            index += 1
            continue
        if arg == "--":
            positional.extend(argv[index + 1 :])
            break
        positional.append(arg)
        index += 1
    if len(positional) < 3 or positional[0] != "pr" or positional[1] not in {"view", "checks"}:
        return None
    selector = positional[2]
    if not selector or selector.startswith("-"):
        return None
    return selector, repo


def _lookup_happened(records):
    """True when a recorded gh invocation looked up a PR or repository."""
    for argv, _cwd in records:
        if not argv or argv[0] != "gh":
            continue
        if _gh_pr_lookup(argv) is not None or "api" in argv[1:]:
            return True
    return False


def _observed_targets(records):
    """Unique PR identities from recorded gh view/checks calls."""
    found = []
    seen = set()
    for argv, cwd in records:
        parsed = _gh_pr_lookup(argv)
        if parsed is None:
            continue
        selector, repo = parsed
        identity = target_identity(selector, repo)
        cwd_text = cwd or ""
        try:
            cwd_key = str(Path(cwd_text).resolve()) if cwd_text else ""
        except OSError:
            cwd_key = cwd_text
        key = (identity["repository"], str(identity["pr"]), cwd_key)
        if key in seen:
            continue
        seen.add(key)
        found.append({"repository": identity["repository"], "pr": str(identity["pr"]), "cwd": cwd_text})
    return found


def _expected_targets_match(expected, observed, lookup_happened, invocation_cwd):
    if "targets" in expected:
        expected_list = expected["targets"]
        if not isinstance(expected_list, list):
            return False
        if len(expected_list) == 0:
            return not lookup_happened
        return _lists_match(expected_list, observed, invocation_cwd)
    if "target" in expected:
        if len(observed) != 1:
            return False
        return _one_target_matches(expected["target"], observed[0], invocation_cwd)
    return True


def classify_judgment(expected, judgment, invocation_cwd, observed, lookup_happened):
    """Pass only when disposition, reason class and the observed lookup match.

    A reported target is not evidence. If it disagrees with the observed
    lookup, the row fails. Blocking a required allow is an over-block.
    Allowing a required block or refusal is an unsafe allow.
    """
    expected_disposition = expected.get("disposition")

    def dangerous():
        if expected_disposition == "allow" and judgment.exit_code != 0:
            return "over_block"
        if expected_disposition in {"block", "refuse"} and judgment.exit_code == 0:
            return "unsafe_allow"
        return None

    if judgment.reported_targets is not None and not _lists_match(judgment.reported_targets, observed, invocation_cwd):
        return dangerous() or "fail"
    if judgment.source == "exit" and (expected_disposition == "refuse" or expected.get("reason_class") is not None):
        return dangerous() or "fail"
    if not judgment.consistent or judgment.disposition is None:
        return dangerous() or "fail"
    disposition_ok = judgment.disposition == expected_disposition
    reason_ok = judgment.reason_class == expected.get("reason_class")
    target_ok = _expected_targets_match(expected, observed, lookup_happened, invocation_cwd)
    if disposition_ok and reason_ok and target_ok:
        return "pass"
    if expected_disposition == "allow" and judgment.disposition in {"block", "refuse"}:
        return "over_block"
    if expected_disposition in {"block", "refuse"} and judgment.disposition == "allow":
        return "unsafe_allow"
    return "fail"


def _stripped_git_env():
    env = os.environ.copy()
    for name in (*_SHELL_OPTION_NAMES, *_GIT_ENV_NAMES, "CDPATH"):
        env.pop(name, None)
    return env


def _real_git_binary():
    """Absolute git binary, never a PATH shim that would re-enter the recorder."""
    for candidate in ("/usr/bin/git", "/bin/git"):
        path = Path(candidate)
        if not path.is_file() or not os.access(path, os.X_OK):
            continue
        if path.read_bytes()[:2] != b"#!":
            return candidate
    return "/usr/bin/git"


def _install_lookup_recorder(base):
    """Record gh and git argv plus physical cwd. gh exits red; git is real.

    A red or green exit is not target evidence. The record is.
    """
    binaries = base / "bin"
    records = base / "records"
    binaries.mkdir(parents=True, exist_ok=True)
    records.mkdir(parents=True, exist_ok=True)
    git_bin = _real_git_binary()
    script = binaries / "lookup-record"
    record_dir = shlex.quote(str(records))
    script.write_text(
        "#!/bin/bash\n"
        "name=${0##*/}\n"
        f'printf "%s\\0" "$(pwd -P)" "$name" "$@" > {record_dir}/$$-$RANDOM || exit 1\n'
        f'if [[ "$name" == git ]]; then exec {shlex.quote(git_bin)} "$@"; fi\n'
        "echo 'gh unavailable to the oracle scorer' >&2\n"
        "exit 1\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    for name in ("git", "gh"):
        path = binaries / name
        if path.is_symlink() or path.exists():
            path.unlink()
        path.symlink_to(script)
    return binaries, records


def _clear_directory(path):
    for child in path.iterdir():
        if child.is_file() or child.is_symlink():
            child.unlink()


def _read_lookup_records(records):
    found = []
    for path in sorted(records.iterdir()):
        if not path.is_file():
            continue
        fields = path.read_bytes().decode(errors="replace").split("\0")[:-1]
        if len(fields) < 2:
            continue
        cwd, name, *args = fields
        found.append(([name, *args], cwd))
    return found


def _prepare_probe(base):
    """Synthetic primary and worktree. Git discovery is real; gh is a red stub."""
    primary = base / "primary"
    primary.mkdir()
    git_env = _stripped_git_env()

    def git(*args):
        subprocess.run(["git", *args], env=git_env, check=True, capture_output=True, timeout=30)

    git("init", "-b", "main", str(primary))
    git("-C", str(primary), "config", "user.email", "oracle@example.invalid")
    git("-C", str(primary), "config", "user.name", "oracle")
    (primary / "README").write_text("probe\n", encoding="utf-8")
    git("-C", str(primary), "add", "README")
    git("-C", str(primary), "-c", "commit.gpgsign=false", "commit", "-m", "probe")
    worktree = primary / ".worktrees" / "wt"
    git("-C", str(primary), "worktree", "add", "-b", "wt", str(worktree))
    (primary / "wt").symlink_to(worktree, target_is_directory=True)
    (primary / "a" / "b").mkdir(parents=True)
    (primary / "primary").symlink_to(primary, target_is_directory=True)
    (primary / "link").symlink_to(worktree, target_is_directory=True)
    (primary / "file").write_text("git checkout\ngh pr merge\nx\n", encoding="utf-8")
    (primary / "script").write_text("gh pr merge 5\n", encoding="utf-8")
    binaries, records = _install_lookup_recorder(base)
    return primary, worktree, binaries, records, binaries / "gh"


def _row_directory(row, primary, worktree):
    return worktree if row.get("cwd") == "worktree" else primary


def _scoring_environment(primary, binaries):
    """Only the variables the hooks need. Host shell options are not copied."""
    env = {
        "PATH": os.pathsep.join((str(binaries), "/usr/bin", "/bin")),
        "GH_REPO": "fixture/default",
        "HOME": str(primary),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    temporary = os.environ.get("TMPDIR")
    if temporary:
        env["TMPDIR"] = temporary
    return env


def _empty_counts(names, *, residual=False):
    counts = {}
    for name in names:
        bucket = {"pass": 0, "fail": 0, "over_block": 0, "unsafe_allow": 0, "failing_ids": []}
        if residual:
            bucket["accepted_residual"] = 0
        counts[name] = bucket
    return counts


def _add_verdict(bucket, verdict, row_id):
    bucket[verdict] += 1
    if verdict != "pass":
        bucket["failing_ids"].append(row_id)


def _bucket_totals(counts):
    names = ("pass", "fail", "over_block", "unsafe_allow")
    return {name: sum(bucket.get(name, 0) for bucket in counts.values()) for name in names}


def _score_typed_rows(typed, *, hooks, primary, worktree, own_probe, counts):
    scored = []
    with tempfile.TemporaryDirectory(prefix="guard-oracle-scorer-") as probe_name:
        base = Path(probe_name)
        if own_probe:
            primary, worktree, binaries, records, _gh = _prepare_probe(base)
            stub_path = os.pathsep.join((str(binaries), "/usr/bin", "/bin"))
            found = shutil.which("gh", path=stub_path)
            if found is None or Path(found).name != "gh":
                raise RuntimeError("oracle scorer refused to run: gh on PATH is not the local stub")
        else:
            binaries, records = _install_lookup_recorder(base)
            if primary is None:
                primary = Path("/oracle-probe")
                worktree = primary / "worktree"
        environment = _scoring_environment(primary, binaries)
        active_hooks = hooks
        with patch.dict(os.environ, environment, clear=True):
            if active_hooks is None:
                active_hooks = {name: load_hook(module_name) for name, module_name in _TYPED_HOOKS.items()}
            branch_module = active_hooks.get("branch") if own_probe else None
            branch_patch = (
                patch.object(branch_module, "PROTECTED_ROOTS", [primary])
                if branch_module is not None
                else nullcontext()
            )
            with branch_patch:
                for row in typed:
                    _clear_directory(records)
                    kind = row["hook"]
                    directory = _row_directory(row, primary, worktree)
                    command = row["command"].replace("{primary}", str(primary))
                    code, _stdout, stderr = invoke_hook_main(active_hooks[kind], command, str(directory))
                    judgment = parse_hook_judgment(code, stderr)
                    recorded = _read_lookup_records(records)
                    observed = _observed_targets(recorded)
                    lookup = _lookup_happened(recorded)
                    verdict = classify_judgment(row["expected"], judgment, directory, observed, lookup)
                    _add_verdict(counts[kind], verdict, row["id"])
                    scored.append(
                        {
                            "id": row["id"],
                            "hook": kind,
                            "verdict": verdict,
                            "disposition": judgment.disposition,
                            "reason_class": judgment.reason_class,
                            "observed_targets": observed,
                        }
                    )
    return scored


def _summarize_legacy(report):
    """Disposition-only verdicts from the raw oracle. Accepted rows stay residuals."""
    counts = _empty_counts((*_TYPED_HOOKS, "argv"), residual=True)
    rows_out = []
    for obs in report["observations"]:
        kind = obs["hook"]
        if kind not in counts:
            counts[kind] = _empty_counts((kind,), residual=True)[kind]
        if obs["accepted"]:
            verdict = "accepted_residual"
        elif obs["operation_executed"] and not obs["blocked"]:
            verdict = "unsafe_allow"
        elif obs["miss"] and obs["overblock"]:
            verdict = "fail"
        elif obs["overblock"]:
            verdict = "over_block"
        elif obs["miss"]:
            verdict = "fail"
        else:
            verdict = "pass"
        bucket = counts[kind]
        if verdict == "accepted_residual":
            bucket["accepted_residual"] += 1
        else:
            _add_verdict(bucket, verdict, obs["id"])
        rows_out.append(
            {
                "id": obs["id"],
                "hook": kind,
                "verdict": verdict,
                "blocked": obs["blocked"],
                "executed": obs["operation_executed"],
            }
        )
    return counts, rows_out


def score_guard_oracle(rows=None, *, hooks=None, primary=None, worktree=None):
    """Score active rows through each hook's main().

    Typed rows compare disposition, reason class and the observed lookup.
    Legacy rows compare disposition only, against real Bash and the red stub.
    A failed typed row is never rescored as legacy.
    """
    if rows is None:
        rows = json.loads((ROOT / "tests/fixtures/guard_bash_oracle.json").read_text(encoding="utf-8"))["rows"]
    active = resolve_active_rows(rows)
    typed = [row for row in active if _is_typed(row)]
    legacy = [row for row in active if not _is_typed(row)]
    injected = hooks is not None
    counts = _empty_counts(_TYPED_HOOKS)
    scored = []
    if typed:
        scored = _score_typed_rows(
            typed,
            hooks=hooks,
            primary=primary,
            worktree=worktree,
            own_probe=not injected and primary is None,
            counts=counts,
        )
    legacy_counts = _empty_counts((*_TYPED_HOOKS, "argv"), residual=True)
    legacy_rows_out = []
    if legacy:
        if injected:
            raise RuntimeError("legacy rows are scored through the real hook main(), not an injected hook")
        legacy_counts, legacy_rows_out = _summarize_legacy(run_oracle(rows=legacy, traffic=[]))
    return {
        "active_typed_rows": len(typed),
        "untyped_active_rows": len(legacy),
        "superseded_rows": len(rows) - len(active),
        "overblock_budget": _OVERBLOCK_BUDGET,
        "hooks": counts,
        "typed_totals": _bucket_totals(counts),
        "legacy_hooks": legacy_counts,
        "legacy_totals": _bucket_totals(legacy_counts),
        "rows": scored,
        "legacy_rows": legacy_rows_out,
    }


def score_status(report):
    """Fail on any unsafe allow or other failure. Over-blocks have a budget of four."""
    fails = unsafe = overs = 0
    for section in ("hooks", "legacy_hooks"):
        for bucket in report.get(section, {}).values():
            fails += bucket.get("fail", 0)
            unsafe += bucket.get("unsafe_allow", 0)
            overs += bucket.get("over_block", 0)
    return int(fails > 0 or unsafe > 0 or overs > _OVERBLOCK_BUDGET)


def main():
    if sys.argv[1:] == ["--score"]:
        report = score_guard_oracle()
        print(json.dumps(report, indent=2))
        return score_status(report)
    report = run_oracle()
    print(json.dumps(report, indent=2))
    totals = report["totals"]
    return int(
        totals["misses"] > 0
        or totals["overblocks"] > _OVERBLOCK_BUDGET
        or totals["traffic_blocks"] > 0
        or totals.get("expected_mismatches", 0) > 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
