"""Unicode boundary regressions through the shared usage reader (#9556)."""

import json

import pytest

from scripts.agent_runtime.usage import _iter_usage_records


@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_reader_preserves_unicode_separators(ending, tmp_path):
    record = {"probe": "before\u0085middle\u2028more\u2029after"}
    path = tmp_path / "usage_fixture.jsonl"
    path.write_bytes((json.dumps(record, ensure_ascii=False) + ending).encode("utf-8"))
    unreadable = {"files": 0, "lines": 0, "records": 0}

    assert list(_iter_usage_records(path, unreadable)) == [record]
    assert unreadable == {"files": 0, "lines": 0, "records": 0}
