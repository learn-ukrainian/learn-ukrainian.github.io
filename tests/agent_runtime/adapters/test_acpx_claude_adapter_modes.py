
import pytest

from scripts.agent_runtime.adapters import acpx as acpx_module
from scripts.agent_runtime.adapters.acpx import AcpxShadowRefusalError
from tests.agent_runtime.test_acpx_adapter import _fake_installed_claude_adapter


def test_claude_adapter_modes_group_writable_directory(tmp_path):
    binary = _fake_installed_claude_adapter(tmp_path)
    package_root = tmp_path / "node_modules" / "@agentclientprotocol" / "claude-agent-acp"
    package_root.chmod(0o775)

    with pytest.raises(AcpxShadowRefusalError, match=r"package directory failed check: group-or-world writable \(node_modules/@agentclientprotocol/claude-agent-acp, mode 0o775\)") as exc:
        acpx_module._require_local_claude_acp_adapter(str(binary), adapter_label="AcpxClaudeShadowAdapter")

    assert exc.value.failure_code == "acp_adapter_incompatible"

def test_claude_adapter_modes_group_writable_manifest(tmp_path):
    binary = _fake_installed_claude_adapter(tmp_path)
    manifest = tmp_path / "node_modules" / "@agentclientprotocol" / "claude-agent-acp" / "package.json"
    manifest.chmod(0o664)

    with pytest.raises(AcpxShadowRefusalError, match=r"manifest failed check: group-or-world writable \(node_modules/@agentclientprotocol/claude-agent-acp/package.json, mode 0o664\)") as exc:
        acpx_module._require_local_claude_acp_adapter(str(binary), adapter_label="AcpxClaudeShadowAdapter")

    assert exc.value.failure_code == "acp_adapter_incompatible"

def test_claude_adapter_modes_group_writable_executable(tmp_path):
    binary = _fake_installed_claude_adapter(tmp_path)
    executable = tmp_path / "node_modules" / "@agentclientprotocol" / "claude-agent-acp" / "dist" / "index.js"
    executable.chmod(0o775)

    with pytest.raises(AcpxShadowRefusalError, match=r"executable failed check: group-or-world writable \(node_modules/@agentclientprotocol/claude-agent-acp/dist/index.js, mode 0o775\)") as exc:
        acpx_module._require_local_claude_acp_adapter(str(binary), adapter_label="AcpxClaudeShadowAdapter")

    assert exc.value.failure_code == "acp_adapter_incompatible"

def test_claude_adapter_modes_world_writable_refuses(tmp_path):
    binary = _fake_installed_claude_adapter(tmp_path)
    manifest = tmp_path / "node_modules" / "@agentclientprotocol" / "claude-agent-acp" / "package.json"
    manifest.chmod(0o666)

    with pytest.raises(AcpxShadowRefusalError, match=r"manifest failed check: group-or-world writable \(node_modules/@agentclientprotocol/claude-agent-acp/package.json, mode 0o666\)") as exc:
        acpx_module._require_local_claude_acp_adapter(str(binary), adapter_label="AcpxClaudeShadowAdapter")

    assert exc.value.failure_code == "acp_adapter_incompatible"

def test_claude_adapter_modes_correct_passes(tmp_path):
    binary = _fake_installed_claude_adapter(tmp_path)

    metadata = acpx_module._require_local_claude_acp_adapter(str(binary), adapter_label="AcpxClaudeShadowAdapter")
    assert metadata["claude_acp_launch_source"] == "installed"


def test_claude_adapter_modes_normalization(tmp_path):
    # umask 002-like environment
    binary = _fake_installed_claude_adapter(tmp_path)
    package_root = tmp_path / "node_modules" / "@agentclientprotocol" / "claude-agent-acp"
    manifest = package_root / "package.json"
    executable = package_root / "dist" / "index.js"

    package_root.chmod(0o775)
    manifest.chmod(0o664)
    executable.chmod(0o775)

    # Check it fails initially
    with pytest.raises(AcpxShadowRefusalError):
        acpx_module._require_local_claude_acp_adapter(str(binary), adapter_label="AcpxClaudeShadowAdapter")

    # Run the normalization
    import subprocess
    repo_root = acpx_module._REPO_ROOT
    script_path = repo_root / "scripts" / "agent_runtime" / "normalize_acp_modes.js"
    subprocess.run(["node", str(script_path)], cwd=tmp_path, check=True, timeout=10)

    # Should pass now
    metadata = acpx_module._require_local_claude_acp_adapter(str(binary), adapter_label="AcpxClaudeShadowAdapter")
    assert metadata["claude_acp_launch_source"] == "installed"

def test_claude_adapter_modes_normalization_symlinked_root(tmp_path):
    import subprocess
    repo_root = acpx_module._REPO_ROOT
    script_path = repo_root / "scripts" / "agent_runtime" / "normalize_acp_modes.js"

    unrelated_dir = tmp_path / "unrelated"
    unrelated_dir.mkdir()
    unrelated_file = unrelated_dir / "target.js"
    unrelated_file.write_text("console.log('hi');")
    unrelated_dir.chmod(0o775)
    unrelated_file.chmod(0o664)

    package_parent = tmp_path / "node_modules" / "@agentclientprotocol"
    package_parent.mkdir(parents=True, exist_ok=True)
    package_root = package_parent / "claude-agent-acp"
    package_root.symlink_to(unrelated_dir)

    result = subprocess.run(["node", str(script_path)], cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert "is a symlink" in result.stderr

    # Assert modes unchanged
    assert oct(unrelated_dir.stat().st_mode).endswith("775")
    assert oct(unrelated_file.stat().st_mode).endswith("664")

def test_claude_adapter_modes_normalization_symlink_inside(tmp_path):
    import subprocess
    repo_root = acpx_module._REPO_ROOT
    script_path = repo_root / "scripts" / "agent_runtime" / "normalize_acp_modes.js"

    binary = _fake_installed_claude_adapter(tmp_path)
    package_root = tmp_path / "node_modules" / "@agentclientprotocol" / "claude-agent-acp"

    unrelated_file = tmp_path / "unrelated.js"
    unrelated_file.write_text("console.log('hi');")

    symlink_file = package_root / "symlink.js"
    symlink_file.symlink_to(unrelated_file)

    result = subprocess.run(["node", str(script_path)], cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert "Symlink found" in result.stderr

def test_claude_adapter_modes_normalization_absent_package(tmp_path):
    import subprocess
    repo_root = acpx_module._REPO_ROOT
    script_path = repo_root / "scripts" / "agent_runtime" / "normalize_acp_modes.js"

    # Package is not created
    result = subprocess.run(["node", str(script_path)], cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0
    assert "is absent" in result.stdout

def test_claude_adapter_modes_normalization_chmod_failure(tmp_path):
    import subprocess
    repo_root = acpx_module._REPO_ROOT
    script_path = repo_root / "scripts" / "agent_runtime" / "normalize_acp_modes.js"

    binary = _fake_installed_claude_adapter(tmp_path)
    package_root = tmp_path / "node_modules" / "@agentclientprotocol" / "claude-agent-acp"

    dist_dir = package_root / "dist"
    index_file = dist_dir / "index.js"
    # Make the file writable so we want to chmod it
    index_file.chmod(0o777)

    # Read-only parent (lacks execute/search bit)
    dist_dir.chmod(0o444)

    result = subprocess.run(["node", str(script_path)], cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0

    # Restore permissions so pytest can clean up
    dist_dir.chmod(0o755)
