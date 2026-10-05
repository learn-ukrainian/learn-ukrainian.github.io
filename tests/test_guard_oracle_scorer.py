"""Typed transitive-supersession scorer for the frozen guard oracle (#9484)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = Path("/oracle-probe")


def _oracle():
    spec = importlib.util.spec_from_file_location("guard_oracle_scorer", ROOT / "scripts/hooks/bash_oracle.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(row_id, hook, disposition, reason=None, *, target=None, targets=None, supersedes=None, command="true"):
    expected = {"disposition": disposition, "reason_class": reason}
    if target is not None:
        expected["target"] = target
    if targets is not None:
        expected["targets"] = targets
    row = {"id": row_id, "hook": hook, "command": command, "expected": expected}
    if supersedes is not None:
        row["supersedes"] = supersedes
    return row


class _Hook:
    def __init__(self, disposition, reason=None, target=None, targets=None, code=None):
        self.disposition = disposition
        self.reason = reason
        self.target = target
        self.targets = targets
        self.code = (0 if disposition == "allow" else 2) if code is None else code
        self.main_calls = 0

    def main(self):
        self.main_calls += 1
        payload = {"disposition": self.disposition, "reason_class": self.reason}
        if self.target is not None:
            payload["target"] = self.target
        if self.targets is not None:
            payload["targets"] = self.targets
        sys.stderr.write("GUARD_JUDGMENT " + json.dumps(payload) + "\n")
        return self.code


class _HelperHook:
    """main() allows; the helper would block. Only main() is the entry point."""

    def __init__(self):
        self.main_calls = 0
        self.helper_calls = 0

    def main(self):
        self.main_calls += 1
        return 0

    def _command_danger_reason(self, command, cwd=None):
        self.helper_calls += 1
        return "git checkout -b creates and switches to a new branch in the main worktree"


def _score(oracle, rows, hook):
    kind = rows[0]["hook"]
    return oracle.score_guard_oracle(rows, hooks={kind: hook})


def test_cycle_fails_the_oracle() -> None:
    oracle = _oracle()
    rows = [
        _row("a", "merge", "allow", supersedes="b"),
        _row("b", "merge", "block", supersedes="a"),
    ]
    with pytest.raises(oracle.SupersessionCycle, match="supersession cycle"):
        oracle.score_guard_oracle(rows, hooks={"merge": _Hook("allow")})


def test_dangling_supersession_fails_the_oracle() -> None:
    oracle = _oracle()
    rows = [_row("a", "merge", "allow", supersedes="missing-row")]
    with pytest.raises(oracle.DanglingSupersession, match="dangling supersession"):
        oracle.score_guard_oracle(rows, hooks={"merge": _Hook("allow")})


def test_two_active_successors_fail_the_oracle() -> None:
    oracle = _oracle()
    rows = [
        _row("old", "admin", "allow"),
        _row("left", "admin", "block", supersedes="old"),
        _row("right", "admin", "refuse", reason="UNKNOWN_REPOSITORY", supersedes="old"),
    ]
    with pytest.raises(oracle.MultipleActiveSuccessors, match="multiple active successors"):
        oracle.score_guard_oracle(rows, hooks={"admin": _Hook("allow")})


@pytest.mark.parametrize("mutation", ["pr", "repository", "cwd"])
def test_right_disposition_with_wrong_target_fails(mutation: str) -> None:
    oracle = _oracle()
    target = {"repository": "github.com/fixture/other", "pr": "5", "cwd": str(PROBE)}
    if mutation == "pr":
        target["pr"] = "7"
    elif mutation == "repository":
        target["repository"] = "github.com/fixture/wrong"
    else:
        target["cwd"] = "/wrong-directory"
    rows = [
        _row(
            "target-row",
            "merge",
            "block",
            target={"repository": "github.com/fixture/other", "pr": "5"},
        )
    ]
    report = _score(oracle, rows, _Hook("block", target=target))
    assert report["rows"][0]["verdict"] == "fail"
    assert report["rows"][0]["disposition"] == "block"
    assert report["hooks"]["merge"]["pass"] == 0
    assert report["hooks"]["merge"]["fail"] == 1


def test_empty_target_list_rejects_a_reported_target() -> None:
    oracle = _oracle()
    rows = [_row("no-lookup", "merge", "refuse", reason="UNKNOWN_REPOSITORY", targets=[])]
    hook = _Hook(
        "refuse",
        reason="UNKNOWN_REPOSITORY",
        target={"repository": "github.com/fixture/other", "pr": "5", "cwd": str(PROBE)},
    )
    report = _score(oracle, rows, hook)
    assert report["rows"][0]["verdict"] == "fail"
    assert report["rows"][0]["disposition"] == "refuse"


def test_right_disposition_with_wrong_reason_class_fails() -> None:
    oracle = _oracle()
    rows = [_row("reason-row", "branch", "refuse", reason="UNKNOWN_EXECUTOR")]
    report = _score(oracle, rows, _Hook("refuse", reason="DYNAMIC_COMMAND"))
    assert report["rows"][0]["verdict"] == "fail"
    assert report["rows"][0]["disposition"] == "refuse"
    assert report["rows"][0]["reason_class"] == "DYNAMIC_COMMAND"
    assert report["hooks"]["branch"]["fail"] == 1
    assert report["hooks"]["branch"]["pass"] == 0


def test_superseded_row_label_is_not_scored() -> None:
    oracle = _oracle()
    rows = [
        _row("old", "branch", "allow"),
        _row("mid", "branch", "refuse", reason="UNKNOWN_CONTEXT", supersedes="old"),
        _row("successor", "branch", "block", supersedes="mid"),
    ]
    # The hook emits the superseded allow. That label must not pass.
    allowed = _score(oracle, rows, _Hook("allow"))
    assert [row["id"] for row in allowed["rows"]] == ["successor"]
    assert allowed["rows"][0]["verdict"] == "fail"
    assert allowed["rows"][0]["disposition"] == "allow"
    assert allowed["hooks"]["branch"]["pass"] == 0
    # The same command's final successor expects block, and only that label passes.
    blocked = _score(oracle, rows, _Hook("block"))
    assert [row["id"] for row in blocked["rows"]] == ["successor"]
    assert blocked["rows"][0]["verdict"] == "pass"
    assert blocked["hooks"]["branch"]["pass"] == 1


def test_helper_entry_point_is_not_accepted() -> None:
    oracle = _oracle()
    hook = _HelperHook()
    rows = [_row("helper-row", "branch", "block", command="git checkout -b evil")]
    report = _score(oracle, rows, hook)
    assert report["rows"][0]["verdict"] == "fail"
    assert report["rows"][0]["disposition"] == "allow"
    assert hook.main_calls == 1
    assert hook.helper_calls == 0


def test_frozen_oracle_supersession_is_a_chain_of_single_successors() -> None:
    oracle = _oracle()
    rows = json.loads((ROOT / "tests/fixtures/guard_bash_oracle.json").read_text(encoding="utf-8"))["rows"]
    active = oracle.resolve_active_rows(rows)
    typed = [row for row in active if "expected" in row and row.get("hook") in {"merge", "admin", "branch"}]
    assert len(rows) == 1520
    assert len(active) == 1495
    assert len(typed) == 890
    assert len(rows) - len(active) == 25


def test_real_merge_hook_allow_is_scored_through_main() -> None:
    oracle = _oracle()
    rows = [_row("probe-allow", "merge", "allow", command="echo hi")]
    report = oracle.score_guard_oracle(rows)
    assert report["rows"][0]["verdict"] == "pass"
    assert report["rows"][0]["disposition"] == "allow"
    assert report["hooks"]["merge"]["pass"] == 1
