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


@pytest.mark.parametrize("hook", ["merge", "admin"])
@pytest.mark.parametrize(
    "shell_options",
    [
        "bash -c --",
        "sh -c --",
        "bash -c -e",
        "bash -c -x",
        "bash -c +x",
        "bash -ce --",
        "bash -c -o errexit",
        "bash -c +o errexit",
        "bash -c -O extglob",
        "bash -c +O extglob",
    ],
)
def test_shell_options_after_c_execute_and_cannot_bypass_guards(hook, shell_options):
    oracle = _oracle()
    command = f"{shell_options} 'gh pr merge 5{' --admin' if hook == 'admin' else ''}'"
    row = {
        "id": "9484-c-options-guarded",
        "family": "shell-c-options",
        "command": command,
        "hook": hook,
        "accepted": False,
        "oracle_pr": "5",
    }
    report = oracle.run_oracle(rows=[row], traffic=[])
    observation = report["observations"][0]
    # An invalid shell invocation is not proof that the guard stopped a merge.
    assert observation["operation_executed"], observation
    assert observation["blocked"], observation
    assert report["failures"] == [], report
    assert report["totals"]["misses"] == 0, report


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
    # #10521 closed-allowlist ruling: 41 successor rows, each citing its ruling item.
    assert len(rows) == 1589
    assert len(active) == 1520
    assert len(typed) == 915
    assert len(rows) - len(active) == 69
    successors = [row for row in rows if row["family"] == "closed-allowlist-ruling"]
    assert len(successors) == 41
    assert all(row["expected"]["disposition"] == "refuse" and row["supersedes"] for row in successors)
    over_refusals = [row for row in successors if "ENUMERATED OVER-REFUSAL" in row["addition_reason"]]
    assert len(over_refusals) == 6


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
    duplicate_keys = 'GUARD_JUDGMENT {"disposition":"allow","reason_class":null,"disposition":"block"}\n'
    assert not oracle.parse_hook_judgment(0, duplicate_keys).consistent
    assert not oracle.parse_hook_judgment(0, _line({**allow, "note": "extra"})).consistent
    assert not oracle.parse_hook_judgment(2, _line({**refuse, "reason_class": "NOT_A_CLASS"})).consistent
    assert not oracle.parse_hook_judgment(
        0, _line({"disposition": "allow", "reason_class": "UNKNOWN_TARGET"})
    ).consistent
    assert not oracle.parse_hook_judgment(
        2, _line({"disposition": "block", "reason_class": "UNKNOWN_TARGET"})
    ).consistent
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


@pytest.mark.parametrize(
    "operation", ["checkout -b fixture", "switch -c fixture", "branch -D main", "worktree add .worktrees/new"]
)
def test_dynamic_branch_identity_is_only_the_branch_hooks_scope(operation):
    oracle = _oracle()
    rows = [
        {
            "id": f"scope-{kind}",
            "family": "scope-regression",
            "hook": kind,
            "command": f"G=gi; ${{G}}t {operation}",
            "accepted": False,
        }
        for kind in ("merge", "admin")
    ]
    report = oracle.run_oracle(rows=rows, traffic=[])
    assert all(row["executed"][0]["argv"][:2] == ["git", operation.split()[0]] for row in report["observations"])
    assert [row["blocked"] for row in report["observations"]] == [False, False]


def test_lowercase_recording_bindings_are_row_scoped(monkeypatch):
    oracle = _oracle()
    rows = json.loads((ROOT / "tests/fixtures/guard_bash_oracle.json").read_text())["rows"]
    # The dynamic `$git` row's successor (ruling item 2) refuses; the oracle resolves the chain.
    rows = [
        row
        for row in rows
        if any(f"freeze-h-table-{n:03d}-" in row["id"] + row.get("supersedes", "") for n in range(4))
    ]
    monkeypatch.setenv("git", "unrelated-inherited-program")
    monkeypatch.setenv("gh", "unrelated-inherited-program")
    report = oracle.run_oracle(rows=rows, traffic=[])
    assert len(report["observations"]) == 12
    assert all(row["executed"] for row in report["observations"])
    assert report["totals"]["expected_matches"] == 12
    # The row binding is not inherited by unrelated inputs.
    report = oracle.run_oracle(
        rows=[
            {
                "id": "unbound-name",
                "family": "recording-binding",
                "hook": "merge",
                "command": "$gh pr merge 5",
                "accepted": False,
            }
        ],
        traffic=[],
    )
    assert report["observations"][0]["executed"] == []
    assert report["observations"][0]["blocked"]


def test_managed_probe_is_removed_after_success():
    oracle = _oracle()
    with oracle._managed_probe("guard-success-test") as directory:
        lease = directory.parent
        assert json.loads((lease / "lease.json").read_text())["state"] == "registered"
        (directory / "record").write_text("recording evidence")
    assert not lease.exists()


def test_managed_probe_preserves_incomplete_run():
    oracle = _oracle()
    with pytest.raises(TimeoutError, match="unfinished recorder"):
        with oracle._managed_probe("guard-interrupted-test") as directory:
            (directory / "record").write_text("incomplete evidence")
            raise TimeoutError("unfinished recorder")
    assert (directory / "record").read_text() == "incomplete evidence"
    assert json.loads((directory.parent / "lease.json").read_text())["state"] == "preserved"


@pytest.mark.parametrize("prefix", ["cd .;", "pushd .; popd;", "cd -- .;"])
def test_literal_directory_prefix_keeps_dynamic_branch_in_its_own_hook(prefix):
    oracle = _oracle()
    rows = [
        {
            "id": f"directory-prefix-{kind}",
            "family": "scope-prefix",
            "hook": kind,
            "command": f"{prefix} G=gi; ${{G}}t switch -c fixture",
            "accepted": False,
        }
        for kind in ("branch", "merge", "admin")
    ]
    report = oracle.run_oracle(rows=rows, traffic=[])
    assert all(row["executed"][0]["argv"] == ["git", "switch", "-c", "fixture"] for row in report["observations"])
    assert [row["blocked"] for row in report["observations"]] == [True, False, False]


def test_complete_frozen_recording_denominator_passes_in_process():
    report = _oracle().run_oracle()
    assert report["totals"]["rows"] == 1517
    assert report["totals"]["rows"] == 1517
    assert report["totals"]["expected_rows"] == 915
    assert report["totals"]["expected_matches"] == 914
    assert report["totals"]["expected_mismatches"] == 1
    assert report["known_main_overblock_count"] == 10
    assert all(row["blocked"] and not row["expected_match"] for row in report["known_main_overblocks"])
    assert report["scored_totals"]["rows"] == 1507
    assert report["scored_totals"]["expected_matches"] == report["scored_totals"]["expected_rows"] == 914
    assert report["scored_totals"]["expected_mismatches"] == report["totals"]["misses"] == 0
    assert report["totals"]["wrong_target_judgments"] == report["totals"]["missing_target_judgments"] == 0
    assert report["scored_totals"]["overblocks"] <= 4
    # #10521 ruling item 5 over-refusals are enumerated by id, never folded into the budget.
    assert sorted(report["ruled_overblock_ids"]) == sorted(_oracle().RULED_OVERBLOCKS)
    assert report["scored_totals"]["ruled_overblocks"] == len(_oracle().RULED_OVERBLOCKS) == 12
    assert report["totals"]["traffic_rows"] == 1200
    assert report["totals"]["traffic_blocks"] == 0


@pytest.mark.parametrize("hook", ["merge", "admin"])
def test_fully_assembled_owned_operation_is_refused(hook):
    row = {
        "id": "assembled-owned-operation",
        "family": "scope-assembly",
        "hook": hook,
        "command": "G=g; H=h; P=p; R=r; M=mer; GE=ge; ${G}${H} ${P}${R} ${M}${GE} 5 --admin",
        "accepted": False,
    }
    report = _oracle().run_oracle(rows=[row], traffic=[])
    [observation] = report["observations"]
    assert observation["executed"][0]["argv"] == ["gh", "pr", "merge", "5", "--admin"]
    assert observation["blocked"]
    assert report["totals"]["misses"] == 0


def test_known_main_overblocks_keep_frozen_labels_and_block_decisions():
    oracle = _oracle()
    frozen = json.loads((ROOT / "tests/fixtures/guard_bash_oracle.json").read_text())["rows"]
    rows = [row for row in frozen if row["id"] in oracle.KNOWN_MAIN_OVERBLOCKS]
    assert len(rows) == 10
    report = oracle.run_oracle(rows=rows, traffic=[])
    assert len(report["observations"]) == report["totals"]["rows"] == 10
    assert report["totals"]["expected_rows"] == 1
    assert report["totals"]["expected_matches"] == 0
    assert report["totals"]["expected_mismatches"] == 1
    assert report["totals"]["overblocks"] == 10
    assert report["scored_totals"].get("rows", 0) == 0
    assert report["known_main_overblock_count"] == 10
    assert {row["id"] for row in report["known_main_overblocks"]} == set(oracle.KNOWN_MAIN_OVERBLOCKS)
    assert all(row["blocked"] and row["overblock"] and not row["miss"] for row in report["observations"])
    assert rows[-1]["expected"] == {"disposition": "allow", "reason_class": None}


@pytest.mark.parametrize("mutation", ["allow", "wrong_target", "command", "hook", "label"])
def test_known_residual_never_masks_unsafe_allow_or_changed_identity(mutation):
    oracle = _oracle()
    frozen = json.loads((ROOT / "tests/fixtures/guard_bash_oracle.json").read_text())["rows"]
    row = next(row for row in frozen if row["id"] == "freeze-review-home-000")
    row = json.loads(json.dumps(row))
    hook = _Hook("block")
    if mutation == "allow":
        hook = _Hook("allow")
    elif mutation == "wrong_target":
        hook = _Hook("block", targets=[{"repository": "github.com/fixture/wrong", "pr": "5", "cwd": str(PROBE)}])
    elif mutation == "command":
        row["command"] += "; gh pr merge 5"
    elif mutation == "hook":
        row["hook"] = "merge"
    else:
        row["expected"]["disposition"] = "block"
    report = _score(oracle, [row], hook)
    assert report["hooks"][row["hook"]]["known_main_overblock"] == 0
    if mutation in {"allow", "wrong_target"}:
        assert oracle.score_status(report) == 1


def test_known_residual_typed_score_is_separate_from_expected_match():
    oracle = _oracle()
    frozen = json.loads((ROOT / "tests/fixtures/guard_bash_oracle.json").read_text())["rows"]
    row = next(row for row in frozen if row["id"] == "freeze-review-home-000")
    report = _score(oracle, [row], _Hook("block"))
    assert report["active_typed_rows"] == 1
    assert report["hooks"]["branch"]["pass"] == 0
    assert report["hooks"]["branch"]["known_main_overblock"] == 1
    assert report["rows"][0]["verdict"] == "known_main_overblock"
    assert oracle.score_status(report) == 0


def test_complete_frozen_typed_judgments_and_observed_targets():
    oracle = _oracle()
    report = oracle.score_guard_oracle()
    assert report["active_typed_rows"] == 915
    assert report["typed_totals"] == {"pass": 914, "fail": 0, "over_block": 0, "unsafe_allow": 0}
    assert sum(bucket["known_main_overblock"] for bucket in report["hooks"].values()) == 1
    assert oracle.score_status(report) == 0
    targets = {row["id"]: row["observed_targets"] for row in report["rows"]}
    row_id = "freeze-b-target-boolean-003"
    assert len(targets[row_id]) == 1
    assert targets[row_id][0]["repository"] == "github.com/fixture/default"
    assert targets[row_id][0]["pr"] == "5"
    assert Path(targets[row_id][0]["cwd"]).name == "primary"
    # `HOME=$P cd && gh pr merge 5` now refuses before any lookup (#10521 ruling item 4).
    assert targets["freeze-k-closed-allowlist-030"] == []
