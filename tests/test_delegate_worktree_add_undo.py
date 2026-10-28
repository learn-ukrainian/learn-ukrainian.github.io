"""A failed ``git worktree add`` never has a registered worktree removed for it (#8663).

Dispatch reserves the path with ``mkdir`` and records the reservation before
git starts. A slow add is stopped with SIGTERM first, so git's own signal
cleanup deletes its partial worktree and admin directory; SIGKILL follows
only after a grace. Dispatch then removes nothing, not even the empty
directory it reserved: git 2.53 can register another add there while it is
still empty, so the directory is left as it is and ``reserved_dir_left``
records that. A worktree git left registered is reported as
``needs_attention: initializing_leftover`` with a "verify first:" removal
command, never removed, unlocked or pruned.

Every test runs in a tmp git repository. Slowness is simulated, by a fake
runner that leaves the state a killed add leaves, by ``sleep`` stubs, or by a
slow smudge filter or ``reference-transaction`` hook behind a ``git``
wrapper, under tiny bounds; nothing here generates host load.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from pathlib import Path
from typing import Any

import pytest

from scripts.orchestration import worktree_prep

# --- the real ``git`` Popen path -------------------------------------------------------------


# What each stage has checked out when the add is stopped.


# --- no automatic removal of a registered worktree ------------------------------------------

# Every function on the worktree-prep path. None may run a removal, unlock or
# prune of a registered worktree.
_REPORT_ONLY_FUNCTIONS = [
    *(
        obj
        for _name, obj in inspect.getmembers(worktree_prep, inspect.isfunction)
        if obj.__module__ == worktree_prep.__name__
    ),
]
_FORBIDDEN_CALLS = {
    "remove_unclaimed_worktree",
    "git_worktree_remove",
    "rmtree",
    "_remove_acp_runtime_worktree",
    "rmdir",
    "removedirs",
}
# ``unlink``/``remove`` are allowed only on the task-record file, never on a worktree path.
_FILE_REMOVALS = {"unlink", "remove"}
_TASK_RECORD_NAMES = {"state_path"}
_FORBIDDEN_GIT_WORDS = {"remove", "unlock", "prune"}


def _string_constants(node: ast.AST) -> set[str]:
    return {item.value for item in ast.walk(node) if isinstance(item, ast.Constant) and isinstance(item.value, str)}


@pytest.mark.parametrize("function", _REPORT_ONLY_FUNCTIONS, ids=lambda fn: f"{fn.__module__}.{fn.__name__}")
def test_worktree_prep_and_leftover_report_never_remove_a_registered_worktree(function: Any) -> None:
    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callee = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
        assert callee not in _FORBIDDEN_CALLS, f"{function.__name__} calls {callee}"
        if callee in _FILE_REMOVALS:
            receiver = node.func.value if isinstance(node.func, ast.Attribute) else None
            targets = [receiver, *node.args] if isinstance(receiver, ast.Name) and receiver.id != "os" else node.args
            names = {target.id for target in targets if isinstance(target, ast.Name)}
            assert names and names <= _TASK_RECORD_NAMES, f"{function.__name__} calls {callee} on {sorted(names)}"
        # A git argv (a list/tuple literal passed to a call) never names remove, unlock or prune.
        for arg in [*node.args, *(keyword.value for keyword in node.keywords)]:
            if isinstance(arg, (ast.List, ast.Tuple)):
                words = _string_constants(arg) & _FORBIDDEN_GIT_WORDS
                assert not words, f"{function.__name__} passes {sorted(words)} to {callee}"


def test_the_removal_command_is_only_ever_displayed() -> None:
    source = inspect.getsource(worktree_prep.verify_first_command)
    assert "subprocess" not in source and "_git(" not in source
    assert worktree_prep.verify_first_command(Path("/r"), Path("/r/w x")).startswith(
        "verify first: git -C /r worktree unlock '/r/w x' && "
    )


# --- the bounded add itself ------------------------------------------------------------------
