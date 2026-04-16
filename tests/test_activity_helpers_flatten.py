"""Tests for the shape-normalising helper that reads activities YAML.

Context for #1294 — multiple callsites (pre-review gate, dashboard,
scoring, quality pipeline) use ``isinstance(activities, list)`` to
decide whether to process the YAML. That branch is never entered for
V6 modules, whose activities YAML is a dict with ``inline:`` and
``workbook:`` buckets. ``flatten_activities`` is the shared normaliser
callers should route through to avoid that class of bug.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from audit.checks.activity_helpers import flatten_activities


def test_flatten_activities_handles_legacy_bare_list() -> None:
    raw = [
        {"id": "a", "type": "quiz"},
        {"id": "b", "type": "fill-in"},
    ]
    assert flatten_activities(raw) == raw


def test_flatten_activities_handles_v6_inline_workbook_dict() -> None:
    raw = {
        "version": "1.0",
        "module": "hello",
        "level": "a1",
        "inline": [
            {"id": "x", "type": "fill-in"},
            {"id": "y", "type": "quiz"},
        ],
        "workbook": [
            {"id": "z", "type": "anagram"},
        ],
    }
    flat = flatten_activities(raw)
    assert [a["id"] for a in flat] == ["x", "y", "z"]


def test_flatten_activities_handles_dict_with_only_inline() -> None:
    raw = {"inline": [{"id": "only", "type": "quiz"}]}
    assert flatten_activities(raw) == [{"id": "only", "type": "quiz"}]


def test_flatten_activities_handles_older_activities_wrapper() -> None:
    # Older wrapper shape — {"activities": [...]}. Only honoured when there
    # is no inline/workbook bucket, so we don't double-count on hybrid files.
    raw = {"activities": [{"id": "w", "type": "match-up"}]}
    assert flatten_activities(raw) == [{"id": "w", "type": "match-up"}]


def test_flatten_activities_prefers_v6_buckets_over_wrapper_when_both_present() -> None:
    # If a file has BOTH V6 buckets and an older "activities" wrapper
    # (unlikely but not impossible from LLM output), the V6 buckets win and
    # the wrapper is not merged in — we must not count the same activity
    # twice from two different fields.
    raw = {
        "inline": [{"id": "v6", "type": "fill-in"}],
        "activities": [{"id": "legacy", "type": "quiz"}],
    }
    flat = flatten_activities(raw)
    assert [a["id"] for a in flat] == ["v6"]


def test_flatten_activities_drops_non_dict_entries_silently() -> None:
    raw = {
        "inline": [
            {"id": "ok", "type": "quiz"},
            "stray string from LLM",
            None,
            42,
            {"id": "also_ok", "type": "fill-in"},
        ]
    }
    flat = flatten_activities(raw)
    assert [a["id"] for a in flat] == ["ok", "also_ok"]


def test_flatten_activities_returns_empty_list_for_none() -> None:
    assert flatten_activities(None) == []


def test_flatten_activities_returns_empty_list_for_unexpected_types() -> None:
    assert flatten_activities("not a yaml document") == []
    assert flatten_activities(42) == []


def test_flatten_activities_returns_empty_for_empty_dict() -> None:
    assert flatten_activities({}) == []


def test_flatten_activities_handles_dict_buckets_that_are_not_lists() -> None:
    # Malformed YAML where inline: is a dict or a string — don't explode,
    # just skip. Downstream checks will flag absence of activities.
    raw = {"inline": {"oops": "not a list"}, "workbook": "also not a list"}
    assert flatten_activities(raw) == []
