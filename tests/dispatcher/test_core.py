"""Private-input policy, child environment, CLI flags, timeouts and admission."""

import dataclasses
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import yaml

from scripts.dispatcher import agy_sandbox, checks, cli, git, providers, store, worker
from scripts.dispatcher.cli import ALIASES, build_parser
from scripts.dispatcher.environment import child_env
from scripts.dispatcher.providers import muse
from scripts.dispatcher.types import Invocation, TaskSpec
from scripts.lib import rules_core
from tests.dispatcher.conftest import await_file, run_git

# ---- ported from tests/test_delegate_review_test_slots.py and tests/test_delegate.py (C-2188 unit D) ----


def test_legacy_archive_is_read_only_and_nonce_checked(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    archive = tmp_path / "archive"
    archive.mkdir()
    result = archive / "old.result"
    result.write_text("archived report")
    path = archive / "old.json"
    path.write_text(
        json.dumps(
            dict(task_id="old", status="needs_finalize", run_nonce="n", result_file=str(tmp_path / "old.result"))
        )
    )
    before = path.read_bytes()
    assert store.read("old", "n")["result_file"] == str(result)
    assert store.list_tasks() == []
    assert len(store.list_tasks(include_archive=True)) == 1
    with pytest.raises(ValueError, match="nonce mismatch"):
        store.read("old", "wrong")
    with pytest.raises(ValueError, match="legacy task"):
        worker.cancel("old", "n")
    assert path.read_bytes() == before


@pytest.fixture
def spec(tmp_path):
    prompt = tmp_path / "brief.txt"
    prompt.write_text("public input")
    return TaskSpec("task", "muse", "model", None, "read-only", tmp_path, prompt, tmp_path / "task.result")


def assert_private_input_policy(spec, repo_key, error):
    if spec.agent == "muse":
        spec = dataclasses.replace(spec, options={**spec.options, "contributor_mode": "on"})
        checks.check_private_input(spec, repo_key)
        argv = muse.build(spec, {}).argv
        assert argv[argv.index("--contributor-mode") + 1] == "off"
    else:
        with pytest.raises(ValueError, match=error):
            checks.check_private_input(spec, repo_key)


@pytest.mark.parametrize("agent", ["muse", "opencode"])
@pytest.mark.parametrize("classification", [{"role": "private-product"}, {"role": "product", "private": True}])
def test_private_repo_and_prompt_origin_cannot_bypass_private_policy(spec, private_repos, agent):
    private, alias = private_repos
    spec = dataclasses.replace(spec, agent=agent)
    assert_private_input_policy(spec, "private", "private input")
    for origin in (private / "secret.txt", alias / "secret.txt"):
        assert_private_input_policy(
            dataclasses.replace(spec, options={"prompt_file": str(origin)}), "public", "private prompt file"
        )


@pytest.fixture
def classification():
    return {"role": "private-product"}


@pytest.fixture
def private_repos(tmp_path, monkeypatch, classification):
    config = tmp_path / "repos.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "repos": {
                    "public": {"default": True, "local_name": "public", "role": "public-monorepo"},
                    "private": {
                        "local_name": "vault-data",
                        "github": "ExampleOrg/SealedNotes",
                        **classification,
                    },
                }
            }
        )
    )
    monkeypatch.setattr(git, "CONFIG", config)
    monkeypatch.setattr(git, "ROOT", tmp_path / "public")
    private = tmp_path / "vault-data"
    private.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(private, target_is_directory=True)
    return private, alias


@pytest.mark.parametrize("classification", [{"role": "private-product"}, {"role": "product", "private": True}])
@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
@pytest.mark.parametrize("source", ["repo", "prompt-origin", "symlink-origin", "owned-path", "encoded-identifier"])
def test_private_muse_never_receives_contributor_on(spec, private_repos, mode, source):
    private, alias = private_repos
    options = {"contributor_mode": "on", "unrelated": "preserved"}
    if source in {"prompt-origin", "symlink-origin"}:
        root = private if source == "prompt-origin" else alias
        options["prompt_file"] = str(root / "brief.txt")
    elif source == "owned-path":
        spec.prompt_file.write_text(f"Owned paths: {private}/notes.md")
    elif source == "encoded-identifier":
        spec.prompt_file.write_text("Owned paths: %56AULT%2dDATA/notes.md")
    expected_options = {**options, "contributor_mode": "off"}
    spec = dataclasses.replace(spec, mode=mode, options=options)
    before = spec.prompt_file.read_bytes()

    checks.check_private_input(spec, "private" if source == "repo" else "public")

    argv = muse.build(spec, {}).argv
    assert argv[argv.index("--contributor-mode") + 1] == "off"
    assert spec.options == expected_options
    assert spec.prompt_file.read_bytes() == before


def test_public_muse_contributor_on_is_preserved(spec, private_repos):
    spec = dataclasses.replace(spec, options={"contributor_mode": "on"})
    checks.check_private_input(spec, "public")
    argv = muse.build(spec, {}).argv
    assert argv[argv.index("--contributor-mode") + 1] == "on"


@pytest.mark.parametrize("agent", ["muse", "opencode"])
@pytest.mark.parametrize(
    "prompt",
    [
        pytest.param('Read "{private}/a=b.txt".', id="quoted-equals-private-path"),
        pytest.param("Read ({private}/a=b.txt).", id="parenthesized-equals-private-path"),
        pytest.param("Read file://{private}/secret.txt?v=1", id="file-uri-query-equals"),
        pytest.param("Read source:{encoded}", id="encoded-source-private-path"),
    ],
)
def test_private_path_equals_and_encoded_source_cannot_bypass_private_policy(spec, private_repos, agent, prompt):
    """Old tokenizer lost the private path after '=' or left source: escapes undecoded."""
    private, _ = private_repos
    prompt = prompt.format(private=private, encoded=str(private / "secret.txt").replace("/", "%2F"))
    spec = dataclasses.replace(spec, agent=agent)
    spec.prompt_file.write_text(prompt)
    assert_private_input_policy(spec, "public", "private path")
    assert spec.prompt_file.read_text() == prompt


@pytest.mark.parametrize("agent", ["muse", "opencode"])
@pytest.mark.parametrize(
    "prompt",
    [
        pytest.param("Discuss VAULT-DATA notes.", id="plain-directory"),
        pytest.param("Discuss EXAMPLEORG/SEALEDNOTES.", id="plain-slug"),
        pytest.param("Read file://{private}/secret.txt", id="file-uri-private-root"),
        pytest.param("Read file:///ExampleOrg/SealedNotes/secret.txt", id="file-uri-slug"),
        pytest.param("Discuss %56AULT%2dDATA notes.", id="once-encoded-directory"),
        pytest.param("Discuss %45XAMPLEORG%2f%53EALEDNOTES.", id="once-encoded-slug"),
        pytest.param("Read {encoded}", id="once-encoded-path"),
        pytest.param("Read --input={private}/secret.txt", id="option-private-path"),
    ],
)
def test_private_identifier_substring_contract(spec, private_repos, agent, prompt):
    """CTO policy replaces path tokenization with conservative identifier substrings."""
    private, _ = private_repos
    prompt = prompt.format(private=private, encoded=str(private / "secret.txt").replace("/", "%2F"))
    spec = dataclasses.replace(spec, agent=agent)
    spec.prompt_file.write_text(prompt)
    assert_private_input_policy(spec, "public", "private path")
    assert spec.prompt_file.read_text() == prompt


@pytest.mark.parametrize("agent", ["muse", "opencode"])
@pytest.mark.parametrize("prompt", ["[notes](100%.md)", "Read file:///public/100%.md"])
def test_public_literal_percent_is_not_a_malformed_escape_refusal(spec, private_repos, agent, prompt):
    """Old tokenizer incorrectly refused public100percent CommonMark and file URI inputs."""
    spec = dataclasses.replace(spec, agent=agent)
    spec.prompt_file.write_text(prompt)
    checks.check_private_input(spec, "public")
    assert spec.prompt_file.read_text() == prompt


@pytest.mark.parametrize("agent", ["muse", "opencode"])
@pytest.mark.parametrize(
    "prompt",
    [
        "./alias/secret.txt",
        "'alias/a file.txt'",
        "--input=alias/secret.txt",
        "%2556AULT%252dDATA",
        "https://example.invalid/guide?q=100%25",
        "Public input with 100% progress, %GG, and an unfinished [link](",
    ],
)
def test_lexical_contract_allows_aliases_double_encoding_and_public_text(spec, private_repos, agent, prompt):
    """Approved policy change: old alias refusals now pass; no alias resolution or recursive decoding."""
    spec = dataclasses.replace(spec, agent=agent, options={"prompt_file": "-"})
    spec.prompt_file.write_text(prompt)
    checks.check_private_input(spec, "public")
    assert spec.prompt_file.read_text() == prompt


@pytest.mark.parametrize("agent", ["codex", "claude", "cursor", "agy"])
def test_private_input_policy_leaves_other_providers_unchanged(spec, private_repos, agent):
    private, _ = private_repos
    spec = dataclasses.replace(spec, agent=agent, options={"prompt_file": str(private / "brief.txt")})
    spec.prompt_file.write_text("Read ExampleOrg/SealedNotes with 100% progress.")
    checks.check_private_input(spec, "private")


@pytest.mark.parametrize("agent", ["muse", "opencode"])
def test_empty_private_identifiers_do_not_refuse_all_public_prompts(spec, tmp_path, monkeypatch, agent):
    config = tmp_path / "repos.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "repos": {
                    "private": {"default": True, "local_name": "", "github": "", "private": True},
                    "public": {"local_name": "public"},
                }
            }
        )
    )
    monkeypatch.setattr(git, "CONFIG", config)
    root = tmp_path / "protected-root"
    monkeypatch.setattr(git, "ROOT", root)
    spec = dataclasses.replace(spec, agent=agent)
    checks.check_private_input(spec, "public")
    spec.prompt_file.write_text(f"Read {root}/secret.txt")
    assert_private_input_policy(spec, "public", "private path")


@pytest.mark.parametrize("character", ["\n", "\u202e", "\u2028"])
def test_worktree_path_contract_defers_unicode_characters_to_git(sandbox, character):
    """Approved policy change: remove extra Unicode refusal while retaining dispatch containment."""
    path = sandbox.repo / ".worktrees/dispatch/codex" / f"name{character}part"
    planned, branch, sha = git.worktree_plan(sandbox.repo, "codex", "path-policy", "main", worktree=path)
    assert planned == path
    assert branch == "codex/path-policy"
    assert sha == run_git(sandbox.repo, "rev-parse", "main")


def test_worktree_plan_retains_containment_symlinks_repo_identity_and_git_failures(sandbox):
    parent = sandbox.repo / ".worktrees/dispatch/codex"
    parent.mkdir(parents=True)
    alias = parent / "alias"
    alias.symlink_to(parent, target_is_directory=True)
    for path in (sandbox.repo / "outside", alias / "child"):
        with pytest.raises(ValueError, match="dispatch directory without symlinks"):
            git.worktree_plan(sandbox.repo, "codex", "safe-path", "main", worktree=path)
    with pytest.raises(subprocess.CalledProcessError):
        git.worktree_plan(sandbox.repo, "codex", "missing-cwd", "main", cwd=parent / "missing")
    path = parent / "existing"
    sha = run_git(sandbox.repo, "rev-parse", "main")
    git.create_worktree(sandbox.repo, path, "codex/existing", sha)
    assert git.worktree_plan(sandbox.repo, "codex", "existing", "main", cwd=path) == (path, "codex/existing", sha)
    with pytest.raises(ValueError, match="existing dispatch worktree root"):
        git.worktree_plan(sandbox.repo, "codex", "nested", "main", cwd=path / "scripts")
    foreign = parent / "foreign"
    foreign.mkdir()
    run_git(foreign, "init", "-b", "main")
    with pytest.raises(ValueError, match="different repository"):
        git.worktree_plan(sandbox.repo, "codex", "foreign", "main", cwd=foreign)


def test_review_family_uses_model_family_not_harness_and_refuses_unknown():
    checks.check_review_family("gpt-6.1-sol", "claude-opus-5-5")
    checks.check_review_family("claude-opus-5-5", "grok-4.7-high")
    for author, reviewer in (
        ("gpt-6.1-sol", "gpt-6-luna"),
        ("claude-opus-5-5", "claude-sonnet-5-5"),
        ("unknown", "gpt-6.1-sol"),
        ("gpt-6.1-sol", "unknown"),
    ):
        with pytest.raises(ValueError, match="known, different"):
            checks.check_review_family(author, reviewer)


def test_resource_floor_and_both_filesystems_with_injected_values(tmp_path, monkeypatch):
    real_read = Path.read_text
    available = 8.5 * 1024**3
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda path, *a, **kw: (
            f"MemAvailable: {int(available / 1024)} kB\n"
            if path == Path("/proc/meminfo")
            else real_read(path, *a, **kw)
        ),
    )
    probes = []
    monkeypatch.setattr(
        checks.shutil, "disk_usage", lambda path: probes.append(path) or SimpleNamespace(used=89, total=100)
    )
    checks.check_resources([tmp_path, tmp_path / "nonexistent"])
    assert probes == [tmp_path, tmp_path]
    available -= 1024
    with pytest.raises(ValueError, match=r"8\.5 GiB"):
        checks.check_resources([tmp_path])
    available += 1024
    monkeypatch.setattr(checks.shutil, "disk_usage", lambda path: SimpleNamespace(used=90, total=100))
    with pytest.raises(ValueError, match="90%"):
        checks.check_resources([tmp_path])


def test_environment_contains_only_context_and_selected_auth(spec, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    for name in ("GH_TOKEN", "SSH_AUTH_SOCK", "INFRA_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "MUSE_API_KEY"):
        monkeypatch.setenv(name, f"test-{name.lower()}")
    env = child_env(spec)
    assert env["MUSE_API_KEY"] == "test-muse_api_key"
    assert not {"GH_TOKEN", "SSH_AUTH_SOCK", "INFRA_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"} & env.keys()
    for account, directory in (("a", ".claude"), ("b", ".claude-b")):
        env = child_env(dataclasses.replace(spec, agent="claude", claude_account=account))
        assert env["CLAUDE_CONFIG_DIR"] == str(tmp_path / directory)
        assert "MUSE_API_KEY" not in env


def test_cursor_child_env_present_process_key_wins_over_env_file(spec, monkeypatch):
    loader = Mock(return_value="stub-file-key")
    monkeypatch.setattr("scripts.agent_runtime.adapters.cursor._load_cursor_api_key_from_env_file", loader)
    monkeypatch.setenv("CURSOR_API_KEY", "stub-process-key")

    env = child_env(dataclasses.replace(spec, agent="cursor"))

    assert env["CURSOR_API_KEY"] == "stub-process-key"
    loader.assert_not_called()


@pytest.mark.parametrize("process_key", [None, "", " \t\n"], ids=["missing", "blank", "whitespace_only"])
def test_cursor_child_env_missing_or_blank_process_key_falls_back_to_env_file(spec, monkeypatch, process_key):
    loader = Mock(return_value="stub-file-key")
    monkeypatch.setattr("scripts.agent_runtime.adapters.cursor._load_cursor_api_key_from_env_file", loader)
    if process_key is None:
        monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    else:
        monkeypatch.setenv("CURSOR_API_KEY", process_key)

    env = child_env(dataclasses.replace(spec, agent="cursor"))

    assert env["CURSOR_API_KEY"] == "stub-file-key"
    assert os.environ.get("CURSOR_API_KEY") == process_key
    loader.assert_called_once_with()


@pytest.mark.parametrize("process_key", [None, "", " \t\n"], ids=["missing", "blank", "whitespace_only"])
def test_cursor_child_env_missing_or_blank_key_without_file_key_forwards_nothing(spec, monkeypatch, process_key):
    loader = Mock(return_value=None)
    monkeypatch.setattr("scripts.agent_runtime.adapters.cursor._load_cursor_api_key_from_env_file", loader)
    if process_key is None:
        monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    else:
        monkeypatch.setenv("CURSOR_API_KEY", process_key)

    assert "CURSOR_API_KEY" not in child_env(dataclasses.replace(spec, agent="cursor"))
    loader.assert_called_once_with()


@pytest.mark.parametrize("agent", ["codex", "claude", "agy", "muse", "opencode"])
@pytest.mark.parametrize("process_key", [None, "stub-process-key", "", " \t\n"])
def test_non_cursor_child_env_never_loads_or_forwards_cursor_key(spec, monkeypatch, agent, process_key):
    loader = Mock(return_value="stub-file-key")
    monkeypatch.setattr("scripts.agent_runtime.adapters.cursor._load_cursor_api_key_from_env_file", loader)
    if process_key is None:
        monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    else:
        monkeypatch.setenv("CURSOR_API_KEY", process_key)

    assert "CURSOR_API_KEY" not in child_env(dataclasses.replace(spec, agent=agent))
    loader.assert_not_called()


def test_cursor_child_env_corrupt_invalid_utf8_file_forwards_no_key_without_raising(spec, monkeypatch, tmp_path, capsys):
    key_file = tmp_path / "api.key.env"
    key_file.write_bytes(b"CURSOR_API_KEY=stub-\xff-key\n")
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    monkeypatch.setattr("scripts.agent_runtime.adapters.cursor._cursor_api_key_env_path", lambda: key_file)

    assert "CURSOR_API_KEY" not in child_env(dataclasses.replace(spec, agent="cursor"))
    assert capsys.readouterr() == ("", "")


def test_grok_is_no_alias_and_an_unknown_agent_names_the_supported_agents(sandbox):
    """Operator 2026-10-27: --agent grok silently launched cursor-agent; Grok runs as cursor + grok-4.7-high."""
    result = sandbox.cli("dispatch", "--agent", "grok", "--model", "grok-4.7-high", "--prompt", "Explain X",
                         expected=2)
    assert "unknown agent 'grok'; supported agents: codex, claude, cursor, agy, muse, opencode" in result.stderr
    assert "dispatch Grok as --agent cursor --model grok-4.7-high" in result.stderr
    assert not sandbox.tasks.exists()


@pytest.mark.parametrize("agent", providers.PROVIDERS)
def test_read_only_mode_denies_edits_on_every_provider(sandbox, tmp_path, monkeypatch, agent):
    """C-2916 P6 removed the lexical refusal; read-only is now held by each CLI's own write lock or refused."""
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Fix the bug in X.\n")
    spec = TaskSpec("ro", agent, "vendor/model", None, "read-only", tmp_path, prompt, tmp_path / "final", "a")
    refused: dict[str, str] = {}
    if agent in refused:
        with pytest.raises(ValueError, match=f"read_only_unenforceable: {agent} cannot run --mode read-only"):
            providers.load(agent).build(spec, {})
        result = sandbox.cli("dispatch", "--agent", agent, "--model", "vendor/model", "--prompt", "Fix X", expected=2)
        assert f"read_only_unenforceable: {agent} cannot run --mode read-only" in result.stderr
        assert refused[agent] in result.stderr
        assert not sandbox.tasks.exists()
        return
    if agent == "agy":
        # AGY has no write lock of its own: read-only is refused where its bubblewrap boundary cannot
        # start, and otherwise every build returns that boundary, never a bare agy (C-3027).
        monkeypatch.setattr("scripts.dispatcher.agy_sandbox.unavailable", lambda: "bubblewrap (bwrap) is not installed")
        with pytest.raises(ValueError, match="read_only_unenforceable: agy cannot run --mode read-only: bubblewrap"):
            providers.load(agent).build(spec, {})
        monkeypatch.setattr("scripts.dispatcher.agy_sandbox.unavailable", lambda: None)
    invocation = providers.load(agent).build(spec, {})
    argv = invocation.argv
    if agent == "agy":
        split = argv.index("--")
        assert argv[1:4] == ["-I", "-c", agy_sandbox._BOOTSTRAP] and argv[4] == str(agy_sandbox.ROOT)
        assert argv[argv.index("--worktree") + 1] == str(tmp_path) and argv[split + 1] == "agy"
        assert argv[argv.index("--receipt") + 1] == str(tmp_path / "final.sandbox.json")
        assert argv[argv.index("--add-dir") + 1] == str(tmp_path)
        assert argv[argv.index("--log-file") + 1] == str(agy_sandbox.log_file("ro"))  # private scratch
        assert argv.index("--dangerously-skip-permissions") > split
    elif agent == "codex":
        assert 'sandbox_mode="read-only"' in argv and "--dangerously-bypass-approvals-and-sandbox" not in argv
    elif agent == "cursor":
        assert argv[argv.index("--mode") + 1] == "ask"
    elif agent == "muse":
        assert {"--disable-write", "--disable-shell"} <= set(argv)
    elif agent == "claude":
        assert argv[argv.index("--permission-mode") + 1] == "dontAsk"
        # Bash is allowed only behind the review boundary: every command goes through its shell prefix (#12378).
        assert "Bash" in argv[argv.index("--allowedTools") + 1].split(",")
        assert invocation.env["CLAUDE_CODE_SHELL_PREFIX"] == str(agy_sandbox.SHELL_PREFIX)
        assert {"Edit", "Write", "NotebookEdit"} <= set(argv[argv.index("--disallowedTools") + 1].split(","))
        # dontAsk still runs what a loaded settings file allows, and a worktree loads the main checkout's
        # local file (Grok F4). Lists merge across sources, so no source's write allow may take effect.
        write_rule = "Bash(touch *)"
        policy = json.dumps({"permissions": {"allow": [write_rule]}})
        # --restricted still loads managed settings (Sol F5): a managed file or a server-managed cache refuses.
        managed, config = tmp_path / "etc-claude-code", tmp_path / "config"
        monkeypatch.setattr("scripts.agent_runtime.env_sanitize._CLAUDE_MANAGED_SETTINGS_DIR", managed)
        config.mkdir()
        run_env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path), "CLAUDE_CONFIG_DIR": str(config)}
        for source, expected in ((managed / "managed-settings.json", "managed policy in /etc/claude-code is present"),
                                 (config / "remote-settings.json", "the server-managed settings cache holds a policy")):
            source.parent.mkdir(exist_ok=True)
            source.write_text(policy)
            assert providers.read_only_refusal(agent, run_env) == (
                f"read_only_unenforceable: claude cannot run --mode read-only: {expected}; "
                "use codex, cursor, agy, muse, opencode"
            )
            source.unlink()
        assert providers.read_only_refusal(agent, run_env) is None
        for account in ("a", "b"):
            argv = providers.load(agent).build(dataclasses.replace(spec, claude_account=account), run_env).argv
            assert argv[argv.index("--append-system-prompt-file") + 1] == str(
                rules_core.source_path(rules_core.CORE_REL))  # --restricted skips CLAUDE.md (Sol F6)
            if "--restricted" in argv:  # loads only managed settings, absent above, and --settings
                sources = []
            elif "--setting-sources" in argv:
                sources = argv[argv.index("--setting-sources") + 1].split(",")
            else:
                sources = ["user", "project", "local"]
            allows = set(argv[argv.index("--allowedTools") + 1].split(","))
            if sources:  # each settings file loaded from these sources allows write_rule
                allows.add(write_rule)
            if "--settings" in argv:
                allows |= set(json.loads(argv[argv.index("--settings") + 1]).get("permissions", {}).get("allow", []))
            assert write_rule not in allows, account
            assert argv[argv.index("--tools") + 1] == "Read,Grep,Glob,Bash,WebFetch,WebSearch"
        plan = sandbox.cli("dispatch", "--agent", agent, "--model", "vendor/model", "--prompt", "Fix X", "--dry-run")
        assert "--restricted" in json.loads(plan.stdout)["argv"]
    else:
        assert agent == "opencode" and "--auto" not in argv
        permission = json.loads(invocation.env["OPENCODE_PERMISSION"])
        assert permission["edit"] == "deny"
        assert permission["bash"]["*"] == "deny" and permission["bash"]["*>*"] == "deny"
        assert list(permission["bash"])[-1] == "*>*"  # the last matching pattern wins


def test_aliases_and_all_retained_metadata_flags_parse():
    assert dict(sol="codex", gemini="agy", deepseek="opencode") == ALIASES
    args = build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "sol",
            "--model",
            "gpt-6.1-sol",
            "--prompt",
            "x",
            "--owned-path",
            "scripts",
            "--research-owned-path",
            "tests",
            "--risk",
            "critical",
            "--review-mode",
            "red_team",
            "--language-lane",
            "en",
            "--output-schema",
            "schema.json",
        ]
    )
    assert args.owned_path == ["scripts"]
    assert args.research_owned_path == ["tests"]


def test_initial_response_timeout_default_is_600():
    """Ported from tests/test_delegate.py::test_initial_response_timeout_default_is_600."""
    args = build_parser().parse_args(["dispatch", "--agent", "codex", "--model", "gpt-6.1-sol", "--prompt", "hi"])
    assert args.initial_response_timeout == 600
    assert args.silence_timeout == 3600


def test_run_worker_silence_timeout_kills_silent_subprocess(sandbox):
    """Ported from tests/test_delegate.py with the same test name, including process-tree cleanup."""
    started = time.monotonic()
    task = sandbox.dispatch("tree", "--hard-timeout", "30", "--silence-timeout", "1")
    record = sandbox.settle(task, expected=1)
    assert time.monotonic() - started < 6
    assert record["returncode"] == -signal.SIGKILL
    assert record["status"] == "timeout"
    assert "stdout_silence_timeout" in record["stderr_excerpt"]
    assert record["silence_timeout"] == 1
    grandchild = int(Path(record["prompt_file"]).with_suffix(".grandchild").read_text())
    assert worker._identity(grandchild) is None


def test_provider_process_lingering_after_its_final_result_settles_with_that_result(sandbox, monkeypatch):
    """Defect class: a finished run held open until timeout."""
    from scripts.dispatcher import watchdog
    from scripts.dispatcher.providers import agy
    from scripts.dispatcher.types import Invocation

    monkeypatch.setenv("LU_TASKS_DIR", str(sandbox.tasks))
    monkeypatch.setattr(worker, "_reap_settled", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(worker.headroom, "check_plan", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(worker.headroom, "check_runtime", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(watchdog, "_PROCESS_ACTIVITY_POLL_INTERVAL_S", 0.05)
    monkeypatch.setattr(watchdog, "TERMINAL_EXIT_GRACE_S", 1)
    monkeypatch.setattr(worker, "TERMINAL_EXIT_GRACE_S", 1)
    monkeypatch.setattr(worker.agy_sandbox, "verify", lambda *_args: ({}, None, None))
    spec = TaskSpec("agy-final-hang", "agy", "gemini-3.8-flash-high", None, "read-only", sandbox.repo,
                    sandbox.repo / "agy-final-hang.prompt", sandbox.tasks / "agy-final-hang.result",
                    options={"hard_timeout": "5", "silence_timeout": "0.5"})
    spec.prompt_file.write_bytes(b"literal final response")
    log = sandbox.repo / "provider.log"
    code = (
        "import json, sys, time\n"
        "print(json.dumps({'event': 'init', 'init': {'model': 'gemini-3.8-flash-high'}}), flush=True)\n"
        "print(json.dumps({'event': 'result', 'result': {'status': 'SUCCESS', "
        "'response': 'literal final response'}}), flush=True)\n"
        "with open(sys.argv[2], 'a') as log:\n"
        "    while True:\n"
        "        log.write('idle housekeeping\\n'); log.flush(); time.sleep(0.02)\n"
    )
    monkeypatch.setattr(agy, "build", lambda _spec, env: Invocation(
        [sys.executable, "-c", code, "--log-file", str(log)],
        b'{"event":"user","message":{"role":"user","content":[{"type":"text","text":""}]}}\n', env, None))
    head = run_git(sandbox.repo, "rev-parse", "HEAD")
    record = store.new_record(spec, {"key": "public", "github": str(sandbox.remote)}, "main", head,
                              {"research_owned_path": []})
    record["prompt_file"] = str(sandbox.tasks / "agy-final-hang.prompt")
    path = store.create(record, b"literal final response")
    (sandbox.tasks / "logs").mkdir()

    started = time.monotonic()
    worker.supervise(path)
    elapsed = time.monotonic() - started

    result = json.loads(path.read_text())
    assert result["status"] == "done"
    assert result["error"] is None
    assert elapsed < 3
    assert worker._identity(result["provider_pgid"]) is None
    assert log.stat().st_size > 0
    assert spec.final_file.read_text() == "literal final response"


@pytest.mark.parametrize(("mode", "status"), [("read-only", "done"), ("workspace-write", "no_deliverable")])
def test_a_run_settling_while_a_task_it_dispatched_still_runs_names_that_task(sandbox, mode, status):
    """Defect class: a worker's result orphaned by its own end read as a bare no_deliverable (#12156)."""
    sandbox.env.pop("LEARN_UKRAINIAN_DISPATCH_TASK_ID", None)  # the parent is dispatched from outside any run
    parent = sandbox.dispatch("blocked", "--mode", mode)
    await_file(sandbox.tasks / f"{parent[0]}.started")
    # The child is dispatched from inside the parent's run, which hands its commands the parent's task id.
    result = subprocess.run(
        [sys.executable, "scripts/dispatch.py", "dispatch", "--agent", "sol", "--model", "blocked",
         "--prompt", "literal child request"],
        cwd=sandbox.repo, env={**sandbox.env, "LEARN_UKRAINIAN_DISPATCH_TASK_ID": parent[0]},
        text=True, capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    child = tuple(result.stdout.splitlines())
    await_file(sandbox.tasks / f"{child[0]}.started")
    assert json.loads((sandbox.tasks / f"{child[0]}.json").read_text())["parent_task_id"] == parent[0]
    assert "parent_task_id" not in json.loads((sandbox.tasks / f"{parent[0]}.json").read_text())

    (sandbox.tasks / f"{parent[0]}.release").touch()
    record = sandbox.settle(parent, expected=0 if status == "done" else 1)
    assert record["status"] == status
    assert record["orphaned_child_tasks"] == [child[0]]
    if status == "done":
        assert record["error"] is None
    else:
        assert record["error"] == f"orphaned_child_tasks: {child[0]}; {record['no_deliverable_reason']}"

    (sandbox.tasks / f"{child[0]}.release").touch()
    assert "orphaned_child_tasks" not in sandbox.settle(child)


def test_agy_write_run_does_not_settle_while_its_child_is_running(sandbox, monkeypatch):
    """Defect class: an AGY workspace-write run that exits 0 on an interim reply while a child task is still active settles done or no_deliverable."""
    from scripts.dispatcher.providers import agy
    from scripts.dispatcher.types import Invocation

    monkeypatch.setenv("LU_TASKS_DIR", str(sandbox.tasks))
    monkeypatch.setattr(worker, "_reap_settled", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(worker.headroom, "check_plan", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(worker.headroom, "check_runtime", lambda *_args, **_kwargs: None)
    code = (
        "import json\n"
        "print(json.dumps({'event': 'init', 'init': {'model': 'gemini-3.8-flash-high'}}), flush=True)\n"
        "print(json.dumps({'event': 'result', 'result': {'status': 'SUCCESS', "
        "'response': 'I will pause to await the review verdict.'}}), flush=True)\n"
    )
    monkeypatch.setattr(agy, "build", lambda _spec, env: Invocation(
        [sys.executable, "-c", code],
        b'{"event":"user","message":{"role":"user","content":[{"type":"text","text":""}]}}\n', env, None))
    head = run_git(sandbox.repo, "rev-parse", "HEAD")
    remote = {"key": "public", "github": str(sandbox.remote)}
    spec = TaskSpec("agy-write-child", "agy", "gemini-3.8-flash-high", None, "workspace-write", sandbox.repo,
                    sandbox.repo / "agy-write-child.prompt", sandbox.tasks / "agy-write-child.result")
    spec.prompt_file.write_bytes(b"literal parent request")
    record = store.new_record(spec, remote, "main", head, {"research_owned_path": []})
    record["prompt_file"] = str(sandbox.tasks / "agy-write-child.prompt")
    path = store.create(record, b"literal parent request")
    child_spec = TaskSpec("agy-write-review", "sol", "blocked", None, "read-only", sandbox.repo,
                          sandbox.repo / "agy-write-review.prompt", sandbox.tasks / "agy-write-review.result")
    child_spec.prompt_file.write_bytes(b"literal child request")
    child = store.new_record(child_spec, remote, "main", head, {"research_owned_path": []})
    child["prompt_file"] = str(sandbox.tasks / "agy-write-review.prompt")
    child_path = store.create(child, b"literal child request")
    child = json.loads(child_path.read_text())
    child.update(status="running", parent_task_id="agy-write-child")
    store.replace(child, child_path, require_existing=True)
    (sandbox.tasks / "logs").mkdir()

    started = time.monotonic()
    worker.supervise(path, {}, 2)
    elapsed = time.monotonic() - started

    result = json.loads(path.read_text())
    assert result["status"] not in {"done", "no_deliverable"}
    assert "agy-write-review" in (result.get("error") or "")
    assert elapsed < 8


@pytest.mark.parametrize(("inherited", "parent"), [("dispatching-run", "dispatching-run"), ("self-run", None),
                                                    (None, None)])
def test_dispatch_records_the_run_it_was_dispatched_from_never_itself(sandbox, inherited, parent):
    """Defect class: orphan detection silently disabled, or a task that names itself as its parent (#12156)."""
    sandbox.env.pop("LEARN_UKRAINIAN_DISPATCH_TASK_ID", None)
    if inherited is not None:
        sandbox.env["LEARN_UKRAINIAN_DISPATCH_TASK_ID"] = inherited
    task = sandbox.dispatch("echo", "--task-id", "self-run")
    assert sandbox.settle(task).get("parent_task_id") == parent


def test_run_worker_initial_response_timeout_still_reaps_silent_startup(sandbox):
    """Ported from tests/test_delegate.py with the same test name."""
    started = time.monotonic()
    task = sandbox.dispatch("tree", "--hard-timeout", "30", "--silence-timeout", "30",
                            "--initial-response-timeout", "1")
    record = sandbox.settle(task, expected=1)
    assert time.monotonic() - started < 6
    assert record["returncode"] == -signal.SIGKILL
    assert record["status"] == "timeout"
    excerpt = record["stderr_excerpt"]
    assert "initial_response_timeout" in excerpt
    assert "fired after 1s" in excerpt
    assert "no first observable startup activity" in excerpt
    assert "--initial-response-timeout" in excerpt


@pytest.mark.parametrize("output", ["sys.stdout", "sys.stderr"])
def test_run_worker_periodic_stdout_avoids_silence_timeout(sandbox, output):
    """Ported from tests/test_delegate.py with the same test name, observing both output streams."""
    stub = sandbox.repo / "scripts/dispatcher/providers/codex.py"
    stub.write_text(stub.read_text().replace(
        '    model, prompt, final = sys.argv[1:]',
        f"    for i in range(5):\n        print('tick', file={output}, flush=True)\n        time.sleep(0.2)\n"
        '    model, prompt, final = sys.argv[1:]',
    ))
    task = sandbox.dispatch("echo", "--hard-timeout", "10", "--silence-timeout", "1",
                            "--initial-response-timeout", "1")
    record = sandbox.settle(task)
    assert record["status"] == "done"
    expected = "tick\n" * 5 + "literal final response" if output == "sys.stdout" else "literal final response"
    assert Path(record["result_file"]).read_text() == expected
    assert record["silence_timeout"] == 1
    assert record["initial_response_timeout"] == 1


# Ports of the legacy status-or-fail and child identity contracts in tests/test_delegate.py.
def test_status_or_fail_running_task_exits_zero_quiet(tmp_path, monkeypatch, capsys):
    """Ported from tests/test_delegate.py::test_status_or_fail_running_task_exits_zero_quiet."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    (tmp_path / "sleep-task.json").write_text(json.dumps(dict(
        task_id="sleep-task", status="running", started_at=store.now(),
        pid=os.getpid(), process_start=worker._identity(os.getpid()),
    )))

    rc = cli.main(["status-or-fail", "sleep-task"])

    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


@pytest.mark.parametrize("case, expected_status, nonce", [
    ("dead-pid", "stale", "record-nonce"),
    ("mismatched-process-start", "stale", "record-nonce"),
    ("missing-process-start", "stale", "record-nonce"),
    ("nonce-mismatch", "stale_run_nonce", "wrong-nonce"),
])
def test_status_or_fail_dead_supervisor_never_reported_alive(
    tmp_path, monkeypatch, capsys, case, expected_status, nonce,
):
    """Reject stale supervisor identities and nonces without rewriting the record."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    record = dict(
        task_id="sleep-task", status="running", started_at=store.now(),
        run_nonce="record-nonce", pid=os.getpid(), process_start=worker._identity(os.getpid()),
    )
    if case == "dead-pid":
        with subprocess.Popen([sys.executable, "-c", "pass"]) as process:
            process.wait(timeout=10)
        record["pid"] = process.pid
    elif case == "mismatched-process-start":
        record["process_start"] = "different-process-start"
    elif case == "missing-process-start":
        record.pop("process_start")
    path = tmp_path / "sleep-task.json"
    original = json.dumps(record).encode()
    path.write_bytes(original)

    rc = cli.main(["status-or-fail", "sleep-task", "--verbose", "--run-nonce", nonce])

    assert rc == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["status"] == expected_status
    assert payload["alive"] is False
    assert payload["run_nonce"] == (None if case == "nonce-mismatch" else "record-nonce")
    assert f"task sleep-task is not running (status={expected_status}, age=" in captured.err
    assert path.read_bytes() == original


@pytest.mark.parametrize("status", [
    "done", "failed", "timeout", "rate_limited", "cancelled", "crashed", "dry_run",
    "needs_finalize", "no_deliverable",
])
def test_status_or_fail_completed_task_exits_one(tmp_path, monkeypatch, capsys, status):
    """Ported from tests/test_delegate.py::test_status_or_fail_completed_task_exits_one."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    (tmp_path / "sleep-task.json").write_text(json.dumps(dict(
        task_id="sleep-task", status=status, started_at=store.now(),
    )))

    rc = cli.main(["status-or-fail", "sleep-task"])

    assert rc == 1
    captured = capsys.readouterr()
    assert f"task sleep-task is not running (status={status}, age=" in captured.err
    assert captured.err.rstrip().endswith("s)")


def test_status_or_fail_unknown_task_exits_one(tmp_path, monkeypatch, capsys):
    """Ported from tests/test_delegate.py::test_status_or_fail_unknown_task_exits_one."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))

    rc = cli.main(["status-or-fail", "missing"])

    assert rc == 1
    captured = capsys.readouterr()
    assert "task missing is not running" in captured.err
    assert "task not found" in captured.err


def test_status_or_fail_monitor_api_down_exits_two(monkeypatch, capsys):
    """Ported from tests/test_delegate.py::test_status_or_fail_monitor_api_down_exits_two.

    V2's unavailable authority is its task store, rather than the Monitor API.
    """
    monkeypatch.setattr(store, "read", Mock(side_effect=OSError("unavailable")))

    rc = cli.main(["status-or-fail", "sleep-task"])

    assert rc == 2
    captured = capsys.readouterr()
    assert "Dispatcher state unavailable" in captured.err


def test_status_or_fail_verbose_byte_compatible_without_run_nonce(tmp_path, monkeypatch, capsys):
    """Ported from tests/test_delegate.py::test_status_or_fail_verbose_byte_compatible_without_run_nonce."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    (tmp_path / "test-sof-task.json").write_text(json.dumps(dict(
        task_id="test-sof-task", status="running", started_at="2026-08-20T10:00:00Z",
        run_nonce="sof-nonce-12345", pid=os.getpid(), process_start=worker._identity(os.getpid()),
    )))

    rc = cli.main(["status-or-fail", "test-sof-task", "--verbose"])
    assert rc == 0
    data_no_nonce = json.loads(capsys.readouterr().out)
    assert list(data_no_nonce.keys()) == ["task_id", "status", "age_s", "alive"]
    assert "run_nonce" not in data_no_nonce

    rc2 = cli.main(["status-or-fail", "test-sof-task", "--verbose", "--run-nonce", "sof-nonce-12345"])
    assert rc2 == 0
    data_with_nonce = json.loads(capsys.readouterr().out)
    assert data_with_nonce["run_nonce"] == "sof-nonce-12345"


@pytest.mark.parametrize("agent", ["codex", "claude", "cursor", "agy", "muse", "opencode"])
def test_dispatch_worker_env_carries_dispatch_identity_markers(spec, monkeypatch, agent):
    """Ported from tests/test_delegate.py::test_dispatch_worker_env_carries_dispatch_identity_markers."""
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "parent-task")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "parent-agent")

    env = child_env(dataclasses.replace(spec, task_id="dispatch-marker-check", agent=agent))

    assert env["LEARN_UKRAINIAN_DISPATCH_TASK_ID"] == "dispatch-marker-check"
    assert env["LEARN_UKRAINIAN_DISPATCH_AGENT"] == agent
    assert os.environ["LEARN_UKRAINIAN_DISPATCH_TASK_ID"] == "parent-task"
    assert os.environ["LEARN_UKRAINIAN_DISPATCH_AGENT"] == "parent-agent"

    process = SimpleNamespace(pid=os.getpid(), stdin=SimpleNamespace(write=Mock(), close=Mock()))
    launch = Mock(return_value=process)
    monkeypatch.setattr(worker.subprocess, "Popen", launch)
    monkeypatch.setenv("LU_DISPATCH_ISOLATION", "fallback")
    monkeypatch.setattr(worker.admission.dispatch_isolation, "_caller_in_driver_scope", lambda: False)
    monkeypatch.setattr(worker, "project_interpreter", Mock(return_value=Path(sys.executable)))
    monkeypatch.setattr(store, "create", Mock(return_value=spec.worktree / "record.json"))
    monkeypatch.setattr(store, "replace", Mock())

    worker.start(dataclasses.replace(spec, task_id="dispatch-marker-check", agent=agent),
                 {"run_nonce": "n" * 32}, b"test", 3600)

    supervisor_env = launch.call_args.kwargs["env"]
    assert supervisor_env["LEARN_UKRAINIAN_DISPATCH_TASK_ID"] == "dispatch-marker-check"
    assert supervisor_env["LEARN_UKRAINIAN_DISPATCH_AGENT"] == agent


def _slot_pool(tmp_path, monkeypatch):
    from scripts.common import test_slots

    path = tmp_path / "pool"
    monkeypatch.setenv(test_slots.ENABLE_ENV, "on")
    monkeypatch.setenv(test_slots.DIR_ENV, str(path))
    monkeypatch.setenv(test_slots.COUNT_ENV, "4")
    monkeypatch.setenv(test_slots.WAIT_ENV, "5")
    monkeypatch.delenv(test_slots.HOLDER_ENV, raising=False)
    monkeypatch.delenv(test_slots.SESSION_ENV, raising=False)
    monkeypatch.delenv("CI", raising=False)
    return path


def _review_slot_hold(**overrides):
    from scripts.dispatcher import admission

    arguments = {"agent": "codex", "mode": "read-only", "review_typed": True, "sealed_attempt": False,
                 "task_id": "review-11230-worker-fixture"}
    arguments.update(overrides)
    return admission.hold_review_test_slots(**arguments)


def test_a_codex_read_only_review_holds_review_slots_for_its_task(tmp_path, monkeypatch) -> None:
    from scripts.common import test_slots
    from scripts.dispatcher import admission

    _slot_pool(tmp_path, monkeypatch)
    hold, record = _review_slot_hold()
    try:
        assert hold is not None and record == {"outcome": "held", "slots": 2, "waited_s": record["waited_s"]}
        holders = test_slots.status()["holders"]
        assert [(entry["task_id"], entry["kind"], entry["slots"]) for entry in holders] == [
            ("review-11230-worker-fixture", "review", 2)
        ]
        env = {**os.environ, **hold.environment(), test_slots.TASK_ENV: "review-11230-worker-fixture"}
        assert test_slots.inherited_hold(env) == admission.REVIEW_TEST_SLOTS
    finally:
        if hold is not None:
            hold.release()
    assert test_slots.status()["slots_in_use"] == 0


@pytest.mark.parametrize(
    "overrides",
    [
        {"agent": "claude"},
        {"agent": "agy"},
        {"mode": "workspace-write"},
        {"review_typed": False},
        {"sealed_attempt": True},
    ],
    ids=["claude", "agy", "workspace-write", "not-a-review", "sealed-attempt"],
)
def test_every_other_route_takes_its_own_slots_or_none(tmp_path, monkeypatch, overrides) -> None:
    """No double counting: a seat that can prepare the pool, or runs no tests, holds nothing up front."""
    pool = _slot_pool(tmp_path, monkeypatch)
    assert _review_slot_hold(**overrides) == (None, None)
    assert not pool.exists()


def test_a_disabled_pool_holds_nothing(tmp_path, monkeypatch) -> None:
    from scripts.common import test_slots

    pool = _slot_pool(tmp_path, monkeypatch)
    monkeypatch.setenv(test_slots.ENABLE_ENV, "off")
    assert _review_slot_hold() == (None, {"outcome": "disabled"})
    assert not pool.exists()


def test_a_refused_hold_is_recorded_and_the_review_runs_on(tmp_path, monkeypatch, capsys) -> None:
    from scripts.common import test_slots

    _slot_pool(tmp_path, monkeypatch)
    shared = tmp_path / "shared"
    shared.mkdir(mode=0o777)
    shared.chmod(0o777)  # another user could redirect a pool below it
    monkeypatch.setenv(test_slots.DIR_ENV, str(shared / "pool"))

    assert _review_slot_hold() == (None, {"outcome": "refused", "reason": "pool_unavailable"})
    assert "review test slots refused" in capsys.readouterr().err
    assert not (shared / "pool").exists()


def test_a_dispatched_worker_never_inherits_its_dispatchers_marker(spec, monkeypatch) -> None:
    from scripts.common import test_slots

    monkeypatch.setenv(test_slots.HOLDER_ENV, "2:/elsewhere/holders/x.ticket")
    monkeypatch.setenv(test_slots.SESSION_ENV, "/s")
    env = child_env(dataclasses.replace(spec, agent="codex"))
    assert test_slots.HOLDER_ENV not in env and test_slots.SESSION_ENV not in env


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
@pytest.mark.parametrize("agent", ["codex", "claude", "cursor", "agy", "muse", "opencode"])
def test_worker_env_disables_the_node_compile_cache(spec, monkeypatch, tmp_path, agent, mode):
    """#12474: a worker's lint or tsc run must not add to the shared on-disk Node compile cache."""
    monkeypatch.setenv("NODE_COMPILE_CACHE", str(tmp_path / "shared-cache"))
    monkeypatch.delenv("NODE_DISABLE_COMPILE_CACHE", raising=False)

    env = child_env(dataclasses.replace(spec, agent=agent, mode=mode))

    assert env["NODE_DISABLE_COMPILE_CACHE"] == "1"
    assert "NODE_COMPILE_CACHE" not in env


@pytest.mark.parametrize(
    "extra,code",
    [
        # Ported from tests/test_delegate.py (the claude_account refusal table): unknown labels.
        (["--agent", "claude", "--claude-account", "c"], "claude_account_unknown"),
        (["--agent", "claude", "--claude-account", "B"], "claude_account_unknown"),
        (["--agent", "codex", "--claude-account", "b"], "claude_account_seat_unsupported"),
        (["--agent", "claude", "--claude-account", "b"], "claude_account_ambient_conflict"),
        # API-key labels (C-2643): the same guard, and only their exact names.
        (["--agent", "claude", "--claude-account", "kk"], "claude_account_ambient_conflict"),
        (["--agent", "claude", "--claude-account", "szb"], "claude_account_ambient_conflict"),
        (["--agent", "claude", "--claude-account", "KK"], "claude_account_unknown"),
        (["--agent", "codex", "--claude-account", "szb"], "claude_account_seat_unsupported"),
    ],
)
def test_dispatch_refuses_claude_account_before_any_side_effect(tmp_path, monkeypatch, capsys, extra, code):
    from scripts.dispatcher import cli

    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "fixture-ambient-" + "e" * 30)
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", str(tmp_path / "absent.json"))
    for target, name in ((git, "create_worktree"), (git, "resolve_repo"), (worker, "start")):
        monkeypatch.setattr(target, name, lambda *_a, _name=name, **_k: pytest.fail(f"{_name} ran before refusal"))

    assert cli.main(["dispatch", "--task-id", "claude-account-refused", "--prompt", "test", "--model", "m", *extra]) == 2

    err = capsys.readouterr().err
    assert f"CLAUDE_ACCOUNT_REFUSED: {code}\n" in err
    assert "fixture-ambient" not in err
    assert not tasks.exists()


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
def test_claude_argv_caps_an_api_key_run_and_leaves_a_subscription_run_alone(tmp_path, mode):
    """An uncapped paid run is the defect: only an API-key label carries ``--max-budget-usd``."""
    from scripts.agent_runtime.attempt_boundary import CLAUDE_API_KEY_BUDGET_USD

    spec = TaskSpec("cap", "claude", "m", None, mode, tmp_path, tmp_path / "p", tmp_path / "f")
    spec.prompt_file.write_bytes(b"prompt")
    build = providers.load("claude").build
    for label, amount in CLAUDE_API_KEY_BUDGET_USD.items():
        invocation = build(dataclasses.replace(spec, claude_account=label), {})
        assert invocation.argv[invocation.argv.index("--max-budget-usd") + 1] == f"{amount:.2f}"
        assert invocation.env.get("CLAUDE_CODE_PROMPT_CACHE_TTL") == ("1h" if mode == "workspace-write" else None)
    lowered = dataclasses.replace(spec, claude_account="kk", options={"max_budget_usd": "2.5"})
    assert build(lowered, {}).argv[build(lowered, {}).argv.index("--max-budget-usd") + 1] == "2.50"
    for label in ("a", "b", None):
        invocation = build(dataclasses.replace(spec, claude_account=label), {})
        assert "--max-budget-usd" not in invocation.argv
        assert "CLAUDE_CODE_PROMPT_CACHE_TTL" not in invocation.env


def _plan_headroom_policy(tmp_path, monkeypatch, used, **extra):
    from scripts.dispatcher import headroom

    path = tmp_path / "model-pause.json"
    policy = {"headroom": [{"lane": "claude", "pattern": "claude-*", "max_weekly_used_pct": 90}], **extra}
    path.write_text(json.dumps(policy), encoding="utf-8")
    monkeypatch.setenv("LU_MODEL_PAUSE_FILE", str(path))
    monkeypatch.setattr(headroom.model_pause, "routing_budget_used_pct", lambda _lane, *, account: used)
    return headroom


def test_check_plan_judges_an_api_key_account_by_its_spend_cap(tmp_path, monkeypatch):
    """Defect (#12356): an API-key account has no plan meter, so the plan cap refused it as unknown usage."""
    headroom = _plan_headroom_policy(tmp_path, monkeypatch, None)
    record = {"claude_account": "kk", "mode": "read-only"}
    headroom.check_plan("claude", "claude-opus-5-5", record)
    with pytest.raises(ValueError, match=r"^CLAUDE_ACCOUNT_REFUSED: claude_account_budget_cap_invalid$"):
        headroom.check_plan("claude", "claude-opus-5-5", {**record, "max_budget_usd": "1000"})
    _plan_headroom_policy(tmp_path, monkeypatch, None, pauses=[{"pattern": "claude-*", "until": "2999-01-01T00:00:00Z"}])
    with pytest.raises(headroom.model_pause.ModelPausedRefused, match="MODEL_PAUSED"):
        headroom.check_plan("claude", "claude-opus-5-5", record)


@pytest.mark.parametrize(("used", "reason"), [(95.0, "MODEL_HEADROOM:"), (None, "MODEL_HEADROOM_USAGE_UNKNOWN:")])
def test_check_plan_keeps_subscription_plan_headroom(tmp_path, monkeypatch, used, reason):
    """Control (#12356): a subscription account is still judged by its plan meter."""
    headroom = _plan_headroom_policy(tmp_path, monkeypatch, used)
    for label in ("a", "b"):
        with pytest.raises(headroom.model_pause.ModelPausedRefused, match=f"^{reason}"):
            headroom.check_plan("claude", "claude-opus-5-5", {"claude_account": label, "mode": "read-only"})
    _plan_headroom_policy(tmp_path, monkeypatch, 50.0)
    headroom.check_plan("claude", "claude-opus-5-5", {"claude_account": "a", "mode": "read-only"})


@pytest.mark.parametrize(
    ("model", "mode", "options", "advised"),
    [
        ("claude-sonnet-5-5", "workspace-write", {}, True),
        ("claude-sonnet-5-5", "read-only", {}, False),
        ("claude-opus-5-5", "workspace-write", {}, False),
        ("claude-haiku-5-5", "workspace-write", {}, False),
        ("claude-haiku-5-5", "workspace-write", {"advisor": "opus"}, True),
        ("sonnet[1m]", "workspace-write", {}, True),
        ("haiku", "workspace-write", {}, False),
        ("haiku", "workspace-write", {"advisor": "opus"}, True),
    ],
)
def test_claude_advisor_is_attached_only_to_the_approved_runs(tmp_path, model, mode, options, advised):
    """Advisor spend outside the approved scope is the defect: only the approved runs carry ``--advisor opus``."""
    spec = TaskSpec("adv", "claude", model, None, mode, tmp_path, tmp_path / "p", tmp_path / "f", options=options)
    spec.prompt_file.write_bytes(b"prompt")
    for label in (None, "kk"):
        invocation = providers.load("claude").build(dataclasses.replace(spec, claude_account=label), {})
        assert ("--advisor" in invocation.argv) is advised
        if advised:
            assert invocation.argv[invocation.argv.index("--advisor") + 1] == "opus"
            assert invocation.argv[invocation.argv.index("--model") + 1].startswith(("claude-sonnet-5-5", "claude-haiku-5-5"))
            assert "CLAUDE_CODE_DISABLE_ADVISOR_TOOL" not in invocation.env
            assert "DISABLE_TELEMETRY" not in invocation.env
        else:
            assert invocation.env["CLAUDE_CODE_DISABLE_ADVISOR_TOOL"] == "1"


def test_advised_claude_run_on_another_executor_model_settles_as_a_failure(sandbox, monkeypatch):
    """Defect: an advised run silently executing on an unapproved model settled done."""
    from scripts.dispatcher.providers import claude

    result = {"type": "result", "subtype": "success", "is_error": False, "result": "done", "usage": {},
              "modelUsage": {"claude-sonnet-4-6": {"canonicalModel": "claude-sonnet-4-6"},
                             "claude-opus-5-5": {"canonicalModel": "claude-opus-5-5"}}}
    code = f"import sys\nsys.stdin.read()\nprint({json.dumps(result)!r})\n"
    monkeypatch.setenv("LU_TASKS_DIR", str(sandbox.tasks))
    monkeypatch.setattr(claude, "build", lambda spec, env: Invocation([sys.executable, "-c", code], b"", env, None))
    monkeypatch.setattr(worker, "_reap_settled", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(worker.headroom, "check_plan", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(worker.headroom, "check_runtime", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(git, "snapshot_delivery", lambda *_args: {})
    spec = TaskSpec("advised", "claude", "sonnet", None, "workspace-write", sandbox.repo,
                    sandbox.repo / "advised.prompt", sandbox.tasks / "advised.result")
    spec.prompt_file.write_bytes(b"prompt")
    record = store.new_record(spec, {"key": "public", "github": str(sandbox.remote)}, "main",
                              run_git(sandbox.repo, "rev-parse", "HEAD"), {"research_owned_path": []})
    record["prompt_file"] = str(sandbox.tasks / "advised.prompt")
    path = store.create(record, b"prompt")
    (sandbox.tasks / "logs").mkdir()
    worker.supervise(path, {}, 10)
    settled = json.loads(path.read_text())
    assert settled["status"] == "failed"
    assert settled["error"] == (
        "claude_advisor_executor_unverified: approved claude-sonnet-5-5, reported claude-opus-5-5, claude-sonnet-4-6"
    )
    assert (settled["resolved_model"], settled["resolved_model_known"], settled["resolved_model_source"]) == (
        "claude-sonnet-4-6", True, "claude-result-model-usage")


def _spawn_refused_record(tmp_path, monkeypatch, task_id):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    path = store.record_path(task_id)
    record = {"task_id": task_id, "run_nonce": "n" * 32, "status": "spawning", "pid": None,
              "prompt_file": str(path.with_suffix(".prompt"))}
    spec = TaskSpec(task_id, "codex", "m", None, "read-only", tmp_path, path.with_suffix(".prompt"),
                    path.with_suffix(".result"))
    return spec, record, path


def test_dispatch_ambiguous_scope_start_marks_task_failed(tmp_path, monkeypatch) -> None:
    from scripts.dispatcher import admission
    from scripts.orchestration import dispatch_isolation

    spec, record, path = _spawn_refused_record(tmp_path, monkeypatch, "ambiguous-scope")

    def explode(*_args, **_kwargs):
        raise dispatch_isolation.DispatchIsolationError(
            "systemd-run: worker start marker arrived after the startup timeout (2s) "
            "for unit lu-worker-ambiguous-scope; the scope was stopped and will not be relaunched"
        )

    monkeypatch.setattr(dispatch_isolation, "spawn_detached_worker", explode)
    with pytest.raises(admission.LaunchRefused):
        worker.start(spec, record, b"prompt", 60)

    state = json.loads(path.read_text())
    assert state["status"] == "failed"
    assert state["pid"] is None
    assert state["error"].startswith("dispatch_isolation_failed: ")
    assert "will not be relaunched" in state["error"]


@pytest.mark.parametrize(
    "reason",
    ["inside-driver-scope; systemd-run unavailable", "caller-cgroup-unavailable", "caller-cgroup-unverifiable"],
)
def test_dispatch_fallback_refusal_records_no_worker_started(tmp_path, monkeypatch, reason) -> None:
    from scripts.dispatcher import admission
    from scripts.orchestration import dispatch_isolation

    spec, record, path = _spawn_refused_record(tmp_path, monkeypatch, "fallback-refusal")
    refusal = f"fallback-refused: {reason}"
    spawn = Mock(side_effect=dispatch_isolation.DispatchIsolationError(refusal))
    popen = Mock()
    monkeypatch.setattr(dispatch_isolation, "spawn_detached_worker", spawn)
    monkeypatch.setattr(subprocess, "Popen", popen)
    with pytest.raises(admission.LaunchRefused):
        worker.start(spec, record, b"prompt", 60)

    spawn.assert_called_once()
    popen.assert_not_called()
    state = json.loads(path.read_text())
    assert state["status"] == "failed"
    assert state["pid"] is None
    assert state["error"].startswith("dispatch_fallback_refused: ")
    assert refusal in state["error"]
    assert "ambiguous" not in state["error"]


def test_dispatch_popen_failure_records_worktree_head(tmp_path, monkeypatch) -> None:
    """Ported from tests/test_delegate.py::test_dispatch_popen_failure_records_worktree_head.

    v2 records the worktree head (``head_sha``) when the record is created; a failed spawn keeps it.
    """
    from scripts.dispatcher import admission
    from scripts.orchestration import dispatch_isolation

    spec, record, path = _spawn_refused_record(tmp_path, monkeypatch, "popen-head")
    record["head_sha"] = "a" * 40
    monkeypatch.setattr(
        dispatch_isolation, "spawn_detached_worker", Mock(side_effect=FileNotFoundError("no such file"))
    )
    with pytest.raises(admission.LaunchRefused):
        worker.start(spec, record, b"prompt", 60)

    state = json.loads(path.read_text())
    assert state["status"] == "failed"
    assert state["pid"] is None
    assert state["error"] == "worker_spawn_failed: Popen failed: FileNotFoundError: no such file"
    assert state["head_sha"] == "a" * 40


def _fake_pool(directory, *, current, file_cache, high=21 * 1024**3):
    """Ported from tests/test_dispatch_admission.py::_fake_pool."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "memory.current").write_text(f"{current}\n", encoding="ascii")
    (directory / "memory.high").write_text(f"{high}\n", encoding="ascii")
    (directory / "memory.max").write_text(f"{23 * 1024**3}\n", encoding="ascii")
    (directory / "memory.stat").write_text(f"active_file {file_cache}\ninactive_file 0\n", encoding="ascii")
    return directory


def _full_disk(monkeypatch, *readings):
    """Ported from tests/test_delegate_admission.py::_full_disk."""
    from scripts.orchestration import dispatch_admission

    seen = {"readings": list(readings), "alerts": []}

    def probe():
        values = seen["readings"]
        used = values.pop(0) if len(values) > 1 else values[0]
        used_bytes = int(400 * 1024**3 * used / 100)
        return dispatch_admission.DiskProbe(used_bytes=used_bytes, free_bytes=400 * 1024**3 - used_bytes)

    monkeypatch.setattr(dispatch_admission, "probe_disk", probe)
    monkeypatch.setattr(dispatch_admission, "post_disk_alert", lambda body, _key: seen["alerts"].append(body))
    return seen


def _credit_balance_snapshot():
    """Inlined ports of test_credit_lane::_credit_balance_snapshot, _budget, _live and _codex."""
    from datetime import UTC, datetime

    codex = {
        "status": "near_cap", "remaining_pct": 1.0, "burn_pct_7d": 99.0,
        "freshness": "fresh", "age_s": 60.0, "eligible": True, "health": {"healthy": True},
        "credit_balance": 62500.0, "reset_credits": None,
        "runtime": {"headroom_blocked": False, "rate_limited": 0},
        "codexbar": {
            "weekly_used_pct": 99.0, "weekly_remaining_pct": 1.0,
            "weekly_resets_at": "2026-10-03T17:00:00+00:00", "will_last_to_reset": False,
            "pace_summary": "13% in deficit", "freshness": "fresh", "age_s": 60.0, "stale": False,
            "fetched_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        },
    }
    return {
        "agents": {"codex": codex}, "api_accounts": {}, "diagnostics": {"stale": False},
        "recommendation": {"primary_agent_for_code": "codex", "rationale": "", "warnings": []},
    }


# D5 ports of legacy admission contracts; originals remain untouched.
@pytest.fixture
def admission_dispatch(sandbox, monkeypatch):
    """Ported setup from test_delegate_admission::_stub_worktree and credit_lane::dispatch_env."""
    from scripts.dispatcher import cli

    monkeypatch.setenv("LU_TASKS_DIR", str(sandbox.tasks))
    monkeypatch.setattr(git, "ROOT", sandbox.repo)
    monkeypatch.setattr(git, "CONFIG", sandbox.repo / "scripts/config/fleet_repos.yaml")
    spawned = []

    def start(spec, record, prompt, hard_timeout):
        store.create(record, prompt)
        record.update(pid=os.getpid(), process_start=worker._identity(os.getpid()))
        store.replace(record)
        spawned.append(record)

    monkeypatch.setattr(worker, "start", start)

    def dispatch(*flags, model="echo", mode="workspace-write", task_id="adm-worker"):
        return cli.main(["dispatch", "--agent", "sol", "--model", model, "--mode", mode,
                         "--task-id", task_id, "--prompt", "Map the parser flags.", *flags])

    yield SimpleNamespace(dispatch=dispatch, box=sandbox, spawned=spawned)
    # The fake supervisor is this test process; release its records before sandbox cancellation.
    for path in sandbox.tasks.glob("*.json"):
        record = json.loads(path.read_text())
        if record.get("pid") == os.getpid():
            record["status"] = "done"
            store.replace(record, path)


def test_dispatch_refuses_a_write_worker_at_the_cap_with_one_line(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_dispatch_refuses_a_write_worker_at_the_cap_with_one_line."""
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")
    assert admission_dispatch.dispatch("--dry-run") == 3
    refusal = [line for line in capsys.readouterr().err.splitlines() if "admission" in line]
    assert refusal == [
        "❌ dispatch admission refused for a workspace-write worker: live write workers 0/0 reached the cap "
        "(DISPATCH_MAX_LIVE_WRITE_WORKERS=0). Wait for a worker to finish or for the host to recover, raise the "
        'threshold through the named environment variable, or pass --force-admission "<reason>" to override.'
    ]
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()


def test_read_only_dispatch_is_exempt(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_read_only_dispatch_is_exempt."""
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")
    assert admission_dispatch.dispatch(mode="read-only") == 0
    assert "admission" not in capsys.readouterr().err
    assert "admission" not in store.read("adm-worker")


def test_full_shared_pool_refuses_a_write_worker(admission_dispatch, tmp_path, monkeypatch, capsys):
    """Ported from tests/test_dispatch_admission.py::test_full_shared_pool_refuses_a_write_worker."""

    pool = _fake_pool(tmp_path / "lu.slice", current=21 * 1024**3, file_cache=1024**3 // 2)
    monkeypatch.setenv("LU_SLICE_CGROUP", str(pool))
    assert admission_dispatch.dispatch() == 3
    assert ("lu.slice non-cache use 20.5 GiB plus a 2.5 GiB worker reserve exceeds MemoryHigh 21.0 GiB "
            "(DISPATCH_WORKER_MEM_RESERVE_GIB=2.5)") in capsys.readouterr().err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.repo / ".worktrees").exists()
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()


def test_file_cache_does_not_count_against_the_pool(admission_dispatch, tmp_path, monkeypatch, capsys):
    """Ported from tests/test_dispatch_admission.py::test_file_cache_does_not_count_against_the_pool."""

    pool = _fake_pool(tmp_path / "lu.slice", current=28 * 1024**3, file_cache=14 * 1024**3)
    monkeypatch.setenv("LU_SLICE_CGROUP", str(pool))
    assert admission_dispatch.dispatch() == 0
    assert "lu.slice 14.0/21.0 GiB non-cache (+14.0 GiB file cache; worker reserve 2.5 GiB)" in capsys.readouterr().err
    record = store.read("adm-worker")
    assert record["admission"]["pool_nonreclaimable_gib"] == 14.0
    assert record["admission"]["pool_file_cache_gib"] == 14.0
    assert record["admission"]["pool_limit_gib"] == 21.0


def test_locked_recheck_refuses_a_dispatch_that_lost_the_race(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_locked_recheck_refuses_a_dispatch_that_lost_the_race."""
    from scripts.dispatcher import host_admission as admission
    from scripts.orchestration import dispatch_admission

    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "1")
    real_evaluate = admission.evaluate
    calls = []

    def evaluate_after_competitor(mode, **kwargs):
        calls.append(kwargs)
        if len(calls) == 2:
            record = dict(schema_version=2, task_id="competitor", status="running", mode="workspace-write",
                          pid=os.getpid(), process_start=worker._identity(os.getpid()))
            store.replace(record)
        return real_evaluate(mode, **kwargs)

    monkeypatch.setattr(admission, "evaluate", evaluate_after_competitor)
    monkeypatch.setattr(git, "create_worktree", lambda *_a, **_k: pytest.fail("must not create a worktree"))
    assert admission_dispatch.dispatch() == 3
    assert len(calls) == 2
    assert "live write workers 1/1 reached the cap" in capsys.readouterr().err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()
    assert dispatch_admission.scan_task_records(admission_dispatch.box.tasks).live_task_ids == ("competitor",)


def test_admitted_dispatch_holds_its_slot_while_the_worktree_is_created(admission_dispatch, monkeypatch):
    """Ported from tests/test_delegate_admission.py::test_admitted_dispatch_holds_its_slot_while_the_worktree_is_created."""
    from scripts.guardrails.delegate_ownership import _task_still_active
    from scripts.orchestration import dispatch_admission

    seen = {}
    create = git.create_worktree

    def create_worktree(*args, **kwargs):
        held = store.read("adm-worker")
        seen["record"] = held
        seen["live"] = dispatch_admission.scan_task_records(admission_dispatch.box.tasks).live_task_ids
        assert _task_still_active("adm-worker", os.getpid(), admission_dispatch.box.tasks, created_at=0)
        assert [state["task_id"] for _, state in dispatch_admission.iter_active_records(
            admission_dispatch.box.tasks)] == ["adm-worker"]
        return create(*args, **kwargs)

    monkeypatch.setattr(git, "create_worktree", create_worktree)
    assert admission_dispatch.dispatch() == 0
    held = seen["record"]
    assert held["status"] == "spawning" and held["pid"] is None and held["mode"] == "workspace-write"
    assert held[dispatch_admission.ADMISSION_HOLD_KEY]["owner_pid"] == os.getpid()
    assert seen["live"] == ("adm-worker",)
    final = store.read("adm-worker")
    assert dispatch_admission.ADMISSION_HOLD_KEY not in final
    assert final["run_nonce"] == held["run_nonce"]
    assert final["admission"] == held["admission"]


def test_dispatch_that_stops_after_admission_drops_its_hold(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_dispatch_that_stops_after_admission_drops_its_hold."""
    def disappear(*_args, **_kwargs):
        assert store.read("adm-worker")["admission_hold"]
        raise ValueError("worktree disappeared before its task record was published")

    monkeypatch.setattr(git, "create_worktree", disappear)
    assert admission_dispatch.dispatch() == 2
    assert "disappeared before its task record was published" in capsys.readouterr().err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()


def test_admission_marks_a_record_whose_dispatcher_died_crashed(admission_dispatch):
    """Ported from tests/test_delegate_admission.py::test_admission_marks_a_record_whose_dispatcher_died_crashed."""
    from scripts.dispatcher import host_admission as admission
    from scripts.orchestration import dispatch_admission
    from tests.worktree_prep_helpers import exited_process_identity

    pid, start = exited_process_identity()
    record = dict(schema_version=2, task_id="orphan", run_nonce="nonce-orphan", status="spawning", pid=None,
                  mode="workspace-write", started_at=store.now(),
                  admission_hold=dict(run_nonce="nonce-orphan", owner_pid=pid, owner_start=start))
    admission_dispatch.box.tasks.mkdir(exist_ok=True)
    store.replace(record)
    decision = admission.evaluate("workspace-write", sweep=True)
    assert decision.live_task_ids == ()
    assert decision.dead_task_ids == ("orphan",)
    healed = store.read("orphan")
    assert healed["status"] == "crashed"
    assert healed["returncode_reason"] == dispatch_admission.ORPHANED_HOLD_REASON
    assert "marked crashed by admission probe" in healed["stderr_excerpt"]
    assert "admission_hold" not in healed


@pytest.mark.parametrize("model", ["gpt-6-astra", "gpt-5-codex", "claude-opus-5-5"])
def test_admission_refuses_off_allowlist_model_on_credit_balance_lane(admission_dispatch, monkeypatch, capsys, model):
    """Ported from tests/test_credit_lane.py::test_admission_refuses_off_allowlist_model_on_credit_balance_lane."""
    from scripts.fleet import credit_lane

    monkeypatch.setattr(credit_lane, "read_routing_budget", _credit_balance_snapshot)
    assert admission_dispatch.dispatch(model=model, mode="read-only") == 2
    err = capsys.readouterr().err
    assert "❌ dispatch refused: CREDIT_PERIOD_MODEL_REFUSED: lane codex is credit_balance_present" in err
    assert f"model {model} is outside the credit-period allowlist [gpt-6.1-sol, gpt-6-luna]" in err
    assert "credit_lanes.yaml" in err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.repo / ".worktrees").exists()
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()


@pytest.mark.parametrize("model", ["gpt-6.1-sol", "gpt-6-luna", "codex:gpt-6-luna", "GPT-6.1-Sol", None])
def test_admission_accepts_allowlisted_and_default_models_without_reading_state(monkeypatch, model):
    """Ported from tests/test_credit_lane.py::test_admission_accepts_allowlisted_and_default_models_without_reading_state."""
    from scripts.dispatcher import host_admission as admission
    from scripts.fleet import credit_lane

    monkeypatch.setattr(credit_lane, "read_routing_budget", lambda **_k: pytest.fail("must not read state"))
    assert admission.credit_period_refusal("codex", model) is None


def test_force_admission_records_the_reason(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_force_admission_records_the_reason."""
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")
    assert admission_dispatch.dispatch("--force-admission", "hotfix #1234 while one worker drains") == 0
    assert "overridden by --force-admission ('hotfix #1234 while one worker drains')" in capsys.readouterr().err
    decision = store.read("adm-worker")["admission"]
    assert decision["admitted"] is False
    assert decision["forced"] is True
    assert decision["force_reason"] == "hotfix #1234 while one worker drains"
    assert decision["max_live_write_workers"] == 0


def test_force_admission_requires_a_reason(admission_dispatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_force_admission_requires_a_reason."""
    assert admission_dispatch.dispatch("--force-admission", "   ") == 2
    assert "--force-admission requires a non-empty reason" in capsys.readouterr().err
    assert not admission_dispatch.spawned


def test_live_forced_dispatch_on_a_full_disk_stops_at_the_first_gate(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_live_forced_dispatch_on_a_full_disk_stops_at_the_first_gate."""

    disk = _full_disk(monkeypatch, 90.0)
    assert admission_dispatch.dispatch("--force-admission", "hotfix while the disk drains") == 4
    # Disk admission measures, alerts and refuses; only each task's creator removes its worktree.
    assert disk["alerts"]
    assert "--force-admission cannot override a full disk" in capsys.readouterr().err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()
    assert not (admission_dispatch.box.repo / ".worktrees").exists()


def test_locked_recheck_holds_a_disk_refusal_against_a_force_reason(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_locked_recheck_holds_a_disk_refusal_against_a_force_reason."""

    disk = _full_disk(monkeypatch, 60.0, 90.0)
    monkeypatch.setattr(git, "create_worktree", lambda *_a, **_k: pytest.fail("must not create a worktree"))
    assert admission_dispatch.dispatch("--force-admission", "hotfix while the disk drains") == 4
    err = capsys.readouterr().err
    assert "disk 90.0% used" in err and "--force-admission cannot override a full disk" in err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()


def test_force_admission_skips_the_early_refusal(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_force_admission_skips_the_early_refusal."""
    from scripts.orchestration import dispatch_admission

    overloaded = dispatch_admission.HostProbe(mem_available_bytes=1024**3, load1=40.0, cpu_count=8, proc_available=True)
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: overloaded)
    assert admission_dispatch.dispatch("--force-admission", "drain one worker") == 0
    assert "overridden by --force-admission ('drain one worker'): MemAvailable 1.0 GiB" in capsys.readouterr().err
    assert store.read("adm-worker")["admission"]["forced"] is True


def test_early_refusal_reports_an_invalid_threshold_as_an_invalid_request(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_early_refusal_reports_an_invalid_threshold_as_an_invalid_request."""
    monkeypatch.setenv("DISPATCH_MIN_MEM_AVAILABLE_GIB", "-1")
    assert admission_dispatch.dispatch() == 2
    assert "invalid dispatch admission threshold: DISPATCH_MIN_MEM_AVAILABLE_GIB='-1' must be zero or more" in capsys.readouterr().err
    assert not admission_dispatch.spawned


def test_read_only_dispatch_on_an_overloaded_host_is_exempt(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_read_only_dispatch_on_an_overloaded_host_is_exempt."""
    from scripts.orchestration import dispatch_admission

    overloaded = dispatch_admission.HostProbe(mem_available_bytes=1024**3, load1=40.0, cpu_count=8, proc_available=True)
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: overloaded)
    assert admission_dispatch.dispatch(mode="read-only") == 0
    assert "admission" not in capsys.readouterr().err


@pytest.mark.parametrize("failure", ["prompt-collision", "log-directory", "interrupted-setup"])
def test_spawn_setup_failure_never_strands_published_record(tmp_path, monkeypatch, failure):
    """Setup can fail after record publication but before any supervisor exists."""
    spec, record, path = _spawn_refused_record(tmp_path, monkeypatch, "setup-failure")
    path.parent.mkdir()
    if failure == "prompt-collision":
        spec.prompt_file.write_bytes(b"original prompt")
        expected = FileExistsError
    elif failure == "log-directory":
        (path.parent / "logs").touch()
        expected = FileExistsError
    else:
        create = store.create

        def interrupted(*args):
            create(*args)
            raise KeyboardInterrupt

        monkeypatch.setattr(store, "create", interrupted)
        expected = KeyboardInterrupt
    with pytest.raises(expected):
        worker.start(spec, record, b"submitted prompt", 60)
    state = store.read(spec.task_id)
    assert state["status"] == "failed"
    assert state["returncode_reason"] == "spawn_setup_failed"
    assert state["pid"] is None
    assert state["finished_at"]
    assert "admission_hold" not in state
    if failure == "prompt-collision":
        assert spec.prompt_file.read_bytes() == b"original prompt"


def test_spawn_setup_failure_does_not_overwrite_existing_run(tmp_path, monkeypatch):
    spec, record, path = _spawn_refused_record(tmp_path, monkeypatch, "duplicate-run")
    other = {**record, "run_nonce": "other-run"}
    store.create(other, b"original")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="task id already exists"):
        worker.start(spec, record, b"duplicate", 60)
    assert path.read_bytes() == before


@pytest.mark.parametrize("command", ["list", "status", "wait", "list-active"])
def test_cli_recovers_old_spawn_without_process(sandbox, command):
    """Existing ownerless records settle through the actual dispatcher entry point."""
    sandbox.tasks.mkdir(exist_ok=True)
    path = sandbox.tasks / "old-spawn.json"
    path.write_text(json.dumps(dict(schema_version=2, task_id="old-spawn", run_nonce="old-nonce",
                                   status="spawning", pid=None, started_at="2026-01-01T00:00:00Z")))
    args = {"list": ["list"], "status": ["status", "old-spawn"],
            "wait": ["wait", "old-spawn", "--run-nonce", "old-nonce", "--timeout", "0.1"],
            "list-active": ["list", "--status", "spawning"]}[command]
    response = json.loads(sandbox.cli(*args, expected=1 if command == "wait" else 0).stdout)
    if command == "list-active":
        assert response == []
    else:
        state = response[0] if command == "list" else response
        assert state["status"] == "crashed"
        assert state["returncode_reason"] == "spawn_process_missing"
        assert state["finished_at"]
    saved = json.loads(path.read_text())
    assert saved["status"] == "crashed"
    assert saved["run_nonce"] == "old-nonce"


@pytest.mark.parametrize("case", ["recent", "live-owner", "unknown-owner", "pid", "terminal", "legacy"])
def test_stale_spawn_recovery_preserves_unproven_or_live_records(tmp_path, monkeypatch, case):
    from scripts.orchestration.dispatch_admission import new_admission_hold

    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    record = dict(schema_version=2, task_id="preserved", run_nonce="same-run", status="spawning",
                  pid=None, started_at="2026-01-01T00:00:00Z")
    if case == "recent":
        record["started_at"] = store.now()
    elif case == "live-owner":
        record["admission_hold"] = new_admission_hold("same-run")
    elif case == "unknown-owner":
        record["admission_hold"] = {"run_nonce": "same-run", "owner_pid": os.getpid(), "owner_identity": "unverifiable"}
    elif case == "pid":
        record.update(pid=os.getpid(), process_start=worker._identity(os.getpid()))
    elif case == "terminal":
        record["status"] = "failed"
    else:
        record.pop("schema_version")
    store.replace(record)
    before = store.record_path("preserved").read_bytes()
    assert worker._observe(record)["status"] == record["status"]
    assert store.record_path("preserved").read_bytes() == before


def test_stale_spawn_recovery_rechecks_process_before_terminalizing(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    stale = dict(schema_version=2, task_id="racing-spawn", run_nonce="same-run", status="spawning",
                 pid=None, started_at="2026-01-01T00:00:00Z")
    current = {**stale, "status": "running", "pid": os.getpid(),
               "process_start": worker._identity(os.getpid())}
    store.replace(current)
    assert worker._observe(stale)["status"] == "running"
    assert store.read("racing-spawn")["status"] == "running"


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
def test_dispatch_prompt_destination_collision_settles_failed_spawn(sandbox, mode):
    """A prompt file that already holds the submission is that task's prompt, not a failed spawn.

    A different occupant still fails closed
    (``test_spawn_setup_failure_never_strands_published_record``).
    """
    sandbox.tasks.mkdir(exist_ok=True)
    prompt = sandbox.tasks / "prompt-collision.prompt"
    prompt.write_text("the operator's submitted prompt")
    sandbox.cli("dispatch", "--agent", "sol", "--model", "echo", "--task-id", "prompt-collision",
                "--mode", mode, "--prompt-file", str(prompt))
    state = json.loads(sandbox.cli("status", "prompt-collision").stdout)
    assert state["status"] in {"spawning", "running", "done"}
    assert state.get("returncode_reason") != "spawn_setup_failed"
    assert state.get("pid")
    assert prompt.read_text() == "the operator's submitted prompt"
