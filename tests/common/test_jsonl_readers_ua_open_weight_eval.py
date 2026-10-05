"""Unicode boundary regressions through real ua_open_weight_eval readers (#9556)."""

import pytest
from jsonl_reader_cases import reader_case


@pytest.mark.parametrize(
    "module, function, site",
    [
        ("scripts.projects.ua_open_weight_eval.hf_jobs_worker", "read_jsonl", 208),
        ("scripts.projects.ua_open_weight_eval.suite_cli", "read_jsonl", 196),
    ],
    ids=lambda value: str(value),
)
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_reader_preserves_unicode_separators(module, function, site, ending, tmp_path, monkeypatch):
    reader_case(module, function, site, ending, tmp_path, monkeypatch)
