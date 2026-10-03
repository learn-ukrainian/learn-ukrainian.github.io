"""Unicode boundary regressions through real ai_agent_bridge readers (#9556)."""

import pytest
from jsonl_reader_cases import reader_case


@pytest.mark.parametrize(
    "module, function, site",
    [
        ("scripts.ai_agent_bridge._grok_build", "_native_grok_turn_status", 449),
        ("scripts.ai_agent_bridge._opencode", "read_opencode_turn_status", 263),
        ("scripts.ai_agent_bridge._opencode", "_parse_opencode_stream", 1419),
        ("scripts.ai_agent_bridge._ui_agy", "_read_transcript_events", 118),
        ("scripts.ai_agent_bridge._ui_agy", "_parse_stdout_events", 138),
        ("scripts.ai_agent_bridge._ui_codex", "send", 159),
    ],
    ids=lambda value: str(value),
)
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_reader_preserves_unicode_separators(module, function, site, ending, tmp_path, monkeypatch):
    reader_case(module, function, site, ending, tmp_path, monkeypatch)
