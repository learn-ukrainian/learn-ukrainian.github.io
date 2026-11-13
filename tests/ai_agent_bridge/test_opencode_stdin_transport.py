"""OpenCode prompt transport contracts, isolated from whole-tree invariants."""

import json
import sys
from unittest.mock import patch

import pytest

from scripts.ai_agent_bridge._opencode import _run_opencode
from scripts.lib import rules_core


@pytest.mark.parametrize("attachment", [False, True], ids=["prompt-only", "with-attachment"])
def test_large_prepared_prompt_avoids_e2big_and_reaches_non_tty_stdin(tmp_path, attachment):
    """Never put the >128 KiB prompt in argv or mistake --file for prompt input."""
    binary = tmp_path / "opencode"
    binary.write_text(
        f"#!{sys.executable}\nimport json, sys\n"
        "args = sys.argv[1:]\n"
        "assert args[:5] == ['run', '--model', 'deepseek/deepseek-flash', '--format', 'json']\n"
        "assert args[5:] == ['--variant', 'high', '--'] or "
        "(args[5:8] == ['--variant', 'high', '--file'] and len(args) == 10 and args[-1] == '--')\n"
        "print(json.dumps([sys.stdin.isatty(), sys.stdin.read()]))\n"
    )
    binary.chmod(0o700)
    content = "- " + "large transport payload\n" * 7000 + "END-12852"
    expected = rules_core.with_core(content)
    assert len(expected.encode("utf-8")) > 128 * 1024
    data = tmp_path / "context.md"
    data.write_text("attachment stays separate")
    with patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value=str(binary)):
        result = _run_opencode(
            content, "deepseek/deepseek-flash", variant="high", output_format="json",
            data=str(data) if attachment else None,
        )
    assert json.loads(result) == [False, expected]
