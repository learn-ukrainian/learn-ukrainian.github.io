
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

def test_claude_adapter_modes_correct_passes(tmp_path):
    binary = _fake_installed_claude_adapter(tmp_path)

    metadata = acpx_module._require_local_claude_acp_adapter(str(binary), adapter_label="AcpxClaudeShadowAdapter")
    assert metadata["claude_acp_launch_source"] == "installed"
