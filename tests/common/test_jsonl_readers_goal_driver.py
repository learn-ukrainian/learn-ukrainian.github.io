"""Unicode boundary regressions through real goal_driver readers (#9556)."""

import pytest
from jsonl_reader_cases import reader_case


@pytest.mark.parametrize(
    "module, function, site",
    [
        ("scripts.goal_driver.stop_hook", "_last_status_from_transcript", 169),
    ],
    ids=lambda value: str(value),
)
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_reader_preserves_unicode_separators(module, function, site, ending, tmp_path, monkeypatch):
    reader_case(module, function, site, ending, tmp_path, monkeypatch)
