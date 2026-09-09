"""Tests for scripts/fleet_repos.py (#672 P2.1)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.fleet_repos import (
    FleetRepoError,
    default_repo_key,
    load_fleet_repos,
    resolve_fleet_repo,
)


def test_load_canonical_fleet_repos_catalog():
    repos = load_fleet_repos()
    assert set(repos) == {"public", "infra-private", "hramatka"}
    assert default_repo_key(repos) == "public"
    assert repos["hramatka"].github == "learn-ukrainian/hramatka"
    assert repos["infra-private"].local_name == "learn-ukrainian-infra-private"


def test_resolve_public_uses_primary_root(tmp_path: Path):
    primary = tmp_path / "learn-ukrainian"
    primary.mkdir()
    (primary / ".git").mkdir()
    repo, checkout = resolve_fleet_repo("public", primary_root=primary)
    assert repo.key == "public"
    assert checkout == primary.resolve()


def test_resolve_hramatka_sibling(tmp_path: Path):
    primary = tmp_path / "learn-ukrainian"
    sibling = tmp_path / "hramatka"
    primary.mkdir()
    sibling.mkdir()
    (primary / ".git").mkdir()
    (sibling / ".git").mkdir()
    repo, checkout = resolve_fleet_repo("hramatka", primary_root=primary)
    assert repo.github.endswith("/hramatka")
    assert checkout == sibling.resolve()


def test_resolve_unknown_key_fails(tmp_path: Path):
    primary = tmp_path / "learn-ukrainian"
    primary.mkdir()
    (primary / ".git").mkdir()
    with pytest.raises(FleetRepoError, match="unknown --repo"):
        resolve_fleet_repo("not-a-repo", primary_root=primary)


def test_resolve_missing_sibling_fails_closed(tmp_path: Path):
    primary = tmp_path / "learn-ukrainian"
    primary.mkdir()
    (primary / ".git").mkdir()
    with pytest.raises(FleetRepoError, match="expects sibling checkout"):
        resolve_fleet_repo("hramatka", primary_root=primary)


def test_catalog_requires_exactly_one_default(tmp_path: Path):
    path = tmp_path / "fleet_repos.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "repos": {
                    "a": {"github": "o/a", "local_name": "a", "default": True},
                    "b": {"github": "o/b", "local_name": "b", "default": True},
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(FleetRepoError, match="exactly one default"):
        load_fleet_repos(path)
