"""Sources review config provenance under --ignore-user-config.

Installed codex-cli 0.160.0 ``exec --help`` says: "Do not load
`$CODEX_HOME/config.toml`; auth still uses `CODEX_HOME`". It documents -c:
"Use a dotted path (`foo.bar.baz`) to override nested values."
Official precedence (https://learn.chatgpt.com/docs/config-file/config-basic):
CLI, project, profile, user, cloud-managed, system, built-in defaults.
Native config/read/includeLayers preserves shadowed foreign definitions.
These tests never start a model turn.
"""

import json
import shutil
import sys

import pytest

from scripts.agent_runtime.adapters import codex


def write_config_probe_binary(path, *, signed_in_layer=None, refresh_auth=False, unavailable_when_signed_in=False):
    """Model Codex's config/read protocol without running an installed engine."""
    path.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "assert sys.argv[1:] == ['app-server']\n"
        "assert 'UNRELATED_SECRET' not in os.environ\n"
        "assert 'ANTHROPIC_API_KEY' not in os.environ\n"
        "assert 'NODE_OPTIONS' not in os.environ\n"
        "for line in sys.stdin:\n"
        "    request = json.loads(line)\n"
        "    if request.get('method') == 'config/read':\n"
        "        assert request['params']['cwd'] == os.getcwd()\n"
        "        assert request['params']['includeLayers'] is True\n"
        "        layers = [{'name': {'type': 'user', 'file': os.path.join(os.environ['CODEX_HOME'], 'config.toml')},"
        " 'config': {}}]\n"
        "        auth = Path(os.environ['CODEX_HOME']) / 'auth.json'\n"
        "        if auth.exists():\n"
        f"            if {signed_in_layer!r}:\n"
        f"                layers.append({{'name': {{'type': {signed_in_layer!r}}},"
        " 'config': {'mcp_servers': {'cloud_only': {'command': 'foreign'}}}})\n"
        f"            if {refresh_auth!r}:\n"
        "                refreshed = auth.with_suffix('.refresh')\n"
        '                refreshed.write_text(\'{"session":"refreshed-fixture"}\')\n'
        "                refreshed.replace(auth)\n"
        f"            if {unavailable_when_signed_in!r}:\n"
        "                layers = None\n"
        "        print(json.dumps({'id': request['id'], 'result': {'layers': layers}}), flush=True)\n"
    )
    path.chmod(0o755)
    return path


def layer(kind, servers, **source):
    return {"name": {"type": kind, **source}, "config": {"mcp_servers": servers}, "version": "fixture"}


@pytest.mark.parametrize(
    "kind",
    [
        "project",
        "system",
        "enterpriseManaged",
        "mdm",
        "user",
        "packagedDefaults",
        "cloudManagedConfig",
        "cloudRequirements",
    ],
)
@pytest.mark.parametrize("name", ["sources", "other"])
def test_foreign_layer_refuses_even_when_shadowed(kind, name, tmp_path):
    expected = {"sources": {"command": "trusted"}}
    layers = [layer(kind, {name: {"command": "foreign"}}), layer("sessionFlags", expected)]
    with pytest.raises(codex.CodexReviewConfigError, match="review_mcp_foreign_config_layer"):
        codex._validate_review_mcp_layers(layers, expected, str(tmp_path))


def test_ignored_base_user_config_is_not_a_loaded_layer(tmp_path):
    expected = {"sources": {"command": "trusted"}}
    layers = [layer("user", {"other": {}}, file=str(tmp_path / "config.toml")), layer("system", {})]
    codex._validate_review_mcp_layers(layers, expected, str(tmp_path))


def test_profile_is_not_ignored_base_user_config(tmp_path):
    with pytest.raises(codex.CodexReviewConfigError, match="review_mcp_foreign_config_layer"):
        codex._validate_review_mcp_layers(
            [layer("user", {"sources": {}}, file=str(tmp_path / "config.toml"), profile="review")], {}, str(tmp_path)
        )


@pytest.mark.parametrize("layers", [[], [{}], [layer("sessionFlags", {"sources": {"command": "different"}})]])
def test_unproven_sources_definition_refuses(layers, tmp_path):
    with pytest.raises(codex.CodexReviewConfigError):
        codex._validate_review_mcp_layers(layers, {"sources": {"command": "trusted"}}, str(tmp_path))


@pytest.mark.parametrize(
    "servers",
    [
        {"sources.command": "foreign"},
        {"sources": {"env.INJECTED": "value"}},
        {"sources": {"command": "trusted"}, "other": {"command": "foreign"}},
    ],
)
def test_dotted_or_foreign_overrides_refuse_before_probe(tmp_path, monkeypatch, servers):
    monkeypatch.setattr(codex, "_codex_config_layers", lambda *_args: pytest.fail("untrusted overrides reached probe"))
    with pytest.raises(codex.CodexReviewConfigError, match="review_mcp_foreign_config_override"):
        build(tmp_path, {"ignore_user_config": True, "mcp_servers": servers})


def build(cwd, config):
    return codex.CodexAdapter().build_invocation(
        prompt="inspect",
        mode="read-only",
        cwd=cwd,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=config,
    )


def test_adapter_guards_foreign_only_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(
        codex, "_codex_config_layers", lambda *_args: [layer("system", {"sources": {"command": "foreign"}})]
    )
    with pytest.raises(codex.CodexReviewConfigError, match="review_mcp_foreign_config_layer"):
        build(tmp_path, {"ignore_user_config": True})


def test_adapter_written_sources_receives_read_allowlist(tmp_path, monkeypatch):
    expected = {"sources": {"command": "trusted", "args": []}}
    monkeypatch.setattr(codex, "_codex_config_layers", lambda *_args: [layer("system", {})])
    plan = build(tmp_path, {"ignore_user_config": True, "mcp_servers": expected})
    try:
        grants = next(arg.split("=", 1)[1] for arg in plan.cmd if arg.startswith("mcp_servers.sources.enabled_tools="))
        assert "verify_words" in json.loads(grants)
        assert "query_wikipedia" not in json.loads(grants)
        assert 'mcp_servers.sources.command="trusted"' in plan.cmd
    finally:
        plan.output_file.unlink()


def test_native_config_layer_probe_without_model_call(tmp_path, monkeypatch):
    binary = shutil.which("codex")
    if binary is None:
        pytest.skip("installed Codex CLI unavailable")
    home = tmp_path / "home"
    home.mkdir()
    expected = {"sources": {"command": "/bin/false"}}
    # A scoped home prevents unrelated user settings and credentials from entering diagnostics.
    layers = codex._codex_config_layers(binary, tmp_path, str(home))
    assert any(item["name"]["type"] == "user" for item in layers)
    codex._validate_review_mcp_layers(layers, expected, str(home))


def test_native_probe_failure_is_typed(tmp_path):
    with pytest.raises(codex.CodexReviewConfigError, match="review_mcp_config_layers_unavailable"):
        codex._codex_config_layers("/nonexistent/codex", tmp_path, str(tmp_path))


def test_sealed_adapter_defers_config_layer_probe_until_auth_staging(tmp_path, monkeypatch):
    from scripts.review.isolation import review_isolation_tool_config
    from tests.test_review_isolation import _private_review_roots

    monkeypatch.setattr(
        codex, "_codex_config_layers", lambda *_args, **_kwargs: pytest.fail("signed-out adapter reached probe")
    )
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    write, execution = _private_review_roots(tmp_path, "sealed-config-layers")
    home = write / "home" / ".codex"
    assert not home.exists()
    config = {
        **review_isolation_tool_config("codex"),
        "review_engine_binary": "/bin/true",
        "review_snapshot_root": str(snapshot),
        "review_reject_root": str(snapshot),
        "review_reject_roots": [str(snapshot)],
        "review_write_root": str(write),
        "review_exec_root": str(execution),
    }
    plan = build(snapshot, config)
    try:
        assert home.is_dir() and not home.is_symlink()
        assert not (home / "auth.json").exists()
        assert plan.cwd == write / "exec"
        assert "--ignore-user-config" in plan.cmd
        assert "--dangerously-bypass-approvals-and-sandbox" in plan.cmd
        assert not any(arg.startswith("mcp_servers.sources.") for arg in plan.cmd)
    finally:
        plan.output_file.unlink()


def test_config_layer_probe_forwards_only_codex_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("UNRELATED_SECRET", "fixture")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture")
    monkeypatch.setenv("NODE_OPTIONS", "fixture")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    binary = write_config_probe_binary(tmp_path / "codex")
    home = tmp_path / "home"
    home.mkdir()
    layers = codex._codex_config_layers(str(binary), tmp_path, str(home))
    codex._validate_review_mcp_layers(layers, {}, str(home))


def test_sealed_adapter_refuses_a_symlinked_scoped_home_before_probing(tmp_path, monkeypatch):
    from scripts.review.isolation import review_isolation_tool_config
    from tests.test_review_isolation import _private_review_roots

    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    write, execution = _private_review_roots(tmp_path, "symlinked-home")
    (write / "home" / ".codex").symlink_to(snapshot, target_is_directory=True)
    monkeypatch.setattr(codex, "_codex_config_layers", lambda *_args: pytest.fail("unsafe home reached probe"))
    with pytest.raises(codex.CodexReviewConfigError, match="review_mcp_config_home_unsafe"):
        build(
            snapshot,
            {
                **review_isolation_tool_config("codex"),
                "review_engine_binary": "/bin/true",
                "review_snapshot_root": str(snapshot),
                "review_write_root": str(write),
                "review_exec_root": str(execution),
            },
        )
    assert list(snapshot.iterdir()) == []
    assert list((write / "tmp").iterdir()) == []


def test_unowned_session_definition_refuses_even_when_equal_to_authored_definition(tmp_path):
    expected = {"sources": {"command": "trusted"}}
    with pytest.raises(codex.CodexReviewConfigError, match="review_mcp_foreign_config_layer"):
        codex._validate_review_mcp_layers([layer("sessionFlags", expected)], expected, str(tmp_path))


def test_policy_keys_cannot_replace_an_adapter_written_sources_transport(tmp_path):
    with pytest.raises(codex.CodexReviewConfigError, match="review_mcp_sources_definition_mismatch"):
        codex._validate_review_mcp_layers(
            [layer("system", {})], {"sources": {"enabled_tools": ["verify_words"]}}, str(tmp_path)
        )


def test_native_probe_keeps_ignored_user_url_apart_from_authored_stdio(tmp_path):
    binary = shutil.which("codex")
    if binary is None:
        pytest.skip("installed Codex CLI unavailable")
    home = tmp_path / "home"
    home.mkdir()
    (home / "config.toml").write_text('[mcp_servers.sources]\nurl = "https://example.invalid/mcp"\n')
    expected = {"sources": {"command": "/bin/false"}}
    layers = codex._codex_config_layers(binary, tmp_path, str(home))
    assert any(item["config"].get("mcp_servers") for item in layers)
    codex._validate_review_mcp_layers(layers, expected, str(home))


def test_native_project_sources_definition_is_foreign_even_when_shadowed(tmp_path):
    binary = shutil.which("codex")
    if binary is None:
        pytest.skip("installed Codex CLI unavailable")
    home = tmp_path / "home"
    home.mkdir()
    project = tmp_path / "project"
    (project / ".codex").mkdir(parents=True)
    (project / ".git").mkdir()
    (home / "config.toml").write_text(f'[projects.{json.dumps(str(project))}]\ntrust_level = "trusted"\n')
    (project / ".codex/config.toml").write_text('[mcp_servers.sources]\ncommand = "/bin/false"\n')
    layers = codex._codex_config_layers(binary, project, str(home))
    assert any(item["name"]["type"] == "project" and item["config"].get("mcp_servers") for item in layers)
    with pytest.raises(codex.CodexReviewConfigError, match="review_mcp_foreign_config_layer"):
        codex._validate_review_mcp_layers(layers, {"sources": {"command": "authored"}}, str(home))
