"""Unicode boundary regressions through real audit readers (#9556)."""

import pytest
from jsonl_reader_cases import reader_case


@pytest.mark.parametrize(
    "module, function, site",
    [
        ("scripts.audit._judge_eval_lib", "pull_calibration_cases", 124),
        ("scripts.audit.bakeoff_aggregate", "read_jsonl", 216),
        ("scripts.audit.bakeoff_run", "_jsonl_has_event", 91),
        ("scripts.audit.layerb_judge_bridge", "_read_strict_jsonl", 925),
        ("scripts.audit.llm_reviewer_dispatch", "read_daily_spend", 955),
        ("scripts.audit.opencode_judge_calibration", "call_opencode", 109),
        ("scripts.audit.russianism_judge", "_read_jsonl_records", 329),
        ("scripts.audit.score_judge_calibration", "load_gold", 67),
        ("scripts.audit.score_judge_calibration", "load_judgments", 85),
        ("scripts.audit.source_inventory_intake", "_read_jsonl_inventory", 320),
        ("scripts.audit.typesafe_citation_verifier", "load_cases", 471),
    ],
    ids=lambda value: str(value),
)
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_reader_preserves_unicode_separators(module, function, site, ending, tmp_path, monkeypatch):
    reader_case(module, function, site, ending, tmp_path, monkeypatch)
