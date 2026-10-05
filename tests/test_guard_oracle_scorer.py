"""Typed transitive-supersession scorer for the frozen guard oracle (#9484)."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
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
    assert allowed["rows"][0]["verdict"] == "unsafe_allow"
    assert allowed["rows"][0]["disposition"] == "allow"
    assert allowed["hooks"]["branch"]["pass"] == 0
    assert allowed["hooks"]["branch"]["fail"] == 0
    assert allowed["hooks"]["branch"]["unsafe_allow"] == 1
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
    assert report["rows"][0]["verdict"] == "unsafe_allow"
    assert report["rows"][0]["disposition"] == "allow"
    assert report["legacy_rows"] == []
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


def _line(payload: dict) -> str:
    return "GUARD_JUDGMENT " + json.dumps(payload) + "\n"


def test_judgment_line_rules() -> None:
    oracle = _oracle()
    allow = {"disposition": "allow", "reason_class": None}
    block = {"disposition": "block", "reason_class": None}
    refuse = {"disposition": "refuse", "reason_class": "UNKNOWN_REPOSITORY"}
    parsed = oracle.parse_hook_judgment(0, _line(allow))
    assert parsed.consistent and parsed.source == "line" and parsed.disposition == "allow"
    assert oracle.parse_hook_judgment(2, _line(block)).consistent
    assert oracle.parse_hook_judgment(2, _line(refuse)).consistent
    assert not oracle.parse_hook_judgment(0, _line(allow) + _line(allow)).consistent
    assert not oracle.parse_hook_judgment(0, "GUARD_JUDGMENT {not json}\n").consistent
    duplicate_keys = (
        'GUARD_JUDGMENT {"disposition":"allow","reason_class":null,"disposition":"block"}\n'
    )
    assert not oracle.parse_hook_judgment(0, duplicate_keys).consistent
    assert not oracle.parse_hook_judgment(0, _line({**allow, "note": "extra"})).consistent
    assert not oracle.parse_hook_judgment(2, _line({**refuse, "reason_class": "NOT_A_CLASS"})).consistent
    assert not oracle.parse_hook_judgment(0, _line({"disposition": "allow", "reason_class": "UNKNOWN_TARGET"})).consistent
    assert not oracle.parse_hook_judgment(2, _line({"disposition": "block", "reason_class": "UNKNOWN_TARGET"})).consistent
    assert not oracle.parse_hook_judgment(2, _line({"disposition": "refuse", "reason_class": None})).consistent
    assert not oracle.parse_hook_judgment(2, _line(allow)).consistent
    assert not oracle.parse_hook_judgment(0, _line(block)).consistent
    assert not oracle.parse_hook_judgment(1, _line(allow)).consistent
    missing = oracle.parse_hook_judgment(2, "")
    assert missing.source == "exit" and missing.disposition == "block" and missing.reason_class is None
    stdout_only = oracle.parse_hook_judgment(2, "")
    assert stdout_only.disposition == "block"
    refuse_expected = {"disposition": "refuse", "reason_class": "UNKNOWN_REPOSITORY"}
    assert oracle.classify_judgment(refuse_expected, missing, PROBE, [], False) == "fail"
    reason_expected = {"disposition": "block", "reason_class": "UNKNOWN_TARGET"}
    assert oracle.classify_judgment(reason_expected, missing, PROBE, [], False) == "fail"
    block_expected = {"disposition": "block", "reason_class": None}
    assert oracle.classify_judgment(block_expected, missing, PROBE, [], False) == "pass"


def test_stdout_judgment_line_is_not_evidence() -> None:
    oracle = _oracle()

    class StdoutOnly:
        def main(self):
            sys.stdout.write(_line({"disposition": "refuse", "reason_class": "UNKNOWN_REPOSITORY"}))
            return 2

    rows = [_row("stdout-line", "merge", "refuse", reason="UNKNOWN_REPOSITORY")]
    report = _score(oracle, rows, StdoutOnly())
    assert report["rows"][0]["verdict"] == "fail"
    assert report["rows"][0]["disposition"] == "block"


def test_recorded_gh_lookup_parser() -> None:
    oracle = _oracle()
    url = "https://github.com/fixture/other/pull/5"
    assert oracle._gh_pr_lookup(["gh", "pr", "view", "5", "--repo", "fixture/default"]) == ("5", "fixture/default")
    assert oracle._gh_pr_lookup(["gh", "pr", "checks", "5", "--json", "name,bucket,state"]) == ("5", None)
    assert oracle._gh_pr_lookup(["gh", "pr", "view", "5", "--repo=fixture/other"]) == ("5", "fixture/other")
    assert oracle._gh_pr_lookup(["gh", "pr", "view", url]) == (url, None)
    assert oracle._gh_pr_lookup(["git", "rev-parse", "--git-dir"]) is None
    api = (["gh", "api", "repos/fixture/other/branches/main/protection"], "/probe")
    assert oracle._lookup_happened([api]) is True


def _lookup_hook(argv, cwd, disposition, reason=None, *, reported=None, code=None):
    class Hook:
        def main(self):
            if argv is not None:
                subprocess.run(argv, cwd=cwd, check=False, timeout=30)
            payload = {"disposition": disposition, "reason_class": reason}
            if reported is not None:
                payload["target"] = reported
            sys.stderr.write(_line(payload))
            if code is not None:
                return code
            return 0 if disposition == "allow" else 2

    return Hook()


def test_printed_gold_target_cannot_hide_the_wrong_lookup(tmp_path) -> None:
    oracle = _oracle()
    rows = json.loads((ROOT / "tests/fixtures/guard_bash_oracle.json").read_text(encoding="utf-8"))["rows"]
    row = next(item for item in rows if item["id"] == "freeze-b-target-identity-004")
    gold = row["expected"]["target"]
    mutant = _lookup_hook(
        ["gh", "pr", "view", "5", "--repo", "fixture/default"],
        tmp_path,
        "block",
        reported={**gold, "cwd": str(tmp_path)},
    )
    report = oracle.score_guard_oracle([row], hooks={"merge": mutant}, primary=tmp_path, worktree=tmp_path)
    assert report["rows"][0]["verdict"] == "fail"
    assert report["rows"][0]["disposition"] == "block"
    observed = report["rows"][0]["observed_targets"]
    assert observed[0]["repository"] == "github.com/fixture/default"
    assert observed[0]["pr"] == "5"
    honest = _lookup_hook(["gh", "pr", "view", "5", "--repo", "fixture/other"], tmp_path, "block")
    passed = oracle.score_guard_oracle([row], hooks={"merge": honest}, primary=tmp_path, worktree=tmp_path)
    assert passed["rows"][0]["verdict"] == "pass"
    assert passed["rows"][0]["observed_targets"][0]["repository"] == gold["repository"]


@pytest.mark.parametrize("disposition", ["allow", "block"])
def test_empty_target_list_observes_that_no_lookup_happened(disposition: str, tmp_path) -> None:
    oracle = _oracle()
    code = 0 if disposition == "allow" else 2
    rows = [_row("no-lookup", "merge", disposition, targets=[])]
    quiet = _lookup_hook(None, tmp_path, disposition, code=code)
    clean = oracle.score_guard_oracle(rows, hooks={"merge": quiet}, primary=tmp_path, worktree=tmp_path)
    assert clean["rows"][0]["verdict"] == "pass"
    assert clean["rows"][0]["observed_targets"] == []
    noisy = _lookup_hook(["gh", "pr", "view", "5", "--repo", "fixture/default"], tmp_path, disposition, code=code)
    report = oracle.score_guard_oracle(rows, hooks={"merge": noisy}, primary=tmp_path, worktree=tmp_path)
    assert report["rows"][0]["verdict"] == "fail"
    assert report["rows"][0]["observed_targets"][0]["pr"] == "5"


def test_typed_row_superseded_by_untyped_row_fails() -> None:
    oracle = _oracle()
    rows = [
        _row("typed-old", "merge", "block"),
        {"id": "plain-new", "hook": "merge", "command": "true", "accepted": False, "supersedes": "typed-old"},
    ]
    with pytest.raises(oracle.TypedSupersededByUntyped, match="typed row superseded by untyped row"):
        oracle.score_guard_oracle(rows, hooks={"merge": _Hook("block")})


def test_score_hides_host_shell_options(monkeypatch) -> None:
    oracle = _oracle()
    monkeypatch.setenv("SHELLOPTS", "braceexpand:physical")
    monkeypatch.setenv("BASHOPTS", "cdable_vars")

    class Hook:
        def main(self):
            if "SHELLOPTS" in os.environ or "BASHOPTS" in os.environ:
                return 2
            sys.stderr.write(_line({"disposition": "allow", "reason_class": None}))
            return 0

    report = _score(oracle, [_row("clean-env", "merge", "allow")], Hook())
    assert report["rows"][0]["verdict"] == "pass"


def test_overblock_budget_is_four() -> None:
    oracle = _oracle()
    report = {
        "hooks": {"merge": {"fail": 0, "unsafe_allow": 0, "over_block": 4}},
        "legacy_hooks": {"branch": {"fail": 0, "unsafe_allow": 0, "over_block": 0}},
    }
    assert oracle.score_status(report) == 0
    report["hooks"]["merge"]["over_block"] = 5
    assert oracle.score_status(report) == 1
    report["hooks"]["merge"]["over_block"] = 1
    report["legacy_hooks"]["branch"]["over_block"] = 4
    assert oracle.score_status(report) == 1
    report["legacy_hooks"]["branch"]["over_block"] = 0
    report["hooks"]["merge"]["unsafe_allow"] = 1
    assert oracle.score_status(report) == 1
    report["hooks"]["merge"]["unsafe_allow"] = 0
    report["hooks"]["merge"]["fail"] = 1
    assert oracle.score_status(report) == 1


def test_legacy_branch_row_is_scored_through_main(monkeypatch) -> None:
    oracle = _oracle()
    calls = {"main": 0}
    original = oracle.load_hook

    def spy(name):
        module = original(name)
        if name == "guard-branch-switch-in-main":
            real_main = module.main

            def main():
                calls["main"] += 1
                return real_main()

            module.main = main
        return module

    monkeypatch.setattr(oracle, "load_hook", spy)
    rows = json.loads((ROOT / "tests/fixtures/guard_bash_oracle.json").read_text(encoding="utf-8"))["rows"]
    row = next(item for item in rows if item["hook"] == "branch" and "expected" not in item)
    report = oracle.score_guard_oracle([row])
    assert calls["main"] == 1
    assert report["rows"] == []
    assert report["untyped_active_rows"] == 1
    assert report["legacy_rows"][0]["id"] == row["id"]
    bucket = report["legacy_hooks"]["branch"]
    scored = bucket["pass"] + bucket["fail"] + bucket["over_block"] + bucket["unsafe_allow"]
    assert scored == 1
