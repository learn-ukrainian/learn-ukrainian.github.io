"""Shared shell tool recognition is exact and leaves other tools untouched."""

import importlib.util
from pathlib import Path


def test_issue_10337_shell_names_are_exact():
    source = Path(__file__).resolve().parents[1] / "agents_extensions/shared/hooks/tool_names.py"
    spec = importlib.util.spec_from_file_location("hook_tool_names", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for name in ("Bash", "Shell"):
        assert module.is_shell_tool(name)
    for name in ("bash", "shell", "Shell ", "Write", "Edit", "MultiEdit", "WriteShellStdin", "unknown", "", None, [], {}):
        assert not module.is_shell_tool(name)
