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
import shlex
import subprocess
import sys
import tempfile
from collections import Counter
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

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
        return args[:3] == ["gh", "pr", "merge"] and (kind != "admin" or "--admin" in args)
    return args[:3] == ["gh", "pr", "checkout"] or (
        len(args) > 1 and args[0] == "git" and any(word in args for word in ("checkout", "switch", "branch"))
    )


def run_oracle(rows=None, traffic=None):
    """Return privacy-safe aggregate results and failing corpus IDs."""
    rows = (
        rows if rows is not None else json.loads((ROOT / "tests/fixtures/guard_bash_oracle.json").read_text())["rows"]
    )
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
        (primary / "file").touch()
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
                '    if [[ "$1" == -C ]]; then cd "$2" || exit; shift 2;\n'
                '    else cd "${1:2}" || exit; shift; fi\n'
                "  done\n"
                '  if [[ "$1" == rev-parse ]]; then printf "%s\\n" "$PWD"; exit; fi\n'
                "fi\n"
                'printf "%s\\0" "$PWD" "$name" "$@" > ' + shlex.quote(str(records)) + "/$$-$RANDOM\n"
            )
            recorder.chmod(0o755)
        env = {
            **os.environ,
            "PATH": str(binaries) + os.pathsep + os.environ["PATH"],
            "ORACLE_RECORDS": str(records),
            "P": str(primary),
            "x": "gh pr merge 5",
        }
        env.pop("CDPATH", None)

        def protected(directory):
            path = Path(directory).resolve()
            return path.is_relative_to(primary) and not path.is_relative_to(worktree)

        def repository(directory):
            path = Path(directory).resolve()
            return primary if protected(directory) else worktree if path.is_relative_to(worktree) else path

        for row in rows:
            for path in records.iterdir():
                path.unlink()
            command, kind = row["command"], row["hook"]
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
            with (
                patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                redirect_stderr(io.StringIO()),
                patch.dict(os.environ, {"CDPATH": ""}),
            ):
                if kind == "merge":
                    with patch.object(
                        merge, "_judge", lambda args, cwd=None, seen=judged: seen.append((args, cwd)) or "oracle red PR"
                    ):
                        blocked = merge.main() == 2
                elif kind == "admin":
                    with patch.object(
                        admin,
                        "_failing_blocking_checks",
                        lambda pr, cwd=None, seen=judged: seen.append(([str(pr)], cwd)) or ["CI Gate"],
                    ):
                        blocked = admin.main() == 2
                elif kind == "branch":
                    with (
                        patch.object(branch, "PROTECTED_ROOTS", {primary}),
                        patch.object(branch, "_git_repo_root", repository),
                        patch.object(branch, "_in_main_worktree", lambda cwd: Path(cwd).resolve() == primary),
                        patch.object(branch, "_checked_out_branch", lambda cwd: "main"),
                    ):
                        blocked = branch._command_danger_reason(command, start_cwd) is not None
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
            if kind == "admin" and judged:
                # Targets are gold corpus metadata, not inferred by the helper
                # under test. The frozen admin corpus invokes PR 5.
                for argv, cwd in actual:
                    if guarded(argv, kind):
                        mismatch |= not any(
                            args == [row.get("oracle_pr")]
                            and Path(directory or primary).resolve() == Path(cwd).resolve()
                            for args, directory in judged
                        )
            miss = (executed and not blocked) or mismatch or oracle_missing
            over = blocked and not executed and kind != "argv"

            def relative(value):
                return str(value).replace(str(base), "<oracle>")

            observations.append(
                {
                    "id": row["id"],
                    "hook": kind,
                    "accepted": row["accepted"],
                    "executed": [{"argv": [relative(a) for a in argv], "cwd": relative(cwd)} for argv, cwd in actual],
                    "judged": [{"args": [relative(a) for a in args], "cwd": relative(cwd)} for args, cwd in judged],
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


def main():
    report = run_oracle()
    print(json.dumps(report, indent=2))
    totals = report["totals"]
    return int(totals["misses"] > 0 or totals["overblocks"] > 4 or totals["traffic_blocks"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
