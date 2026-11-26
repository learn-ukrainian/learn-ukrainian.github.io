"""The committed consumer profile uses the packaged fleet catalog.

Defect class: the active machinery slug is missing from the canonical catalog field.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from shutil import copyfile

import pytest
from lu_machinery.common.profile import load_profile
from lu_machinery.orchestration.fleet_repos import default_config_path, load_fleet_repos


def test_profile_fleet_repos_loads(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[1] / ".lu-machinery"
    profile_dir = tmp_path / ".lu-machinery"
    profile_dir.mkdir()
    copyfile(source / "profile.v1.json", profile_dir / "profile.v1.json")
    monkeypatch.delenv("LU_PROFILE_PATH", raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_STATE_ROOT", raising=False)
    monkeypatch.setenv("LU_STATE_ROOT", str(tmp_path))

    profile = load_profile()
    assert profile is not None
    assert "fleet_repos" not in profile.config
    packaged_catalog = files("lu_machinery").joinpath("config", "fleet_repos.yaml")
    assert default_config_path().resolve() == Path(str(packaged_catalog)).resolve()
    repos = load_fleet_repos()
    assert repos["public"].sources_server
    assert repos["machinery"].github == "agentic-machinery/machinery"
    assert repos["machinery"].alternate_github == "learn-ukrainian/machinery"
