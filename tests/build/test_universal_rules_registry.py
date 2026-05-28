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
    RuleRegistryError,
    get_rule,
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
    def test_real_registry_discovers_at_least_fifteen_fragments(self) -> None:
        rules = load_all_rules()
        # Step 4 ships 15 fragments extracted from linear-write.md.
        assert len(rules) >= 15, f"expected >=15 fragments, found {len(rules)}: {[r.id for r in rules]}"

    def test_every_real_fragment_parses_cleanly(self) -> None:
        rules = load_all_rules()
        for rule in rules:
            assert rule.id.startswith("R-")
            assert rule.slot in reg.VALID_SLOTS
            assert rule.body, f"{rule.id}: empty body"
            assert rule.description, f"{rule.id}: empty description"

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

    def test_real_registry_depends_on_targets_all_exist(self) -> None:
        """Every depends_on entry must point to a real fragment."""
        rules = load_all_rules()
        ids = {r.id for r in rules}
        for rule in rules:
            for dep in rule.depends_on:
                assert dep in ids, f"{rule.id} depends_on {dep!r} which is not present"

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

    def test_load_all_rules_returns_alphabetical_order(self, tmp_path: Path) -> None:
        _write_fragment(tmp_path, "R-ZULU")
        _write_fragment(tmp_path, "R-ALPHA")
        _write_fragment(tmp_path, "R-MIKE")
        rules = load_all_rules(tmp_path)
        assert [r.id for r in rules] == ["R-ALPHA", "R-MIKE", "R-ZULU"]

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

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        (tmp_path / "R-INCOMPLETE.md").write_text(
            "---\nid: R-INCOMPLETE\nslot: shared.contract\n---\nbody\n",
            encoding="utf-8",
        )
        with pytest.raises(MalformedFragmentError, match="applies_to"):
            load_all_rules(tmp_path)

    def test_invalid_slot_raises(self, tmp_path: Path) -> None:
        _write_fragment(tmp_path, "R-BADSLOT", slot="invalid.slot")
        with pytest.raises(MalformedFragmentError, match="invalid slot"):
            load_all_rules(tmp_path)

    def test_filename_must_match_id(self, tmp_path: Path) -> None:
        path = tmp_path / "R-WRONGSTEM.md"
        path.write_text(
            "---\nid: R-OTHER\napplies_to:\n  levels: [all]\n  tracks: [all]\n  activity_profiles: [all]\nslot: shared.contract\n---\nbody\n",
            encoding="utf-8",
        )
        with pytest.raises(MalformedFragmentError, match="filename stem"):
            load_all_rules(tmp_path)

    def test_id_must_start_with_R_dash(self, tmp_path: Path) -> None:
        path = tmp_path / "R-BADID.md"
        path.write_text(
            "---\nid: '#R-WITH-HASH'\napplies_to:\n  levels: [all]\n  tracks: [all]\n  activity_profiles: [all]\nslot: shared.contract\n---\nbody\n",
            encoding="utf-8",
        )
        with pytest.raises(MalformedFragmentError, match="must be a string starting with 'R-'"):
            load_all_rules(tmp_path)

    def test_unknown_level_in_applies_to_raises(self, tmp_path: Path) -> None:
        _write_fragment(tmp_path, "R-BADLEVEL", levels=["c3"])
        with pytest.raises(MalformedFragmentError, match="unknown values"):
            load_all_rules(tmp_path)

    def test_empty_levels_list_raises(self, tmp_path: Path) -> None:
        # Write directly: _write_fragment treats `levels=[]` as "use default"
        # via `levels or ["all"]`, which would defeat the test.
        (tmp_path / "R-NOLEVELS.md").write_text(
            "---\nid: R-NOLEVELS\napplies_to:\n  levels: []\n  tracks: [all]\n  activity_profiles: [all]\nslot: shared.contract\n---\nbody\n",
            encoding="utf-8",
        )
        with pytest.raises(MalformedFragmentError, match="non-empty list"):
            load_all_rules(tmp_path)

    def test_duplicate_ids_raise(self, tmp_path: Path) -> None:
        """Two fragments declaring the same id (across separate files) is malformed."""
        _write_fragment(tmp_path, "R-A")
        # Second file with same id but different filename — bypass _write_fragment.
        path = tmp_path / "R-A-COPY.md"
        path.write_text(
            "---\nid: R-A\napplies_to:\n  levels: [all]\n  tracks: [all]\n  activity_profiles: [all]\nslot: shared.contract\n---\nbody\n",
            encoding="utf-8",
        )
        # First the filename-stem check should trip for the COPY file.
        with pytest.raises(MalformedFragmentError):
            load_all_rules(tmp_path)

    def test_directory_must_exist(self, tmp_path: Path) -> None:
        missing = tmp_path / "no-such-dir"
        with pytest.raises(RuleRegistryError, match="does not exist"):
            load_all_rules(missing)

    def test_telemetry_id_prepends_hash(self, tmp_path: Path) -> None:
        _write_fragment(tmp_path, "R-XYZ")
        rule = load_all_rules(tmp_path)[0]
        assert rule.telemetry_id == "#R-XYZ"


# ---------------------------------------------------------------------------
# Filtering by level / track / activity_profile / slot
# ---------------------------------------------------------------------------


class TestFiltering:
    def test_levels_all_matches_every_level(self, tmp_path: Path) -> None:
        _write_fragment(tmp_path, "R-UNIVERSAL", levels=["all"])
        for level in ("a1", "a2", "b1", "b2", "c1", "c2"):
            rules = load_applicable_rules(level, "core", "all", directory=tmp_path)
            assert [r.id for r in rules] == ["R-UNIVERSAL"], level

    def test_level_filter_excludes_non_matching_levels(self, tmp_path: Path) -> None:
        _write_fragment(tmp_path, "R-A1ONLY", levels=["a1"])
        _write_fragment(tmp_path, "R-B1ONLY", levels=["b1"])
        a1_rules = load_applicable_rules("a1", "core", "all", directory=tmp_path)
        assert [r.id for r in a1_rules] == ["R-A1ONLY"]
        b1_rules = load_applicable_rules("b1", "core", "all", directory=tmp_path)
        assert [r.id for r in b1_rules] == ["R-B1ONLY"]
        c1_rules = load_applicable_rules("c1", "core", "all", directory=tmp_path)
        assert c1_rules == []

    def test_audience_language_a1_does_not_apply_at_b1(self) -> None:
        """Locks in the answer to design question #1 from the dispatch brief."""
        # Use the real registry directly to verify the level-conditional rules
        # are predicated as designed.
        rules = load_applicable_rules("b1", "core", "all")
        ids = {r.id for r in rules}
        assert "R-AUDIENCE-LANGUAGE-A1" not in ids
        assert "R-SINGLE-VOICE-A1" not in ids
        assert "R-GRAMMAR-TERMS-A1" not in ids
        assert "R-PROSE-FLOOR-A1" not in ids
        # And the universal rules ARE present.
        assert "R-VESUM-ALL-WORDS" in ids
        assert "R-CITE-HONEST" in ids

    def test_track_filter(self, tmp_path: Path) -> None:
        _write_fragment(tmp_path, "R-COREONLY", tracks=["core"])
        _write_fragment(tmp_path, "R-SEMONLY", tracks=["seminar"])
        _write_fragment(tmp_path, "R-BOTH", tracks=["all"])
        core_rules = load_applicable_rules("a1", "core", "all", directory=tmp_path)
        assert {r.id for r in core_rules} == {"R-COREONLY", "R-BOTH"}
        sem_rules = load_applicable_rules("a1", "seminar", "all", directory=tmp_path)
        assert {r.id for r in sem_rules} == {"R-SEMONLY", "R-BOTH"}

    def test_activity_profile_filter(self, tmp_path: Path) -> None:
        _write_fragment(tmp_path, "R-DEFAULT", activity_profiles=["default"])
        _write_fragment(tmp_path, "R-CHECKPOINT", activity_profiles=["checkpoint"])
        _write_fragment(tmp_path, "R-ANY", activity_profiles=["all"])
        default_rules = load_applicable_rules("a1", "core", "default", directory=tmp_path)
        assert {r.id for r in default_rules} == {"R-DEFAULT", "R-ANY"}

    def test_slot_filter(self, tmp_path: Path) -> None:
        _write_fragment(tmp_path, "R-PRE", slot="writer.preamble")
        _write_fragment(tmp_path, "R-BODY", slot="writer.body")
        _write_fragment(tmp_path, "R-RUBRIC", slot="reviewer.rubric")
        _write_fragment(tmp_path, "R-SHARED", slot="shared.contract")
        # No slot filter — get everything.
        all_rules = load_applicable_rules("a1", "core", "all", directory=tmp_path)
        assert len(all_rules) == 4
        # Slot filter narrows.
        body_only = load_applicable_rules("a1", "core", "all", slot="writer.body", directory=tmp_path)
        assert [r.id for r in body_only] == ["R-BODY"]
        shared_only = load_applicable_rules(
            "a1", "core", "all", slot="shared.contract", directory=tmp_path
        )
        assert [r.id for r in shared_only] == ["R-SHARED"]


# ---------------------------------------------------------------------------
# Topological dependency ordering
# ---------------------------------------------------------------------------


class TestTopologicalSort:
    def test_simple_chain_orders_correctly(self, tmp_path: Path) -> None:
        # A depends on B; B should come first.
        _write_fragment(tmp_path, "R-A", depends_on=["R-B"])
        _write_fragment(tmp_path, "R-B")
        ordered = load_applicable_rules("a1", "core", "all", directory=tmp_path)
        assert [r.id for r in ordered] == ["R-B", "R-A"]

    def test_diamond_dependency(self, tmp_path: Path) -> None:
        # D -> {B, C} -> A. A first, then B and C (alphabetical tie), then D.
        _write_fragment(tmp_path, "R-A")
        _write_fragment(tmp_path, "R-B", depends_on=["R-A"])
        _write_fragment(tmp_path, "R-C", depends_on=["R-A"])
        _write_fragment(tmp_path, "R-D", depends_on=["R-B", "R-C"])
        ordered = load_applicable_rules("a1", "core", "all", directory=tmp_path)
        assert [r.id for r in ordered] == ["R-A", "R-B", "R-C", "R-D"]

    def test_circular_dependency_raises(self, tmp_path: Path) -> None:
        # R-X -> R-Y -> R-X (cycle)
        _write_fragment(tmp_path, "R-X", depends_on=["R-Y"])
        _write_fragment(tmp_path, "R-Y", depends_on=["R-X"])
        with pytest.raises(CircularDependencyError, match="circular"):
            load_applicable_rules("a1", "core", "all", directory=tmp_path)

    def test_self_dependency_raises(self, tmp_path: Path) -> None:
        # A rule that depends_on itself is a 1-node cycle.
        _write_fragment(tmp_path, "R-SELF", depends_on=["R-SELF"])
        with pytest.raises(CircularDependencyError):
            load_applicable_rules("a1", "core", "all", directory=tmp_path)

    def test_missing_dependency_raises(self, tmp_path: Path) -> None:
        _write_fragment(tmp_path, "R-NEEDS", depends_on=["R-GHOST"])
        with pytest.raises(MissingDependencyError, match="R-GHOST"):
            load_applicable_rules("a1", "core", "all", directory=tmp_path)

    def test_filtered_out_parent_does_not_break_ordering(self, tmp_path: Path) -> None:
        """If a dep is filtered out by predicates, the dependent still appears,
        and the ordering for the filtered subset is consistent.

        This matters because composition slots may legitimately filter a parent
        rule out — e.g. R-ACTIVITY-COMPOSITION (shared.contract) depends on
        R-RENDERER-CHARTER (writer.preamble). Querying shared.contract alone
        must still return R-ACTIVITY-COMPOSITION (parent is reachable in the
        full registry, just not in the filtered slice).
        """
        _write_fragment(tmp_path, "R-PARENT", slot="writer.preamble")
        _write_fragment(
            tmp_path, "R-CHILD", slot="shared.contract", depends_on=["R-PARENT"]
        )
        shared = load_applicable_rules(
            "a1", "core", "all", slot="shared.contract", directory=tmp_path
        )
        assert [r.id for r in shared] == ["R-CHILD"]

    def test_missing_dep_still_raises_when_dep_is_filtered_out(
        self, tmp_path: Path
    ) -> None:
        """If a depends_on id does NOT exist in the full registry at all, it must
        still raise — even when the rule passes the slot filter. The check is
        against the *full* registry, not just the filtered subset.
        """
        _write_fragment(
            tmp_path, "R-CHILD", slot="shared.contract", depends_on=["R-GHOST"]
        )
        with pytest.raises(MissingDependencyError, match="R-GHOST"):
            load_applicable_rules(
                "a1", "core", "all", slot="shared.contract", directory=tmp_path
            )


# ---------------------------------------------------------------------------
# get_rule + Rule dataclass behavior
# ---------------------------------------------------------------------------


class TestGetRule:
    def test_get_rule_returns_matching_fragment(self) -> None:
        rule = get_rule("R-VESUM-ALL-WORDS")
        assert rule.id == "R-VESUM-ALL-WORDS"
        assert rule.slot == "shared.contract"
        assert "VESUM" in rule.body

    def test_get_rule_missing_raises_key_error(self) -> None:
        with pytest.raises(KeyError, match="R-DOES-NOT-EXIST"):
            get_rule("R-DOES-NOT-EXIST")

    def test_rule_dataclass_is_frozen(self) -> None:
        import dataclasses

        rule = get_rule("R-VESUM-ALL-WORDS")
        with pytest.raises(dataclasses.FrozenInstanceError):
            rule.id = "R-MUTATED"  # type: ignore[misc]
