"""Unicode boundary regressions through real ua_eval_harness readers (#9556)."""

import pytest
from jsonl_reader_cases import reader_case


@pytest.mark.parametrize(
    "module, function, site",
    [
        ("scripts.projects.ua_eval_harness.analyze_v011_evidence", "read_jsonl", 64),
        ("scripts.projects.ua_eval_harness.build_v02_review_packet", "read_jsonl", 64),
        ("scripts.projects.ua_eval_harness.run_codex_baseline", "_read_jsonl", 45),
        ("scripts.projects.ua_eval_harness.verify_release_freeze", "_read_jsonl", 131),
        ("scripts.projects.ua_eval_harness.verify_release_freeze_v011", "_read_jsonl", 194),
    ],
    ids=lambda value: str(value),
)
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_reader_preserves_unicode_separators(module, function, site, ending, tmp_path, monkeypatch):
    reader_case(module, function, site, ending, tmp_path, monkeypatch)
