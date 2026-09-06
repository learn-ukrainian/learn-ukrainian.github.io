"""Offline model-boundary checks for the native Codex diagnostic probe."""
import subprocess
from unittest.mock import patch

import pytest

from scripts.agent_runtime import codex_hook_probe as probe


@pytest.mark.parametrize("model", [None, "gpt-6-astra"])
def test_probe_pins_astra_low(tmp_path, model):
    with patch.object(probe, "_run", return_value=subprocess.CompletedProcess([], 0, "", "")) as run:
        probe._run_case(tmp_path, probe.PROBE_CASES[0], model, 1)
    command = run.call_args.args[0]
    assert command[command.index("--model") + 1] == "gpt-6-astra"
    assert 'model_reasoning_effort="low"' in command


def test_probe_rejects_explicit_old_pin_before_process(tmp_path):
    with patch.object(probe, "_run") as run:
        with pytest.raises(ValueError, match="only gpt-6-astra"):
            probe._run_case(tmp_path, probe.PROBE_CASES[0], "gpt-5.6-sol", 1)
    run.assert_not_called()


def test_probe_rejects_environment_old_pin(monkeypatch):
    monkeypatch.setenv("CODEX_HOOK_PROBE_MODEL", "gpt-5.6-sol")
    monkeypatch.setattr("sys.argv", ["probe"])
    with pytest.raises(SystemExit) as exc:
        probe.parse_args()
    assert exc.value.code == 2
