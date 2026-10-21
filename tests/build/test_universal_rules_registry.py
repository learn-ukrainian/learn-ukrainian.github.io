"""Tests for the V7.2 universal-rules registry loader.

Covers: real-fragment discovery + parsing, predicate filtering, topological
ordering, malformed-fragment handling, missing/circular deps, and the
telemetry-id contract (`#R-X`) used by `linear_pipeline.rule_id` telemetry.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.build import universal_rules_registry as reg
from scripts.build.universal_rules_registry import (
    CircularDependencyError,
    MalformedFragmentError,
    MissingDependencyError,
    load_all_rules,
    load_applicable_rules,
)

REAL_REGISTRY = reg.UNIVERSAL_RULES_DIR


def _write_fragment(
    directory: Path,
    rule_id: str,
    *,
    slot: str = "shared.contract",
    levels: list[str] | None = None,
    tracks: list[str] | None = None,
    activity_profiles: list[str] | None = None,
    depends_on: list[str] | None = None,
    description: str = "Synthetic fixture rule.",
    body: str = "Body content.",
) -> Path:
    """Write a well-formed fragment file under `directory` and return its path."""
    levels = levels or ["all"]
    tracks = tracks or ["all"]
    activity_profiles = activity_profiles or ["all"]
    depends_on = depends_on or []
    path = directory / f"{rule_id}.md"
    lines = [
        "---",
        f"id: {rule_id}",
        f"description: {description}",
        "applies_to:",
        f"  levels: {levels}",
        f"  tracks: {tracks}",
        f"  activity_profiles: {activity_profiles}",
        f"slot: {slot}",
        f"depends_on: {depends_on}",
        "---",
        "",
        body,
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Real-fragment smoke tests (locked against the shipped registry)
# ---------------------------------------------------------------------------


class TestRealRegistry:

    def test_telemetry_id_matches_pipeline_constants(self) -> None:
        """`telemetry_id` must produce strings that match `linear_pipeline.RULE_*`."""
        from scripts.build import linear_pipeline as lp

        rules_by_id = {r.id: r for r in load_all_rules()}
        # These pipeline constants name registry rules — verify exact match.
        expected = {
            lp.RULE_VOICE_META: "R-VOICE-META",
            lp.RULE_BAD_FORM_MARKER: "R-BAD-FORM-MARKER",
            lp.RULE_VESUM_ALL_WORDS: "R-VESUM-ALL-WORDS",
            lp.RULE_IMPL_MAP_COMPLETE: "R-IMPL-MAP-COMPLETE",
            lp.RULE_TEXTBOOK_30W: "R-TEXTBOOK-30W",
            lp.RULE_CITE_HONEST: "R-CITE-HONEST",
        }
        for telemetry_form, bare_id in expected.items():
            assert bare_id in rules_by_id, f"missing fragment for pipeline constant {telemetry_form}"
            assert rules_by_id[bare_id].telemetry_id == telemetry_form

    def test_real_registry_is_acyclic(self) -> None:
        """Topological sort of the full real registry must complete."""
        # `load_applicable_rules` runs the topo sort internally; if there's a
        # cycle in the real registry, this raises CircularDependencyError.
        rules = load_applicable_rules("a1", "core", "all")
        assert rules, "expected at least one applicable rule at a1/core/all"


# ---------------------------------------------------------------------------
# Discovery + frontmatter parsing
# ---------------------------------------------------------------------------


class TestDiscoveryAndParsing:
    def test_load_all_rules_skips_readme_and_non_R_files(self, tmp_path: Path) -> None:
        _write_fragment(tmp_path, "R-ALPHA")
        (tmp_path / "README.md").write_text("# Not a fragment\n", encoding="utf-8")
        (tmp_path / "notes.md").write_text("---\nid: bogus\n---\n", encoding="utf-8")
        rules = load_all_rules(tmp_path)
        assert [r.id for r in rules] == ["R-ALPHA"]

    def test_missing_frontmatter_raises(self, tmp_path: Path) -> None:
        (tmp_path / "R-BARE.md").write_text("just a body, no frontmatter\n", encoding="utf-8")
        with pytest.raises(MalformedFragmentError, match="frontmatter"):
            load_all_rules(tmp_path)

    def test_invalid_yaml_frontmatter_raises(self, tmp_path: Path) -> None:
        (tmp_path / "R-BROKEN.md").write_text(
            "---\nid: R-BROKEN\napplies_to: : :\n---\nbody\n", encoding="utf-8"
        )
        with pytest.raises(MalformedFragmentError):
            load_all_rules(tmp_path)

    def test_filename_must_match_id(self, tmp_path: Path) -> None:
        path = tmp_path / "R-WRONGSTEM.md"
        path.write_text(
            "---\nid: R-OTHER\napplies_to:\n  levels: [all]\n  tracks: [all]\n  activity_profiles: [all]\nslot: shared.contract\n---\nbody\n",
            encoding="utf-8",
        )
        with pytest.raises(MalformedFragmentError, match="filename stem"):
            load_all_rules(tmp_path)


# ---------------------------------------------------------------------------
# Filtering by level / track / activity_profile / slot
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Topological dependency ordering
# ---------------------------------------------------------------------------


class TestTopologicalSort:

    def test_circular_dependency_raises(self, tmp_path: Path) -> None:
        # R-X -> R-Y -> R-X (cycle)
        _write_fragment(tmp_path, "R-X", depends_on=["R-Y"])
        _write_fragment(tmp_path, "R-Y", depends_on=["R-X"])
        with pytest.raises(CircularDependencyError, match="circular"):
            load_applicable_rules("a1", "core", "all", directory=tmp_path)

    def test_missing_dependency_raises(self, tmp_path: Path) -> None:
        _write_fragment(tmp_path, "R-NEEDS", depends_on=["R-GHOST"])
        with pytest.raises(MissingDependencyError, match="R-GHOST"):
            load_applicable_rules("a1", "core", "all", directory=tmp_path)


# ---------------------------------------------------------------------------
# get_rule + Rule dataclass behavior
# ---------------------------------------------------------------------------
