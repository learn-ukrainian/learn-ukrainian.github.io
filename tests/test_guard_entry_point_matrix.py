"""Entry-point matrix for the closed-allowlist Bash guards (#10521).

The ruling note's matrix: every row is an entry point, every column a
construct class, and each class holds one or more reproducers that contain
the row's guarded operation. Rows:

* ``guard-pr-merge``, ``guard-admin-merge`` and ``guard-branch-switch-in-main``
  run in-process through ``main()`` (``bash_oracle.invoke_hook_main``) inside
  the oracle probe: a real Git primary checkout (patched in as the protected
  root) with an added worktree at ``wt``, and git/gh lookup recorders on PATH.
  Every cell must REFUSE: exit 2 plus exactly one consistent ``GUARD_JUDGMENT``
  line whose ``reason_class`` is a typed refusal class. ``F2`` cells must also
  refuse before any directory inference or lookup, so the recorder must see
  zero git/gh calls.
* ``bash_oracle`` replays the same reproducers through real Bash with recording
  git/gh (``bash_oracle.run_oracle``) and must classify each as blocked, with no
  miss.

Columns (``<hook>-<class>-<n>`` ids):

* ``F1``: shadowed builtin as a loop or ``if`` condition.
* ``F2``: refusal before directory inference or probe.
* ``F3``: computed alias / alias expansion, refused even when the operation
  is hidden behind the alias.
* ``fndef``: function definition sharing a command with a guarded operation.
* ``cwd``: subshell, ``;``, ``||`` and pipeline cwd propagation.
* ``env``: ``trap``, ``set -k``, ``BASH_ENV``, ``PATH``/``CDPATH``/``GIT_*``
  prefixes and exported environment.
* ``arith``: arithmetic, ``[[ ]]``, ``coproc`` and background jobs.
* ``runner``: ``env -S``, ``timeout``, ``python -c``, ``ssh`` and ``make`` with a
  Makefile written by the same command.
* ``herestring``: a here-string fed to a shell.
* ``admitted``: forms inside the admitted grammar (``echo | <op>``, ``timeout 5 <op>``);
  they must block, by a typed refusal or by judging the operation in its directory.

Untested boundaries. The frozen threat model puts these out of scope, so they
have no cells: encoded payloads, scripts on disk, harness or profile state,
concurrent processes, and API merges (``gh api``). Also untested here: the
persistent-shell behaviour of harnesses other than Claude Code (Codex, Grok,
AGY, Cursor), the contents of the Claude Code shell snapshot, and the cost of
the computed-name rule.
"""

from __future__ import annotations

import importlib.util
import os
from contextlib import nullcontext
from pathlib import Path
from typing import NamedTuple
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_oracle():
    spec = importlib.util.spec_from_file_location("guard_entry_point_oracle", ROOT / "scripts/hooks/bash_oracle.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = _load_oracle()


class Operation(NamedTuple):
    kind: str  # bash_oracle row kind
    executable: str
    visible: str
    hidden: str  # the same operation spelled through the alias `g`


OPERATIONS = {
    "guard-pr-merge": Operation("merge", "gh", "gh pr merge 5 --squash", "g pr merge 5 --squash"),
    "guard-admin-merge": Operation("admin", "gh", "gh pr merge 5 --admin", "g pr merge 5 --admin"),
    "guard-branch-switch-in-main": Operation("branch", "git", "git checkout feature", "g checkout feature"),
}

# `{op}` is the visible operation, `{exe}` its executable, `{hidden}` the alias spelling.
# Every command runs from the synthetic PRIMARY checkout; `wt` links to its worktree.
# F1 bodies run in real Bash only because of the shadowing function (`break` keeps the
# replay finite); a walker that prunes them by the builtin's meaning misses the operation.
CLASSES = {
    "F1": (
        "false(){{ :; }}; while false; do {op}; break; done",
        "true(){{ return 1; }}; if ! true; then {op}; fi",
        "true(){{ return 1; }}; if true; then :; else {op}; fi",
    ),
    "F2": (
        "f(){{ :; }}; cd wt && {op}",
        "cd wt || exit; {op}",
    ),
    "F3": (
        "n=g; alias $n={exe}\n{hidden}",
        "BASH_ALIASES[g]={exe}\n{hidden}",
        "shopt -s expand_aliases\nalias g={exe}\n{hidden}",
    ),
    "fndef": (
        "f(){{ :; }}; {op}",
        "{op}; f(){{ :; }}",
        '{exe}(){{ command {exe} "$@"; }}; {op}',
    ),
    "cwd": (
        "(cd wt && {op})",
        "cd wt; {op}",
        "cd wt || true; {op}",
    ),
    "env": (
        "trap '{op}' EXIT",
        "set -k; {op} GH_REPO=o/r",
        "BASH_ENV=x {op}",
        "PATH=x {op}",
        "CDPATH=. cd wt && {op}",
        "GIT_DIR=x {op}",
        "export GH_REPO=o/r; {op}",
    ),
    "arith": (
        "(( x )) && {op}",
        "[[ -n x ]] && {op}",
        "coproc {op}",
        "{op} &",
    ),
    "runner": (
        "env -S '{op}'",
        "python -c \"import os; os.system('{op}')\"",
        "ssh h '{op}'",
        "printf 'x:\\n\\t{op}\\n' > Makefile && make x",
    ),
    "herestring": ("bash <<< '{op}'",),
    # Inside the admitted grammar (a transparent wrapper; an admitted command before a
    # pipeline member): the hook may judge these in their real directory instead of
    # refusing, so the cell requires a block, typed whenever it is a refusal.
    "admitted": (
        "echo | {op}",
        "timeout 5 {op}",
    ),
}

# Classes whose refusal must precede directory inference, repository probes and PR lookups.
NO_LOOKUP_CLASSES = frozenset({"F2"})
# Classes inside the admitted grammar: a judged block is the correct outcome.
JUDGED_CLASSES = frozenset({"admitted"})


class Cell(NamedTuple):
    hook: str
    column: str
    command: str


def _cells():
    cells = {}
    for hook, operation in OPERATIONS.items():
        for column, templates in CLASSES.items():
            for number, template in enumerate(templates, start=1):
                command = template.format(op=operation.visible, exe=operation.executable, hidden=operation.hidden)
                cells[f"{hook}-{column}-{number}"] = Cell(hook, column, command)
    return cells


CELLS = _cells()


class Probe(NamedTuple):
    primary: Path
    worktree: Path
    records: Path
    environment: dict
    hooks: dict


@pytest.fixture(scope="module")
def probe():
    """One oracle probe: real Git primary + worktree, recording git/gh first on PATH."""
    with oracle._managed_probe("guard-entry-point-matrix") as directory:
        primary, worktree, binaries, records, _gh = oracle._prepare_probe(Path(directory))
        environment = oracle._scoring_environment(primary, binaries)
        with patch.dict(os.environ, environment, clear=True):
            hooks = {hook: oracle.load_hook(hook) for hook in OPERATIONS}
        yield Probe(primary, worktree, records, environment, hooks)


def _run(probe, hook, command):
    """main() on the hook payload from the primary; return (judgment, stderr, recorded git/gh argv)."""
    oracle._clear_directory(probe.records)
    module = probe.hooks[hook]
    protected = (
        patch.object(module, "PROTECTED_ROOTS", [probe.primary])
        if hook == "guard-branch-switch-in-main"
        else nullcontext()
    )
    with patch.dict(os.environ, probe.environment, clear=True), protected:
        code, _stdout, stderr = oracle.invoke_hook_main(module, command, str(probe.primary))
    return oracle.parse_hook_judgment(code, stderr), stderr, oracle._read_lookup_records(probe.records)


def _describe(command, judgment, stderr, recorded):
    tail = "\n".join(stderr.strip().splitlines()[-4:])
    return f"command={command!r}\njudgment={judgment}\nrecorded={recorded}\nstderr tail:\n{tail}"


@pytest.mark.parametrize("cell_id", list(CELLS))
def test_guard_entry_point_refuses_with_typed_reason(probe, cell_id):
    cell = CELLS[cell_id]
    judgment, stderr, recorded = _run(probe, cell.hook, cell.command)
    detail = _describe(cell.command, judgment, stderr, recorded)
    assert judgment.exit_code == 2, "hook ALLOWED a guarded reproducer\n" + detail
    if cell.column in JUDGED_CLASSES and judgment.source != "line":
        assert judgment.disposition == "block", detail
        return
    assert judgment.source == "line" and judgment.consistent, "no single consistent GUARD_JUDGMENT line\n" + detail
    assert judgment.disposition == "refuse", detail
    assert judgment.reason_class in oracle.REASON_CLASSES, detail
    if cell.column in NO_LOOKUP_CLASSES:
        assert recorded == [], "refusal came after a repository probe or PR lookup\n" + detail


@pytest.mark.parametrize(
    "hook,command,code,lookup",
    [
        ("guard-branch-switch-in-main", "git checkout feature", 2, "git"),
        ("guard-branch-switch-in-main", "git -C wt checkout feature", 0, "git"),
        ("guard-pr-merge", "gh pr merge 5 --squash", 2, "gh"),
    ],
    ids=["control-branch-primary", "control-branch-worktree", "control-merge-primary"],
)
def test_probe_controls(probe, hook, command, code, lookup):
    """The probe is live: the primary is protected, the worktree is not, and lookups are recorded."""
    judgment, stderr, recorded = _run(probe, hook, command)
    detail = _describe(command, judgment, stderr, recorded)
    assert judgment.exit_code == code, detail
    assert any(argv[0] == lookup for argv, _cwd in recorded), detail


@pytest.fixture(scope="module")
def replay():
    """Replay every reproducer through real Bash once; observations keyed by cell id."""
    rows = [
        {
            "id": cell_id,
            "family": "entry-point-matrix",
            "hook": OPERATIONS[cell.hook].kind,
            "command": cell.command,
            "accepted": False,
            "oracle_pr": "5",
        }
        for cell_id, cell in CELLS.items()
    ]
    report = oracle.run_oracle(rows=rows, traffic=[])
    return {observation["id"]: observation for observation in report["observations"]}


@pytest.mark.parametrize("cell_id", list(CELLS), ids=[f"bash_oracle.{cell_id}" for cell_id in CELLS])
def test_bash_oracle_replay_blocks(replay, cell_id):
    observation = replay[cell_id]
    detail = f"command={CELLS[cell_id].command!r}\nobservation={observation}"
    assert observation["blocked"], "oracle replay ALLOWED a guarded reproducer\n" + detail
    assert not observation["miss"], detail
