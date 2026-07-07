"""Hermetic tests for the issue-stream auditor (#4708) — no network, no gh."""

from __future__ import annotations

import textwrap

import pytest

from scripts.orchestration.issue_stream_audit import classify, load_registry


@pytest.fixture()
def registry(tmp_path):
    path = tmp_path / "issue_streams.yaml"
    path.write_text(
        textwrap.dedent(
            """
            schema_version: 1
            streams:
              product:
                title: "Product"
                epics: [100, 150]
              infra:
                title: "Infra"
                epics: [200]
            """
        ),
        encoding="utf-8",
    )
    return load_registry(path)


def _issues(*numbers):
    return [{"number": n, "title": f"issue {n}"} for n in numbers]


def test_orphan_detected(registry):
    report = classify(
        _issues(100, 150, 200, 5, 6),
        registry,
        {100: ({5}, set()), 150: (set(), set()), 200: (set(), set())},
    )
    assert [o["number"] for o in report["orphans"]] == [6]
    assert report["ok"] is False


def test_epics_are_exempt_from_membership(registry):
    report = classify(
        _issues(100, 150, 200),
        registry,
        {100: (set(), set()), 150: (set(), set()), 200: (set(), set())},
    )
    assert report["orphans"] == []
    assert report["ok"] is True


def test_body_reference_counts_but_flags_pending_migration(registry):
    report = classify(
        _issues(100, 150, 200, 7),
        registry,
        {100: (set(), {7}), 150: (set(), set()), 200: (set(), set())},
    )
    assert report["orphans"] == []
    assert report["pending_native_link"] == [7]


def test_multi_homed_across_streams_flagged(registry):
    report = classify(
        _issues(100, 150, 200, 8),
        registry,
        {100: ({8}, set()), 150: (set(), set()), 200: ({8}, set())},
    )
    assert [m["number"] for m in report["multi_homed"]] == [8]
    assert report["multi_homed"][0]["streams"] == ["infra", "product"]
    # codex F1: multi-homed violates the exactly-one-stream invariant.
    assert report["ok"] is False


def test_same_stream_double_reference_is_not_multi_homed(registry):
    report = classify(
        _issues(100, 150, 200, 9),
        registry,
        {100: ({9}, set()), 150: ({9}, set()), 200: (set(), set())},
    )
    assert report["multi_homed"] == []


def test_closed_epic_surfaces(registry):
    report = classify(
        _issues(100, 200),  # 150 is not open
        registry,
        {100: (set(), set()), 150: (set(), set()), 200: (set(), set())},
    )
    assert report["closed_or_missing_epics"] == [150]
    assert report["ok"] is False


def test_registry_rejects_empty_stream(tmp_path):
    path = tmp_path / "issue_streams.yaml"
    path.write_text("streams:\n  broken:\n    title: x\n    epics: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="broken"):
        load_registry(path)


def test_native_link_wins_over_prose_mention(registry):
    """Once an issue is a native sub-issue somewhere, body refs elsewhere must
    not multi-home it (prose mentions are not membership)."""
    report = classify(
        _issues(100, 150, 200, 11),
        registry,
        {100: ({11}, set()), 150: (set(), set()), 200: (set(), {11})},
    )
    assert report["multi_homed"] == []
    assert report["orphans"] == []
