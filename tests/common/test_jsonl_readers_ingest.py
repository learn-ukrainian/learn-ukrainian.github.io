"""Unicode boundary regressions through real ingest readers (#9556)."""

import pytest
from jsonl_reader_cases import reader_case


@pytest.mark.parametrize(
    "module, function, site",
    [
        ("scripts.ingest.owned_books_ingest", "_cached_jsonl_records", 577),
    ],
    ids=lambda value: str(value),
)
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_reader_preserves_unicode_separators(module, function, site, ending, tmp_path, monkeypatch):
    reader_case(module, function, site, ending, tmp_path, monkeypatch)
