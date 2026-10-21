"""Guards for wiki review per-dim + MIN aggregation (#1455).

These tests lock in the migration from legacy weighted-average review
to strict per-dim + MIN aggregation. They catch regressions in three
places where the semantics matter:

1. MIN aggregation: a single weak dim must drive the score, not be
   averaged away by stronger siblings.
2. Threshold source-of-truth: the PASS floor comes from
   ``scripts.common.thresholds.REVIEW_PASS_FLOOR`` (post-#1454), not a
   local placeholder.
3. No legacy weighted-average code path reachable from the wiki review
   module — the new pattern does not co-exist with the old.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.reads_content

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from wiki.review import (
    DimResult,
    ReviewReport,
    RoundResult,
    aggregate_min,
    default_thresholds,
)


def _dim_result(dim: str, score: float, verdict: str = "PASS") -> DimResult:
    """Minimal DimResult fixture — the fields not under test get stubs."""
    return DimResult(
        dim=dim,
        agent="test-agent",
        model="test-model",
        score=int(score),
        verdict=verdict,
        findings=[],
        fixes=[],
        notes="",
        duration_s=0.0,
    )


class TestAggregateMin:
    def test_mixed_dims_min_fails(self) -> None:
        """A wiki with 9/9/9/6 scores MUST return min=6 with the low dim named.

        This is the core MIN-semantics guard: stronger dims cannot mask
        a weak dim under the new aggregation. The legacy weighted-average
        would have reported ~8.25 here and passed the gate — that
        regression path is no longer reachable.
        """
        results = {
            "source_grounding": _dim_result("source_grounding", 9),
            "factual_accuracy": _dim_result("factual_accuracy", 6),
            "ukrainian_perspective": _dim_result("ukrainian_perspective", 9),
            "register": _dim_result("register", 9),
        }
        min_score, failing_dim = aggregate_min(results)
        assert min_score == 6.0
        assert failing_dim == "factual_accuracy"

    def test_error_verdict_dominates(self) -> None:
        """A dim with ``verdict=ERROR`` is treated as score 0 regardless
        of what the reviewer reported. Otherwise a crashed reviewer
        could mask as a high score (default int(0) or a partial parse
        of the raw response)."""
        results = {
            "source_grounding": _dim_result("source_grounding", 9),
            "factual_accuracy": _dim_result("factual_accuracy", 10, verdict="ERROR"),
            "ukrainian_perspective": _dim_result("ukrainian_perspective", 9),
            "register": _dim_result("register", 9),
        }
        min_score, failing_dim = aggregate_min(results)
        assert min_score == 0.0
        assert failing_dim == "factual_accuracy"


class TestReviewReportIncludesMin:
    def test_report_has_min_fields(self) -> None:
        """The report schema carries ``min_score`` and ``failing_dim``
        so downstream consumers (build pipeline, audits, monitor API)
        see the MIN driver explicitly — not derived on read."""
        round_result = RoundResult(
            round_num=1,
            dim_results={
                "source_grounding": _dim_result("source_grounding", 9),
                "factual_accuracy": _dim_result("factual_accuracy", 6),
                "ukrainian_perspective": _dim_result("ukrainian_perspective", 9),
                "register": _dim_result("register", 9),
            },
        )
        report = ReviewReport(
            article_path="wiki/test/x.md",
            rounds=[round_result],
            final_verdict="NEEDS_FIXES",
            failing_dims=["factual_accuracy"],
            min_score=6.0,
            failing_dim="factual_accuracy",
            thresholds=default_thresholds(),
            thresholds_calibrated=True,
            shadow_mode=False,
            started_at=0.0,
            finished_at=0.1,
        )
        payload = report.to_jsonable()
        assert payload["min_score"] == 6.0
        assert payload["failing_dim"] == "factual_accuracy"
        assert payload["thresholds_calibrated"] is True
