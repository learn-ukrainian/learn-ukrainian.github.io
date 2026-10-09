"""AST replacement of the retired redirect scanner (#9484/#9480)."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "agents_extensions/shared/hooks"
sys.path.insert(0, str(HOOKS))
from shell_bash import ShellParseError, read_commands


def test_pinned_real_bash_oracle():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/hooks/bash_oracle.py")], capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["pins"] == {"tree-sitter": "0.26.0", "tree-sitter-bash": "0.25.1"}
    assert report["totals"]["misses"] == 0
    assert report["totals"]["overblocks"] <= 4
    assert report["totals"]["traffic_blocks"] == 0
    assert report["totals"]["traffic_rows"] == 1200
    assert report["totals"]["observed_argv_rows"] == report["totals"]["argv_rows"] == 50
    assert report["families"]["9484-failing-cd"]["executed_rows"] == 3
    assert report["families"]["accepted-residual"]["executed_rows"] == 2


def test_oracle_detects_a_reader_omission():
    spec = importlib.util.spec_from_file_location("bash_oracle", ROOT / "scripts/hooks/bash_oracle.py")
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    original_load = oracle.load_hook

    def mutant(name):
        module = original_load(name)
        module.read_commands = lambda *args, **kwargs: []
        return module

    rows = json.loads((ROOT / "tests/fixtures/guard_bash_oracle.json").read_text())["rows"][:3]
    with patch.object(oracle, "load_hook", mutant):
        report = oracle.run_oracle(rows=rows, traffic=[])
    assert report["totals"]["misses"] == 3


def _oracle_module():
    spec = importlib.util.spec_from_file_location("bash_oracle", ROOT / "scripts/hooks/bash_oracle.py")
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    return oracle


def test_oracle_observes_all_prefix_operations_and_rejects_omitted_argv():
    oracle = _oracle_module()
    rows = json.loads((ROOT / "tests/fixtures/guard_bash_oracle.json").read_text())["rows"]
    rows = [row for row in rows if row["family"] == "9490-prefix"]
    report = oracle.run_oracle(rows=rows, traffic=[])
    assert report["totals"]["observed_argv_rows"] == len(rows) == 50
    assert report["totals"]["misses"] == 0
    with patch.object(oracle, "read_commands", return_value=[]):
        report = oracle.run_oracle(rows=rows, traffic=[])
    assert report["totals"]["misses"] == len(rows)


def test_oracle_rejects_a_judged_directory_mismatch():
    oracle = _oracle_module()
    rows = json.loads((ROOT / "tests/fixtures/guard_bash_oracle.json").read_text())["rows"]
    rows = [row for row in rows if row["family"] == "9480-consecutive-cd"]
    original_load = oracle.load_hook

    def mutant(name):
        module = original_load(name)
        if name == "guard-pr-merge":
            from dataclasses import replace

            original_read = module.read_commands
            module.read_commands = lambda command, cwd=None, **kwargs: [
                replace(inv, cwd=cwd) for inv in original_read(command, cwd=cwd, **kwargs)
            ]
        return module

    with patch.object(oracle, "load_hook", mutant):
        report = oracle.run_oracle(rows=rows, traffic=[])
    assert report["totals"]["misses"] == len(rows) == 3


@pytest.mark.parametrize("hook", ["guard-pr-merge.py", "guard-admin-merge.py", "guard-branch-switch-in-main.py"])
@pytest.mark.parametrize("dependency", ["shell_bash", "tree_sitter", "tree_sitter_bash"])
@pytest.mark.parametrize("failure", ["missing", "raises"])
def test_dependency_failure_is_narrow_and_actionable(hook, dependency, failure):
    bootstrap = """
import builtins,runpy,sys
original=builtins.__import__
def failing(name,*args,**kwargs):
    if name==sys.argv[2]:
        raise ImportError("fixture missing") if sys.argv[3]=="missing" else RuntimeError("fixture raises")
    return original(name,*args,**kwargs)
builtins.__import__=failing
runpy.run_path(sys.argv[1],run_name="__main__")
"""
    for command, expected in [("git switch -c fixture && gh pr merge 5 --admin", 2), ("git status", 0)]:
        result = subprocess.run(
            [sys.executable, "-c", bootstrap, str(HOOKS / hook), dependency, failure],
            input=json.dumps({"tool_input": {"command": command}}),
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == expected, result.stderr
        if expected:
            assert "guard dependency unavailable: shell_bash" in result.stderr
            assert "repair:" in result.stderr and "requirements-hooks.txt" in result.stderr
            assert "Traceback" not in result.stderr


@pytest.mark.parametrize("hook", ["guard-pr-merge.py", "guard-admin-merge.py", "guard-branch-switch-in-main.py"])
def test_wrong_interpreter_cannot_allow_guarded_command(hook):
    # This is the intentional wrong-interpreter failure probe, not a project run.
    wrong = shutil.which("python3", path="/usr/bin:/bin")
    assert wrong
    for command, expected in [("git switch -c fixture && gh pr merge 5 --admin", 2), ("git status", 0)]:
        result = subprocess.run(
            [wrong, str(HOOKS / hook)],
            input=json.dumps({"tool_input": {"command": command}}),
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == expected, result.stderr
        assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "row", json.loads((ROOT / "tests/fixtures/guard_bash_oracle.json").read_text())["rows"], ids=lambda row: row["id"]
)
def test_corpus_is_parsed_or_explicitly_refused(row):
    try:
        invocations = read_commands(row["command"])
    except ShellParseError as exc:
        assert str(exc)
    else:
        assert all(inv.argv and isinstance(inv.argv, list) for inv in invocations)


def test_cd_failure_and_logical_symlink_parent(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "deep").mkdir()
    (tmp_path / "link").symlink_to(tmp_path / "a" / "deep", target_is_directory=True)
    logical = read_commands("cd link/..; gh pr merge 5", cwd=str(tmp_path))
    physical = read_commands("cd -P link/..; gh pr merge 5", cwd=str(tmp_path))
    failed = read_commands("cd missing; gh pr merge 5", cwd=str(tmp_path))
    assert logical[-1].cwd == str(tmp_path)
    assert physical[-1].cwd == str(tmp_path / "a")
    assert failed[-1].cwd == str(tmp_path)


@pytest.mark.parametrize("chdir", ["-C link/..", "-Clink/..", "--chdir=link/.."])
def test_eval_and_env_directory_scope(tmp_path, chdir):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "deep").mkdir()
    (tmp_path / "link").symlink_to(tmp_path / "a" / "deep", target_is_directory=True)
    evaluated = read_commands("eval 'cd a'; gh pr merge 5", cwd=str(tmp_path))
    wrapped = read_commands(f"env {chdir} gh pr merge 5; gh pr merge 6", cwd=str(tmp_path))
    assert evaluated[-1].cwd == str(tmp_path / "a")
    assert wrapped[0].cwd == str(tmp_path / "a")
    assert wrapped[-1].cwd == str(tmp_path)


def test_cd_option_order_and_unknown_directory_stack(tmp_path):
    from shell_bash import cd_target

    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "deep").mkdir()
    (tmp_path / "link").symlink_to(tmp_path / "a" / "deep", target_is_directory=True)
    assert cd_target(["cd", "-LP", "link/.."], str(tmp_path)) == str(tmp_path / "a")
    assert cd_target(["cd", "-PL", "link/.."], str(tmp_path)) == str(tmp_path)
    assert cd_target(["cd", "--unknown", "a"], str(tmp_path)) is None
    assert read_commands("pushd +1; gh pr merge 5", cwd=str(tmp_path))[-1].cwd is None


@pytest.mark.parametrize("prefix,suffix", [("(", ")"), ("echo $(", ")"), ("cat <(", ")")])
def test_nested_cd_is_sequential_but_not_exported(tmp_path, prefix, suffix):
    (tmp_path / "a").mkdir()
    rows = read_commands(prefix + "cd a; gh pr merge 5" + suffix + "; gh pr merge 6", cwd=str(tmp_path))
    merges = [row for row in rows if row.argv[:3] == ["gh", "pr", "merge"]]
    assert [row.cwd for row in merges] == [str(tmp_path / "a"), str(tmp_path)]


def test_dynamic_wrapper_directory_refuses():
    with pytest.raises(ShellParseError, match="dynamic wrapper argument"):
        read_commands('env -C "$P" gh pr merge 5')


@pytest.mark.parametrize(
    "command",
    [
        "f(){ cd ..; }; f; gh pr merge 5",
        "f(){ gh pr merge 5; }; f",
        'f(){ "$@"; }; f gh pr merge 5',
        "inner(){ cd ..; }; outer(){ inner; }; outer; gh pr merge 5",
        "f(){ f; }; f; gh pr merge 5",
    ],
)
def test_called_functions_are_refused_at_execution_site(command):
    with pytest.raises(ShellParseError, match="called function"):
        read_commands(command)


def test_uncalled_function_definition_is_inert():
    rows = read_commands("f(){ gh pr merge 5; }; printf benign")
    assert [row.argv for row in rows] == [["printf", "benign"]]


@pytest.mark.parametrize(
    "command",
    [
        "trap 'gh pr merge 5' EXIT",
        "printf 'gh pr merge 5' | sh",
        "sh <<< 'gh pr merge 5'",
        "find . -exec gh pr merge 5 \\;",
        "xargs gh pr merge 5",
        "setsid gh pr merge 5",
        "flock lock gh pr merge 5",
        "ionice gh pr merge 5",
        "env -S 'gh pr merge 5'",
        "sudo -D /tmp gh pr merge 5",
    ],
)
def test_visible_deferred_payload_is_judged_or_refused(command):
    try:
        rows = read_commands(command)
    except ShellParseError as exc:
        assert str(exc)
    else:
        assert any(row.argv[:3] == ["gh", "pr", "merge"] for row in rows)


def test_shell_option_and_loop_state_are_unknown_before_operation(tmp_path):
    (tmp_path / "a").mkdir()
    for command in [
        "set -P; gh pr merge 5",
        "shopt -s lastpipe; true | cd a; gh pr merge 5",
        "for i in 1 2; do gh pr merge 5; cd a; done",
    ]:
        rows = read_commands(command, cwd=str(tmp_path))
        assert any(row.cwd_unreadable for row in rows if row.argv[:3] == ["gh", "pr", "merge"])


def test_work_limit_is_an_explicit_refusal(monkeypatch):
    import shell_bash

    monkeypatch.setattr(shell_bash, "MAX_WORK", 2)
    with pytest.raises(ShellParseError, match="work limit"):
        read_commands("true; gh pr merge 5")


@pytest.mark.parametrize("text", ["gh pr merge 5", r"gh pr m\erge 5", "g'h' pr 'merge' 5", r"gh pr $'\x6d\x65rge' 5"])
def test_visible_payload_gate_preserves_shell_spellings(text):
    from shell_bash import operation_candidate

    assert operation_candidate(text)
    assert not operation_candidate("git status")


@pytest.mark.parametrize("option", ["set -P", "shopt -s cdspell"])
def test_absolute_cd_cannot_reset_unknown_shell_option_semantics(tmp_path, option):
    rows = read_commands(f"{option}; cd {tmp_path}; gh pr merge 5")
    assert rows[-1].cwd_unreadable


def test_ambiguous_merge_directory_never_selects_one_target(tmp_path):
    (tmp_path / "a").mkdir()
    rows = read_commands("if false; then cd a; fi; gh pr merge 5", cwd=str(tmp_path))
    merges = [row for row in rows if row.argv[:3] == ["gh", "pr", "merge"]]
    assert len(merges) == 1 and merges[0].cwd_unreadable


def test_oracle_rejects_wrong_pr_target_even_when_blocking():
    from dataclasses import replace

    oracle = _oracle_module()
    original_load = oracle.load_hook

    def mutant(name):
        module = original_load(name)
        if name == "guard-pr-merge":
            original_read = module.read_commands
            module.read_commands = lambda command, cwd=None, **kwargs: [
                replace(inv, argv=["gh", "pr", "merge", "6"]) for inv in original_read(command, cwd=cwd, **kwargs)
            ]
        return module

    row = dict(id="wrong-target", family="held-out-mutation", command="gh pr merge 5", hook="merge", accepted=False)
    with patch.object(oracle, "load_hook", mutant):
        report = oracle.run_oracle(rows=[row], traffic=[])
    assert report["totals"]["misses"] == 1


@pytest.mark.parametrize(
    "command",
    [
        "env sudo -C 3 gh pr merge 5",
        "env -u -C gh pr merge 5",
        "sudo -p env gh pr merge 5",
    ],
)
def test_wrapper_option_values_cannot_change_another_wrappers_directory(command, tmp_path):
    rows = read_commands(command, cwd=str(tmp_path))
    assert rows[-1].cwd == str(tmp_path)


def test_wrapper_scopes_are_explicit_and_xargs_stops_unwrapping():
    from shell_bash import wrapper_scopes

    assert wrapper_scopes(["env", "-C", "a", "sudo", "-C", "3", "gh"]) == (
        6,
        [("env", ["-C", "a"]), ("sudo", ["-C", "3"])],
    )
    assert wrapper_scopes(["xargs", "gh", "pr", "merge", "5"]) == (0, [])


@pytest.mark.parametrize(
    "command",
    [
        'x="gh pr merge 5"; trap "$x" EXIT',
        "f(){ gh pr merge 5; }; trap f EXIT",
        'x="gh pr merge 5"; find file -exec bash -c "$x" \\;',
        "shopt -s expand_aliases\nalias f='gh pr merge 5'\nf",
        "hash -p /fixture/gh f; f pr merge 5",
        "BASH_CMDS[f]=/fixture/gh; f pr merge 5",
    ],
)
def test_visible_payload_cannot_hide_behind_deferred_binding(command):
    with pytest.raises(ShellParseError):
        read_commands(command)


@pytest.mark.parametrize("utility", ["python", "python3", "python3.12"])
def test_publisher_name_as_data_does_not_exempt_indirect_code(utility):
    with pytest.raises(ShellParseError, match="indirect execution"):
        read_commands(utility + " -c 'execute(gh, pr, merge, 5)' scripts.publish")


def test_inherited_lastpipe_cannot_prove_parent_directory(monkeypatch):
    monkeypatch.setenv("BASHOPTS", "lastpipe")
    rows = read_commands("true | cd ..; gh pr merge 5")
    assert rows[-1].cwd_unreadable


def test_filesystem_mutation_invalidates_absolute_repository_probe(tmp_path):
    rows = read_commands(f"ln -sfn primary alias; git -C {tmp_path} checkout -b fixture")
    assert rows[-1].repository_unknown


@pytest.mark.parametrize("fault", ["selector", "directory"])
def test_oracle_admin_judgments_must_match_gold_target_and_actual_directory(fault):
    from dataclasses import replace

    oracle = _oracle_module()
    original_load = oracle.load_hook

    def mutant(name):
        module = original_load(name)
        if name == "guard-admin-merge":
            if fault == "selector":
                module._pr_number = lambda args: "6"
            else:
                original_read = module.read_commands
                module.read_commands = lambda command, cwd=None, **kwargs: [
                    replace(inv, cwd=str(Path(cwd) / ".worktrees/wt"))
                    for inv in original_read(command, cwd=cwd, **kwargs)
                ]
        return module

    row = dict(
        id="admin-wrong-target",
        family="held-out-mutation",
        command="gh pr merge 5 --admin",
        hook="admin",
        accepted=False,
        oracle_pr="5",
    )
    with patch.object(oracle, "load_hook", mutant):
        report = oracle.run_oracle(rows=[row], traffic=[])
    assert report["totals"]["misses"] == 1


@pytest.mark.parametrize(
    "command, argv",
    [
        ("g\\\nit checkout -b fixture", ["git", "checkout", "-b", "fixture"]),
        ("git check\\\nout -b fixture", ["git", "checkout", "-b", "fixture"]),
        ("gh pr mer\\\nge 5", ["gh", "pr", "merge", "5"]),
        ("gh pr merge 5 --ad\\\nmin", ["gh", "pr", "merge", "5", "--admin"]),
        ("printf '%s' 'g\\\nit'", ["printf", "%s", "g\\\nit"]),
    ],
)
def test_line_continuations_join_executed_words_and_preserve_quoted_data(command, argv):
    assert read_commands(command)[-1].argv == argv


@pytest.mark.parametrize(
    "command",
    [
        "strace gh pr merge 5",
        "script -qc 'gh pr merge 5' fixture",
        "numactl --localalloc git checkout -b fixture",
        "systemd-run --scope gh pr merge 5",
        "uv run --no-project gh pr merge 5",
        "git bisect run gh pr merge 5",
        'f(){ git "$@"; }; f checkout -b fixture',
        'f(){ gh "$1" merge 5; }; f pr',
        'command -p "$candidate" pr merge 5',
        "command -p gh pr merge 5",
    ],
)
def test_review_executor_and_forwarding_forms_fail_closed(command):
    with pytest.raises(ShellParseError):
        read_commands(command)


@pytest.mark.parametrize("hook", ["guard-pr-merge", "guard-admin-merge"])
@pytest.mark.parametrize(
    "command, selector, repository",
    [
        ("gh pr merge --subject 7 5 --admin", "5", None),
        ("gh pr merge -t 7 5 --admin", "5", None),
        ("gh pr merge 5 --repo=fixture/other --admin", "5", "fixture/other"),
        ("GH_REPO=fixture/other gh pr merge 5 --admin", "5", "fixture/other"),
        ("GH_REPO=fixture/other gh pr merge 5 -R fixture/explicit --admin", "5", "fixture/explicit"),
    ],
)
def test_merge_target_options_and_environment_reach_the_judged_identity(hook, command, selector, repository, tmp_path):
    import io

    module = _oracle_module().load_hook(hook)
    seen = []
    if hook == "guard-pr-merge":

        def judge(args, cwd=None, repo=None):
            seen.append((module._pr_selector(args), module._repo_option(args) or repo, cwd))
            return "fixture red check"

        patches = patch.object(module, "_judge", judge)
    else:

        def checks(pr, cwd=None, repo=None):
            seen.append((pr, repo, cwd))
            return ["fixture red check"]

        patches = patch.object(module, "_failing_blocking_checks", checks)
    payload = {"cwd": str(tmp_path), "tool_input": {"command": command}}
    with patches, patch.object(sys, "stdin", io.StringIO(json.dumps(payload))):
        assert module.main() == 2
    assert seen == [(selector, repository, str(tmp_path))]


@pytest.mark.parametrize("hook", ["guard-pr-merge", "guard-admin-merge"])
def test_url_selector_and_repository_conflict_never_lookup_another_target(hook):
    rows = json.loads((ROOT / "tests/fixtures/guard_bash_oracle.json").read_text())["rows"]
    oracle = _oracle_module()
    selected = [
        row
        for row in rows
        if row["family"] in {"target-identity", "target-conflict"}
        and row["hook"] == ("merge" if hook == "guard-pr-merge" else "admin")
    ]
    report = oracle.run_oracle(rows=selected, traffic=[])
    assert report["totals"]["wrong_target_judgments"] == 0
    assert report["totals"]["missing_target_judgments"] == 0
    assert report["totals"]["expected_mismatches"] == 0


def test_stopped_paths_and_false_loops_do_not_emit_guarded_invocations(tmp_path):
    assert not any(
        row.argv[:2] == ["git", "checkout"]
        for row in read_commands("cd missing || exit; git checkout -b fixture", cwd=str(tmp_path))
    )
    assert read_commands("while false; do gh pr merge 5; done", cwd=str(tmp_path)) == []
    assert any(
        row.argv[:3] == ["gh", "pr", "merge"]
        for row in read_commands("until false; do gh pr merge 5; break; done", cwd=str(tmp_path))
    )


def test_directory_only_function_tracking_is_explicit_and_literal(tmp_path):
    (tmp_path / "other").mkdir()
    command = "f(){ cd other; }; f; git checkout -b fixture"
    with pytest.raises(ShellParseError, match="called function"):
        read_commands(command, cwd=str(tmp_path))
    rows = read_commands(command, cwd=str(tmp_path), follow_directory_functions=True)
    assert rows[-1].cwd == str(tmp_path / "other")
    with pytest.raises(ShellParseError, match="called function"):
        read_commands(
            'f(){ cd "$target"; }; f; git checkout -b fixture', cwd=str(tmp_path), follow_directory_functions=True
        )


def test_home_override_uses_only_an_unmodified_inherited_parameter(tmp_path, monkeypatch):
    monkeypatch.setenv("FIXTURE_ROOT", str(tmp_path))
    (tmp_path / "other").mkdir()
    rows = read_commands('HOME="$FIXTURE_ROOT/other" cd && git checkout -b fixture', cwd=str(tmp_path))
    assert rows[-1].cwd == str(tmp_path / "other")
    rows = read_commands(
        'FIXTURE_ROOT=unknown; HOME="$FIXTURE_ROOT/other" cd && git checkout -b fixture', cwd=str(tmp_path)
    )
    assert rows[-1].cwd_unreadable


@pytest.mark.parametrize("hook", ["guard-pr-merge", "guard-admin-merge", "guard-branch-switch-in-main"])
def test_read_only_pipeline_with_temporary_redirect_remains_data(hook, tmp_path):
    import io

    module = _oracle_module().load_hook(hook)
    payload = {"cwd": str(tmp_path), "tool_input": {"command": "gh pr view 5 --json mergeable > $(mktemp) | cat"}}
    with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))):
        assert module.main() == 0


def test_dynamic_cd_redirect_tracks_success_without_changing_repository(tmp_path):
    (tmp_path / "other").mkdir()
    consumer = _oracle_module().load_hook("guard-branch-switch-in-main")._check_consumer
    rows = read_commands(
        'cd other 2>"$(mktemp)" && git checkout -b fixture', cwd=str(tmp_path), consumer_check=consumer
    )
    assert rows[-1].cwd == str(tmp_path / "other")
    assert not rows[-1].repository_unknown


@pytest.mark.parametrize("binding", ["unset -f f", "enable -n cd"])
def test_directory_function_binding_mutation_cannot_license_an_operation(tmp_path, binding):
    (tmp_path / "other").mkdir()
    with pytest.raises(ShellParseError, match="binding"):
        read_commands(
            f"f(){{ cd other; }}; {binding}; f; git checkout -b fixture",
            cwd=str(tmp_path),
            follow_directory_functions=True,
        )


@pytest.mark.parametrize("shell", ["sh", "bash"])
def test_command_local_repository_cannot_be_lost_in_a_nested_shell(shell):
    with pytest.raises(ShellParseError, match="repository environment"):
        read_commands(f"GH_REPO=fixture/other {shell} -c 'gh pr merge 5'")
