"""Structural coverage of the rules core: every frozen inventory unit maps to one anchor that exists.

This proves placement, not meaning. Whether each rule preserves its units' clauses is checked by
review against the private obligation inventory, not by this test.
"""

from __future__ import annotations

import copy
import hashlib
import re
from collections import Counter
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "agents_extensions/shared/rules"
MANIFEST = RULES / "core-manifest.yaml"
EXPECTED_IDS = RULES / "core-expected-ids.txt"
# The frozen denominator: the 345 units (344 inventory units plus Q18, #9618) whose destination is P0-P9, an unconditional
# invariant or the content addendum. Changing the list must be deliberate and reviewed.
EXPECTED_IDS_SHA256 = "299e4e1ccd6a5ce433f8467ed28c106a323a88a47ac836a8204457d71199be22"
SECTIONS = ("core", "content_addendum")
UNIT_ID = re.compile(r"^[A-Z][a-z]?\d{2}$")
ANCHOR_COMMENT = re.compile(r"<!-- ([a-z0-9]+(?:-[a-z0-9]+)*): ([A-Z][a-z]?\d{2}) -->")


def _manifest() -> dict:
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def _expected_ids() -> list[str]:
    return EXPECTED_IDS.read_text(encoding="utf-8").splitlines()


def _anchor_comments(manifest: dict, section: str) -> list[tuple[str, str]]:
    return ANCHOR_COMMENT.findall((ROOT / manifest["files"][section]).read_text(encoding="utf-8"))


def _denominator_faults(manifest: dict, expected: list[str]) -> list[str]:
    mapped = [unit for section in SECTIONS for unit in manifest[section]]
    faults = [f"mapped in more than one section: {unit}" for unit, n in Counter(mapped).items() if n > 1]
    faults += [f"expected but not mapped: {unit}" for unit in sorted(set(expected) - set(mapped))]
    faults += [f"mapped but not expected: {unit}" for unit in sorted(set(mapped) - set(expected))]
    return faults


def _anchor_faults(manifest: dict, section: str) -> list[str]:
    comments = _anchor_comments(manifest, section)
    counts = Counter(anchor for anchor, _lead in comments)
    mapping = manifest[section]
    listed = set(mapping.values())
    faults = [f"{section}: anchor absent from the file: {a}" for a in sorted(listed - set(counts))]
    faults += [f"{section}: anchor stated {n} times: {a}" for a, n in sorted(counts.items()) if n > 1]
    faults += [f"{section}: anchor not in the manifest: {a}" for a in sorted(set(counts) - listed)]
    faults += [
        f"{section}: {anchor} cites {lead}, which the manifest maps to {mapping.get(lead)}"
        for anchor, lead in comments
        if mapping.get(lead) != anchor
    ]
    return faults


def test_expected_ids_are_the_frozen_denominator() -> None:
    raw = EXPECTED_IDS.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_IDS_SHA256, "core-expected-ids.txt changed"
    expected = _expected_ids()
    assert len(expected) == len(set(expected)), "core-expected-ids.txt repeats an id"
    assert all(UNIT_ID.match(unit) for unit in expected), "core-expected-ids.txt holds a malformed id"


def test_manifest_maps_exactly_the_expected_ids() -> None:
    faults = _denominator_faults(_manifest(), _expected_ids())
    assert not faults, "\n".join(faults)


@pytest.mark.parametrize("section", SECTIONS)
def test_every_mapped_anchor_is_stated_once(section: str) -> None:
    faults = _anchor_faults(_manifest(), section)
    assert not faults, "\n".join(faults)


def test_a_substituted_unit_is_caught() -> None:
    manifest = copy.deepcopy(_manifest())
    manifest["core"]["O99"] = manifest["core"].pop("O30")
    faults = _denominator_faults(manifest, _expected_ids())
    assert faults == ["expected but not mapped: O30", "mapped but not expected: O99"]


def test_a_missing_anchor_is_caught() -> None:
    manifest = copy.deepcopy(_manifest())
    manifest["core"]["O30"] = "r2-absent"
    faults = _anchor_faults(manifest, "core")
    assert "core: anchor absent from the file: r2-absent" in faults
