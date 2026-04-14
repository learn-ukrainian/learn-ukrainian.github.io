import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audit.parsing import AuditContext, AuditState
from scripts.audit.phases_report import validate_review_and_finalize


def _write_v6_reviews(
    review_dir: Path,
    *,
    ling_score: float,
    style_overall: float | None = None,
    style_scores: dict[str, float] | None = None,
) -> None:
    if style_scores is None:
        style_scores = {
            "pragmatic_authenticity": style_overall if style_overall is not None else 9.0,
            "stylistic_consistency": style_overall if style_overall is not None else 9.0,
            "culture_and_register": style_overall if style_overall is not None else 9.0,
            "naturalness": style_overall if style_overall is not None else 9.0,
        }
    if style_overall is None:
        style_overall = sum(style_scores.values()) / len(style_scores)

    (review_dir / "review-structured-r1.yaml").write_text(
        f"scores:\n  - score: {ling_score}\n",
        encoding="utf-8",
    )
    (review_dir / "review-structured-style-r1.yaml").write_text(
        "phase: review-style\n"
        "verdict: PASS\n"
        "pass: true\n"
        f"overall_score: {style_overall:.1f}\n"
        "scores:\n"
        + "".join(
            f"  - key: {key}\n    score: {score:.1f}\n"
            for key, score in style_scores.items()
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("level_code", "ling_score", "style_overall", "style_scores", "ok", "expected_reason"),
    [
        ("A1", 9.0, 9.0, None, True, None),
        ("A2", 9.0, 9.1, None, True, None),
        ("B1", 9.2, 9.1, None, True, None),
        (
            "B2",
            8.0,
            8.2,
            None,
            False,
            "Latest style review review-structured-style-r1.yaml has dimension(s) below 8.5: Pragmatic authenticity=8.2, Stylistic consistency=8.2, Culture + register=8.2, Naturalness=8.2",
        ),
        ("A1", 8.0, 9.2, None, False, "Latest review review-structured-r1.yaml score is 8.0 < 9.0"),
        ("A1", 9.5, 8.0, None, False, "Latest style review review-structured-style-r1.yaml score is 8.0 < 9.0"),
        (
            "A1",
            9.5,
            9.1,
            {
                "pragmatic_authenticity": 9.1,
                "stylistic_consistency": 8.4,
                "culture_and_register": 9.2,
                "naturalness": 9.3,
            },
            False,
            "Latest style review review-structured-style-r1.yaml has dimension(s) below 8.5: Stylistic consistency=8.4",
        ),
    ],
)
def test_v6_review_gate_uses_linguistic_and_style_thresholds(
    tmp_path,
    monkeypatch,
    level_code,
    ling_score,
    style_overall,
    style_scores,
    ok,
    expected_reason,
):
    module_file = tmp_path / level_code.lower() / "test-module.md"
    module_file.parent.mkdir()
    module_file.write_text("# Test\n", encoding="utf-8")
    review_dir = module_file.parent / "orchestration" / module_file.stem
    review_dir.mkdir(parents=True)
    _write_v6_reviews(
        review_dir,
        ling_score=ling_score,
        style_overall=style_overall,
        style_scores=style_scores,
    )
    monkeypatch.setattr("scripts.audit.phases_report.save_status_cache", lambda *args, **kwargs: str(tmp_path / "status.json"))
    ctx = AuditContext(str(module_file), "Test", "Test", "", {"version": "2.0"}, {"slug": module_file.stem},
                       None, None, level_code, 1, level_code, level_code, None, "Test Module", 1200, {}, {},
                       "Test", level_code, "Not Specified", False, False, None, False, Path("."))
    state = AuditState()

    assert validate_review_and_finalize(ctx, state) is ok
    if ok:
        assert state.critical_failure_reasons == []
    else:
        assert state.critical_failure_reasons[0] == expected_reason
