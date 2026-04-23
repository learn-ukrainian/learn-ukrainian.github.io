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

import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from common.thresholds import REVIEW_PASS_FLOOR
from wiki.review import (
    DIMS,
    WIKI_REVIEW_THRESHOLD,
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

    def test_all_pass_reports_lowest_still(self) -> None:
        """Even when every dim passes, ``aggregate_min`` names the
        lowest as the driver so callers can surface "closest to floor"."""
        results = {
            "source_grounding": _dim_result("source_grounding", 9),
            "factual_accuracy": _dim_result("factual_accuracy", 10),
            "ukrainian_perspective": _dim_result("ukrainian_perspective", 8),
            "register": _dim_result("register", 10),
        }
        min_score, failing_dim = aggregate_min(results)
        assert min_score == 8.0
        assert failing_dim == "ukrainian_perspective"

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

    def test_empty_results(self) -> None:
        min_score, failing_dim = aggregate_min({})
        assert min_score == 0.0
        assert failing_dim is None

    def test_single_dim(self) -> None:
        results = {"register": _dim_result("register", 8)}
        min_score, failing_dim = aggregate_min(results)
        assert min_score == 8.0
        assert failing_dim == "register"


class TestThresholdSourceOfTruth:
    def test_wiki_threshold_equals_central_floor(self) -> None:
        """Wiki review must read its PASS floor from the central
        ``scripts.common.thresholds.REVIEW_PASS_FLOOR`` (post-#1454) —
        not a local placeholder."""
        assert WIKI_REVIEW_THRESHOLD == REVIEW_PASS_FLOOR

    def test_default_thresholds_uniform_and_central(self) -> None:
        thresholds = default_thresholds()
        assert set(thresholds) == set(DIMS)
        for dim, value in thresholds.items():
            assert value == REVIEW_PASS_FLOOR, (
                f"dim {dim!r} threshold drifted from central floor"
            )


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


class TestLegacyWeightedAveragePathRemoved:
    """Grep-invariant: the legacy weighted-average helpers must be
    fully deleted from the wiki review path. A stray reference to any
    of them regresses the migration."""

    REMOVED = (
        "_parse_review_scores",
        "_build_review_prompt",
        "_extract_review_summary",
        "_send_review",
        "_dim_review_article",
    )

    def test_compile_py_has_no_legacy_helpers(self) -> None:
        compile_py = (
            PROJECT_ROOT / "scripts" / "wiki" / "compile.py"
        ).read_text(encoding="utf-8")
        for name in self.REMOVED:
            assert name not in compile_py, (
                f"legacy weighted-average helper {name!r} still present in "
                "scripts/wiki/compile.py"
            )

    def test_no_weighted_average_terms_in_wiki_review_path(self) -> None:
        """Semantic grep across wiki review path — 'weighted average',
        'mean_score', ``.mean(`` must not appear. Presence signals the
        old pattern being reintroduced."""
        review_py = (
            PROJECT_ROOT / "scripts" / "wiki" / "review.py"
        ).read_text(encoding="utf-8")
        compile_py = (
            PROJECT_ROOT / "scripts" / "wiki" / "compile.py"
        ).read_text(encoding="utf-8")
        forbidden = re.compile(
            r"weighted[_\s]*average|mean_score|\.mean\(",
            re.IGNORECASE,
        )
        for path, body in (("review.py", review_py), ("compile.py", compile_py)):
            match = forbidden.search(body)
            assert match is None, (
                f"legacy weighted-average terminology found in "
                f"scripts/wiki/{path}: {match.group(0)!r}"
            )


@pytest.mark.parametrize(
    ("scores", "expected_min", "expected_driver"),
    [
        ((10, 10, 10, 10), 10.0, "source_grounding"),  # tie → first-seen
        ((8, 8, 8, 8), 8.0, "source_grounding"),
        ((10, 9, 8, 7), 7.0, "register"),
        ((7, 10, 10, 10), 7.0, "source_grounding"),
    ],
)
def test_aggregate_min_parametric(
    scores: tuple[int, int, int, int],
    expected_min: float,
    expected_driver: str,
) -> None:
    """Parametric matrix — ``aggregate_min`` is dict-order-preserving
    on ties and picks the strictly-lowest otherwise."""
    results = {
        dim: _dim_result(dim, score) for dim, score in zip(DIMS, scores, strict=True)
    }
    min_score, failing_dim = aggregate_min(results)
    assert min_score == expected_min
    assert failing_dim == expected_driver
