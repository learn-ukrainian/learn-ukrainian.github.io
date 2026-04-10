"""Tests for scripts/tools/update_plan_activities.py.

Covers the deterministic plan-activity-hints updater delivered for
issue #1148. The test suite exercises the shipping API (``update_plan``
+ ``build_activity_hints``); a richer API (backup tracking,
normalize_activity_hints with custom-hint preservation, etc.) is a
follow-up concern and not currently implemented.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from tools import update_plan_activities as updater

# ---------------------------------------------------------------------------
# build_activity_hints — shape of generated hints
# ---------------------------------------------------------------------------

def test_build_activity_hints_from_mock_profile():
    profile = {
        "inline": [
            {
                "type": "quiz",
                "after_section": "Конфліктна карта",
                "focus": "Перевірка розуміння дебатів",
            },
            {
                "type": "reading",
                "after_section": "Читання",
                "focus": "Розуміння тексту",
            },
        ],
        "workbook": [
            {"type": "comparative-study", "focus": "Порівняння інтерпретацій"},
            {"type": "essay-response", "focus": "Есе про значення теми"},
        ],
    }
    plan = {"title": "Назва модуля"}
    hints = updater.build_activity_hints(profile, plan)

    # Shape checks. _contextualize_focus appends "(title)" to
    # comparative-study and essay-response focuses, so we check the
    # prefix rather than equality for those two entries.
    assert len(hints) == 4
    assert hints[0] == {
        "type": "quiz",
        "placement": "inline",
        "after_section": "Конфліктна карта",
        "focus": "Перевірка розуміння дебатів",
        "items": 5,
    }
    assert hints[1] == {
        "type": "reading",
        "placement": "inline",
        "after_section": "Читання",
        "focus": "Розуміння тексту",
    }
    assert hints[2]["type"] == "comparative-study"
    assert hints[2]["placement"] == "workbook"
    assert "Порівняння інтерпретацій" in hints[2]["focus"]
    assert "Назва модуля" in hints[2]["focus"]
    assert hints[3]["type"] == "essay-response"
    assert hints[3]["placement"] == "workbook"
    assert "Есе про значення теми" in hints[3]["focus"]


def test_build_activity_hints_includes_items_only_for_quiz_and_true_false():
    profile = {
        "inline": [
            {"type": "quiz", "after_section": "X", "focus": "q"},
            {"type": "true-false", "after_section": "Y", "focus": "tf"},
            {"type": "reading", "after_section": "Z", "focus": "r"},
        ],
        "workbook": [],
    }
    hints = updater.build_activity_hints(profile, {"title": "T"})
    assert hints[0]["items"] == 5  # quiz
    assert hints[1]["items"] == 5  # true-false
    assert "items" not in hints[2]  # reading


# ---------------------------------------------------------------------------
# update_plan — file I/O + idempotency
# ---------------------------------------------------------------------------

def test_update_plan_replaces_broken_hints(tmp_path):
    """A plan with forbidden fill-in hints gets rewritten."""
    profile = {
        "inline": [
            {"type": "quiz", "after_section": "Конфліктна карта", "focus": "qf"},
            {"type": "reading", "after_section": "Читання", "focus": "rf"},
        ],
        "workbook": [
            {"type": "critical-analysis", "focus": "cf"},
            {"type": "essay-response", "focus": "ef"},
        ],
    }
    plan = {
        "title": "Test plan",
        "slug": "test",
        "activity_hints": [
            {"type": "fill-in", "focus": "legacy"},
            {"type": "note", "focus": "legacy"},
            {"type": "quiz", "focus": "legacy"},
        ],
    }
    plan_path = tmp_path / "test.yaml"
    plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")

    changed = updater.update_plan(plan_path, profile, dry_run=False)
    assert changed is True

    # Reload and verify the new hints don't contain any forbidden types
    reloaded = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    new_types = {h["type"] for h in reloaded["activity_hints"]}
    assert new_types.isdisjoint(updater.FORBIDDEN_TYPES)
    assert "quiz" in new_types
    assert "reading" in new_types
    assert "essay-response" in new_types


def test_update_plan_skips_already_compliant_plans(tmp_path):
    """A plan with 5+ hints that already uses valid seminar types is
    left alone — re-running the updater must be idempotent."""
    profile = {
        "inline": [
            {"type": "quiz", "after_section": "Конфліктна карта", "focus": "qf"},
            {"type": "reading", "after_section": "Читання", "focus": "rf"},
        ],
        "workbook": [
            {"type": "source-evaluation", "focus": "sf"},
            {"type": "comparative-study", "focus": "cf"},
            {"type": "critical-analysis", "focus": "crf"},
            {"type": "essay-response", "focus": "ef"},
        ],
    }
    plan = {
        "title": "Clean plan",
        "slug": "clean",
        "activity_hints": updater.build_activity_hints(profile, {"title": "Clean plan"}),
    }
    plan_path = tmp_path / "clean.yaml"
    plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
    before = plan_path.read_text(encoding="utf-8")

    changed = updater.update_plan(plan_path, profile, dry_run=False)
    assert changed is False  # nothing to change
    after = plan_path.read_text(encoding="utf-8")
    assert before == after  # file untouched


def test_update_plan_dry_run_does_not_write(tmp_path):
    """Dry-run mode returns True when a change would occur but
    leaves the file unchanged."""
    profile = {
        "inline": [
            {"type": "quiz", "after_section": "X", "focus": "q"},
        ],
        "workbook": [
            {"type": "essay-response", "focus": "e"},
        ],
    }
    plan = {
        "title": "T",
        "activity_hints": [{"type": "fill-in", "focus": "old"}],
    }
    plan_path = tmp_path / "t.yaml"
    plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
    before = plan_path.read_text(encoding="utf-8")

    would_change = updater.update_plan(plan_path, profile, dry_run=True)
    assert would_change is True
    assert plan_path.read_text(encoding="utf-8") == before


# ---------------------------------------------------------------------------
# Profile loading from the YAML template
# ---------------------------------------------------------------------------

def test_load_activity_profiles_returns_expected_tracks():
    profiles = updater.load_activity_profiles()
    # The 16 canonical seminar tracks must all have a profile
    expected = {
        "folk", "hist", "bio", "istorio",
        "lit", "lit-essay", "lit-hist-fic", "lit-fantastika",
        "lit-war", "lit-humor", "lit-youth", "lit-drama",
        "lit-doc", "lit-crimea",
        "oes", "ruth",
    }
    assert expected.issubset(profiles.keys())


def test_get_profile_falls_back_to_lit_for_unknown_lit_subtrack():
    profiles = {"lit": {"inline": [{"type": "quiz"}], "workbook": []}, "folk": {}}
    resolved = updater.get_profile(profiles, "lit-nonexistent")
    assert resolved["inline"] == [{"type": "quiz"}]


def test_get_profile_for_known_track_returns_its_profile():
    profiles = updater.load_activity_profiles()
    hist = updater.get_profile(profiles, "hist")
    assert "inline" in hist
    assert "workbook" in hist
    assert any(a["type"] == "reading" for a in hist["inline"])


# ---------------------------------------------------------------------------
# Production sanity: the 16 canonical tracks each produce valid hints
# ---------------------------------------------------------------------------

def test_every_track_produces_valid_hints():
    """For each canonical track, building hints from the real profile
    must produce at least 5 entries and zero forbidden types."""
    profiles = updater.load_activity_profiles()
    plan = {"title": "Sample", "content_outline": []}
    for track in updater.ALL_SEMINAR_TRACKS:
        profile = updater.get_profile(profiles, track)
        assert profile, f"no profile for {track}"
        hints = updater.build_activity_hints(profile, plan)
        assert len(hints) >= 5, f"{track} produced only {len(hints)} hints"
        types = {h["type"] for h in hints}
        forbidden_present = types & updater.FORBIDDEN_TYPES
        assert not forbidden_present, f"{track} has forbidden types: {forbidden_present}"
        # Every track should have at least quiz + essay-response
        assert "quiz" in types, f"{track} missing quiz"
        assert "essay-response" in types, f"{track} missing essay-response"
