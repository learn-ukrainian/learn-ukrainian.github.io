import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audit.parsing import AuditContext, AuditState
from scripts.audit.phases_report import validate_review_and_finalize


@pytest.mark.parametrize(
    ("level_code", "score", "ok", "threshold"),
    [("A1", 9.0, True, 9.0), ("A2", 9.0, True, 9.0), ("B1", 9.0, True, 9.0),
     ("B2", 8.0, True, 8.0), ("C1", 8.0, True, 8.0), ("A1", 8.0, False, 9.0),
     ("B2", 7.0, False, 8.0)],
)
def test_v6_review_gate_uses_level_threshold(tmp_path, monkeypatch, level_code, score, ok, threshold):
    module_file = tmp_path / level_code.lower() / "test-module.md"
    module_file.parent.mkdir()
    module_file.write_text("# Test\n", encoding="utf-8")
    review_dir = module_file.parent / "orchestration" / module_file.stem
    review_dir.mkdir(parents=True)
    (review_dir / "review-structured-r1.yaml").write_text(f"scores:\n  - score: {score}\n", encoding="utf-8")
    monkeypatch.setattr("scripts.audit.phases_report.save_status_cache", lambda *args, **kwargs: str(tmp_path / "status.json"))
    ctx = AuditContext(str(module_file), "Test", "Test", "", {"version": "2.0"}, {"slug": module_file.stem},
                       None, None, level_code, 1, level_code, level_code, None, "Test Module", 1200, {}, {},
                       "Test", level_code, "Not Specified", False, False, None, False, Path("."))
    state = AuditState()

    assert validate_review_and_finalize(ctx, state) is ok
    if ok:
        assert state.critical_failure_reasons == []
    else:
        assert state.critical_failure_reasons == [
            f"Latest review review-structured-r1.yaml score is {score:.1f} < {threshold:.1f}"
        ]
