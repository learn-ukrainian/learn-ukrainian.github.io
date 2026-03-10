"""Tests for scoring/aggregator.py — metric aggregation and scoring."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from scoring.aggregator import (
    TrackMetrics,
    aggregate_track_metrics,
    calculate_criterion_score,
    calculate_track_score,
)
from scoring.metrics import ModuleMetrics


def _make_module(slug="test", level="hist", **kwargs):
    """Create a ModuleMetrics with sensible defaults."""
    defaults = dict(
        module_slug=slug, level=level, md_exists=True, meta_exists=True,
        activities_exists=True, vocabulary_exists=True, status_exists=True,
        audit_status="pass", word_count=5000, total_sentences=100,
        agency_markers=15, quote_callouts=2, myth_buster_callouts=1,
        analysis_callouts=1, activity_count=5, activity_items=30,
        vocab_items=20, naturalness_score=9.0, cross_references=2,
    )
    defaults.update(kwargs)
    return ModuleMetrics(**defaults)


class TestAggregateTrackMetrics:
    def test_empty_modules(self):
        tm = aggregate_track_metrics([], "hist")
        assert tm.track_id == "hist"
        assert tm.modules_found == 0
        assert tm.passing_modules == 0

    def test_single_passing_module(self):
        modules = [_make_module()]
        tm = aggregate_track_metrics(modules, "hist")
        assert tm.modules_found == 1
        assert tm.passing_modules == 1
        assert tm.failing_modules == 0

    def test_aggregates_word_counts(self):
        modules = [
            _make_module(slug="m1", word_count=5000),
            _make_module(slug="m2", word_count=3000),
        ]
        tm = aggregate_track_metrics(modules, "hist")
        assert tm.total_word_count == 8000
        assert tm.avg_word_count == 4000.0

    def test_aggregates_callouts(self):
        modules = [
            _make_module(slug="m1", quote_callouts=3, myth_buster_callouts=2),
            _make_module(slug="m2", quote_callouts=1, myth_buster_callouts=0),
        ]
        tm = aggregate_track_metrics(modules, "hist")
        assert tm.total_quote_callouts == 4
        assert tm.avg_quote_callouts == 2.0
        assert tm.total_myth_buster_callouts == 2

    def test_agency_ratio(self):
        modules = [
            _make_module(agency_markers=20, total_sentences=100),
        ]
        tm = aggregate_track_metrics(modules, "hist")
        assert tm.agency_marker_ratio == pytest.approx(0.2)

    def test_naturalness_average(self):
        modules = [
            _make_module(slug="m1", naturalness_score=8.0),
            _make_module(slug="m2", naturalness_score=10.0),
        ]
        tm = aggregate_track_metrics(modules, "hist")
        assert tm.avg_naturalness_score == pytest.approx(9.0)

    def test_mixed_audit_status(self):
        modules = [
            _make_module(slug="m1", audit_status="pass"),
            _make_module(slug="m2", audit_status="fail"),
            _make_module(slug="m3", audit_status="unknown"),
        ]
        tm = aggregate_track_metrics(modules, "hist")
        assert tm.passing_modules == 1
        assert tm.failing_modules == 1
        assert tm.unknown_modules == 1

    def test_file_coverage(self):
        modules = [
            _make_module(slug="m1", activities_exists=False, vocabulary_exists=False),
            _make_module(slug="m2"),
        ]
        tm = aggregate_track_metrics(modules, "hist")
        assert tm.modules_with_md == 2
        assert tm.modules_with_activities == 1
        assert tm.modules_with_vocabulary == 1


class TestCalculateTrackScore:
    def test_perfect_track_scores_high(self):
        modules = [_make_module(slug=f"m{i}") for i in range(10)]
        tm = aggregate_track_metrics(modules, "hist")
        score = calculate_track_score(tm, "hist")
        assert score.total_weighted_score >= 5.0  # A perfect track should score well

    def test_empty_track_scores_low(self):
        tm = aggregate_track_metrics([], "hist")
        score = calculate_track_score(tm, "hist")
        assert score.total_weighted_score <= 2.0

    def test_score_has_criteria(self):
        modules = [_make_module()]
        tm = aggregate_track_metrics(modules, "hist")
        score = calculate_track_score(tm, "hist")
        assert len(score.final_criterion_scores) > 0
        for name, value in score.final_criterion_scores.items():
            assert 0.0 <= value <= 10.0, f"{name} score {value} out of range"
