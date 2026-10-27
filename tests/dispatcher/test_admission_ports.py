"""Legacy launch-admission tests ported to the v2 dispatcher (C-2188 unit D).

Each test names its legacy source; assertions are adapted to the v2 entry points only.
"""

import os
import subprocess

import pytest

from scripts.dispatcher import admission, cli, git, providers, worker, write_intent
from scripts.dispatcher.environment import child_env
from scripts.dispatcher.types import TaskSpec
from scripts.lib import rules_core
from tests.agent_runtime.test_attempt_boundary import CLAUDE_AMBIENT_AUTH, _private_json
from tests.agent_runtime.test_claude_account_worker import _calls, _run, accounts  # noqa: F401  (fixture)
from tests.test_rules_core_loading import core_without_addendum, missing_core  # noqa: F401  (fixtures)


def _refuse_side_effects(monkeypatch, tmp_path):
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    for target, name in ((git, "create_worktree"), (git, "resolve_repo"), (worker, "start")):
        monkeypatch.setattr(target, name, lambda *_a, _name=name, **_k: pytest.fail(f"{_name} ran before refusal"))
    return tasks


# ----------------------------------------------------------------- Claude account (#10619)


def _labelled(accounts, monkeypatch):  # noqa: F811
    monkeypatch.setenv("PATH", f"{accounts.binary.parent}{os.pathsep}{os.environ['PATH']}")
    prompt = accounts.workdir / "prompt.txt"
    prompt.write_text("do the task")
    spec = TaskSpec(
        "labelled", "claude", "m", None, "workspace-write", accounts.workdir, prompt, accounts.workdir / "final",
        claude_account="b",
    )
    # The fixture CLI logs its calls through a variable the v2 environment does not pass on.
    env = {**child_env(spec), "LU_FAKE_CLAUDE_DUMP": str(accounts.dump)}
    return spec, providers.load("claude").build(spec, env)


@pytest.mark.parametrize(
    ("name", "settings"),
    [
        ("settings.local.json", {"apiKeyHelper": "fixture-helper-command"}),
        ("settings.json", {"apiKeyHelper": "fixture-helper-command"}),
        ("settings.local.json", {"env": {"CLAUDE_CODE_USE_BEDROCK": "1"}}),
    ],
)
def test_bound_label_checkout_setting_that_changes_auth_is_refused(accounts, monkeypatch, name, settings):  # noqa: F811
    """Ported from tests/agent_runtime/test_claude_account_worker.py::test_bound_label_checkout_setting_that_changes_auth_is_refused.

    A project or local setting the run still loads cannot switch its authentication.
    """
    _private_json(accounts.workdir / ".claude" / name, settings)
    spec, invocation = _labelled(accounts, monkeypatch)

    with pytest.raises(ValueError) as refused:
        admission.claude_launch(spec, invocation)

    assert str(refused.value) == "CLAUDE_ACCOUNT_REFUSED: claude_account_auth_method_conflict"
    assert len(_calls(accounts, "auth_status")) == 1
    assert _calls(accounts, "run") == []


def test_bound_label_runs_with_only_the_bound_login_directory(accounts, monkeypatch):  # noqa: F811
    """Ported from tests/agent_runtime/test_claude_account_worker.py::test_bound_label_runs_with_only_the_bound_login_directory.

    Label b's worker runs behind the launch guard in the bound login directory, with no user-scope
    settings and no other credential source.
    """
    spec, invocation = _labelled(accounts, monkeypatch)
    launched = admission.claude_launch(spec, invocation)

    completed = subprocess.run(
        launched.argv, input=launched.stdin, env=launched.env, cwd=spec.worktree, capture_output=True, timeout=60
    )

    assert completed.returncode == 0, completed.stderr
    seen = _run(accounts)
    env = seen["env"]
    assert env["CLAUDE_CONFIG_DIR"] == str(accounts.config_dir)
    assert not {name for name in env if name.upper() in CLAUDE_AMBIENT_AUTH or name.upper().startswith("ANTHROPIC_")}
    assert not [name for name, value in env.items() if accounts.bound_token in value or accounts.default_token in value]
    assert accounts.profile_calls == [accounts.bound_token]
    argv = seen["argv"]
    assert argv[argv.index("--setting-sources") + 1] == "project,local"
    assert str(accounts.config_dir) not in repr(argv) + repr(launched.argv)


# ----------------------------------------------------------------- rules core


def test_delegate_dispatch_without_the_core_refuses(tmp_path, monkeypatch, missing_core, capsys):  # noqa: F811
    """Ported from tests/test_rules_core_loading.py::test_delegate_dispatch_without_the_core_refuses."""
    tasks = _refuse_side_effects(monkeypatch, tmp_path)

    assert cli.main(["dispatch", "--agent", "codex", "--model", "m", "--prompt", "the source prompt"]) == 2

    err = capsys.readouterr().err
    assert "dispatch refused" in err
    assert "agents_extensions/shared/rules/core.md" in err
    assert not tasks.exists()


def test_delegate_content_seat_without_the_addendum_refuses(
    tmp_path, monkeypatch, core_without_addendum, capsys  # noqa: F811
):
    """Ported from tests/test_rules_core_loading.py::test_delegate_content_seat_without_the_addendum_refuses."""
    monkeypatch.setenv(rules_core.SEAT_ENV, "content")
    tasks = _refuse_side_effects(monkeypatch, tmp_path)

    assert cli.main(["dispatch", "--agent", "codex", "--model", "m", "--prompt", "the source prompt"]) == 2

    assert "core-curriculum.md" in capsys.readouterr().err
    assert not tasks.exists()


# ----------------------------------------------------------------- read-only write intent (#8703)


@pytest.mark.parametrize(
    "mode_args",
    [
        pytest.param([], id="default-read-only"),
        pytest.param(["--mode", "read-only"], id="explicit-read-only"),
    ],
)
def test_dispatch_rejects_write_shaped_prompt_in_read_only_mode(tmp_path, monkeypatch, capsys, mode_args):
    """Ported from tests/test_delegate.py::test_dispatch_rejects_write_shaped_prompt_in_read_only_mode."""
    tasks = _refuse_side_effects(monkeypatch, tmp_path)
    prompt = "Implement the requested dispatch guard and add regression tests."

    assert cli.main(["dispatch", "--agent", "codex", "--model", "m", "--prompt", prompt, *mode_args]) == 2

    err = capsys.readouterr().err
    assert "write-shaped prompt" in err
    assert "--mode workspace-write --worktree" in err
    assert not tasks.exists()


def test_dispatch_rejects_write_shaped_prompt_file_in_read_only_mode(tmp_path, monkeypatch, capsys):
    """Ported from tests/test_delegate.py::test_dispatch_rejects_write_shaped_prompt_file_in_read_only_mode."""
    tasks = _refuse_side_effects(monkeypatch, tmp_path)
    prompt_file = tmp_path / "write-brief.md"
    prompt_file.write_text("- Update scripts/delegate.py and add tests.\n", encoding="utf-8")

    assert cli.main(["dispatch", "--agent", "codex", "--model", "m", "--prompt-file", str(prompt_file)]) == 2

    assert "write-shaped prompt" in capsys.readouterr().err
    assert not tasks.exists()


def test_write_shaped_prompt_is_admitted_by_write_capable_modes():
    """Ported from tests/test_delegate.py::test_write_shaped_prompt_is_admitted_by_write_capable_modes (v2 has no danger mode)."""
    prompt = "Fix the dispatch guard and update its tests."
    assert write_intent._read_only_write_intent_error(mode="workspace-write", prompt=prompt) is None


def test_read_only_change_discussion_is_not_misclassified_as_write_intent():
    """Ported from tests/test_delegate.py::test_read_only_change_discussion_is_not_misclassified_as_write_intent."""
    prompt = "Review the proposed changes and explain the safest implementation; do not edit files."
    assert write_intent._read_only_write_intent_error(mode="read-only", prompt=prompt) is None


def test_read_only_critique_of_fenced_brief_is_not_misclassified_as_write_intent():
    """Ported from tests/test_delegate.py::test_read_only_critique_of_fenced_brief_is_not_misclassified_as_write_intent."""
    prompt = (
        "Critique the attached brief for gaps and contradictions; do not edit files.\n"
        "\n"
        "```markdown\n"
        "# Brief\n"
        "- Add a CLI for authority delivery.\n"
        "- Fix the status command output.\n"
        "```\n"
        "\n"
        "Report findings only.\n"
    )
    assert write_intent._read_only_write_intent_error(mode="read-only", prompt=prompt) is None


def test_read_only_critique_of_blockquoted_brief_is_not_misclassified_as_write_intent():
    """Ported from tests/test_delegate.py::test_read_only_critique_of_blockquoted_brief_is_not_misclassified_as_write_intent."""
    prompt = (
        "Review the brief quoted below and list its weaknesses.\n"
        "\n"
        "> ## Work\n"
        "> 1. Implement the delivery guard in scripts/delegate.py.\n"
        "> 2. Add regression tests.\n"
    )
    assert write_intent._read_only_write_intent_error(mode="read-only", prompt=prompt) is None


def test_read_only_write_directive_outside_quoted_content_is_still_refused():
    """Ported from tests/test_delegate.py::test_read_only_write_directive_outside_quoted_content_is_still_refused."""
    prompt = (
        "The attached brief says:\n"
        "\n"
        "```markdown\n"
        "- Add a CLI for authority delivery.\n"
        "```\n"
        "\n"
        "Please implement the brief in scripts/delegate.py and add tests.\n"
    )
    error = write_intent._read_only_write_intent_error(mode="read-only", prompt=prompt)
    assert error is not None
    assert "write-shaped prompt" in error


def test_read_only_wrapped_prose_continuation_line_is_not_refused():
    """Ported from tests/test_delegate.py::test_read_only_wrapped_prose_continuation_line_is_not_refused."""
    prompt = (
        "Review the task deliverable and verify that the\n"
        "fix report `batch_state/tasks/impl-conftest-light-r2.result`.\n"
    )
    assert write_intent._read_only_write_intent_error(mode="read-only", prompt=prompt) is None
