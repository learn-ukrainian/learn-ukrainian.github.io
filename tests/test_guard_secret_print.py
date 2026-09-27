"""Unit tests for the secret-print guard hook (#M-5 / #1908).

Exercises the narrow decision logic in
``agents_extensions/shared/hooks/guard-secret-print.py``:

  * clear secret dump shapes are blocked,
  * key-only/count/presence checks are allowed,
  * quoted command-message bodies do not trigger substring false positives, and
  * the LEARN_UK_SECRETS_OK=1 override is honored.

The hook filename has hyphens, so it is loaded by path via importlib. ``main``
is guarded by ``__name__ == "__main__"``, so import has no side effects.
"""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "agents_extensions/shared" / "hooks" / "guard-secret-print.py"


def _load_hook():
    spec = importlib.util.spec_from_file_location("guard_secret_print", HOOK_PATH)
    assert spec and spec.loader, f"could not load hook at {HOOK_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_hook()


def _run(monkeypatch, command: str, *, env_override: bool = False) -> int:
    payload = json.dumps({"tool_input": {"command": command}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    if env_override:
        monkeypatch.setenv("LEARN_UK_SECRETS_OK", "1")
    else:
        monkeypatch.delenv("LEARN_UK_SECRETS_OK", raising=False)
    return guard.main()


@pytest.mark.parametrize(
    "cmd",
    [
        "env",
        "cat ~/.aws/credentials",
        "cat .env",
        "tail .envrc",
        "grep KEY .envrc",
        "echo $GH_TOKEN",
    ],
)
def test_secret_dump_shapes_blocked(monkeypatch, capsys, cmd):
    assert _run(monkeypatch, cmd) == 2
    err = capsys.readouterr().err
    assert "BLOCKED by guard-secret-print (#M-5)" in err
    assert "cut -d= -f1" in err
    assert "jq keys" in err
    assert '[ -n "${X:-}" ]' in err
    assert "LEARN_UK_SECRETS_OK=1" in err


@pytest.mark.parametrize(
    "cmd",
    [
        "git commit -m fix#123 && cat .env",
        "echo hi#$GH_TOKEN",
    ],
)
def test_unquoted_midword_hash_keeps_secret_checks_active(monkeypatch, capsys, cmd):
    assert _run(monkeypatch, cmd) == 2
    assert "BLOCKED by guard-secret-print (#M-5)" in capsys.readouterr().err


@pytest.mark.parametrize(
    "command",
    [
        "git status # echo x > AGENTS.md",
        "echo hi # $GH_TOKEN",
        "# tee AGENTS.md",
        "echo hi # cat .env",
        "echo '#' ; echo safe",
        "echo $(printf '# hidden') # $GH_TOKEN",
        "echo `printf '# hidden'` # cat .env",
        "echo hi # <<EOF\ncat .env",
    ],
)
def test_bash_comments_do_not_trigger_secret_guard(monkeypatch, command):
    assert _run(monkeypatch, command) == 0


@pytest.mark.parametrize(
    "command",
    [
        "git commit -m fix#123 && cat .env",
        "echo hi#$GH_TOKEN",
        "echo '#' ; cat .env",
    ],
)
def test_bash_comments_keep_executable_secret_words(monkeypatch, command):
    assert _run(monkeypatch, command) == 2


def test_bash_comment_stripping_keeps_next_line_for_secret_parser():
    # Parsing newline separators in this hook is tracked separately.
    assert guard._strip_shell_comments("echo hi # c; cat .env\ncat .env") == "echo hi \ncat .env"
    assert guard._strip_heredoc_bodies("echo hi # <<EOF\ncat .env") == "echo hi # <<EOF\ncat .env"


@pytest.mark.parametrize("operator", [";", "&", "|", "(", ")"])
def test_bash_comment_starts_after_control_operator_in_secret_hook(operator):
    assert guard._strip_shell_comments(f"echo hi{operator}# hidden\ncat .env") == (f"echo hi{operator}\ncat .env")


@pytest.mark.parametrize(
    "cmd",
    [
        "env | cut -d= -f1",
        '[ -n "${X:-}" ] && echo SET',
        "cat README.md",
        "cat agents_extensions/shared/hooks/guard-secret-print.py",
        "cat test_api_key.py",
        "cat token_utils.py",
        "python -m pytest tests/foo.py -q 2>&1 | tail -3",
        "tail secret-print",
        "tail -n 5",
        "head -20 file.py",
        "jq keys",
        'git commit -m "notes: gh pr merge --admin and echo $GH_TOKEN"',
        'git commit -m "ref guard-secret-print.py"',
        'git commit -m "document scripts.session_supervisor worker-env"',
        "git commit -F - <<EOF\nref guard-secret-print\nEOF",
        "tail -3 <<EOF\n.env\nEOF",
        "LEARN_UK_SECRETS_OK=1 env",
    ],
)
def test_safe_commands_allowed(monkeypatch, cmd):
    assert _run(monkeypatch, cmd) == 0


def test_environment_override_allowed(monkeypatch):
    assert _run(monkeypatch, "env", env_override=True) == 0


def test_single_quoted_secret_var_literal_allowed(monkeypatch):
    assert _run(monkeypatch, "echo '$GH_TOKEN'") == 0


def test_unrelated_echo_after_secret_export_allowed(monkeypatch):
    assert _run(monkeypatch, 'export HCLOUD_TOKEN=placeholder; echo "server=$s"') == 0
    assert _run(monkeypatch, 'HCLOUD_TOKEN=placeholder echo "server=$s"') == 0


def test_echo_of_exported_secret_still_blocked(monkeypatch):
    assert _run(monkeypatch, 'export HCLOUD_TOKEN=placeholder; echo "$HCLOUD_TOKEN"') == 2


@pytest.mark.parametrize(
    "cmd",
    [
        "scripts.session_supervisor worker-env",
        "python -m scripts.session_supervisor worker-env",
        ".venv/bin/python -m scripts.session_supervisor worker-env --all",
        "python3 -m scripts.session_supervisor --all worker-env",
    ],
)
def test_worker_env_commands_are_blocked(monkeypatch, capsys, cmd):
    assert _run(monkeypatch, cmd) == 2
    assert "worker-env" in capsys.readouterr().err
