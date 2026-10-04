"""Unicode boundary regressions through real eval readers (#9556)."""

import pytest
from jsonl_reader_cases import reader_case


@pytest.mark.parametrize(
    "module, function, site",
    [
        ("scripts.eval.zno_nmt.adapters", "_parse_sse_or_json", 328),
        ("scripts.eval.zno_nmt.adapters", "_parse_stream_json", 512),
        ("scripts.eval.zno_nmt.mcp_proxy", "decode_response", 28),
    ],
    ids=lambda value: str(value),
)
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_reader_preserves_unicode_separators(module, function, site, ending, tmp_path, monkeypatch):
    reader_case(module, function, site, ending, tmp_path, monkeypatch)
