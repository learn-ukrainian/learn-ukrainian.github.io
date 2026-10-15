"""Bash AST guards and retained lexical consumer contracts (#9484/#9480)."""

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
from shell_redirects import command_repository_unknown, preprocess_branch_command, scope_events, unmodeled_shell_offset
from shell_shlex import ShellPreprocessLimit, preprocess_shell_command


def test_pinned_real_bash_oracle():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/hooks/bash_oracle.py")], capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["pins"] == {"tree-sitter": "0.26.0", "tree-sitter-bash": "0.25.1"}
    assert report["totals"]["misses"] == 0
    assert report["totals"]["rows"] == 1517
    assert report["totals"]["expected_rows"] == 915
    assert report["totals"]["overblocks"] == 14
    assert report["totals"]["expected_matches"] == 914
    assert report["totals"]["expected_mismatches"] == 1
    assert report["scored_totals"]["rows"] == 1507
    assert report["scored_totals"]["expected_matches"] == report["scored_totals"]["expected_rows"] == 914
    assert report["scored_totals"]["expected_mismatches"] == 0
    assert report["scored_totals"]["overblocks"] <= 4
    assert report["known_main_overblock_count"] == 10
    assert all(row["blocked"] and not row["expected_match"] for row in report["known_main_overblocks"])
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


def _merge_operation(argv):
    """The merge hook's own operation predicate, as `guard-pr-merge` passes it to the reader."""
    return _oracle_module().load_hook("guard-pr-merge")._merge_args(argv) is not None


def _hook_exit(hook, command, cwd):
    """Run one guard hook's `main()` with every judge reporting a red check."""
    import io

    module = _oracle_module().load_hook(hook)
    payload = {"cwd": str(cwd), "tool_input": {"command": command}}
    with (
        patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
        patch.object(module, "_judge", return_value="fixture red check", create=True),
        patch.object(module, "_failing_blocking_checks", return_value=["fixture red check"], create=True),
    ):
        return module.main()


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
    # The `9480-consecutive-cd` rows now refuse (ruling item 4), so no directory is
    # judged there; the one admitted `cd <literal> &&` form carries the judged cwd.
    rows = [
        dict(
            id=f"held-out-leading-cd-{index}", family="held-out-mutation", command=command, hook="merge", accepted=False
        )
        for index, command in enumerate(
            ["cd wt && gh pr merge 5", "cd link && gh pr merge 5", "cd wt && gh pr merge 5 | cat"]
        )
    ]
    assert oracle.run_oracle(rows=rows, traffic=[])["totals"]["misses"] == 0
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
    logical = read_commands("cd link/.. && gh pr merge 5", cwd=str(tmp_path))
    assert logical[-1].cwd == str(tmp_path)
    # Ruling item 4: only one leading `cd <literal> &&` is admitted; `;`, `-P` and a failing cd refuse.
    for command in ("cd link/..; gh pr merge 5", "cd -P link/.. && gh pr merge 5", "cd missing && gh pr merge 5"):
        with pytest.raises(ShellParseError) as refused:
            read_commands(command, cwd=str(tmp_path))
        assert refused.value.reason_class == "UNKNOWN_CONTEXT"


@pytest.mark.parametrize("chdir", ["-C link/..", "-Clink/..", "--chdir=link/.."])
def test_eval_and_env_directory_scope(tmp_path, chdir):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "deep").mkdir()
    (tmp_path / "link").symlink_to(tmp_path / "a" / "deep", target_is_directory=True)
    # Ruling item 4: `eval` before the merge operation refuses.
    with pytest.raises(ShellParseError) as refused:
        read_commands("eval 'cd a'; gh pr merge 5", cwd=str(tmp_path), operation=_merge_operation)
    assert refused.value.reason_class == "UNKNOWN_EXECUTOR"
    wrapped = read_commands(f"env {chdir} gh pr merge 5; gh pr merge 6", cwd=str(tmp_path))
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
    # Ruling item 4: `pushd` before a guarded operation refuses.
    with pytest.raises(ShellParseError) as refused:
        read_commands("pushd +1; gh pr merge 5", cwd=str(tmp_path))
    assert refused.value.reason_class == "UNKNOWN_CONTEXT"


@pytest.mark.parametrize("prefix,suffix", [("(", ")"), ("echo $(", ")"), ("cat <(", ")")])
def test_nested_cd_is_sequential_but_not_exported(tmp_path, prefix, suffix):
    (tmp_path / "a").mkdir()
    # Ruling item 3: a guarded operation inside a subshell or substitution refuses.
    with pytest.raises(ShellParseError, match="compound construct"):
        read_commands(prefix + "cd a; gh pr merge 5" + suffix + "; gh pr merge 6", cwd=str(tmp_path))


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
    with pytest.raises(ShellParseError, match=r"called function|shell function|forwarded arguments"):
        read_commands(command)


def test_uncalled_function_definition_with_operation_text_refuses():
    # Ruling item 3: any function definition beside operation-shaped text refuses.
    from shell_bash import ShellDefinitionError

    with pytest.raises(ShellDefinitionError) as refused:
        read_commands("f(){ gh pr merge 5; }; printf benign")
    assert refused.value.reason_class == "ALIAS_EXECUTION"


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
        "sudo -D . gh pr merge 5",
    ],
)
def test_visible_deferred_payload_is_judged_or_refused(command, tmp_path):
    try:
        rows = read_commands(command)
    except ShellParseError as exc:
        assert str(exc)
    else:
        # Closed allowlist (#10521): an unmodelled wrapper keeps its whole argv,
        # so the merge text stays visible and the merge hook refuses it.
        assert any(row.argv[-4:-1] == ["gh", "pr", "merge"] for row in rows)
        assert _hook_exit("guard-pr-merge", command, tmp_path) == 2


def test_shell_option_and_loop_state_are_unknown_before_operation(tmp_path):
    (tmp_path / "a").mkdir()
    # Ruling items 3-5: shell options, pipelines and loops before or around the merge refuse.
    for command in [
        "set -P; gh pr merge 5",
        "shopt -s lastpipe; true | cd a; gh pr merge 5",
        "for i in 1 2; do gh pr merge 5; cd a; done",
    ]:
        with pytest.raises(ShellParseError):
            read_commands(command, cwd=str(tmp_path), operation=_merge_operation)


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
    # Ruling items 4/5: a shell option or `cd ;` before the merge refuses.
    with pytest.raises(ShellParseError):
        read_commands(f"{option}; cd {tmp_path}; gh pr merge 5")


def test_ambiguous_merge_directory_never_selects_one_target(tmp_path):
    (tmp_path / "a").mkdir()
    # Ruling item 3: a compound construct before the merge refuses.
    with pytest.raises(ShellParseError) as refused:
        read_commands("if false; then cd a; fi; gh pr merge 5", cwd=str(tmp_path))
    assert refused.value.reason_class == "UNKNOWN_CONTEXT"


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
def test_publisher_name_as_data_does_not_exempt_indirect_code(utility, tmp_path):
    # The refusal moved to the merge hook's consumer check (#10521 closed allowlist).
    command = utility + " -c 'execute(gh, pr, merge, 5)' scripts.publish"
    merge = _oracle_module().load_hook("guard-pr-merge")
    with pytest.raises(ShellParseError, match=r"indirect execution|unknown consumer"):
        read_commands(
            command,
            cwd=str(tmp_path),
            operation=_merge_operation,
            consumer_check=lambda *args: merge._check_consumer(*args, eval_guarded=True),
        )
    assert _hook_exit("guard-pr-merge", command, tmp_path) == 2


def test_inherited_lastpipe_cannot_prove_parent_directory(monkeypatch):
    monkeypatch.setenv("BASHOPTS", "lastpipe")
    # Ruling item 4: a pipeline `cd` before the merge refuses.
    with pytest.raises(ShellParseError):
        read_commands("true | cd ..; gh pr merge 5")


def test_filesystem_mutation_invalidates_absolute_repository_probe(tmp_path):
    # Ruling item 4: a filesystem mutation before the branch operation refuses.
    branch = _oracle_module().load_hook("guard-branch-switch-in-main")
    with pytest.raises(ShellParseError) as refused:
        read_commands(
            f"ln -sfn primary alias; git -C {tmp_path} checkout -b fixture",
            cwd=str(tmp_path),
            operation=branch._branch_operation,
            consumer_check=branch._check_consumer,
        )
    assert refused.value.reason_class == "UNKNOWN_EXECUTOR"


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
    "command, hooks",
    [
        ("strace gh pr merge 5", ["guard-pr-merge"]),
        ("script -qc 'gh pr merge 5' fixture", ["guard-pr-merge"]),
        ("numactl --localalloc git checkout -b fixture", ["guard-branch-switch-in-main", "guard-pr-merge"]),
        ("systemd-run --scope gh pr merge 5", ["guard-pr-merge"]),
        ("uv run --no-project gh pr merge 5", ["guard-pr-merge"]),
    ],
)
def test_review_executors_are_refused_by_the_hooks(command, hooks, tmp_path):
    # The closed-allowlist reader keeps an unmodelled executor's whole argv; the
    # hook's consumer check now refuses the visible operation text (#10521).
    for hook in hooks:
        assert _hook_exit(hook, command, tmp_path) == 2


@pytest.mark.parametrize(
    "command",
    [
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


@pytest.mark.parametrize("prefix", ["", "exit(){ :; }; ", "cd(){ :; }; "])
def test_cd_or_exit_keeps_the_continuation_in_the_failed_cd_state(tmp_path, prefix):
    """A function can shadow `exit` or `cd`, so `|| exit` never ends analysis (#10521 ruling)."""
    # Ruling items 1/3/4: `cd ... || exit` is no longer modelled; with or without a definition it refuses.
    with pytest.raises(ShellParseError) as refused:
        read_commands(prefix + "cd missing || exit; git checkout -b fixture", cwd=str(tmp_path))
    assert refused.value.reason_class in {"UNKNOWN_CONTEXT", "ALIAS_EXECUTION"}


def test_loops_with_guarded_operations_refuse(tmp_path):
    # Ruling items 1/3: loops are no longer modelled; a merge inside one refuses.
    for command in ("while false; do gh pr merge 5; done", "until false; do gh pr merge 5; break; done"):
        with pytest.raises(ShellParseError, match="compound construct"):
            read_commands(command, cwd=str(tmp_path))


def test_directory_only_function_tracking_is_explicit_and_literal(tmp_path):
    from shell_bash import ShellDefinitionError

    (tmp_path / "other").mkdir()
    # Ruling items 1/3: function modelling is deleted; a directory function beside the operation refuses.
    for command in ("f(){ cd other; }; f; git checkout -b fixture", 'f(){ cd "$target"; }; f; git checkout -b fixture'):
        with pytest.raises(ShellDefinitionError) as refused:
            read_commands(command, cwd=str(tmp_path))
        assert refused.value.reason_class == "ALIAS_EXECUTION"


def test_home_override_uses_only_an_unmodified_inherited_parameter(tmp_path, monkeypatch):
    monkeypatch.setenv("FIXTURE_ROOT", str(tmp_path))
    (tmp_path / "other").mkdir()
    # Ruling item 4: only a plain `cd <literal> &&` is admitted; a HOME-driven `cd` refuses.
    for command in (
        'HOME="$FIXTURE_ROOT/other" cd && git checkout -b fixture',
        'FIXTURE_ROOT=unknown; HOME="$FIXTURE_ROOT/other" cd && git checkout -b fixture',
    ):
        with pytest.raises(ShellParseError) as refused:
            read_commands(command, cwd=str(tmp_path))
        assert refused.value.reason_class == "UNKNOWN_CONTEXT"


@pytest.mark.parametrize("hook", ["guard-pr-merge", "guard-admin-merge", "guard-branch-switch-in-main"])
def test_read_only_pipeline_preserves_main_blocks_by_hook(hook, tmp_path):
    import io

    module = _oracle_module().load_hook(hook)
    payload = {"cwd": str(tmp_path), "tool_input": {"command": "gh pr view 5 --json mergeable > $(mktemp) | cat"}}
    with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))):
        assert module.main() == (2 if hook == "guard-pr-merge" else 0)


def test_dynamic_cd_redirect_tracks_success_without_changing_repository(tmp_path):
    (tmp_path / "other").mkdir()
    consumer = _oracle_module().load_hook("guard-branch-switch-in-main")._check_consumer
    # Ruling item 4: the leading `cd` must be a plain literal; a substituted redirect refuses.
    with pytest.raises(ShellParseError) as refused:
        read_commands('cd other 2>"$(mktemp)" && git checkout -b fixture', cwd=str(tmp_path), consumer_check=consumer)
    assert refused.value.reason_class == "UNKNOWN_CONTEXT"


@pytest.mark.parametrize("binding", ["unset -f f", "enable -n cd"])
def test_directory_function_binding_mutation_cannot_license_an_operation(tmp_path, binding):
    (tmp_path / "other").mkdir()
    # `enable` is a builtin override: the #10521 definition refusal names it.
    with pytest.raises(ShellParseError, match=r"binding|builtin override|changes what later words run") as refused:
        read_commands(f"f(){{ cd other; }}; {binding}; f; git checkout -b fixture", cwd=str(tmp_path))
    assert refused.value.reason_class == "ALIAS_EXECUTION"


@pytest.mark.parametrize("shell", ["sh", "bash"])
def test_command_local_repository_cannot_be_lost_in_a_nested_shell(shell):
    # Ruling item 3: a guarded operation inside a shell `-c` payload refuses.
    with pytest.raises(ShellParseError, match=r"repository environment|compound construct"):
        read_commands(f"GH_REPO=fixture/other {shell} -c 'gh pr merge 5'")


@pytest.mark.parametrize("option", ["+c", "+xc", "+cx"])
@pytest.mark.parametrize("trailing", [[], ["-c", "printf second"]])
def test_plus_command_option_selects_first_payload(option, trailing):
    result = subprocess.run(["bash", option, "printf first", *trailing], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "first"
    suffix = " -c 'echo harmless'" if trailing else ""
    # Ruling item 3: a guarded operation inside a shell payload refuses.
    with pytest.raises(ShellParseError, match="compound construct"):
        read_commands(f"bash {option} 'gh pr merge 5 --admin'{suffix}")


@pytest.mark.parametrize("hook", ["guard-pr-merge", "guard-admin-merge"])
@pytest.mark.parametrize("option", ["+c", "+xc", "+cx"])
def test_plus_command_payload_cannot_bypass_merge_guards(hook, option, tmp_path):
    import io

    module = _oracle_module().load_hook(hook)
    command = f"bash {option} 'gh pr merge 5 --admin' -c 'echo harmless'"
    payload = {"cwd": str(tmp_path), "tool_input": {"command": command}}
    if hook == "guard-pr-merge":
        judge = patch.object(module, "_judge", return_value="fixture red check")
    else:
        judge = patch.object(module, "_failing_blocking_checks", return_value=["fixture red check"])
    with judge as seen, patch.object(sys, "stdin", io.StringIO(json.dumps(payload))):
        assert module.main() == 2
    # Ruling item 3: the payload merge is refused before any check is judged.
    seen.assert_not_called()


@pytest.mark.parametrize(
    "arguments, reason",
    [
        ("+co fixture 'gh pr merge 5' -c 'echo harmless'", "packed shell"),
        # Ruling item 5: a shell started with `shopt` options refuses unconditionally.
        ("+cO fixture 'gh pr merge 5' -c 'echo harmless'", r"packed shell|`shopt` options"),
        ("+c -x 'gh pr merge 5' -c 'echo harmless'", "shell options"),
    ],
)
def test_plus_command_options_with_unknown_payload_fail_closed(arguments, reason):
    with pytest.raises(ShellParseError, match=reason):
        read_commands(f"bash {arguments}")


def test_plus_command_dynamic_payload_refuses_when_operation_text_is_visible():
    """A dynamic `+c` payload refuses once the command spells an operation (#10521).

    With no operation text anywhere in the command, the payload's value comes from
    outside the command line: an encoded payload or harness state, which the frozen
    threat model records as a residual rather than a reader input.
    """
    with pytest.raises(ShellParseError, match="dynamic shell payload") as refusal:
        read_commands("payload='gh pr merge 5'; bash +c \"$payload\" -c 'echo harmless'")
    assert refusal.value.reason_class == "DYNAMIC_COMMAND"
    assert [row.argv[:2] for row in read_commands("bash +c")] == [["bash", "+c"]]


@pytest.mark.parametrize("repetitions", [16, 28])
def test_unterminated_heredoc_backticks_finish_within_existing_ceiling(repetitions):
    code = (
        "import sys; sys.path.insert(0, 'agents_extensions/shared/hooks'); "
        "from shell_bash import read_commands; "
        "read_commands('cat <<EOF\\n`' + '\\\\_' * int(sys.argv[1]) + '\\nEOF\\ngh pr merge 5')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(repetitions)], cwd=ROOT, capture_output=True, text=True, timeout=0.5
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("body", ["`gh pr merge 5`", "`gh pr \\\nmerge 5`", "`gh pr merge 5 --admin`"])
def test_heredoc_backticks_preserve_escaped_newline_and_merge_extraction(body):
    # Ruling item 3: a merge inside a heredoc command substitution refuses.
    with pytest.raises(ShellParseError, match="compound construct"):
        read_commands(f"cat <<EOF\n{body}\nEOF")


@pytest.mark.parametrize(
    "command",
    [
        'o=-b; git checkout "$o" fixture',
        "find file -exec git checkout -b fixture \\;",
        'x="gh pr merge 5 --admin"; trap "$x" EXIT',
        "gh pr merge 5 --ad\\\nmin",
        "gh pr merge 5 --$ADMIN",
        'x="gh pr view 5"; read x; trap "$x" EXIT',
        'x="gh pr view 5"; x="gh pr merge 5 --admin"; trap "$x" EXIT',
    ],
)
@pytest.mark.parametrize("hook", ["guard-pr-merge", "guard-admin-merge"])
def test_scope_boundary_keeps_opaque_options_and_executable_payloads(command, hook, tmp_path):
    import io

    module = _oracle_module().load_hook(hook)
    payload = {"cwd": str(tmp_path), "tool_input": {"command": command}}
    with (
        patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
        patch.object(module, "_judge", return_value="fixture red check", create=True),
        patch.object(module, "_failing_blocking_checks", return_value=["fixture red check"], create=True),
    ):
        assert module.main() == 2


# Removed with outside_merge_scope by the #10521 closed-allowlist ruling.


_DYNAMIC_WORKTREE_MERGES = [
    "m='gh pr merge 5 --subject'; $m worktree",
    "m='gh pr merge 5 --admin --subject'; $m worktree",
]
# The literal `pr view` arguments do not prove the dynamic executable is a
# read-only `gh pr view`; here `pr` is the merge subject (#10521 F6).
_DYNAMIC_PR_VIEW_MERGES = [
    "m='gh pr merge --subject'; $m pr view",
    "m='gh pr merge --admin --subject'; $m pr view",
]


@pytest.mark.parametrize("command", _DYNAMIC_WORKTREE_MERGES + _DYNAMIC_PR_VIEW_MERGES)
def test_dynamic_executable_worktree_shape_stays_in_merge_scope(command, tmp_path):
    # The branch hook engages only on `worktree add`, so no hook would read
    # this merge if the merge guards declared it out of scope (#10521 F2).
    # outside_merge_scope was deleted; the merge reader refuses the dynamic name.
    with pytest.raises(ShellParseError) as refused:
        read_commands(command, cwd=str(tmp_path), operation=_merge_operation)
    assert refused.value.reason_class == "DYNAMIC_COMMAND"
    record = tmp_path / "argv"
    gh = tmp_path / "gh"
    gh.write_text('#!/bin/sh\nprintf "%s\\0" "$@" > "$RECORD"\n')
    gh.chmod(0o755)
    subprocess.run(
        ["bash", "--noprofile", "--norc", "-c", command],
        env={"PATH": f"{tmp_path}:/usr/bin:/bin", "RECORD": str(record)},
        check=True,
        timeout=10,
    )
    value, _, tail = command.removeprefix("m='").partition("'; $m ")
    argv = value.split()[1:] + tail.split()
    assert argv[:2] == ["pr", "merge"]
    assert record.read_bytes() == b"".join(arg.encode() + b"\0" for arg in argv)


@pytest.mark.parametrize(
    "command,expected",
    [
        (r"python -m $'\163cripts'.p\ublish x", r"python -m scripts.p\ublish x"),
        (r"echo $'\x67h\cA\q' 'it''s'", "echo gh\x01\\q 'it''s'"),
        ("# it's\n" + r"x $'\147'h", "# it's\nx gh"),
        ("echo $'unterminated", None),
        (r"echo $'\U00110000'", None),
    ],
)
def test_ansi_c_reading_decodes_only_parsed_spans(command, expected):
    # Comments and other quoting never shift which spans Bash decodes (#10521 F5).
    from shell_bash import ansi_c_reading

    assert ansi_c_reading(command) == expected


@pytest.mark.parametrize(
    "hook,command",
    [
        ("guard-pr-merge", _DYNAMIC_WORKTREE_MERGES[0]),
        ("guard-pr-merge", _DYNAMIC_WORKTREE_MERGES[1]),
        ("guard-admin-merge", _DYNAMIC_WORKTREE_MERGES[1]),
        ("guard-pr-merge", _DYNAMIC_PR_VIEW_MERGES[0]),
        ("guard-pr-merge", _DYNAMIC_PR_VIEW_MERGES[1]),
        ("guard-admin-merge", _DYNAMIC_PR_VIEW_MERGES[1]),
    ],
)
def test_dynamic_executable_worktree_merge_is_judged(hook, command, tmp_path, capsys):
    import io

    module = _oracle_module().load_hook(hook)
    payload = {"cwd": str(tmp_path), "tool_input": {"command": command}}
    with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))):
        assert module.main() == 2
    assert "dynamic command name" in capsys.readouterr().err


@pytest.mark.parametrize(
    "prefix",
    [
        "",
        "true; ",
        "true && ",
        "true || ",
        "(",
        "x=$(",
        "then ",
        "do ",
        "else ",
        "{ ",
        "! ",
        "time ",
        "X=1 ",
        ">out ",
        "2>out ",
        "time ! { ",
        "time -p ",
        "if ",
        "while ",
        ">$(echo /dev/null) ",
        ">out$(true) ",
    ],
)
def test_case_command_word_refuses_at_its_position(prefix):
    line = prefix + "case x in x) true;; esac"
    assert unmodeled_shell_offset(line) == len(prefix)


@pytest.mark.parametrize(
    "line",
    [
        "echo case",
        "case=1 git status",
        'git commit -m "case x"',
        "'case' x",
        '"case" x',
        r"ca\se x",
        "echo 'case x in x)'",
        'echo "case x in x)"',
        "echo ${x:-word}",
        "echo '${x:-(}'",
        r"echo \${x:-word}",
        "echo x # case x in x)",
        "echo ${case:-word}",
        "echo case >case",
        "echo $(true) case",
        'echo "$(true) case"',
        "git checkout -b feat-$(date +%s)",
        'echo ${x:-"${y:-word}"} && git switch -c fixture',
        "echo ${x:-'${y}'} && git switch -c fixture",
    ],
)
def test_data_words_and_plain_parameter_expansions_are_not_refused(line):
    assert unmodeled_shell_offset(line) is None


@pytest.mark.parametrize(
    "word",
    [
        "${x:-(}",
        "${x:-)}",
        "${x//[(]/}",
        "${x//[)]/}",
        '"${x:-(}"',
        '${x:-"("}',
        "${x:-'('}",
        "${x:-${y:-(}}",
        '${x:-"}"}${y:-(}',
        r"${x:-\(}",
        '"${x:-${y:-)}}"',
    ],
)
def test_parameter_parentheses_refuse_from_containing_word(word):
    assert unmodeled_shell_offset("echo " + word) == 5


def test_quoted_substitution_exposes_case_command_word():
    line = 'echo "$(case x in x) true;; esac)"'
    assert unmodeled_shell_offset(line) == line.index("case")


def test_safe_nested_parameter_does_not_move_a_later_case_tripwire_earlier():
    line = 'echo ${x:-"${y:-word}"} && git switch -c fixture; case x in x) true;; esac'
    assert unmodeled_shell_offset(line) == line.index("case")


def test_heredoc_body_does_not_trigger_refusal():
    command = "cat <<'EOF'\ncase x in x) ${x:-(}\nEOF\ngit switch -c fixture"
    assert all(unmodeled_shell_offset(line) is None for line in preprocess_shell_command(command).splitlines())


def test_whole_command_detector_does_not_split_scope_events():
    kwargs = dict(mark_redirect_unreadable=True, unreadable_marker="?", unparsed=["?"], may_match=lambda _: False)
    command = 'git switch -c fixture; echo "$(case x in x) true;; esac)"'
    assert command_repository_unknown(command)
    events = scope_events(command, **kwargs)
    assert events[0] == ("segment", ["git", "switch", "-c", "fixture"])
    assert not any(kind in {"syntax_unreadable", "line_end", "unreadable"} for kind, _ in events)


@pytest.mark.parametrize(
    "command",
    [
        'echo "unterminated',
        "echo '${x:-word}",
        "cat <<EOF\nnever closed",
        "cat <<'EOF'\nnever closed",
        "echo ${x:-word",
        "echo $(true",
        "echo `unterminated",
        "echo \\",
    ],
)
def test_undecidable_detector_fails_closed(command):
    assert command_repository_unknown(command)


@pytest.mark.parametrize(
    "command",
    [
        "echo case\ngit switch -c fixture",
        "echo ${#arr[@]}",
        "cat <<'EOF'\ncase x in x) ${x:-(}\nEOF\ngit switch -c fixture",
        'echo "two\nlines"',
    ],
)
def test_whole_command_detector_controls(command):
    assert not command_repository_unknown(command)


def test_detector_internal_failure_fails_closed(monkeypatch):
    import shell_redirects

    def broken(command):
        raise RuntimeError("synthetic detector failure")

    monkeypatch.setattr(shell_redirects, "unmodeled_shell_offset", broken)
    assert command_repository_unknown("git switch -c fixture")


@pytest.mark.parametrize(
    "command",
    [
        'echo "$(case x in x) git switch -c fixture;; esac)"',
        'echo "$(case x in\nx) git switch -c fixture;;\nesac)"',
        'echo "$(case x in x) (true);; esac)" && git switch -c fixture',
        'echo "$(case x in x) (git switch -c fixture);; esac)"',
        'echo "$(if true; then case x in x) git switch -c fixture;; esac; fi)"',
        "echo ${x:-$(git switch -c fixture)}",
        "echo ${x:-'('}; git switch -c fixture",
        'git switch -c fixture; echo "unterminated',
        'echo "$(echo $(case x in x) git switch -c fixture;; esac))"',
    ],
)
def test_unknown_repository_reader_keeps_branch_commands_visible(command):
    from shell_redirects import unknown_repository_segments

    assert ["git", "switch", "-c", "fixture"] in unknown_repository_segments(command)


@pytest.mark.parametrize(
    "command",
    [
        'case x in x) echo "git switch -c literal";; esac',
        "echo '${x:-$(git switch -c literal)}'",
        "echo ${x:-'$(git switch -c literal)'}",
        "echo \"$(case x in x) echo 'git switch -c literal';; esac)\"",
    ],
)
def test_unknown_repository_reader_keeps_quoted_branch_prose_inert(command):
    from shell_redirects import unknown_repository_segments

    assert not any(argv[:2] == ["git", "switch"] for argv in unknown_repository_segments(command))


def test_original_argv_order_survives_whole_command_refusal():
    kwargs = dict(mark_redirect_unreadable=True, unreadable_marker="?", unparsed=["?"], may_match=lambda _: False)
    command = "git status; git switch -c ${x:-(}"
    assert command_repository_unknown(command)
    events = scope_events(command, **kwargs)
    assert events[0] == ("segment", ["git", "status"])
    switch = next(i for i, (kind, argv) in enumerate(events) if kind == "segment" and argv[:2] == ["git", "switch"])
    assert switch > 0
    assert not any(kind in {"syntax_unreadable", "line_end"} for kind, _ in events)


@pytest.mark.parametrize("opener", ["<<'EOF'", '<<"EOF"', r"<<\EOF", "<<-'EOF'"])
@pytest.mark.parametrize(
    "wrapper", ['git commit -m "$({body})"', "echo `{body}`", "cat <({body})", 'echo "$(printf %s "$({body})")"']
)
def test_nested_quoted_heredocs_are_inert(opener, wrapper):
    body = f"cat {opener}\ncase study: don't lex ${{y:-(z)}} `case` (text)\nEOF\n"
    command = "git switch -c fixture && " + wrapper.format(body=body)
    assert not command_repository_unknown(command)


@pytest.mark.parametrize(
    "body,unknown",
    [
        ("case study: don't lex (text)", False),
        ("'$(case x in x) true;; esac)'", True),
        ('"`case x in x) true;; esac`"', True),
        ("${y:-(z)}", True),
        (r"\${y:-(z)}", False),
        (r"\$(case x in x) true;; esac)", False),
        (r"\`case x in x) true;; esac\`", False),
        (r"\\${y:-(z)}", True),
        (r"\q${y:-(z)}", True),
        (r"${y:-\(}", True),
        ('${y:-"}"}${z:-(}', True),
        ("${y:-'$(case x in x) true;; esac)'}", True),
        ("$(cat <<'INNER'\ncase study: don't lex ${y:-(z)}\nINNER\n)", False),
    ],
)
def test_unquoted_heredoc_scans_expansions_only(body, unknown):
    command = 'git switch -c fixture && git commit -m "$(cat <<EOF\n' + body + '\nEOF\n)"'
    assert command_repository_unknown(command) is unknown


@pytest.mark.parametrize("tail", ["", "EOF trailing\n)", "\tEOF\n)"])
def test_nested_heredoc_requires_exact_terminator(tail):
    assert command_repository_unknown("echo \"$(cat <<'EOF'\ncase study\n" + tail)


def test_nested_heredoc_tabs_and_multiple_bodies():
    command = 'echo "$(cat <<-ONE <<\\TWO\n\tcase study\n\tONE\nIt\'s fixed\nTWO\n)"'
    assert not command_repository_unknown(command)


@pytest.mark.parametrize("opener", ["<<EOF", "<<'EOF'", '<<"EOF"', "<<-EOF", "<<-'EOF'", r"<<\EOF"])
@pytest.mark.parametrize("tail", ["", "git switch -c fixture", "cat <<'TWO'\nsecond\nTWO\ngit switch -c fixture"])
def test_nested_heredoc_preserves_statement_boundary(opener, tail):
    closer = "\tEOF" if opener.startswith("<<-") else "EOF"
    command = f'echo "$(cat {opener}\nfirst\n{closer}\n{tail}\n)"'
    visible = preprocess_branch_command(command)
    assert "cat </dev/null  ; " in visible
    kwargs = dict(mark_redirect_unreadable=True, unreadable_marker="?", unparsed=["?"], may_match=lambda _: False)
    segments = [argv for kind, argv in scope_events(visible, **kwargs) if kind == "segment"]
    assert (["git", "switch", "-c", "fixture"] in segments) == bool(tail)


def test_nested_heredoc_depth_limit_is_fail_closed():
    command = "cat <<'EOF'\ntext\nEOF"
    for _ in range(17):
        command = "$(" + command + "\n)"
    assert command_repository_unknown(command)


def test_branch_preprocessing_does_not_consume_array_arithmetic_as_a_heredoc():
    command = "x[1 << EOF ]=1\ngit checkout -b fixture\nEOF"
    assert "git checkout -b fixture" in preprocess_branch_command(command)


@pytest.mark.parametrize("opener", ["<<EOF\r", r"<<E\OF"])
def test_branch_preprocessing_preserves_conservative_exotic_delimiter_refusal(opener):
    command = f"cat {opener}\ngit checkout -b fixture\nEOF"
    with pytest.raises(ShellPreprocessLimit, match="ambiguous heredoc delimiter"):
        preprocess_branch_command(command)
    assert command_repository_unknown(command)


@pytest.mark.parametrize("command", [r"echo $'\U00110000'", r"echo $'\Uffffffff'"])
def test_invalid_unicode_operation_escape_is_unreadable(command):
    from shell_bash import operation_candidate

    assert operation_candidate(command)
    with pytest.raises(ShellParseError) as refused:
        read_commands(command)
    assert refused.value.reason_class == "DECODE_FAILURE"


def _checkout(argv):
    return argv[:2] == ["git", "checkout"]


@pytest.mark.parametrize(
    "command",
    [
        "cd(){ :; }",
        "function cd { :; }",
        "cd() ( : )",
        "f(){ g(){ :; }; }",
        "x=$(f(){ :; }; f)",
        "alias cd=:",
        "\\alias cd=:",
        "builtin alias cd=:",
        "enable -n cd",
        "BASH_ALIASES[cd]=:",
        "BASH_ALIASES=([cd]=:)",
        "declare -A BASH_ALIASES=([cd]=:)",
        "BASH_CMDS=([git]=/tmp/x)",
        "printf -v 'BASH_ALIASES[cd]' %s :",
        "let 'BASH_ALIASES[cd]=1'",
        "trap 'builtin(){ :; }' DEBUG",
        "trap \"eval 'cd(){ :; }'\" EXIT",
        "eval 'cd(){ :; }'",
        'trap "$action" EXIT',
        "trap 'f(){' EXIT",
    ],
)
def test_shell_definitions_are_structural(tmp_path, command):
    """Definitions are found anywhere in the AST, with no list of shadowable names (#10521)."""
    # Ported from the deleted shell_definitions(): placed after the operation, so the
    # before-operation grammar cannot be what refuses (ruling items 3 and 5).
    with pytest.raises(ShellParseError) as refused:
        read_commands(
            "git checkout -b fixture; " + command,
            cwd=str(tmp_path),
            consumer_check=lambda *args: None,
            operation=_checkout,
        )
    assert refused.value.reason_class in {"ALIAS_EXECUTION", "VISIBLE_SOURCE"}


@pytest.mark.parametrize(
    "command",
    [
        'echo "foo() { :; }"',
        "echo 'function cd { :; }'",
        'git commit -m "alias x=y"',
        "git commit -m 'f() { gh pr merge 5; }'",
        "cat <<'EOF'\ncd(){ :; }\nEOF",
        "trap 'rm -f /tmp/x' EXIT",
        "bash -c 'cd(){ :; }'",
    ],
)
def test_definition_text_in_arguments_is_data(tmp_path, command):
    """A child shell's definitions are found when the reader parses its payload."""
    from shell_bash import ShellDefinitionError

    # Ported from the deleted shell_definitions(): data after the operation stays readable.
    full = "git checkout -b fixture; " + command
    if command.startswith("bash -c"):
        with pytest.raises(ShellDefinitionError):
            read_commands(full, cwd=str(tmp_path), consumer_check=lambda *args: None, operation=_checkout)
        return
    rows = read_commands(full, cwd=str(tmp_path), consumer_check=lambda *args: None, operation=_checkout)
    assert [row.cwd for row in rows if row.guarded] == [str(tmp_path)]


@pytest.mark.parametrize(
    "command",
    [
        "cd(){ :; }; cd other && git checkout -b fixture",
        "cd other && git checkout -b fixture; cd(){ :; }",
        "bash -c 'cd(){ :; }; cd other && git checkout -b fixture'",
        "x=$(cd(){ :; }; echo); git checkout -b fixture",
        "trap 'builtin(){ :; }' DEBUG; builtin cd other && git checkout -b fixture",
        "command_not_found_handle(){ git checkout -b fixture; }; zz",
        "f(){ eval 'g(){ git checkout -b fixture; }'; }",
    ],
)
def test_definition_with_hook_operation_refuses_regardless_of_order(tmp_path, command):
    from shell_bash import ShellDefinitionError

    (tmp_path / "other").mkdir()
    with pytest.raises(ShellDefinitionError) as refused:
        read_commands(command, cwd=str(tmp_path), consumer_check=lambda *args: None, operation=_checkout)
    assert refused.value.reason_class == "ALIAS_EXECUTION"


@pytest.mark.parametrize(
    "command,operation",
    [
        # A definition without this hook's operation stays readable.
        ("f(){ echo hi; }; f; git status", _checkout),
        # Definition-like data with the operation is not a definition.
        ('echo "cd(){ :; }"; git checkout -b fixture', _checkout),
    ],
)
def test_definition_refusal_needs_the_hook_operation_and_a_definition(tmp_path, command, operation):
    rows = read_commands(command, cwd=str(tmp_path), consumer_check=lambda *args: None, operation=operation)
    # Rows outside the operation are no longer given a judged cwd (closed allowlist).
    assert any(row.argv[0] == "git" for row in rows)
    assert all(row.cwd == str(tmp_path) for row in rows if row.guarded)


def test_definition_beside_operation_shaped_text_refuses_for_another_hook(tmp_path):
    from shell_bash import ShellDefinitionError

    # Ruling item 3: a definition beside text shaped like any guarded operation refuses.
    with pytest.raises(ShellDefinitionError) as refused:
        read_commands(
            "f(){ git status; }; git checkout -b fixture",
            cwd=str(tmp_path),
            consumer_check=lambda *args: None,
            operation=lambda argv: argv[:2] == ["gh", "pr"],
        )
    assert refused.value.reason_class == "ALIAS_EXECUTION"


def test_alias_bindings_refuse_any_guarded_reader(tmp_path):
    from shell_bash import ShellDefinitionError

    for command in ("BASH_ALIASES=([zz]='git checkout -b f')\nzz", "alias zz='git checkout -b f'\nzz"):
        with pytest.raises(ShellDefinitionError):
            read_commands(command, cwd=str(tmp_path), consumer_check=lambda *args: None)


def test_alias_binding_never_proves_merge_out_of_scope(tmp_path):
    from shell_bash import ShellDefinitionError

    # Ported from the deleted outside_merge_scope(): the merge reader refuses the binding (ruling item 5).
    assert not any(row.guarded for row in read_commands("gh pr view 5", cwd=str(tmp_path), operation=_merge_operation))
    for command in ("BASH_ALIASES[gh]='gh pr merge 5 #'\ngh pr view 5", "trap 'alias gh=:' DEBUG; gh pr view 5"):
        with pytest.raises(ShellDefinitionError) as refused:
            read_commands(command, cwd=str(tmp_path), operation=_merge_operation)
        assert refused.value.reason_class == "ALIAS_EXECUTION"
