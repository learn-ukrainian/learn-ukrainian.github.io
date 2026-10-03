"""Unicode boundary regressions through real fleet_comms readers (#9556)."""

import pytest
from jsonl_reader_cases import reader_case


@pytest.mark.parametrize(
    "module, function, site",
    [
        ("scripts.fleet_comms.adapter_conformance", "_parse_jsonl", 93),
        ("scripts.fleet_comms.cli", "cmd_authority_import", 765),
        ("scripts.fleet_comms.message_plane", "_summarize_parity_telemetry", 709),
    ],
    ids=lambda value: str(value),
)
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_reader_preserves_unicode_separators(module, function, site, ending, tmp_path, monkeypatch):
    reader_case(module, function, site, ending, tmp_path, monkeypatch)
