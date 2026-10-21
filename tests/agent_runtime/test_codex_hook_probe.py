"""Offline model-boundary checks for the native Codex diagnostic probe."""
from unittest.mock import patch

import pytest

from scripts.agent_runtime import codex_hook_probe as probe


def test_probe_rejects_explicit_old_pin_before_process(tmp_path):
    with patch.object(probe, "_run") as run:
        with pytest.raises(ValueError, match=r"only gpt-6\.1-sol"):
            probe._run_case(tmp_path, probe.PROBE_CASES[0], "gpt-5.6-sol", 1)
    run.assert_not_called()
