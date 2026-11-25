"""Consumer profile fleet catalog loads under installed machinery.

Defect class: a Learn Ukrainian ``fleet_repos`` row omits a product file the
loader requires (``sources_server`` or ``admission_policy``), or sets one to
a path other than the canonical repo-relative file.
"""

from __future__ import annotations

from pathlib import Path

from lu_machinery.orchestration.fleet_repos import load_fleet_repos


def test_profile_fleet_repos_loads() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    catalog = (repo_root / ".lu-machinery" / "fleet_repos.yaml").resolve()
    repos = load_fleet_repos(catalog)
    public = repos["public"]
    assert public.sources_server
