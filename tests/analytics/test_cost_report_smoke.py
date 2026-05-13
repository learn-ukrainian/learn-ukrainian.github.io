"""Analytics package smoke tests for targeted dispatch verification."""

from scripts.analytics.cost_report import estimate_tokens


def test_estimate_tokens_smoke():
    assert estimate_tokens(3800) == 1000
