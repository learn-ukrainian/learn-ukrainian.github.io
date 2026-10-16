"""Hermetic capacity inputs and a live-snapshot tripwire for reviewer tests."""

import urllib.request
from urllib.parse import urlsplit

import pytest


@pytest.fixture
def reviewer_headroom_snapshot():
    """Fresh headroom on every reviewer lane, independent of the host (#10764)."""
    return {
        "diagnostics": {"records_loaded": 5, "stale": False, "codexbar_data_available": True},
        "agents": {
            seat: {
                "status": "cool",
                "remaining_pct": 90,
                "health": {"healthy": True},
                "codexbar": {
                    "weekly_remaining_pct": 90,
                    "primary_remaining_pct": 90,
                    "will_last_to_reset": True,
                },
            }
            for seat in ("claude", "codex", "grok", "cursor", "agy")
        },
    }


# Reviewer resolver/admission modules from the #10764 sibling sweep. Pure
# resolver calls use ResolverInputs.routing_snapshot; entry-point tests inject
# their reader. Guard the HTTP boundary too, including either delegate import.
_REVIEW_ROUTING_TEST_MODULES = frozenset({
    "test_adjudicate.py",
    "test_agy_review_profile.py",
    "test_ask_review_admission_floor.py",
    "test_authoring_review_feasibility.py",
    "test_bench_health.py",
    "test_cursor_cf_identity.py",
    "test_delegate.py",
    "test_delegate_admission.py",
    "test_delegate_bounded_advisory.py",
    "test_delegate_branch_exists.py",
    "test_delegate_check_budget.py",
    "test_delegate_mechanical_worker_admission.py",
    "test_delegate_review_admission.py",
    "test_delegate_review_brief_warning.py",
    "test_mechanical_admission.py",
    "test_model_catalog_roles.py",
    "test_pace_reserve_routing.py",
    "test_record_cf_verdict.py",
    "test_repo_wide_marker_invariant.py",
    "test_review_capacity_rule.py",
    "test_review_closeout_cli.py",
    "test_review_cursor_grok_reviewer.py",
    "test_review_mcp.py",
    "test_review_reviewer_resolver.py",
    "test_reviewer_language_lanes.py",
    "test_reviewer_resolver.py",
    "test_rules_core_structural_coverage.py",
    "test_target_admission.py",
    "test_target_admission_structure.py",
})


@pytest.fixture(autouse=True)
def _guard_live_reviewer_snapshot(request, monkeypatch):
    """An uninjected reviewer snapshot must fail before reaching the host (#10764)."""
    if request.path.name not in _REVIEW_ROUTING_TEST_MODULES:
        return

    urlopen = urllib.request.urlopen

    def guarded_urlopen(url, *args, **kwargs):
        address = url.full_url if isinstance(url, urllib.request.Request) else url
        if urlsplit(address).path == "/api/state/routing-budget":
            pytest.fail("live reviewer routing snapshot read: inject a fixed snapshot in this test")
        return urlopen(url, *args, **kwargs)

    monkeypatch.setattr(urllib.request, "urlopen", guarded_urlopen)
