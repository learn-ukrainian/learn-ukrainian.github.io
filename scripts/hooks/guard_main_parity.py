#!/usr/bin/env python3
"""Held-out closed-grammar parity corpus for the Bash guard hooks (#10521).

The fixture is a synthetic corpus of Bash commands for the three guard hooks
(`guard-pr-merge`, `guard-admin-merge`, `guard-branch-switch-in-main`). Each
row carries origin/main's frozen decision. The branch must keep every main
BLOCK (AC-02), and every branch refusal of a main ALLOW is enumerated with the
ruling item that makes it a refusal (the over-refusal budget).

`generate` materializes origin/main's hook directory (plus the `scripts`
packages its merge guard imports) into managed scratch, runs every row through
main's hook and the branch's hook as a subprocess inside the synthetic probe of
`scripts/hooks/bash_oracle.py`, rewrites `main`, and reports the over-refusal
diff. `score` runs the branch hooks in-process against the frozen fixture.

The probe's primary checkout counts as protected for both versions through the
hooks' own second protected root, `~/projects/learn-ukrainian-infra-private`:
HOME is the probe primary, and that path is a symlink to the primary. The
in-process run additionally patches `PROTECTED_ROOTS`, as the oracle does.

Run with the project interpreter, e.g.:
  .venv/bin/python scripts/hooks/guard_main_parity.py generate --out tests/fixtures/guard_closed_grammar_heldout.json
  .venv/bin/python scripts/hooks/guard_main_parity.py score
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import tarfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import NamedTuple
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.hooks import bash_oracle

FIXTURE = ROOT / "tests/fixtures/guard_closed_grammar_heldout.json"
HOOK_DIR = "agents_extensions/shared/hooks"
HOOK_FILES = {
    "pr_merge": "guard-pr-merge",
    "admin_merge": "guard-admin-merge",
    "branch_switch_in_main": "guard-branch-switch-in-main",
}
# origin/main's guard-pr-merge imports scripts.publish.merge_guard (and through it
# scripts.ci / scripts.common / scripts.opsec plus their config files). Without
# them main's hook fails closed on every merge-shaped command, which is not
# main's decision.
MAIN_DEPENDENCIES = (
    "scripts/__init__.py",
    "scripts/publish",
    "scripts/ci",
    "scripts/common",
    "scripts/opsec",
    "scripts/config",
    ".github/workflows/ci.yml",
)
# The hooks' second protected root, resolved under HOME (the probe primary).
PRIVATE_ROOT_LINK = Path("projects/learn-ukrainian-infra-private")
RULING_ITEMS = frozenset({"1", "2", "3", "4", "5", "6", "7", "UNRULED"})
# Rows of these classes are never triggers (ruling item 7): the branch must allow them.
MUST_ALLOW_CLASSES = frozenset({"read_only", "data_mention"})
SHA = "0123456789abcdef0123456789abcdef01234567"
WORKERS = 8

# Ruling attribution for a branch refusal of a main ALLOW, by row class.
# None means no ruling item makes the refusal legitimate: it is UNRULED.
RULING_BY_CLASS: dict[str, tuple[str, str] | None] = {
    "plain": None,
    "read_only": None,
    "data_mention": None,
    "benign_compound": None,
    "cd_into_worktree": None,
    "not_admin": None,
    "cd_and": ("4", "a merge after any other command must name PR, --repo and --match-head-commit"),
    "seq_before": ("4", "only read-only git/gh, echo/printf/true/:/test/[/pwd may precede the guarded op"),
    "seq_after": ("2", "a command after the guarded op is outside the closed grammar"),
    "or_before": ("4", "only `&&` after an admitted command may precede the guarded op"),
    "cd_or_exit": ("4", "the one admitted cd must be `cd <literal> &&`, with no `;`/`||` after it"),
    "compound": ("3", "guarded op inside a subshell, group, if/loop/case or negation refuses"),
    "function": ("3", "a function definition in a command with a guarded op refuses"),
    "substitution": ("3", "guarded op inside a command or process substitution refuses"),
    "payload": ("3", "guarded op inside a shell/eval/env -S/trap payload refuses"),
    "background": ("2", "a background job or coprocess is outside the closed grammar (one top-level command)"),
    "wrapper": ("2", "a wrapper or dynamic executable around the guarded op is outside the grammar"),
    "indirect": ("2", "an indirect executor (xargs, interpreter, ssh) is outside the closed grammar"),
    "env_prefix": ("4", "no assignments before or on the guarded op"),
    "cdpath": ("4", "the leading cd requires CDPATH unset and no assignment"),
    "assignment_before": ("4", "no assignments or exports before the guarded op"),
    "binding": ("5", "alias/hash/enable/BASH_ALIASES/BASH_CMDS writes refuse unconditionally"),
    "posix_mode": ("5", "set -k, set -o posix, bash --posix and POSIXLY_CORRECT refuse unconditionally"),
    "computed_name": ("5", "computed-name assignments refuse unconditionally"),
    "arith_test": ("4", "arithmetic and [[ ]] are not admitted before the guarded op"),
    "pipeline": ("3", "a guarded op as a pipeline member refuses"),
    "redirect": ("2", "a redirect on the guarded op is outside the closed grammar"),
    "multiline_before": ("4", "a newline-separated command before the guarded op is not `&&`-admitted"),
    "multiline_after": ("2", "a command after the guarded op is outside the closed grammar"),
    "decoded_word": (
        "2",
        'a word whose Bash value the reader cannot prove ($"...", brace expansion, a locale- or '
        "version-dependent $'...' escape) is outside the closed grammar",
    ),
}


class Run(NamedTuple):
    """One hook invocation: exit code, typed reason class, and recorder evidence."""

    exit: int
    reason_class: str | None
    gh: bool
    git: bool
    lookup: bool

    def as_dict(self) -> dict:
        return self._asdict()


# --------------------------------------------------------------------------- corpus

_BRANCH_OP = "git checkout feature"
_MERGE_OP = "gh pr merge --squash 5"
_ADMIN_OP = "gh pr merge --admin 5"

# Context templates. {op} is the guarded op; {tool}/{rest} split it at the first
# word; {head}/{last} split it at the last word; {dir} is a literal directory.
_CONTEXTS: tuple[tuple[str, str, bool], ...] = (
    # (class, template, also run the branch op from the worktree)
    ("cd_and", "cd {dir} && {op}", True),
    ("seq_before", "echo start; {op}", True),
    ("seq_before", "git status && {op}", False),
    ("seq_after", "{op}; echo done", False),
    ("seq_after", "{op} || true", False),
    ("or_before", "true || {op}", False),
    ("cd_or_exit", "cd {dir} || exit; {op}", True),
    ("cd_or_exit", "cd {dir}; {op}", False),
    ("compound", "( {op} )", True),
    ("compound", "{ {op}; }", False),
    ("compound", "if true; then {op}; fi", True),
    ("compound", "while false; do {op}; done", False),
    ("compound", "until true; do {op}; done", False),
    ("compound", "for i in 1; do {op}; done", False),
    ("compound", "case x in x) {op};; esac", False),
    ("compound", "! {op}", False),
    ("function", "f(){ {op}; }; f", True),
    ("function", "false(){ :; }; while false; do {op}; done", False),
    ("function", "cd(){ :; }; cd wt && {op}", False),
    ("substitution", "echo $({op})", True),
    ("substitution", "echo `{op}`", False),
    ("substitution", "cat <({op})", False),
    ("payload", "bash <<'EOF'\n{op}\nEOF", False),
    ("payload", "bash -c '{op}'", True),
    ("payload", "sh -c '{op}'", False),
    ("payload", "eval '{op}'", True),
    ("payload", "env -S '{op}'", False),
    ("payload", "bash <<< '{op}'", False),
    ("payload", "trap '{op}' EXIT", False),
    ("background", "coproc {op}", False),
    ("background", "{op} &", True),
    ("wrapper", "timeout 5 {op}", True),
    ("wrapper", "nice {op}", False),
    ("wrapper", "sudo {op}", False),
    ("wrapper", "env -C {dir} {op}", False),
    ("indirect", "echo {last} | xargs {head}", False),
    ("indirect", "python3 -c \"import os; os.system('{op}')\"", False),
    ("indirect", "ssh fixture-host '{op}'", False),
    ("indirect", "make release", False),
    ("env_prefix", "BASH_ENV=x {op}", False),
    ("env_prefix", "PATH=/usr/bin {op}", False),
    ("env_prefix", "GIT_DIR={primary}/.git {op}", True),
    ("env_prefix", "GH_REPO=fixture/other {op}", False),
    ("cdpath", "CDPATH=x cd wt && {op}", False),
    ("cdpath", "CDPATH={primary} cd a/b && {op}", True),
    ("assignment_before", "export X=1 && {op}", False),
    ("assignment_before", "X=1; {op}", False),
    ("binding", "alias g={tool}; g {rest}", True),
    ("binding", "shopt -s expand_aliases; alias g={tool}; g {rest}", False),
    ("binding", "n=g; alias $n={tool}; g {rest}", False),
    ("binding", "BASH_ALIASES[g]={tool}; g {rest}", False),
    ("binding", "hash -p /usr/bin/{tool} g; g {rest}", False),
    ("binding", "enable -n cd; cd wt && {op}", False),
    ("posix_mode", "POSIXLY_CORRECT=1; {op}", False),
    ("posix_mode", "set -o posix; {op}", True),
    ("posix_mode", "bash --posix -c '{op}'", False),
    ("posix_mode", "set -k; {op}", False),
    ("computed_name", 'n=X; declare "$n=1"; {op}', False),
    ("computed_name", 'n=X; printf -v "$n" %s 1; {op}', False),
    ("computed_name", 'n=X; read "$n" <<< 1; {op}', False),
    ("arith_test", "(( 1 )) && {op}", False),
    ("arith_test", "[[ -n x ]] && {op}", False),
    ("pipeline", "echo y | {op}", True),
    ("pipeline", "{op} | cat", False),
    ("redirect", "{op} > out.txt", True),
    ("redirect", "{op} 2>&1", False),
    ("multiline_before", "echo a\n{op}", True),
    ("multiline_after", "{op}\necho b", False),
)

# The other blockable operations, each in a few contexts (plain forms are below).
_VARIANT_CONTEXTS: tuple[tuple[str, str, str, str], ...] = (
    ("branch_switch_in_main", "cd_and", "cd a/b && {op}", "git symbolic-ref HEAD refs/heads/topic"),
    ("branch_switch_in_main", "compound", "( {op} )", "git bisect start"),
    ("branch_switch_in_main", "payload", "bash -c '{op}'", "git rebase topic"),
    ("branch_switch_in_main", "seq_before", "echo start; {op}", "git branch -f topic"),
    ("branch_switch_in_main", "binding", "alias g=git; g {rest}", "git switch -c topic"),
    ("branch_switch_in_main", "function", "f(){ {op}; }; f", "git branch -D main"),
    ("branch_switch_in_main", "substitution", "echo $({op})", "gh pr checkout 5"),
    ("branch_switch_in_main", "pipeline", "echo y | {op}", "git rebase main"),
    ("pr_merge", "compound", "{ {op}; }", "python3 -m scripts.publish pr-merge --number 5"),
    ("pr_merge", "payload", "bash -c '{op}'", "python3 -m scripts.publish pr-merge --number 5"),
    ("pr_merge", "seq_before", "echo start; {op}", "python3 -m scripts.publish pr-merge --number 5"),
    ("pr_merge", "cd_and", "cd {dir} && {op}", f"gh pr merge 5 --squash --repo fixture/repo --match-head-commit {SHA}"),
    (
        "pr_merge",
        "seq_before",
        "git status && {op}",
        f"gh pr merge 5 --squash --repo fixture/repo --match-head-commit {SHA}",
    ),
    (
        "admin_merge",
        "cd_and",
        "cd {dir} && {op}",
        f"gh pr merge 5 --admin --repo fixture/repo --match-head-commit {SHA}",
    ),
    ("admin_merge", "compound", "( {op} )", "gh pr merge 5 --squash --admin"),
)

_PLAIN = {
    "branch_switch_in_main": (
        ("git checkout feature", ("primary", "worktree")),
        ("git checkout -b topic", ("primary", "worktree")),
        ("git switch topic", ("primary", "worktree")),
        ("git switch -c topic", ("primary", "worktree")),
        ("git branch -f topic", ("primary", "worktree")),
        ("git branch -D main", ("primary", "worktree")),
        ("git symbolic-ref HEAD refs/heads/topic", ("primary", "worktree")),
        ("git bisect start", ("primary", "worktree")),
        ("git rebase main", ("primary", "worktree")),
        ("gh pr checkout 5", ("primary", "worktree")),
        ("git rebase topic", ("primary",)),
        ("git bisect reset", ("primary",)),
        ("git checkout --detach", ("primary",)),
    ),
    "pr_merge": (
        ("gh pr merge 5 --squash", ("worktree", "primary")),
        ("gh pr merge 5 --auto --squash", ("worktree",)),
        (f"gh pr merge 5 --squash --repo fixture/repo --match-head-commit {SHA}", ("worktree",)),
        ("python3 -m scripts.publish pr-merge --number 5", ("worktree", "primary")),
    ),
    "admin_merge": (
        ("gh pr merge 5 --admin", ("worktree", "primary")),
        ("gh pr merge 5 --squash --admin", ("worktree",)),
        (f"gh pr merge 5 --admin --repo fixture/repo --match-head-commit {SHA}", ("worktree",)),
    ),
}

_READ_ONLY = {
    "branch_switch_in_main": (
        ("git checkout -- file", ("primary", "worktree")),
        ("git checkout HEAD -- file", ("primary",)),
        ("git checkout main", ("primary",)),
        ("git switch main", ("primary",)),
        ("git restore file", ("primary",)),
        ("git branch --list", ("primary", "worktree")),
        ("git branch -vv", ("primary",)),
        ("git branch --show-current", ("primary",)),
        ("git branch topic", ("primary",)),
        ("git branch -d topic", ("primary",)),
        ("git bisect log", ("primary",)),
        ("git rebase --show-current-patch", ("primary",)),
        ("git symbolic-ref HEAD", ("primary",)),
        ("git symbolic-ref --short HEAD", ("primary",)),
        ("git worktree add .worktrees/x -b x", ("primary",)),
        ("git worktree remove .worktrees/wt", ("primary",)),
        ("git worktree list", ("primary", "worktree")),
        ("git status", ("primary",)),
        ("git log --oneline -3", ("primary",)),
        ("gh pr view 5", ("primary",)),
    ),
    "pr_merge": (
        ("gh pr view 5", ("worktree",)),
        ("gh pr checks 5", ("worktree",)),
        ("gh pr list", ("worktree",)),
        ("gh pr diff 5", ("worktree",)),
        ("gh pr status", ("worktree",)),
        ("gh pr view 5 --json mergeStateStatus", ("worktree",)),
        ("python3 -m scripts.publish pr-merge --help", ("worktree",)),
        ("git status", ("worktree",)),
    ),
    "admin_merge": (
        ("gh pr view 5", ("worktree",)),
        ("gh pr checks 5", ("worktree",)),
    ),
}

# Merges the admin guard does not own: no admin flag, or the flag switched off.
_NOT_ADMIN = ("gh pr merge 5 --squash", "gh pr merge 5 --admin=false")

_DATA_MENTIONS = (
    'echo "run gh pr merge later"',
    'git commit -m "fix: git checkout handling"',
    "printf '%s' 'git switch x' > notes.txt",
    "echo 'gh pr merge 5 --admin' > notes.txt",
    'grep -n "git checkout" file',
    "git log --grep='git rebase'",
    "cat <<'EOF'\ngit checkout feature\ngh pr merge 5 --admin\nEOF",
    'git commit -m "docs: explain gh pr merge 5 --admin and git branch -D main"',
    "echo ok # git checkout feature",
)

_BENIGN_COMPOUNDS = (
    "( git status )",
    "{ git status; git log -1; }",
    "if git diff --quiet; then echo clean; fi",
    'for f in a b; do echo "$f"; done',
    "f(){ echo hi; }; f",
)

_PREFIX = {"pr_merge": "pm", "admin_merge": "am", "branch_switch_in_main": "bs"}
_HOOK_OP = {"pr_merge": _MERGE_OP, "admin_merge": _ADMIN_OP, "branch_switch_in_main": _BRANCH_OP}
_HOOK_CWD = {"pr_merge": "worktree", "admin_merge": "worktree", "branch_switch_in_main": "primary"}


def _directory(hook: str, cwd: str) -> str:
    """A literal cd target that lands in the primary (branch) or the worktree (merges)."""
    if hook != "branch_switch_in_main":
        return "{worktree}"
    return "a/b" if cwd == "primary" else "{primary}"


def _render(template: str, op: str, hook: str, cwd: str) -> str:
    tool, _, rest = op.partition(" ")
    head, _, last = op.rpartition(" ")
    values = {"op": op, "tool": tool, "rest": rest, "head": head, "last": last, "dir": _directory(hook, cwd)}
    return re.sub(r"\{(op|tool|rest|head|last|dir)\}", lambda match: values[match.group(1)], template)


def seed_rows() -> list[dict]:
    """The synthetic held-out corpus, in a fixed order. IDs are assigned per hook and class."""
    specs: list[tuple[str, str, str, str]] = []  # hook, cwd, class, command
    for hook, items in _PLAIN.items():
        specs.extend((hook, cwd, "plain", command) for command, cwds in items for cwd in cwds)
    for hook, items in _READ_ONLY.items():
        specs.extend((hook, cwd, "read_only", command) for command, cwds in items for cwd in cwds)
    specs.extend(("admin_merge", "worktree", "not_admin", command) for command in _NOT_ADMIN)
    for hook in HOOK_FILES:
        specs.extend((hook, _HOOK_CWD[hook], "data_mention", command) for command in _DATA_MENTIONS)
        specs.extend((hook, _HOOK_CWD[hook], "benign_compound", command) for command in _BENIGN_COMPOUNDS)
    specs.extend(
        (
            ("branch_switch_in_main", "primary", "cd_into_worktree", "cd .worktrees/wt && git checkout feature"),
            ("branch_switch_in_main", "primary", "cd_into_worktree", "cd wt && git switch -c topic"),
            ("pr_merge", "primary", "cd_into_worktree", f"cd .worktrees/wt && {_MERGE_OP}"),
        )
    )
    for row_class, template, worktree_too in _CONTEXTS:
        for hook in HOOK_FILES:
            cwds = ("primary", "worktree") if hook == "branch_switch_in_main" and worktree_too else (_HOOK_CWD[hook],)
            specs.extend((hook, cwd, row_class, _render(template, _HOOK_OP[hook], hook, cwd)) for cwd in cwds)
    for hook, row_class, template, op in _VARIANT_CONTEXTS:
        cwd = _HOOK_CWD[hook]
        specs.append((hook, cwd, row_class, _render(template, op, hook, cwd)))
    rows: list[dict] = []
    counters: Counter = Counter()
    seen: set[tuple[str, str, str]] = set()
    for hook, cwd, row_class, command in specs:
        key = (hook, cwd, command)
        if key in seen:
            continue
        seen.add(key)
        prefix = f"{_PREFIX[hook]}-{row_class.replace('_', '-')}"
        counters[prefix] += 1
        rows.append(
            {
                "id": f"{prefix}-{counters[prefix]:03d}",
                "hook": hook,
                "cwd": cwd,
                "command": command,
                "class": row_class,
            }
        )
    return rows


# --------------------------------------------------------------------------- probe


def prepare_probe(base: Path) -> tuple[Path, Path, Path, Path]:
    """The oracle's synthetic primary/worktree, plus the hooks' private protected root."""
    primary, worktree, binaries, records, _gh = bash_oracle._prepare_probe(base)
    link = primary / PRIVATE_ROOT_LINK
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(primary, target_is_directory=True)
    return primary, worktree, binaries, records


def probe_environment(primary: Path, binaries: Path) -> dict[str, str]:
    environment = bash_oracle._scoring_environment(primary, binaries)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def row_command(row: dict, primary: Path, worktree: Path) -> str:
    return row["command"].replace("{primary}", str(primary)).replace("{worktree}", str(worktree))


def row_directory(row: dict, primary: Path, worktree: Path) -> Path:
    return worktree if row["cwd"] == "worktree" else primary


def _evidence(code: int, stderr: str, records: Path) -> Run:
    judgment = bash_oracle.parse_hook_judgment(code, stderr)
    recorded = bash_oracle._read_lookup_records(records)
    names = {argv[0] for argv, _cwd in recorded if argv}
    return Run(code, judgment.reason_class, "gh" in names, "git" in names, bash_oracle._lookup_happened(recorded))


def branch_runs(rows: list[dict]) -> dict[str, Run]:
    """Run every row through the branch hooks in-process, inside one probe."""
    results: dict[str, Run] = {}
    with bash_oracle._managed_probe("guard-main-parity") as name:
        primary, worktree, binaries, records = prepare_probe(Path(name))
        with patch.dict(os.environ, probe_environment(primary, binaries), clear=True):
            hooks = {kind: bash_oracle.load_hook(module) for kind, module in HOOK_FILES.items()}
            with patch.object(hooks["branch_switch_in_main"], "PROTECTED_ROOTS", [primary]):
                for row in rows:
                    bash_oracle._clear_directory(records)
                    directory = row_directory(row, primary, worktree)
                    command = row_command(row, primary, worktree)
                    code, _stdout, stderr = bash_oracle.invoke_hook_main(hooks[row["hook"]], command, str(directory))
                    results[row["id"]] = _evidence(code, stderr, records)
    return results


# --------------------------------------------------------------------------- main's hooks


def _git(*args: str, text: bool = True) -> str | bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], check=True, capture_output=True, text=text, timeout=120
    ).stdout


def materialize_main(ref: str, destination: Path) -> str:
    """Write origin/main's hook directory and its imported packages; return the SHA."""
    sha = _git("rev-parse", "--verify", f"{ref}^{{commit}}").strip()
    hooks = destination / HOOK_DIR
    hooks.mkdir(parents=True)
    for name in _git("ls-tree", "--name-only", f"{sha}:{HOOK_DIR}").split():
        (hooks / name).write_bytes(_git("show", f"{sha}:{HOOK_DIR}/{name}", text=False))
    archive = _git("archive", "--format=tar", sha, "--", *MAIN_DEPENDENCIES, text=False)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(destination, filter="data")
    return sha


def _run_subprocess(hook_file: Path, command: str, directory: Path, environment: dict, records: Path) -> Run:
    payload = json.dumps({"cwd": str(directory), "tool_input": {"command": command}})
    bash_oracle._clear_directory(records)
    completed = subprocess.run(
        [sys.executable, str(hook_file)],
        input=payload,
        cwd=directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if "guard dependency unavailable" in completed.stderr:
        raise RuntimeError(f"{hook_file} cannot run in the probe: {completed.stderr.strip()}")
    return _evidence(completed.returncode, completed.stderr, records)


def subprocess_runs(rows: list[dict], hook_dirs: dict[str, Path], base: Path) -> dict[str, dict[str, Run]]:
    """Run every row through each version's hook as a subprocess. One recorder per worker."""
    primary, worktree, _binaries, _records = prepare_probe(base)
    workers = []
    for index in range(WORKERS):
        binaries, records = bash_oracle._install_lookup_recorder(base / f"recorder-{index}")
        workers.append((probe_environment(primary, binaries), records))

    def canary(version: str, hook: str, command: str, cwd: str, expected: int) -> None:
        environment, records = workers[0]
        row = {"cwd": cwd, "command": command}
        run = _run_subprocess(
            hook_dirs[version] / f"{HOOK_FILES[hook]}.py",
            command,
            row_directory(row, primary, worktree),
            environment,
            records,
        )
        if run.exit != expected:
            raise RuntimeError(f"{version} {hook} canary `{command}` in {cwd}: exit {run.exit}, expected {expected}")

    for version in hook_dirs:
        canary(version, "branch_switch_in_main", "git checkout feature", "primary", 2)
        canary(version, "branch_switch_in_main", "git checkout feature", "worktree", 0)
        canary(version, "pr_merge", "gh pr merge 5 --squash", "worktree", 2)
        canary(version, "pr_merge", "gh pr view 5", "worktree", 0)
        canary(version, "admin_merge", "gh pr merge 5 --admin", "worktree", 2)

    def work(index: int) -> list[tuple[str, str, Run]]:
        environment, records = workers[index]
        found = []
        for row in rows[index::WORKERS]:
            directory = row_directory(row, primary, worktree)
            command = row_command(row, primary, worktree)
            for version, hook_dir in hook_dirs.items():
                hook_file = hook_dir / f"{HOOK_FILES[row['hook']]}.py"
                found.append((version, row["id"], _run_subprocess(hook_file, command, directory, environment, records)))
        return found

    results: dict[str, dict[str, Run]] = {version: {} for version in hook_dirs}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for found in pool.map(work, range(WORKERS)):
            for version, row_id, run in found:
                results[version][row_id] = run
    return results


# --------------------------------------------------------------------------- fixture


def load_fixture(path: Path = FIXTURE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_fixture(path: Path, data: dict) -> None:
    """Header keys indented; one row per line so diffs stay reviewable."""
    lines = ["{"]
    keys = list(data)
    for index, key in enumerate(keys):
        value = data[key]
        comma = "," if index < len(keys) - 1 else ""
        if isinstance(value, list):
            lines.append(f"  {json.dumps(key)}: [")
            lines.extend(
                f"    {json.dumps(item, ensure_ascii=False)}{',' if position < len(value) - 1 else ''}"
                for position, item in enumerate(value)
            )
            lines.append(f"  ]{comma}")
        else:
            lines.append(f"  {json.dumps(key)}: {json.dumps(value, ensure_ascii=False)}{comma}")
    lines.append("}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def merge_rows(existing: list[dict], seeds: list[dict]) -> list[dict]:
    """Keep existing ids/classes; append seed rows whose (hook, cwd, command) is new."""
    rows = [{key: row[key] for key in ("id", "hook", "cwd", "command", "class")} for row in existing]
    known = {(row["hook"], row["cwd"], row["command"]) for row in rows}
    used = {row["id"] for row in rows}
    for seed in seeds:
        if (seed["hook"], seed["cwd"], seed["command"]) in known:
            continue
        prefix, number = seed["id"].rsplit("-", 1)
        candidate = int(number)
        while f"{prefix}-{candidate:03d}" in used:
            candidate += 1
        row = {**seed, "id": f"{prefix}-{candidate:03d}"}
        used.add(row["id"])
        rows.append(row)
    return rows


def over_refusal_ids(rows: list[dict], branch: dict[str, Run]) -> list[str]:
    return [row["id"] for row in rows if row["main"] == "allow" and branch[row["id"]].exit == 2]


# Blockable operations #10521 added (ruling item 7) that origin/main did not guard.
_NEW_TRIGGER = re.compile(r"\bgit (?:symbolic-ref HEAD \S|bisect (?!log\b)|rebase (?!--show-current-patch\b))")


def attribute(row: dict, run: Run) -> dict:
    """Name the ruling item that makes the branch's refusal of a main ALLOW legitimate."""

    def entry(item: str, why: str) -> dict:
        return {"id": row["id"], "ruling_item": item, "why": why}

    ruling = RULING_BY_CLASS.get(row["class"])
    # An untyped block is a policy block of a detected trigger, not a grammar refusal.
    if run.reason_class is None and _NEW_TRIGGER.search(row["command"]):
        return entry("7", "symbolic-ref HEAD, bisect and rebase are blockable triggers origin/main did not guard")
    if run.reason_class is None and row["class"] == "decoded_word":
        return entry(
            "1", "Bash decodes the word to the guarded op origin/main misread ($'...' octal wraps, NUL ends it)"
        )
    if run.reason_class is None and ruling is not None:
        return entry("1", "the guarded op is detected in the unpruned tree (through a wrapper) where main missed it")
    if ruling is None:
        return entry("UNRULED", f"no ruling item refuses a `{row['class']}` row")
    return entry(*ruling)


def summarize(rows: list[dict], branch: dict[str, Run], listed: list[dict]) -> dict:
    """Counts plus the AC-02, over-refusal and must-allow violations."""
    measured = set(over_refusal_ids(rows, branch))
    listed_ids = {entry["id"] for entry in listed}
    return {
        "rows": len(rows),
        "main_blocks": sum(row["main"] == "block" for row in rows),
        "branch_blocks": sum(branch[row["id"]].exit == 2 for row in rows),
        "ac02_violations": [row["id"] for row in rows if row["main"] == "block" and branch[row["id"]].exit != 2],
        "over_refusals": len(measured),
        "unlisted_over_refusals": sorted(measured - listed_ids),
        "listed_but_allowed": sorted(listed_ids - measured),
        "unruled": sorted(entry["id"] for entry in listed if entry["ruling_item"] == "UNRULED"),
        "must_allow_blocked": [
            row["id"] for row in rows if row["class"] in MUST_ALLOW_CLASSES and branch[row["id"]].exit != 0
        ],
    }


def generate(out: Path, ref: str, report: Path | None) -> int:
    existing = load_fixture(out) if out.exists() else {}
    rows = merge_rows(existing.get("rows", []), seed_rows())
    previous_main = {row["id"]: row.get("main") for row in existing.get("rows", [])}
    with bash_oracle._managed_probe("guard-main-parity-generate") as name:
        base = Path(name)
        sha = materialize_main(ref, base / "main-src")
        hook_dirs = {"main": base / "main-src" / HOOK_DIR, "branch": ROOT / HOOK_DIR}
        runs = subprocess_runs(rows, hook_dirs, base)
    for row in rows:
        row["main"] = "block" if runs["main"][row["id"]].exit == 2 else "allow"
        row["main_observed"] = runs["main"][row["id"]].as_dict()
    old = {entry["id"]: entry for entry in existing.get("over_refusals", [])}
    measured = over_refusal_ids(rows, runs["branch"])
    by_id = {row["id"]: row for row in rows}
    over_refusals = [old.get(row_id) or attribute(by_id[row_id], runs["branch"][row_id]) for row_id in measured]
    data = {
        "description": (
            "Held-out synthetic Bash corpus for the guard hooks (#10521). `main` is origin/main's frozen "
            "decision (block iff exit 2) measured by scripts/hooks/guard_main_parity.py in the bash_oracle "
            "probe; `{primary}`/`{worktree}` are the probe's synthetic checkouts. `over_refusals` enumerates "
            "every main ALLOW the branch refuses, with the #10521 ruling item that makes it a refusal."
        ),
        "issue": 10521,
        "main_ref": ref,
        "main_sha": sha,
        "rows": rows,
        "over_refusals": over_refusals,
    }
    write_fixture(out, data)
    summary = summarize(rows, runs["branch"], over_refusals)
    changed_main = sorted(i for i, value in previous_main.items() if value and by_id.get(i, {}).get("main") != value)
    diff = {
        "added": sorted(set(measured) - set(old)),
        "removed": sorted(set(old) - set(measured)),
        "main_decision_changed": changed_main,
    }
    branch_detail = {row_id: run.as_dict() for row_id, run in runs["branch"].items()}
    if report is not None:
        report.write_text(json.dumps({"summary": summary, "diff": diff, "branch": branch_detail}, indent=1) + "\n")
    print(json.dumps({"main_sha": sha, "summary": summary, "over_refusal_diff": diff}, indent=2))
    return 0


def score(path: Path) -> int:
    data = load_fixture(path)
    branch = branch_runs(data["rows"])
    summary = summarize(data["rows"], branch, data["over_refusals"])
    print(json.dumps({"main_sha": data["main_sha"], **summary}, indent=2))
    failed = (
        summary["ac02_violations"]
        or summary["unlisted_over_refusals"]
        or summary["listed_but_allowed"]
        or summary["must_allow_blocked"]
    )
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Freeze origin/main's guard-hook decisions on the held-out corpus and score the branch (#10521).",
        epilog="Exit 0 when scoring finds no AC-02 violation and no over-refusal drift; 1 otherwise.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    generator = commands.add_parser(
        "generate", help="re-run origin/main and branch hooks as subprocesses; rewrite `main` and the budget"
    )
    generator.add_argument("--out", type=Path, default=FIXTURE, help="fixture path (default: %(default)s)")
    generator.add_argument("--ref", default="origin/main", help="git ref for main's hooks (default: %(default)s)")
    generator.add_argument("--report", type=Path, help="optional JSON report with branch observations (outside repo)")
    scorer = commands.add_parser("score", help="run the branch hooks in-process against the frozen fixture")
    scorer.add_argument("--fixture", type=Path, default=FIXTURE, help="fixture path (default: %(default)s)")
    args = parser.parse_args(argv)
    if args.command == "generate":
        return generate(args.out, args.ref, args.report)
    return score(args.fixture)


if __name__ == "__main__":
    sys.exit(main())
