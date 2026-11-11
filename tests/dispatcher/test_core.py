"""Private-input policy, child environment, CLI flags, timeouts and worker identity."""

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
from scripts.dispatcher.types import TaskSpec
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
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True, timeout=30)
    workspace = tmp_path / ".worktrees/dispatch/muse/task"
    workspace.mkdir(parents=True)
    prompt = tmp_path / "brief.txt"
    prompt.write_text("public input")
    return TaskSpec("task", "muse", "model", None, "read-only", workspace, prompt, tmp_path / "task.result")


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


def test_public_muse_worker_forces_contributor_off(spec, private_repos):
    """Defect class: a public worker enables unqualified contributor data use."""
    spec = dataclasses.replace(spec, options={"contributor_mode": "on"})
    checks.check_private_input(spec, "public")
    argv = muse.build(spec, {}).argv
    assert argv[argv.index("--contributor-mode") + 1] == "off"


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
    # Dispatch admission refuses a model the catalog does not name (C-4967).
    model = {"codex": "gpt-6.1-sol", "claude": "claude-sonnet-5-5"}.get(agent, "vendor/model")
    spec = TaskSpec("ro", agent, model, None, "read-only", tmp_path, prompt, tmp_path / "final", "a")
    if agent == "muse":
        workspace = sandbox.repo / ".worktrees/dispatch/muse/ro"
        workspace.mkdir(parents=True)
        spec = dataclasses.replace(spec, worktree=workspace)
    refused: dict[str, str] = {}
    if agent in refused:
        with pytest.raises(ValueError, match=f"read_only_unenforceable: {agent} cannot run --mode read-only"):
            providers.load(agent).build(spec, {})
        result = sandbox.cli("dispatch", "--agent", agent, "--model", model, "--prompt", "Fix X", expected=2)
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
        plan = sandbox.cli("dispatch", "--agent", agent, "--model", model, "--prompt", "Fix X", "--dry-run")
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
    """Ported from tests/test_delegate.py with the same test name, including process-tree cleanup.

    Defect class: a silent tree kept until the hard timeout.

    The silence timer is 1s. Dispatch and reaping took the sibling startup check to 6.06s
    on a loaded runner, past a bound of 6. The hard timeout is 60s and the bound is 15s:
    above that run, and below a run that misses the silence timer.
    """
    started = time.monotonic()
    task = sandbox.dispatch("tree", "--hard-timeout", "60", "--silence-timeout", "1")
    record = sandbox.settle(task, expected=1)
    elapsed = time.monotonic() - started
    assert elapsed < 15, f"elapsed={elapsed:.2f}s; a run held to the 60s hard timeout must not pass"
    assert record["returncode"] == -signal.SIGKILL
    assert record["status"] == "timeout"
    assert "stdout_silence_timeout" in record["stderr_excerpt"]
    assert record["silence_timeout"] == 1
    grandchild = int(Path(record["prompt_file"]).with_suffix(".grandchild").read_text())
    assert worker._identity(grandchild) is None


def test_provider_process_lingering_after_its_final_result_settles_with_that_result(sandbox, monkeypatch):
    """Defect class: a finished run held open until timeout.

    The supervisor waits one 1s terminal grace, then ``_end_lingering`` waits up to one more,
    so the fixed path is a little over 2s. A loaded merge-group runner took 3.06s and missed a
    bound of 3. The hard timeout is 60s and the bound is 15s: above that run, and below a run
    that stays open until the timeout.
    """
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
                    options={"hard_timeout": "60", "silence_timeout": "0.5"})
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
    assert result["status"] == "done", (
        f"status={result['status']} error={result.get('error')} elapsed={elapsed:.2f}"
    )
    assert result["error"] is None
    assert "kill_reason" not in result
    assert elapsed < 15, f"elapsed={elapsed:.2f}s; a run held to the 60s timeout must not pass"
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
    """Defect class: an AGY workspace-write run that exits 0 on an interim reply while a child task is still active settles done or no_deliverable.

    The supervisor returns at its 2s deadline, a little over 2s. A bound of 8 sat a few
    seconds above that. The bound is 15s: above that deadline on a loaded runner, and below
    a run held to the 30s terminal grace or the default hard timeout.
    """
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
    assert elapsed < 15, (
        f"elapsed={elapsed:.2f}s; a run held to the 30s terminal grace or the default hard timeout must not pass"
    )


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
    """Ported from tests/test_delegate.py with the same test name.

    Defect class: a silent startup kept until the silence or hard timeout.

    The initial-response timer is 1s. A loaded merge-group runner took 6.06s and missed a
    bound of 6. Silence and hard timeout are 60s and the bound is 15s: above that run, and
    below a run that misses the 1s timer.
    """
    started = time.monotonic()
    task = sandbox.dispatch("tree", "--hard-timeout", "60", "--silence-timeout", "60",
                            "--initial-response-timeout", "1")
    record = sandbox.settle(task, expected=1)
    elapsed = time.monotonic() - started
    assert elapsed < 15, f"elapsed={elapsed:.2f}s; a run held to the 60s timeouts must not pass"
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
