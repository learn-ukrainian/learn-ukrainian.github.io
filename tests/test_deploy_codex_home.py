import json
import stat
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from scripts import deploy_codex_home as deployer


@pytest.fixture
def source(tmp_path):
    root = tmp_path.resolve() / "source"
    (root / "agents").mkdir(parents=True)
    (root / "AGENTS.md").write_text("Reusable instructions.\n")
    (root / "config.toml").write_text(
        'model = "gpt-6-astra"\n[agents]\n'
        'default_subagent_model = "gpt-6-astra"\n'
        'default_subagent_reasoning_effort = "low"\n'
    )
    (root / "agents/worker.toml").write_text(
        'name = "worker"\nmodel = "gpt-6-astra"\n'
        'description = "Bounded worker"\ndeveloper_instructions = "Stay within owned paths."\n'
        'model_reasoning_effort = "low"\nsandbox_mode = "workspace-write"\n'
    )
    return root


def snapshot(root):
    if not root.exists():
        return None
    return {
        str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }


def test_preservation_idempotence_backups(source):
    home = source.parent / "home"
    home.mkdir()
    original = (
        b'# keep comment\nmodel = "old" # picker\nmodel_reasoning_effort = "xhigh"\n'
        b"future = {enabled = true, values = [1, 2]}\n"
        b'[agents]\nmax_threads = 9\ndefault_subagent_model = "old" # worker\n'
        b'[mcp_servers.private]\nurl = "private-sentinel"\n'
    )
    config = home / "config.toml"
    config.write_bytes(original)
    config.chmod(0o640)
    (home / "auth.json").write_text("untouched")
    assert deployer.deploy(source, home) == 0
    result = tomllib.loads(config.read_text())
    assert result["model_reasoning_effort"] == "xhigh"
    assert result["future"] == {"enabled": True, "values": [1, 2]}
    assert result["agents"]["max_threads"] == 9
    assert result["mcp_servers"]["private"]["url"] == "private-sentinel"
    assert "# picker\n" in config.read_text()
    assert "# worker\n" in config.read_text()
    assert (home / "auth.json").read_text() == "untouched"
    assert stat.S_IMODE(config.stat().st_mode) == 0o640
    (run,) = (home / ".deploy-backups").iterdir()
    assert (run / "config.toml").read_bytes() == original
    assert stat.S_IMODE((run / "config.toml").stat().st_mode) == 0o600
    assert stat.S_IMODE(run.stat().st_mode) == 0o700
    receipt = json.loads((run / "receipt.json").read_text())
    assert receipt["status"] == "complete"
    entry = next(e for e in receipt["changes"] if e["path"] == "config.toml")
    assert entry["original_mode"] == 0o640
    before = snapshot(home)
    assert deployer.deploy(source, home) == 0
    assert deployer.deploy(source, home, check=True) == 0
    assert snapshot(home) == before


def test_read_only_clean_install(source):
    home = source.parent / "missing"
    assert deployer.deploy(source, home, dry_run=True) == 0
    assert deployer.deploy(source, home, check=True) == 1
    assert not home.exists()
    assert deployer.deploy(source, home) == 0
    assert tomllib.loads((home / "config.toml").read_text()) == deployer.EXPECTED
    assert (home / "AGENTS.md").read_bytes() == (source / "AGENTS.md").read_bytes()
    assert (home / "agents/worker.toml").is_file()
    before = snapshot(home)
    (source / "AGENTS.md").write_text("changed")
    assert deployer.deploy(source, home, check=True) == 1
    assert deployer.deploy(source, home, dry_run=True) == 0
    assert snapshot(home) == before


@pytest.mark.parametrize(
    "config",
    [
        "model = [broken",
        "agents = {max_threads = 8}\n",
        '"model" = "old"\n',
        'agents = "invalid"\n',
    ],
)
def test_bad_or_unsupported_config_writes_nothing(source, config):
    home = source.parent / "home"
    home.mkdir()
    (home / "config.toml").write_text(config)
    before = snapshot(home)
    with pytest.raises(deployer.DeployError):
        deployer.deploy(source, home)
    assert snapshot(home) == before
    assert not (home / ".deploy-backups").exists()


@pytest.mark.parametrize(
    "relative,content",
    [
        ("config.toml", 'model = "gpt-6-astra"\n'),
        ("config.toml", "[bad"),
        ("agents/worker.toml", "model = [broken"),
        ("AGENTS.md", ""),
    ],
)
def test_bad_source_writes_nothing(source, relative, content):
    (source / relative).write_text(content)
    home = source.parent / "home"
    with pytest.raises(deployer.DeployError):
        deployer.deploy(source, home)
    assert not home.exists()


@pytest.mark.parametrize("location", ["root", "agents", "config.toml", ".deploy-backups"])
def test_target_symlinks_refused(source, location):
    home = source.parent / "home"
    outside = source.parent / "outside"
    outside.mkdir()
    if location == "root":
        home.symlink_to(outside, target_is_directory=True)
    else:
        home.mkdir()
        (home / location).symlink_to(outside, target_is_directory=True)
    with pytest.raises(deployer.DeployError, match="symlink"):
        deployer.deploy(source, home)
    assert list(outside.iterdir()) == []


def test_source_symlink_refused(source):
    (source / "agents/alias.toml").symlink_to(source / "agents/worker.toml")
    home = source.parent / "home"
    with pytest.raises(deployer.DeployError, match="symlink"):
        deployer.deploy(source, home)
    assert not home.exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("model", "gpt-5.5"),
        ("name", "wrong-name"),
        ("description", " "),
        ("developer_instructions", ""),
        ("model_reasoning_effort", "unknown"),
        ("sandbox_mode", "danger-full-access"),
        ("model", None),
        ("name", None),
        ("description", None),
        ("developer_instructions", None),
        ("model_reasoning_effort", None),
        ("sandbox_mode", None),
    ],
)
def test_invalid_profile_cannot_write(source, field, value):
    profile = source / "agents/worker.toml"
    data = tomllib.loads(profile.read_text())
    if value is None:
        del data[field]
    else:
        data[field] = value
    profile.write_text("".join(f"{key} = {json.dumps(item)}\n" for key, item in data.items()))
    home = source.parent / "home"
    home.mkdir()
    (home / "AGENTS.md").write_text("existing instructions")
    before = snapshot(home)
    with pytest.raises(deployer.DeployError, match="source profile"):
        deployer.deploy(source, home)
    assert snapshot(home) == before
    assert not (home / ".deploy-backups").exists()


def test_partial_failure_retains_recovery(source, monkeypatch):
    home = source.parent / "home"
    home.mkdir()
    (home / "AGENTS.md").write_text("old instructions")
    (home / "config.toml").write_text('model = "old"\n')
    real_write = deployer.atomic_write

    def failing_write(path, data, mode=0o600):
        if path == home / "config.toml":
            raise OSError("sensitive-path-must-not-escape")
        return real_write(path, data, mode)

    monkeypatch.setattr(deployer, "atomic_write", failing_write)
    with pytest.raises(deployer.DeployError, match="may be partial") as caught:
        deployer.deploy(source, home)
    assert "sensitive" not in str(caught.value)
    (run,) = (home / ".deploy-backups").iterdir()
    assert (run / "AGENTS.md").read_text() == "old instructions"
    assert (run / "config.toml").read_text() == 'model = "old"\n'
    assert json.loads((run / "receipt.json").read_text())["status"] == "partial_failure"


def test_cli_requires_explicit_home():
    result = subprocess.run([sys.executable, str(Path(deployer.__file__))], capture_output=True, text=True)
    assert result.returncode == 2
    assert "--codex-home" in result.stderr


def test_nested_agents_table_preserved():
    data = b'[agents.worker]\nconfig_file = "worker.toml"\n'
    result = deployer.merge_config(data)
    assert tomllib.loads(result.decode())["agents"]["worker"] == {"config_file": "worker.toml"}
    assert data in result
