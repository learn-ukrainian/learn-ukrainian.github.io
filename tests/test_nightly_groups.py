"""Nightly test groups join the slow lane, except tests CI must prove ran."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import conftest

ROOT = Path(conftest.__file__).resolve().parents[1]


class Item:
    def __init__(self, rel: str, markers: tuple[str, ...] = ()) -> None:
        self.path = ROOT / rel
        self.names = set(markers)

    def get_closest_marker(self, name: str):
        return name if name in self.names else None

    def add_marker(self, marker) -> None:
        self.names.add(marker.name)


@pytest.mark.parametrize(
    ("rel", "markers", "slow"),
    [
        ("tests/projects/x/test_a.py", (), True),
        ("tests/audit/test_b.py", (), True),
        ("tests/test_open_model_c.py", (), True),
        ("tests/projects/x/test_d.py", ("needs_artifact",), False),
        ("tests/api/test_e.py", (), False),
        ("tests/test_opsec_f.py", (), False),
    ],
)
def test_nightly_groups_are_marked_slow(rel: str, markers: tuple[str, ...], slow: bool) -> None:
    item = Item(rel, markers)
    conftest._mark_nightly_groups([item])
    assert ("slow" in item.names) is slow
