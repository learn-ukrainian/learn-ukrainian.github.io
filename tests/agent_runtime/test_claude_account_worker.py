"""An ordinary Claude worker authenticates as its account label's account (#10619).

The default label (or none) keeps the host login and the base plan
byte-for-byte (a checked-in snapshot of the base behaviour). Label ``b`` runs
the worker with the bound account's verified login directory as its only
credential source: a conflicting ambient credential, a competing key source in
the login directory's user settings, a checkout setting that changes the
effective authentication, or an unknown label is refused with a value-free
code before the worker spawns. The fake ``claude`` runs through the real
runner and sanitizer. For ``auth status`` it resolves ``--settings``,
``--setting-sources`` and the user, project and local settings files the way
Claude Code 2.1.299 did in a fixture probe; for a run it records the argv and
environment it received. Where the installed Claude CLI is present, the real
``claude auth status`` and ``claude mcp list`` check the same plans. Every
identity, token and directory is a fixture.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from scripts.agent_runtime import attempt_boundary, env_sanitize, runner
from scripts.agent_runtime.adapters import claude
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.claude import LABELLED_ACCOUNT_SETTING_SOURCES, ClaudeAdapter
from scripts.agent_runtime.attempt_boundary import CLAUDE_ACCOUNT_REFUSAL_CODES, ClaudeAccountRefused
from scripts.agent_runtime.env_sanitize import (
    CLAUDE_LAUNCH_GUARD_EXIT,
    build_agent_env,
    claude_labelled_inputs_digest,
)
from tests.agent_runtime.test_attempt_boundary import (
    ACCOUNT_ORG_UUIDS,
    BOUND_ACCOUNT_UUID,
    CLAUDE_AMBIENT_AUTH,
    DEFAULT_ACCOUNT_UUID,
    MACHINE_POLICY,
    PROFILE_ORGANIZATIONS,
    _credentials,
    _login_identity,
    _mock_selected_account_runtime,
    _private_json,
)

_GOLDEN = Path(__file__).resolve().parents[1] / "fixtures" / "claude_default_account_plan.json"
_REAL_CLAUDE = shutil.which("claude")

_FAKE_CLAUDE = textwrap.dedent(
    """
    import json, os, sys

    argv = sys.argv[1:]
    if "--version" in argv:
        print("2.1.289 (Claude Code)")
        sys.exit(0)

    def option(name):
        return argv[argv.index(name) + 1] if name in argv else None

    def load(path):
        try:
            with open(path, encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError):
            return {}

    log = os.environ["LU_FAKE_CLAUDE_DUMP"]
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.environ["HOME"], ".claude")
    if argv[-3:-1] == ["auth", "status"] and argv[-1] in ("--json", "--text"):
        with open(log, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"kind": "auth_status", "argv": argv, "cwd": os.getcwd()}) + "\\n")
        mode = os.environ.get("LU_FAKE_CLAUDE_STATUS_MODE", "")
        if mode == "garbage":
            print("not json")
            sys.exit(1)
        touch = os.environ.get("LU_FAKE_CLAUDE_STATUS_TOUCH")
        if touch:  # a settings input that changes while it is being verified
            with open(touch, "w", encoding="utf-8") as handle:
                handle.write("{}")
        sources = (option("--setting-sources") or "user,project,local").split(",")
        # (scope, settings) in Claude Code's load order, the flag last. The global
        # config's env applies whatever the setting sources (probe, 2.1.300).
        scopes = [("global", load(os.path.join(config_dir, ".claude.json")))]
        if "user" in sources:
            scopes.append(("user", load(os.path.join(config_dir, "settings.json"))))
        if "project" in sources:
            scopes.append(("project", load(os.path.join(os.getcwd(), ".claude", "settings.json"))))
        if "local" in sources:
            scopes.append(("local", load(os.path.join(os.getcwd(), ".claude", "settings.local.json"))))
        flag = option("--settings")
        if flag:
            scopes.append(("flag", json.loads(flag)))
        env, helper = dict(os.environ), None
        for scope, settings in scopes:
            for name, value in (settings.get("env") or {}).items():
                # Probe: project and local scopes applied provider switches, not keys or endpoints.
                if scope in ("global", "user", "flag") or name.startswith("CLAUDE_CODE_USE_"):
                    env[name] = value
            if scope != "global":
                helper = settings.get("apiKeyHelper") or helper
        status = {"loggedIn": True, "apiProvider": "firstParty", "configDirectory": config_dir}
        if env.get("CLAUDE_CODE_USE_BEDROCK"):
            status.update(authMethod="third_party", apiProvider="bedrock")
        elif helper:
            status["authMethod"] = "api_key_helper"
        elif env.get("ANTHROPIC_API_KEY"):
            status.update(authMethod="api_key", apiKeySource="ANTHROPIC_API_KEY")
        elif os.path.exists(os.path.join(config_dir, ".credentials.json")):
            status["authMethod"] = "claude.ai"
            # The plan Claude Code resolves for the login is the one stored with its credential.
            oauth = load(os.path.join(config_dir, ".credentials.json")).get("claudeAiOauth") or {}
            plan = "team" if mode == "team_plan" else oauth.get("subscriptionType")
            if plan is not None:
                status["subscriptionType"] = plan
        else:
            status = {"loggedIn": False, "authMethod": "none", "apiProvider": "firstParty"}
        if mode == "other_dir":
            status["configDirectory"] = os.environ["HOME"]
        if mode == "key_source":
            status["apiKeySource"] = "/login managed key"
        if argv[-1] == "--json":
            print(json.dumps(status))
        else:
            lines = ["Login method: Claude Max account"] if status["authMethod"] == "claude.ai" else []
            lines += ["Email: fixture@example.invalid"]
            if env.get("ANTHROPIC_BASE_URL"):
                lines.append("Anthropic base URL: " + env["ANTHROPIC_BASE_URL"])
            if env.get("HTTPS_PROXY"):
                lines.append("Proxy: " + env["HTTPS_PROXY"])
            if mode == "text_endpoint":
                lines.append("Anthropic base URL: https://fixture.invalid")
            print("\\n".join(lines))
        sys.exit(0 if status["loggedIn"] else 1)
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"kind": "run", "argv": argv, "env": dict(os.environ)}) + "\\n")
    session = "00000000-0000-4000-8000-000000010619"
    print(json.dumps({"type": "system", "subtype": "init", "session_id": session}))
    if os.environ.get("LU_FAKE_CLAUDE_FAIL_RUN"):
        print(json.dumps({"type": "result", "subtype": "error_during_execution", "is_error": True,
                          "result": "Failed to authenticate", "session_id": session}))
        sys.exit(1)
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "done", "session_id": session}))
    """
)

# Labelled user settings: (i) an API key in env, (ii) a key helper, (iii) clean.
USER_SETTINGS = {
    "env_api_key": {"env": {"ANTHROPIC_API_KEY": "fixture-settings-" + "k" * 30}},
    "api_key_helper": {"apiKeyHelper": "fixture-helper-command"},
    # Only allowlisted names: an unknown one refuses (test_bound_label_unknown_setting_is_refused).
    "clean": {"model": "fixture-model", "env": {"DISABLE_TELEMETRY": "1"}},
}


@pytest.fixture
def accounts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """The default account in HOME and account b under its own bound login directory."""
    home = tmp_path / "home"
    home.mkdir(mode=0o700)
    monkeypatch.setenv("HOME", str(home))
    identities, calls = _mock_selected_account_runtime(tmp_path, monkeypatch)
    for key in (*CLAUDE_AMBIENT_AUTH, "CLAUDE_CONFIG_DIR"):
        monkeypatch.delenv(key, raising=False)
    found = SimpleNamespace(
        home=home,
        default_token="fixture-default-" + "d" * 30,
        bound_token="fixture-bound-" + "b" * 30,
        config_dir=tmp_path / "bound-config",
        profile_calls=calls,
    )
    identities.update({found.default_token: DEFAULT_ACCOUNT_UUID, found.bound_token: BOUND_ACCOUNT_UUID})
    _credentials(home / ".claude" / ".credentials.json", found.default_token)
    (home / ".claude").chmod(0o700)
    _private_json(home / ".claude.json", {"oauthAccount": {"accountUuid": DEFAULT_ACCOUNT_UUID}})
    found.config_dir.mkdir(mode=0o700)
    _credentials(found.config_dir / ".credentials.json", found.bound_token)
    _private_json(found.config_dir / ".claude.json", {"oauthAccount": _login_identity(BOUND_ACCOUNT_UUID)})
    binding = tmp_path / "private-config" / "claude_accounts.json"
    _private_json(
        binding,
        {
            "schema_version": 1,
            "accounts": {"b": {"config_dir": str(found.config_dir), "account_uuid": BOUND_ACCOUNT_UUID}},
        },
    )
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", str(binding))
    script = tmp_path / "fake_claude.py"
    script.write_text(_FAKE_CLAUDE, encoding="utf-8")
    found.binary = tmp_path / "claude"
    found.binary.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8")
    found.binary.chmod(0o755)
    found.dump = tmp_path / "dump.jsonl"
    monkeypatch.setenv("LU_FAKE_CLAUDE_DUMP", str(found.dump))
    found.workdir = tmp_path / "work"
    found.workdir.mkdir()
    # The launch guard runs in its own process: it reads the same synthetic machine policy root.
    monkeypatch.setattr(claude, "_LAUNCH_GUARD_CODE", _relocated_guard_code(env_sanitize._CLAUDE_MANAGED_SETTINGS_DIR))
    return found


def _relocated_guard_code(root: Path) -> str:
    """The launch guard's code, unchanged except that it reads machine policy from ``root``."""
    call = "run_claude_launch_guard(sys.argv[1:])"
    assert claude._LAUNCH_GUARD_CODE.endswith(call)
    relocate = (
        f"import scripts.agent_runtime.env_sanitize as e; e._CLAUDE_MANAGED_SETTINGS_DIR = e.Path({str(root)!r}); "
    )
    return claude._LAUNCH_GUARD_CODE.removesuffix(call) + relocate + call


def _calls(accounts: SimpleNamespace, kind: str) -> list[dict]:
    if not accounts.dump.exists():
        return []
    calls = [json.loads(line) for line in accounts.dump.read_text(encoding="utf-8").splitlines()]
    return [call for call in calls if call["kind"] == kind]


def _run(accounts: SimpleNamespace) -> dict:
    (spawn,) = _calls(accounts, "run")
    return spawn


def _invoke(accounts: SimpleNamespace, **tool_config) -> tuple[runner.Result, list]:
    with (
        patch.object(runner, "has_headroom", return_value=(True, "")),
        patch.object(runner, "write_record") as record,
    ):
        result = runner.invoke(
            "claude",
            "do the task",
            mode="workspace-write",
            cwd=accounts.workdir,
            tool_config={"cmd_prefix": [str(accounts.binary)], **tool_config},
            hard_timeout=60,
        )
    return result, record.call_args_list


def _plan(accounts: SimpleNamespace, **tool_config) -> InvocationPlan:
    return ClaudeAdapter().build_invocation(
        prompt="do the task",
        mode="workspace-write",
        cwd=accounts.workdir,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"cmd_prefix": [str(accounts.binary)], **tool_config},
    )


def _user_settings(accounts: SimpleNamespace, settings: dict, *, home_too: bool = False) -> None:
    """Write the labelled account's user settings (and optionally the default account's)."""
    _private_json(accounts.config_dir / "settings.json", settings)
    if home_too:
        _private_json(accounts.home / ".claude" / "settings.json", settings)


def test_bound_label_runs_with_only_the_bound_login_directory(accounts):
    """AC-01: label b's worker gets the bound login directory and no other credential source."""
    result, records = _invoke(accounts, claude_account="b")

    assert result.ok is True
    seen = _run(accounts)
    env = seen["env"]
    assert env["CLAUDE_CONFIG_DIR"] == str(accounts.config_dir)
    assert not {name for name in env if name.upper() in CLAUDE_AMBIENT_AUTH or name.upper().startswith("ANTHROPIC_")}
    assert not [name for name, value in env.items() if accounts.bound_token in value or accounts.default_token in value]
    # Verified against the provider with the bound account's own login only.
    assert accounts.profile_calls == [accounts.bound_token]
    # Neither the directory nor the token reaches argv, the usage record or the result.
    rendered = repr(seen["argv"]) + repr(records) + repr(result)
    assert str(accounts.config_dir) not in rendered
    assert accounts.bound_token not in rendered


def test_bound_label_strips_an_inherited_api_key_name_variant(accounts, monkeypatch):
    """The sanitizer keeps the login directory the only source even for a key the check cannot see."""
    monkeypatch.setenv("anthropic_api_key", "fixture-ambient-" + "k" * 30)

    _invoke(accounts, claude_account="b")

    env = _run(accounts)["env"]
    assert env["CLAUDE_CONFIG_DIR"] == str(accounts.config_dir)
    assert "anthropic_api_key" not in env


@pytest.mark.parametrize("case", ["env_api_key", "api_key_helper"])
def test_bound_label_user_settings_key_source_is_refused(accounts, case):
    """AC-01 (i)/(ii): a key or key helper in the labelled user settings is refused value-free, before spawn.

    On fa814a2919 these did not raise: the plan only set the login directory,
    and Claude Code then reported ``api_key`` / ``api_key_helper`` for it.
    """
    _user_settings(accounts, USER_SETTINGS[case])

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == "claude_account_settings_credential_source"
    assert str(refused.value) == "claude_account_settings_credential_source"
    assert "fixture" not in repr(refused.value.__context__) + repr(refused.value.__cause__)
    assert not accounts.dump.exists()
    assert accounts.profile_calls == []


@pytest.mark.parametrize(
    "settings",
    [
        {"env": {"ANTHROPIC_BASE_URL": "https://fixture.invalid"}},
        {"env": {"ANTHROPIC_AUTH_TOKEN": "fixture-token-" + "t" * 30}},
        {"env": {"CLAUDE_CODE_OAUTH_TOKEN": "fixture-token-" + "o" * 30}},
        {"env": {"CLAUDE_CODE_USE_BEDROCK": "1"}},
        {"env": {"CLAUDE_CODE_USE_VERTEX": "1"}},
        {"env": {"CLAUDE_CODE_USE_FOUNDRY": "1"}},
        {"env": {"ANTHROPIC_BEDROCK_BASE_URL": "https://fixture.invalid"}},
        {"env": {"ANTHROPIC_VERTEX_PROJECT_ID": "fixture"}},
        {"env": {"CLAUDE_CONFIG_DIR": "/fixture"}},
        {"env": {"anthropic_api_key": "fixture-key-" + "k" * 30}},
        {"awsAuthRefresh": "fixture-command"},
        {"awsCredentialExport": "fixture-command"},
    ],
)
def test_bound_label_user_settings_credential_class_is_refused(accounts, settings):
    """Every credential, provider or endpoint setting in the labelled user scope is refused."""
    _user_settings(accounts, settings)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")

    assert refused.value.code == "claude_account_settings_credential_source"
    assert accounts.profile_calls == []


@pytest.mark.parametrize(
    ("content", "mode", "code"),
    [
        ("{not json", 0o600, "claude_account_settings_invalid"),
        ('{"env": ["ANTHROPIC_API_KEY"]}', 0o600, "claude_account_settings_invalid"),
        ("[]", 0o600, "claude_account_settings_invalid"),
        ("{}", 0o620, "claude_account_settings_not_private"),
    ],
)
def test_bound_label_unreadable_user_settings_fail_closed(accounts, content, mode, code):
    """Settings that cannot be read as owner-controlled JSON are refused, not skipped."""
    path = accounts.config_dir / "settings.json"
    path.write_text(content, encoding="utf-8")
    path.chmod(mode)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")

    assert refused.value.code == code


def _global_config(accounts: SimpleNamespace, **fields) -> None:
    """Add ``fields`` to the labelled login directory's global config (``.claude.json``)."""
    path = accounts.config_dir / ".claude.json"
    _private_json(path, {**json.loads(path.read_text(encoding="utf-8")), **fields})


# Global-config env names off the allowlist: endpoint, key, provider switch,
# proxy, certificate, an unknown name, a name variant, and a null value.
GLOBAL_CONFIG_ENV_REFUSED = {
    "endpoint": {"ANTHROPIC_BASE_URL": "https://fixture.invalid"},
    "key": {"ANTHROPIC_API_KEY": "fixture-key-" + "k" * 30},
    "helper_ttl": {"CLAUDE_CODE_API_KEY_HELPER_TTL_MS": "1"},
    "provider": {"CLAUDE_CODE_USE_BEDROCK": "1"},
    "proxy": {"HTTPS_PROXY": "http://127.0.0.1:9"},
    "certificate": {"NODE_EXTRA_CA_CERTS": "/fixture/ca.pem"},
    "unknown": {"FIXTURE_UNKNOWN": "1"},
    "lowercase": {"anthropic_base_url": "https://fixture.invalid"},
    "null_value": {"ANTHROPIC_BASE_URL": None},
}


@pytest.mark.parametrize("case", sorted(GLOBAL_CONFIG_ENV_REFUSED))
def test_bound_label_global_config_env_off_the_allowlist_is_refused(accounts, case):
    """Blocker 1: the global config's env applies whatever the setting sources, so it is held to the allowlist.

    On 8599d23ad5 these did not raise (``DID NOT RAISE ClaudeAccountRefused``):
    only the user ``settings.json`` was checked, and ``firstParty`` was taken
    to attest the endpoint.
    """
    _global_config(accounts, env=GLOBAL_CONFIG_ENV_REFUSED[case])

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == "claude_account_config_credential_source"
    assert "fixture" not in str(refused.value)
    assert accounts.profile_calls == []
    assert not accounts.dump.exists()


def test_bound_label_allowlisted_global_config_env_is_admitted(accounts):
    _global_config(accounts, env={"DISABLE_TELEMETRY": "1", "MCP_TIMEOUT": "1000"})

    result, _ = _invoke(accounts, claude_account="b")

    assert result.ok is True


@pytest.mark.parametrize("env", [["ANTHROPIC_BASE_URL"], None, "x"])
def test_bound_label_malformed_global_config_env_is_refused(accounts, env):
    _global_config(accounts, env=env)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")

    assert refused.value.code == "claude_account_config_invalid"


def test_bound_label_legacy_global_config_is_refused(accounts):
    """Claude Code reads a legacy ``.config.json`` in the login directory instead of ``.claude.json``."""
    _private_json(accounts.config_dir / ".config.json", {"oauthAccount": {"accountUuid": BOUND_ACCOUNT_UUID}})

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")

    assert refused.value.code == "claude_account_config_ambiguous"
    assert accounts.profile_calls == []


@pytest.mark.parametrize(
    "settings",
    [{"theme": "dark", "forceLoginMethod": "console"}, {"env": {"FIXTURE_UNKNOWN": "1"}}, {"otelHeadersHelper": "x"}],
)
def test_bound_label_unknown_setting_is_refused(accounts, settings):
    """User settings are held to an allowlist of keys and environment names, not a list of bad ones."""
    _user_settings(accounts, settings)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")

    assert refused.value.code == "claude_account_settings_credential_source"


def test_bound_label_null_user_settings_is_invalid_not_absent(accounts):
    (accounts.config_dir / "settings.json").write_text("null", encoding="utf-8")
    (accounts.config_dir / "settings.json").chmod(0o600)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")

    assert refused.value.code == "claude_account_settings_invalid"


@pytest.mark.parametrize(
    ("mode", "code"),
    [("text_endpoint", "claude_account_status_override"), ("key_source", "claude_account_auth_method_conflict")],
)
def test_bound_label_status_naming_an_override_is_refused(accounts, monkeypatch, mode, code):
    """The text status must name nothing but the login; the JSON must carry no key source."""
    monkeypatch.setenv("LU_FAKE_CLAUDE_STATUS_MODE", mode)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == code
    assert _calls(accounts, "run") == []


def test_bound_label_endpoint_attestation_holds_without_the_static_check(accounts, monkeypatch):
    """Even with the endpoint name allowlisted, the effective endpoint the status names refuses the run."""
    monkeypatch.setattr(
        attempt_boundary,
        "CLAUDE_LABELLED_ENV_ALLOWLIST",
        attempt_boundary.CLAUDE_LABELLED_ENV_ALLOWLIST | {"ANTHROPIC_BASE_URL"},
    )
    _global_config(accounts, env={"ANTHROPIC_BASE_URL": "https://fixture.invalid"})

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == "claude_account_status_override"
    assert _calls(accounts, "run") == []


def test_bound_label_plan_runs_the_cli_behind_the_launch_guard(accounts):
    """The plan binds the verified settings digest and launches the CLI only through the guard."""
    plan = _plan(accounts, claude_account="b")

    guard = plan.cmd.index("--")
    assert plan.cmd[1:4] == ["-I", "-c", claude._LAUNCH_GUARD_CODE]
    digest = plan.cmd[guard - 1]
    assert digest == claude_labelled_inputs_digest(
        login_dir=str(accounts.config_dir),
        cwd=accounts.workdir,
        settings=plan.cmd[plan.cmd.index("--settings") + 1],
        setting_sources="project,local",
        environ=build_agent_env(provider="claude", overrides=plan.env_overrides),
    )
    assert plan.cmd[guard + 1] == str(accounts.binary)
    assert "--" not in _plan(accounts).cmd[:2]  # the default plan is unwrapped (see the golden snapshot)


def test_bound_label_launch_digests_are_domain_separated_one_way_fingerprints(tmp_path):
    """A file's bytes take domain-separated BLAKE2b-256; a credential-bearing record takes scrypt (#10619)."""
    settings = tmp_path / "settings.json"
    _private_json(settings, {"env": {}})
    record = {"accessToken": "fixture-bound-" + "b" * 30, "expiresAt": 4_102_444_800_000}

    assert (
        env_sanitize._file_fingerprint(settings)
        == hashlib.blake2b(settings.read_bytes(), digest_size=32, person=b"lu-launch-digest").hexdigest()
    )
    assert (
        env_sanitize.claude_credential_fingerprint(record)
        == hashlib.scrypt(
            json.dumps(record, sort_keys=True).encode(), salt=b"lu-launch-digest", n=1 << 14, r=8, p=1, dklen=32
        ).hex()
    )


def _settings_change_after_build(accounts: SimpleNamespace, change) -> runner.Result:
    """Run label b, changing a settings input after the plan is verified and before the spawn."""
    build = ClaudeAdapter.build_invocation

    def build_then_change(self, **kwargs):
        plan = build(self, **kwargs)
        change()
        return plan

    with patch.object(ClaudeAdapter, "build_invocation", build_then_change):
        result, _ = _invoke(accounts, claude_account="b")
    return result


@pytest.mark.parametrize("scope", ["local", "project", "global_config", "user"])
def test_bound_label_settings_changed_after_verification_never_launch(accounts, scope):
    """Blocker 2: an input changed between verification and launch stops the run before the CLI starts.

    On 8599d23ad5 the worker started (the runner relaunched the CLI, which
    reread the changed file): ``_calls(accounts, "run")`` held one spawn.
    """

    def change() -> None:
        if scope in ("local", "project"):
            name = "settings.local.json" if scope == "local" else "settings.json"
            _private_json(accounts.workdir / ".claude" / name, {"apiKeyHelper": "fixture-helper-command"})
        elif scope == "global_config":
            _global_config(accounts, env={"ANTHROPIC_BASE_URL": "https://fixture.invalid"})
        else:
            _user_settings(accounts, {"apiKeyHelper": "fixture-helper-command"})

    result = _settings_change_after_build(accounts, change)

    assert result.ok is False
    assert _calls(accounts, "run") == []
    assert "CLAUDE_ACCOUNT_REFUSED: claude_account_settings_changed" in result.stderr_excerpt
    assert "fixture-helper" not in result.stderr_excerpt


def test_bound_label_main_checkout_local_settings_are_bound_for_a_linked_worktree(accounts, tmp_path):
    """A linked worktree's run also loads its main checkout's local settings; a later change there is caught."""
    main = tmp_path / "main"
    main.mkdir()
    git = ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid"]
    subprocess.run([*git, "init", "-q", str(main)], check=True, timeout=30)
    subprocess.run([*git, "-C", str(main), "commit", "-q", "--allow-empty", "-m", "base"], check=True, timeout=30)
    linked = tmp_path / "linked"
    subprocess.run([*git, "-C", str(main), "worktree", "add", "-q", str(linked)], check=True, timeout=30)
    accounts.workdir = linked

    result = _settings_change_after_build(
        accounts,
        lambda: _private_json(main / ".claude" / "settings.local.json", {"apiKeyHelper": "fixture-helper-command"}),
    )

    assert result.ok is False
    assert _calls(accounts, "run") == []


def test_bound_label_unchanged_inputs_launch_through_a_symlinked_working_directory(accounts, tmp_path):
    """The guard sees the physical working directory; an unchanged launch still starts the CLI."""
    link = tmp_path / "work-link"
    link.symlink_to(accounts.workdir, target_is_directory=True)
    accounts.workdir = link

    result, _ = _invoke(accounts, claude_account="b")

    assert result.ok is True
    assert len(_calls(accounts, "run")) == 1


def test_bound_label_settings_changed_during_verification_is_refused(accounts, monkeypatch):
    """An input that changes while the status probes run is refused before any plan is returned."""
    (accounts.workdir / ".claude").mkdir()
    monkeypatch.setenv("LU_FAKE_CLAUDE_STATUS_TOUCH", str(accounts.workdir / ".claude" / "settings.local.json"))

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")

    assert refused.value.code == "claude_account_settings_changed"


@pytest.mark.parametrize(
    "argv", [[], ["digest"], ["digest", "--"], ["digest", "x", "claude"], ["0" * 64, "--", "claude"]]
)
def test_launch_guard_refuses_a_malformed_or_unbound_launch(accounts, argv, monkeypatch):
    """The guard execs nothing unless it is given a digest, ``--`` and a CLI argv whose inputs match it."""
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(accounts.config_dir))
    done = subprocess.run(
        [sys.executable, "-I", "-c", claude._LAUNCH_GUARD_CODE, str(claude._CODE_ROOT), *argv],
        cwd=accounts.workdir,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert done.returncode == CLAUDE_LAUNCH_GUARD_EXIT
    assert done.stderr == "CLAUDE_ACCOUNT_REFUSED: claude_account_settings_changed\n"
    assert done.stdout == ""


def test_bound_label_clean_user_settings_is_admitted(accounts):
    """AC-01 (iii): clean user settings run, with the user scope unloaded and the auth method verified."""
    _user_settings(accounts, USER_SETTINGS["clean"])
    accounts.config_dir.joinpath("settings.json").chmod(0o644)  # readable by others is fine

    result, _ = _invoke(accounts, claude_account="b")

    assert result.ok is True
    argv = _run(accounts)["argv"]
    assert argv[argv.index("--setting-sources") + 1] == LABELLED_ACCOUNT_SETTING_SOURCES == "project,local"
    statuses = _calls(accounts, "auth_status")
    assert [status["argv"][-1] for status in statuses] == ["--json", "--text"]
    for status in statuses:
        assert status["cwd"] == str(accounts.workdir)
        assert status["argv"][-5:-1] == ["--setting-sources", "project,local", "auth", "status"]
        assert status["argv"][status["argv"].index("--settings") + 1] == argv[argv.index("--settings") + 1]


@pytest.mark.parametrize(
    ("name", "settings"),
    [
        ("settings.local.json", {"apiKeyHelper": "fixture-helper-command"}),
        ("settings.json", {"apiKeyHelper": "fixture-helper-command"}),
        ("settings.local.json", {"env": {"CLAUDE_CODE_USE_BEDROCK": "1"}}),
    ],
)
def test_bound_label_checkout_setting_that_changes_auth_is_refused(accounts, name, settings):
    """A project or local setting the run still loads cannot switch its authentication."""
    _private_json(accounts.workdir / ".claude" / name, settings)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == "claude_account_auth_method_conflict"
    assert len(_calls(accounts, "auth_status")) == 1
    assert _calls(accounts, "run") == []


@pytest.mark.parametrize(
    ("mode", "code"),
    [("garbage", "claude_account_auth_status_unavailable"), ("other_dir", "claude_account_auth_method_conflict")],
)
def test_bound_label_unconfirmed_auth_status_is_refused(accounts, monkeypatch, mode, code):
    """No parseable status, or a status for another directory, never admits the run."""
    monkeypatch.setenv("LU_FAKE_CLAUDE_STATUS_MODE", mode)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == code
    assert _calls(accounts, "run") == []


def test_bound_label_logged_out_status_is_refused(accounts):
    accounts.config_dir.joinpath(".credentials.json").unlink()
    binding = attempt_boundary.ClaudeAccountBinding("b", accounts.config_dir, BOUND_ACCOUNT_UUID)
    with patch.object(claude, "_claude_account_binding", return_value=binding):
        with pytest.raises(ClaudeAccountRefused) as refused:
            _plan(accounts, claude_account="b")

    assert refused.value.code == "claude_account_auth_method_conflict"


def test_bound_label_loads_no_user_hooks_permissions_or_mcp_servers(accounts):
    """Stance: the labelled user scope (hooks, permission rules, MCP servers) never applies; it is not refused.

    The run gets the harness settings and the checkout's settings only, so it
    has no more authority than a default run; the allow list names no user
    server.
    """
    _user_settings(
        accounts,
        {
            "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "/fixture/hook"}]}]},
            "permissions": {"allow": ["mcp__fixtureuser__*", "NotebookEdit"]},
        },
    )
    global_config = json.loads((accounts.config_dir / ".claude.json").read_text(encoding="utf-8"))
    global_config["mcpServers"] = {"fixtureuser": {"type": "stdio", "command": "/bin/true", "args": []}}
    _private_json(accounts.config_dir / ".claude.json", global_config)

    plan = _plan(accounts, claude_account="b")

    sources = [plan.cmd[i + 1] for i, arg in enumerate(plan.cmd) if arg == "--setting-sources"]
    assert sources == ["project,local"]
    allowed = plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    assert not [tool for tool in allowed if "fixtureuser" in tool or tool == "NotebookEdit"]
    assert "--setting-sources" not in _plan(accounts).cmd


def test_bound_label_auth_failure_is_a_failure_not_a_retry_as_another_account(accounts, monkeypatch):
    """A mid-run auth failure (e.g. a failed token refresh) fails the run; nothing re-runs it on the host login.

    The runner's failover re-sends the same tool_config, label included
    (``failover.tool_config_with_route``), and configures no Claude chain.
    """
    monkeypatch.setenv("LU_FAKE_CLAUDE_FAIL_RUN", "1")

    result, _ = _invoke(accounts, claude_account="b")

    assert result.ok is False
    (spawn,) = _calls(accounts, "run")
    assert spawn["env"]["CLAUDE_CONFIG_DIR"] == str(accounts.config_dir)


def _golden_view(accounts: SimpleNamespace, plan: InvocationPlan) -> dict:
    """The plan in the snapshot's normalised form; the sanitizer runs with the five ambient variables set."""
    ambient = {
        "CLAUDE_CONFIG_DIR": str(accounts.home / "elsewhere"),
        "CLAUDE_CODE_OAUTH_TOKEN": "fixture-ambient-" + "o" * 30,
        "ANTHROPIC_API_KEY": "fixture-ambient-" + "k" * 30,
        "ANTHROPIC_AUTH_TOKEN": "fixture-ambient-" + "t" * 30,
        "CLAUDE_API_KEY": "fixture-ambient-" + "c" * 30,
    }
    with patch.dict(os.environ, ambient):
        env = build_agent_env(provider="claude", overrides=plan.env_overrides)
    cmd = list(plan.cmd)
    settings = cmd.index("--settings") + 1
    assert cmd[settings] == claude._headless_worker_settings(publish_guard=False)
    cmd[settings] = "<worker-settings>"
    tmp = str(accounts.workdir.parent)
    return {
        "cmd": [arg.replace(tmp, "<tmp>") for arg in cmd],
        "env_overrides": dict(plan.env_overrides),
        "env_unsets": list(plan.env_unsets),
        "liveness_paths": [str(path).replace(tmp, "<tmp>") for path in plan.liveness_paths],
        "metadata": plan.metadata,
        "sanitized_env": {key: env.get(key) for key in sorted({*ambient, *plan.env_overrides})},
        "stdin_payload": plan.stdin_payload,
    }


@pytest.mark.parametrize("case", sorted(USER_SETTINGS))
@pytest.mark.parametrize("tool_config", [{}, {"claude_account": "a"}], ids=["omitted", "explicit_default"])
def test_default_label_plan_matches_the_base_snapshot(accounts, monkeypatch, tool_config, case):
    """AC-02 golden: the default account's plan and sanitised environment equal the base snapshot.

    The snapshot was built from the base before this change; the user
    settings of either account never alter the default plan, and nothing
    is verified or probed for it.
    """
    _user_settings(accounts, USER_SETTINGS[case], home_too=True)
    expected = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    expected.pop("_provenance")

    assert _golden_view(accounts, _plan(accounts, **tool_config)) == expected
    assert accounts.profile_calls == []
    assert _calls(accounts, "auth_status") == []


@pytest.mark.parametrize("tool_config", [{}, {"claude_account": "a"}], ids=["omitted", "explicit_default"])
def test_default_label_never_reads_machine_policy(accounts, monkeypatch, tool_config):
    """The default account's plan stays the base snapshot on a host with machine policy, which it never reads."""
    MACHINE_POLICY["policy_helper"]()

    def unread() -> str:
        pytest.fail("machine policy was read for the default account")

    monkeypatch.setattr(attempt_boundary, "claude_machine_policy_state", unread)
    monkeypatch.setattr(env_sanitize, "claude_machine_policy_state", unread)
    expected = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    expected.pop("_provenance")

    assert _golden_view(accounts, _plan(accounts, **tool_config)) == expected
    assert accounts.profile_calls == []


@pytest.mark.parametrize("tool_config", [{}, {"claude_account": "a"}], ids=["omitted", "explicit_default"])
def test_default_label_environment_keeps_existing_sanitisation(accounts, monkeypatch, tool_config):
    """The default account keeps the host login and the existing sanitisation, unverified."""
    other = accounts.home / "elsewhere"
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(other))
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "fixture-ambient-" + "o" * 30)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-ambient-" + "k" * 30)
    monkeypatch.setattr(env_sanitize, "_isolated_git_env", lambda *_a, **_k: {"GIT_CONFIG_NOSYSTEM": "1"})

    plan = _plan(accounts, **tool_config)

    assert "CLAUDE_CONFIG_DIR" not in plan.env_overrides
    env = build_agent_env(provider="claude", overrides=plan.env_overrides)
    # Existing default sanitisation: no config directory or OAuth token; the API key passes.
    assert "CLAUDE_CONFIG_DIR" not in env and "CLAUDE_CODE_OAUTH_TOKEN" not in env
    assert env["ANTHROPIC_API_KEY"] == "fixture-ambient-" + "k" * 30
    assert accounts.profile_calls == []


@pytest.mark.parametrize("name", [*CLAUDE_AMBIENT_AUTH, "CLAUDE_CONFIG_DIR"])
def test_conflicting_ambient_credential_with_bound_label_is_refused(accounts, monkeypatch, name):
    """AC-01: an ambient token, API key or other config directory is refused value-free, before spawn."""
    value = str(accounts.home / ".claude") if name == "CLAUDE_CONFIG_DIR" else "fixture-ambient-" + "e" * 30
    monkeypatch.setenv(name, value)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == "claude_account_ambient_conflict"
    assert str(refused.value) == "claude_account_ambient_conflict"
    assert not accounts.dump.exists()
    assert accounts.profile_calls == []


@pytest.mark.parametrize("label", ["c", "B", "", 2])
def test_unknown_label_is_refused_before_any_probe(accounts, monkeypatch, label):
    """AC-01: an unknown label never reaches the version probe, the binding or a spawn."""

    def no_probe(*_args, **_kwargs):
        raise AssertionError("probed before the label was refused")

    monkeypatch.setattr(claude, "_ensure_supported_claude_cli_version", no_probe)
    monkeypatch.setattr(claude, "_default_claude_bin", no_probe)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account=label)

    assert refused.value.code == "claude_account_unknown"
    assert accounts.profile_calls == []


def test_bound_label_on_an_unsealed_isolation_route_is_refused(accounts):
    """A bridge isolation run builds its own environment, so it cannot honour another account."""
    with pytest.raises(ClaudeAccountRefused) as refused:
        claude._claude_account_binding({"claude_account": "b", "review_isolation": True})

    assert refused.value.code == "claude_account_route_unsealed"
    assert accounts.profile_calls == []


def test_sealed_attempt_keeps_selecting_its_account_at_its_boundary(accounts):
    """The attempt boundary authenticates a sealed attempt; the adapter adds no login directory."""
    assert claude._claude_account_binding({"claude_account": "b", "review_attempt_boundary": object()}) is None
    assert accounts.profile_calls == []


def test_bound_label_binding_refusal_is_value_free(accounts):
    _credentials(accounts.config_dir / ".credentials.json", accounts.default_token)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")

    assert refused.value.code == "claude_account_unverified"
    assert refused.value.code in CLAUDE_ACCOUNT_REFUSAL_CODES
    assert str(accounts.config_dir) not in str(refused.value)


def test_new_refusal_codes_are_registered():
    assert {
        "claude_account_settings_credential_source",
        "claude_account_auth_method_conflict",
        "claude_account_auth_status_unavailable",
        "claude_account_settings_invalid",
        "claude_account_settings_not_private",
        "claude_account_config_credential_source",
        "claude_account_config_ambiguous",
        "claude_account_status_override",
        "claude_account_settings_changed",
        "claude_account_plan_unsupported",
        "claude_account_plan_unverified",
        "claude_account_policy_cache_present",
        "claude_account_policy_cache_unavailable",
        "claude_account_profile_store_present",
        "claude_account_machine_policy_present",
        "claude_account_machine_policy_unavailable",
    } <= CLAUDE_ACCOUNT_REFUSAL_CODES


def test_bound_label_session_and_liveness_use_the_login_directory(accounts):
    """Tool-call recovery and liveness read the bound account's sessions, not the host's."""
    plan = _plan(accounts, claude_account="b")
    session = "00000000-0000-4000-8000-000000010619"
    project = accounts.config_dir / "projects" / claude._claude_project_slug(accounts.workdir)
    project.mkdir(parents=True)
    tool_use = {"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "a"}}
    (project / f"{session}.jsonl").write_text(
        json.dumps({"type": "assistant", "message": {"content": [tool_use]}}) + "\n", encoding="utf-8"
    )
    (accounts.home / ".claude" / "projects" / "host-project").mkdir(parents=True)

    stdout = json.dumps(
        {"type": "result", "subtype": "success", "is_error": False, "result": "ok", "session_id": session}
    )
    parsed = ClaudeAdapter().parse_response(stdout=stdout, stderr="", returncode=0, output_file=None, plan=plan)

    assert [call["name"] for call in parsed.tool_calls] == ["Read"]
    assert ClaudeAdapter().liveness_signal_paths(plan) == (project,)


def test_sanitizer_admits_the_login_directory_only_from_the_claude_adapter(monkeypatch):
    """The override survives the token-shape filter; ambient or other-provider values never pass."""
    login_dir = "/fixture/desk-b/claude"  # contains a token-shaped "sk-b" substring
    monkeypatch.setenv("CLAUDE_API_KEY", "fixture-ambient-" + "k" * 30)

    env = build_agent_env(provider="claude", overrides={"CLAUDE_CONFIG_DIR": login_dir})
    assert env["CLAUDE_CONFIG_DIR"] == login_dir
    assert "CLAUDE_API_KEY" not in env

    monkeypatch.setenv("CLAUDE_CONFIG_DIR", login_dir)
    assert "CLAUDE_CONFIG_DIR" not in build_agent_env(provider="claude")
    assert build_agent_env(provider="claude")["CLAUDE_API_KEY"] == "fixture-ambient-" + "k" * 30
    assert "CLAUDE_CONFIG_DIR" not in build_agent_env(provider="codex", overrides={"CLAUDE_CONFIG_DIR": login_dir})
    assert os.environ["CLAUDE_CONFIG_DIR"] == login_dir


# --- Consumer plans only (#10619) ------------------------------------------------------------------
#
# Organisational (Team or Enterprise) policy can reach a run after its checks,
# so a labelled account is admitted only on a consumer plan, classified from the
# live profile of the exact credential the run launches with. Held out: written
# against 0cefef3f25, where none of the refusals below happened.

# Server-delivered policy state Claude Code 2.1.300 keeps in its config
# directory: remote managed settings and policy limits, their signatures, sync
# stamps and consent records. A consumer login neither fetches nor writes any.
POLICY_CACHES = (
    "remote-settings.json",
    "remote-settings.json.signature.json",
    "remote-settings.json.signature-iat.json",
    "remote-settings.json.synced-at",
    "remote-settings-consent.json",
    "remote-settings-helper-consent",
    "policy-limits.json",
    "policy-limits.json.signature.json",
    "policy-limits.json.signature-iat.json",
    "policy-limits.json.stamp.json",
)


def _live_plan(monkeypatch: pytest.MonkeyPatch, organization_type: str | None) -> None:
    """The organisation type the bound credential's live profile reports; ``None``: it reports no organisation."""
    if organization_type is None:
        monkeypatch.delitem(PROFILE_ORGANIZATIONS, BOUND_ACCOUNT_UUID)
        return
    organization = {"uuid": ACCOUNT_ORG_UUIDS[BOUND_ACCOUNT_UUID], "organization_type": organization_type}
    monkeypatch.setitem(PROFILE_ORGANIZATIONS, BOUND_ACCOUNT_UUID, organization)


def _account_record(accounts: SimpleNamespace, record: dict) -> None:
    _global_config(accounts, oauthAccount=record)


def _profile_store_entry(store: Path, entry: str) -> None:
    """A profile login Claude Code would take instead of the login directory's credential."""
    if entry == "configs":
        _private_json(store / "configs" / "default.json", {"authentication": {"type": "user_oauth"}})
    else:
        store.mkdir(parents=True, exist_ok=True)
        (store / "active_config").write_text("fixture\n", encoding="utf-8")


# AC-01: (live organisation type, plan stored with the credential, refusal; None admits).
PLAN_TABLE = {
    "consumer_max": ("claude_max", "max", None),
    "consumer_pro": ("claude_pro", "pro", None),
    "team": ("claude_team", "team", "claude_account_plan_unsupported"),
    "enterprise": ("claude_enterprise", "enterprise", "claude_account_plan_unsupported"),
    "unknown": ("claude_fixture_unknown", "max", "claude_account_plan_unsupported"),
    "missing": (None, "max", "claude_account_plan_unsupported"),
}


@pytest.mark.parametrize("case", list(PLAN_TABLE))
def test_bound_label_admits_only_a_consumer_plan(accounts, monkeypatch, case):
    """Only ``claude_max`` and ``claude_pro`` run; any other, unknown or missing type refuses before any probe."""
    organization_type, stored, code = PLAN_TABLE[case]
    _live_plan(monkeypatch, organization_type)
    _credentials(accounts.config_dir / ".credentials.json", accounts.bound_token, plan=stored)

    if code is None:
        result, _ = _invoke(accounts, claude_account="b")
        assert result.ok is True
        assert len(_calls(accounts, "run")) == 1
        return
    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")
    assert str(refused.value) == refused.value.code == code
    assert _calls(accounts, "auth_status") == [] and _calls(accounts, "run") == []


def test_bound_label_organisational_credential_with_consumer_metadata_is_refused(accounts, monkeypatch):
    """Held-out: the stored plan and account record say Max; the exact credential is a Team organisation's."""
    _live_plan(monkeypatch, "claude_team")

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == "claude_account_plan_unsupported"
    assert accounts.profile_calls == [accounts.bound_token]
    assert _calls(accounts, "run") == []


# Cached metadata that disagrees with the live classification of the exact credential.
STALE_METADATA = {
    "stored_plan_organisational": lambda accounts: _credentials(
        accounts.config_dir / ".credentials.json", accounts.bound_token, plan="team"
    ),
    "stored_plan_missing": lambda accounts: _credentials(
        accounts.config_dir / ".credentials.json", accounts.bound_token, plan=None
    ),
    "stored_plan_other_consumer": lambda accounts: _credentials(
        accounts.config_dir / ".credentials.json", accounts.bound_token, plan="pro"
    ),
    "record_other_organisation": lambda accounts: _account_record(
        accounts, {**_login_identity(BOUND_ACCOUNT_UUID), "organizationUuid": ACCOUNT_ORG_UUIDS[DEFAULT_ACCOUNT_UUID]}
    ),
    "record_without_organisation": lambda accounts: _account_record(accounts, {"accountUuid": BOUND_ACCOUNT_UUID}),
}


@pytest.mark.parametrize("case", sorted(STALE_METADATA))
def test_bound_label_stale_or_edited_plan_metadata_is_refused(accounts, case):
    """Held-out: stale or edited cached plan metadata never stands in for the live classification."""
    STALE_METADATA[case](accounts)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == "claude_account_plan_unverified"
    assert _calls(accounts, "run") == []


def test_bound_label_status_resolving_an_organisational_plan_is_refused(accounts, monkeypatch):
    """The plan Claude Code itself resolves for the run's login must be a consumer one."""
    monkeypatch.setenv("LU_FAKE_CLAUDE_STATUS_MODE", "team_plan")

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == "claude_account_plan_unverified"
    assert _calls(accounts, "run") == []


@pytest.mark.parametrize("name", POLICY_CACHES)
def test_bound_label_policy_cache_present_is_refused(accounts, name):
    """Held-out: any server-delivered policy state in the login directory refuses, before any probe."""
    _private_json(accounts.config_dir / name, {"env": {"ANTHROPIC_BASE_URL": "https://fixture.invalid"}})

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == "claude_account_policy_cache_present"
    assert "fixture" not in str(refused.value)
    assert accounts.profile_calls == []
    assert not accounts.dump.exists()


def test_bound_label_policy_cache_link_or_directory_is_refused(accounts):
    """A dangling link or a directory at a cache path is present, not absent."""
    (accounts.config_dir / "policy-limits.json").symlink_to(accounts.config_dir / "absent-target")
    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")
    assert refused.value.code == "claude_account_policy_cache_present"

    (accounts.config_dir / "policy-limits.json").unlink()
    (accounts.config_dir / "remote-settings.json").mkdir()
    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")
    assert refused.value.code == "claude_account_policy_cache_present"


def test_bound_label_unreadable_policy_cache_state_is_refused(accounts, monkeypatch):
    """A cache path whose state cannot be read refuses, value-free."""
    original = os.stat

    def denied(path, *args, **kwargs):
        if path == "policy-limits.json":
            raise PermissionError(13, "fixture-private-detail")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(os, "stat", denied)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")

    assert refused.value.code == "claude_account_policy_cache_unavailable"
    assert "fixture-private-detail" not in repr(refused.value) + repr(refused.value.__cause__)


@pytest.mark.parametrize("name", POLICY_CACHES)
def test_bound_label_policy_delivered_after_verification_never_launches(accounts, name):
    """Held-out (delayed policy delivery): a cache written between verification and launch stops the exec.

    On 0cefef3f25 only ``remote-settings.json`` was bound; for every other
    name the CLI started (``_calls(accounts, "run")`` held one spawn).
    """
    result = _settings_change_after_build(
        accounts,
        lambda: _private_json(accounts.config_dir / name, {"env": {"ANTHROPIC_BASE_URL": "https://fixture.invalid"}}),
    )

    assert result.ok is False
    assert _calls(accounts, "run") == []
    assert "CLAUDE_ACCOUNT_REFUSED: claude_account_settings_changed" in result.stderr_excerpt


@pytest.mark.parametrize(
    ("location", "entry"),
    [("home", "configs"), ("home", "active_config"), ("xdg", "configs"), ("named", "active_config")],
)
def test_bound_label_profile_store_login_is_refused(accounts, monkeypatch, tmp_path, location, entry):
    """A profile store Claude Code could take the login from instead breaks the credential binding."""
    if location == "home":
        store = accounts.home / ".config" / "anthropic"
    elif location == "xdg":
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
        store = tmp_path / "xdg" / "anthropic"
    else:
        monkeypatch.setenv("ANTHROPIC_CONFIG_DIR", str(tmp_path / "named"))
        store = tmp_path / "named"
    _profile_store_entry(store, entry)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == "claude_account_profile_store_present"
    assert accounts.profile_calls == []


def test_bound_label_empty_profile_store_directory_is_admitted(accounts):
    """The directory alone selects no profile; only its active profile or profile configs do."""
    (accounts.home / ".config" / "anthropic").mkdir(parents=True)

    result, _ = _invoke(accounts, claude_account="b")

    assert result.ok is True


@pytest.mark.parametrize("entry", ["configs", "active_config"])
def test_bound_label_profile_written_after_verification_never_launches(accounts, entry):
    result = _settings_change_after_build(
        accounts, lambda: _profile_store_entry(accounts.home / ".config" / "anthropic", entry)
    )

    assert result.ok is False
    assert _calls(accounts, "run") == []
    assert "CLAUDE_ACCOUNT_REFUSED: claude_account_settings_changed" in result.stderr_excerpt


@pytest.mark.parametrize(
    "change",
    ["credential_replaced", "stored_plan_edited", "record_organisation_edited"],
)
def test_bound_label_account_metadata_changed_after_verification_never_launches(accounts, change):
    """Held-out: the launch uses exactly the classified credential and its plan metadata.

    On 0cefef3f25 neither the credential nor the account record was bound and
    the CLI started.
    """

    def edit() -> None:
        credentials = accounts.config_dir / ".credentials.json"
        if change == "credential_replaced":
            _credentials(credentials, "fixture-organisation-" + "o" * 30)
        elif change == "stored_plan_edited":
            _credentials(credentials, accounts.bound_token, plan="team")
        else:
            other = ACCOUNT_ORG_UUIDS[DEFAULT_ACCOUNT_UUID]
            _account_record(accounts, {**_login_identity(BOUND_ACCOUNT_UUID), "organizationUuid": other})

    result = _settings_change_after_build(accounts, edit)

    assert result.ok is False
    assert _calls(accounts, "run") == []
    assert "CLAUDE_ACCOUNT_REFUSED: claude_account_settings_changed" in result.stderr_excerpt
    assert "fixture-organisation" not in result.stderr_excerpt


def test_bound_label_credential_changed_after_classification_is_refused(accounts, monkeypatch):
    """Held-out: a credential replaced after it was classified, before the launch is bound, is never bound."""
    classify = attempt_boundary.verify_claude_account

    def classify_then_replace(label, **kwargs):
        binding = classify(label, **kwargs)
        _credentials(accounts.config_dir / ".credentials.json", "fixture-organisation-" + "o" * 30)
        return binding

    monkeypatch.setattr(attempt_boundary, "verify_claude_account", classify_then_replace)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")

    assert refused.value.code == "claude_account_settings_changed"


# --- No machine-level policy (#10619) ---------------------------------------------------------------
#
# A machine policy helper's output reaches a run from a program the launch
# digest cannot bind (final review of f8dce2b219). So a labelled account runs
# only on a host with no machine policy source at all; presence refuses,
# whatever it holds. Held out: written against f8dce2b219.


def _policy_helper(accounts: SimpleNamespace) -> Path:
    """Configure a machine policy helper answering from a policy service (a file here); return that answer."""
    answer = accounts.workdir.parent / "policy-service-answer.json"
    answer.write_text(json.dumps({"managedSettings": {}}), encoding="utf-8")
    helper = accounts.workdir.parent / "policy-helper.sh"
    helper.write_text(f'#!/bin/sh\nexec cat "{answer}"\n', encoding="utf-8")
    helper.chmod(0o700)
    root = env_sanitize._CLAUDE_MANAGED_SETTINGS_DIR
    _private_json(root / "managed-settings.json", {"policyHelper": {"path": str(helper), "timeoutMs": 3000}})
    return answer


@pytest.mark.parametrize("entry", sorted(MACHINE_POLICY))
def test_bound_label_machine_policy_source_is_refused(accounts, entry):
    """Any machine policy source refuses before any probe or spawn, value-free.

    On f8dce2b219 every case ran the worker.
    """
    MACHINE_POLICY[entry]()

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert str(refused.value) == refused.value.code == "claude_account_machine_policy_present"
    assert accounts.profile_calls == []
    assert not accounts.dump.exists()


def test_bound_label_machine_policy_helper_is_refused_whatever_it_answers(accounts):
    """The final review's reproduction: a helper whose service answers empty settings at verification refuses.

    On f8dce2b219 it was admitted and the guarded launch ran, so a later answer
    (an endpoint override) reached the run with the bound digest unchanged.
    """
    _policy_helper(accounts)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _invoke(accounts, claude_account="b")

    assert refused.value.code == "claude_account_machine_policy_present"
    assert not accounts.dump.exists()


def test_launch_guard_stops_a_machine_policy_helper_whose_answer_changed(accounts):
    """The reproduction at the guard: only the helper's answer changes, the digest does not, the CLI never starts.

    On f8dce2b219 the guard accepted the unchanged digest and exec'd the CLI
    (exit 0, one recorded run).
    """
    answer = _policy_helper(accounts)
    settings = claude._headless_worker_settings(publish_guard=False)
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(accounts.config_dir)}

    def digest() -> str:
        return claude_labelled_inputs_digest(
            login_dir=str(accounts.config_dir),
            cwd=accounts.workdir,
            settings=settings,
            setting_sources=LABELLED_ACCOUNT_SETTING_SOURCES,
            environ=env,
        )

    bound = digest()
    answer.write_text(json.dumps({"managedSettings": {"env": {"ANTHROPIC_BASE_URL": "https://fixture.invalid"}}}))
    assert digest() == bound  # nothing the digest reads changed
    cmd = [str(accounts.binary), "-p", "--settings", settings, "--setting-sources", "project,local", "--", "fixture"]

    done = subprocess.run(
        [sys.executable, "-I", "-c", claude._LAUNCH_GUARD_CODE, str(claude._CODE_ROOT), bound, "--", *cmd],
        cwd=accounts.workdir,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert done.returncode == CLAUDE_LAUNCH_GUARD_EXIT
    assert done.stderr == "CLAUDE_ACCOUNT_REFUSED: claude_account_settings_changed\n"
    assert _calls(accounts, "run") == []


@pytest.mark.parametrize("entry", sorted(MACHINE_POLICY))
def test_bound_label_machine_policy_installed_after_verification_never_launches(accounts, entry):
    """Machine policy that appears between verification and launch stops the guard with exit 78."""
    result = _settings_change_after_build(accounts, MACHINE_POLICY[entry])

    assert result.ok is False
    assert result.returncode == CLAUDE_LAUNCH_GUARD_EXIT
    assert _calls(accounts, "run") == []
    assert "CLAUDE_ACCOUNT_REFUSED: claude_account_settings_changed" in result.stderr_excerpt


def test_bound_label_machine_policy_installed_after_classification_is_refused(accounts, monkeypatch):
    """Policy that appears after the account is classified, before the launch is bound, is never bound."""
    classify = attempt_boundary.verify_claude_account

    def classify_then_install(label, **kwargs):
        binding = classify(label, **kwargs)
        MACHINE_POLICY["managed_memory"]()
        return binding

    monkeypatch.setattr(attempt_boundary, "verify_claude_account", classify_then_install)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")

    assert refused.value.code == "claude_account_machine_policy_present"


def test_bound_label_unreadable_machine_policy_is_refused(accounts, monkeypatch):
    """A machine policy root whose entries cannot be listed refuses, value-free."""
    root = env_sanitize._CLAUDE_MANAGED_SETTINGS_DIR
    root.mkdir()
    original = os.scandir

    def denied(path=".", *args, **kwargs):
        if isinstance(path, str | os.PathLike) and Path(path) == root:
            raise PermissionError(13, "fixture-private-detail")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(os, "scandir", denied)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(accounts, claude_account="b")

    assert refused.value.code == "claude_account_machine_policy_unavailable"
    assert "fixture-private-detail" not in repr(refused.value) + repr(refused.value.__cause__)
    assert accounts.profile_calls == []


@pytest.mark.parametrize("root", ["absent", "empty_directory"])
def test_bound_label_without_machine_policy_is_admitted(accounts, root):
    """No machine policy root, or an empty one, keeps the labelled run as before."""
    if root == "empty_directory":
        env_sanitize._CLAUDE_MANAGED_SETTINGS_DIR.mkdir()

    result, _ = _invoke(accounts, claude_account="b")

    assert result.ok is True
    assert len(_calls(accounts, "run")) == 1


# --- The installed Claude CLI, where present ------------------------------------------------------


@pytest.fixture
def real_cli(accounts: SimpleNamespace) -> SimpleNamespace:
    if not _REAL_CLAUDE:
        pytest.skip("Claude CLI is not installed; the fake CLI above covers the same plans")
    accounts.binary = Path(_REAL_CLAUDE)
    # The CLI reports a subscription login only for a token carrying inference scope.
    _credentials(
        accounts.config_dir / ".credentials.json", accounts.bound_token, scopes=["user:inference", "user:profile"]
    )
    return accounts


def _real(accounts: SimpleNamespace, *args: str, sources: bool = True) -> str:
    settings = claude._headless_worker_settings(publish_guard=False)
    argv = [str(accounts.binary), "--settings", settings]
    if sources:
        argv += ["--setting-sources", LABELLED_ACCOUNT_SETTING_SOURCES]
    env = build_agent_env(provider="claude", overrides={"CLAUDE_CONFIG_DIR": str(accounts.config_dir)})
    done = subprocess.run(
        [*argv, *args], cwd=accounts.workdir, env=env, capture_output=True, text=True, timeout=60, check=False
    )
    return done.stdout


def test_real_cli_admits_a_clean_bound_login(real_cli):
    _user_settings(real_cli, USER_SETTINGS["clean"])

    plan = _plan(real_cli, claude_account="b")

    assert plan.env_overrides["CLAUDE_CONFIG_DIR"] == str(real_cli.config_dir)


@pytest.mark.parametrize(
    ("name", "settings"),
    [
        ("settings.local.json", {"apiKeyHelper": "fixture-helper-command"}),
        ("settings.local.json", {"env": {"CLAUDE_CODE_USE_BEDROCK": "1"}}),
    ],
)
def test_real_cli_checkout_setting_that_changes_auth_is_refused(real_cli, name, settings):
    _private_json(real_cli.workdir / ".claude" / name, settings)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(real_cli, claude_account="b")

    assert refused.value.code == "claude_account_auth_method_conflict"


@pytest.mark.parametrize("case", ["env_api_key", "api_key_helper"])
def test_real_cli_unloads_the_labelled_user_scope(real_cli, case):
    """The user-scope key source the static check refuses is also not loaded by the labelled run's arguments."""
    _user_settings(real_cli, USER_SETTINGS[case])

    loaded = json.loads(_real(real_cli, "auth", "status", "--json", sources=False))
    unloaded = json.loads(_real(real_cli, "auth", "status", "--json"))

    assert loaded["authMethod"] in {"api_key", "api_key_helper"}  # the fixture is effective
    assert unloaded["authMethod"] == "claude.ai"


def test_real_cli_labelled_run_loads_no_user_mcp_server(real_cli):
    global_config = json.loads((real_cli.config_dir / ".claude.json").read_text(encoding="utf-8"))
    global_config["mcpServers"] = {"fixtureuser": {"type": "stdio", "command": "/bin/true", "args": []}}
    _private_json(real_cli.config_dir / ".claude.json", global_config)

    assert "fixtureuser" in _real(real_cli, "mcp", "list", sources=False)
    assert "fixtureuser" not in _real(real_cli, "mcp", "list")


@pytest.mark.parametrize("case", ["endpoint", "key", "provider", "proxy"])
def test_real_cli_global_config_override_is_refused(real_cli, case):
    """Blocker 1 against the installed CLI: the global config's env is checked before any status probe."""
    _global_config(real_cli, env=GLOBAL_CONFIG_ENV_REFUSED[case])

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(real_cli, claude_account="b")

    assert refused.value.code == "claude_account_config_credential_source"


@pytest.mark.parametrize("name", ["ANTHROPIC_BASE_URL", "HTTPS_PROXY"])
def test_real_cli_status_attests_the_endpoint_and_proxy(real_cli, monkeypatch, name):
    """With the name let through, the installed CLI's text status still names the override and the run refuses.

    Its JSON status for the same input reports ``claude.ai`` / ``firstParty`` /
    the bound directory, which is why the JSON alone cannot attest it.
    """
    monkeypatch.setattr(
        attempt_boundary, "CLAUDE_LABELLED_ENV_ALLOWLIST", attempt_boundary.CLAUDE_LABELLED_ENV_ALLOWLIST | {name}
    )
    _global_config(real_cli, env={name: "http://127.0.0.1:9"})
    loaded = json.loads(_real(real_cli, "auth", "status", "--json"))
    assert (loaded["authMethod"], loaded["apiProvider"]) == ("claude.ai", "firstParty")

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(real_cli, claude_account="b")

    assert refused.value.code == "claude_account_status_override"


def test_real_cli_stored_key_in_global_config_is_refused(real_cli):
    """A key stored in the global config is reported as a key source beside the login, and refused."""
    _global_config(real_cli, primaryApiKey="fixture-key-" + "k" * 30)

    with pytest.raises(ClaudeAccountRefused) as refused:
        _plan(real_cli, claude_account="b")

    assert refused.value.code == "claude_account_auth_method_conflict"
