"""Every obligation the coverage manifest lists is stated in the rules core at its anchor."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "agents_extensions/shared/rules/core-manifest.yaml"
UNIT_ID = re.compile(r"^[A-Z][a-z]?\d{2}$")
ANCHOR_COMMENT = re.compile(r"<!-- ([a-z0-9]+(?:-[a-z0-9]+)*): ([A-Z][a-z]?\d{2}) -->")


def _manifest() -> dict:
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def _sections() -> list[str]:
    return list(_manifest()["files"])


def _anchor_comments(section: str) -> list[tuple[str, str]]:
    path = ROOT / _manifest()["files"][section]
    return ANCHOR_COMMENT.findall(path.read_text(encoding="utf-8"))


def test_manifest_covers_the_denominator_once() -> None:
    manifest = _manifest()
    units = [unit for section in _sections() for unit in manifest[section]]
    duplicated = sorted(unit for unit, count in Counter(units).items() if count > 1)
    malformed = sorted(unit for unit in units if not UNIT_ID.match(unit))
    assert not duplicated, f"units mapped more than once: {duplicated}"
    assert not malformed, f"malformed unit ids: {malformed}"
    assert len(units) == manifest["denominator"], (
        f"manifest maps {len(units)} units; denominator is {manifest['denominator']}"
    )


@pytest.mark.parametrize("section", ["core", "content_addendum"])
def test_every_listed_anchor_exists_once(section: str) -> None:
    anchors = Counter(anchor for anchor, _lead in _anchor_comments(section))
    listed = set(_manifest()[section].values())
    missing = sorted(anchor for anchor in listed if anchor not in anchors)
    repeated = sorted(anchor for anchor, count in anchors.items() if count > 1)
    assert not missing, f"{section}: manifest anchors absent from the file: {missing}"
    assert not repeated, f"{section}: anchors stated more than once: {repeated}"


@pytest.mark.parametrize("section", ["core", "content_addendum"])
def test_every_anchor_cites_a_unit_the_manifest_maps_to_it(section: str) -> None:
    mapping = _manifest()[section]
    mismatched = sorted(
        f"{anchor} cites {lead}, manifest maps it to {mapping.get(lead)}"
        for anchor, lead in _anchor_comments(section)
        if mapping.get(lead) != anchor
    )
    assert not mismatched, f"{section}: inline citations disagree with the manifest: {mismatched}"
