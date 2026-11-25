"""The committed consumer profile uses the packaged fleet catalog.

Defect class: a profile entry hides a packaged catalog again.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from lu_machinery.common.profile import load_profile
from lu_machinery.orchestration.fleet_repos import load_fleet_repos


def test_profile_fleet_repos_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("LU_PROFILE_PATH", str(repo_root / ".lu-machinery" / "profile.v1.json"))

    profile = load_profile()
    assert profile is not None
    assert profile.config == {}
    assert load_fleet_repos()["public"].sources_server
