from pathlib import Path

import pytest

from scripts.build.prev_next import get_prev_next_links
from scripts.manifest_utils import Module


def test_prev_next_links(monkeypatch):
    def mock_get_modules(level):
        return [
            Module(slug="m19", title="", level="a1", track="core", local_num=19, global_num=19),
            Module(slug="m20", title="", level="a1", track="core", local_num=20, global_num=20),
            Module(slug="m21", title="", level="a1", track="core", local_num=21, global_num=21),
            Module(slug="m22", title="", level="a1", track="core", local_num=22, global_num=22),
        ]

    monkeypatch.setattr("scripts.build.prev_next.get_modules_for_level", mock_get_modules)

    def exists_mock(self):
        # m19 exists, m20 exists, m21 does not exist, m22 exists
        return self.name in ("m19.mdx", "m20.mdx", "m22.mdx")

    monkeypatch.setattr(Path, "exists", exists_mock)

    # both exist (for m20, prev is m19 which exists. next is m21 which DOES NOT exist. Wait, let's make m21 exist for this test)
    def exists_all(self): return True
    monkeypatch.setattr(Path, "exists", exists_all)
    prev_val, next_val = get_prev_next_links("a1", 20)
    assert prev_val == "m19"
    assert next_val == "m21"

    # prev only (m19 exists, m21 does not)
    def exists_prev_only(self): return self.name == "m19.mdx"
    monkeypatch.setattr(Path, "exists", exists_prev_only)
    prev_val, next_val = get_prev_next_links("a1", 20)
    assert prev_val == "m19"
    assert next_val is False

    # next only (m19 does not exist, m21 exists)
    def exists_next_only(self): return self.name == "m21.mdx"
    monkeypatch.setattr(Path, "exists", exists_next_only)
    prev_val, next_val = get_prev_next_links("a1", 20)
    assert prev_val is False
    assert next_val == "m21"

    # neither exists
    def exists_neither(self): return False
    monkeypatch.setattr(Path, "exists", exists_neither)
    prev_val, next_val = get_prev_next_links("a1", 20)
    assert prev_val is False
    assert next_val is False

    # out of bounds / not in curriculum
    with pytest.raises(ValueError):
        get_prev_next_links("a1", 99)
