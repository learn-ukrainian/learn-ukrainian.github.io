"""Deployment needles for the leak scanners: loading, fallback and patterns."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.opsec import needles as nd
from scripts.projects.open_model_data.v4_mine_stem_controls import ssh_or_host_re

# Fictional deployment values; only their shape matters.
FIXTURE_USER = "fixture-runner"
FIXTURE_HOME = "/".join(("", "srv", "fixture-runner-home"))
OTHER_HOME = "/".join(("", "home", "someone"))


def _write(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_location_honours_the_override_then_the_config_home(tmp_path: Path) -> None:
    assert nd.needles_file({nd.ENV_NEEDLES_FILE: str(tmp_path / "n.json")}) == tmp_path / "n.json"
    assert nd.needles_file({nd.ENV_NEEDLES_FILE: ""}) is None
    assert nd.needles_file({"XDG_CONFIG_HOME": str(tmp_path)}) == (tmp_path / "learn-ukrainian" / nd.NEEDLES_FILE_NAME)


def test_absent_file_yields_no_deployment_needles(tmp_path: Path) -> None:
    assert nd.load_needles(tmp_path / "missing.json") == nd.Needles()
    assert nd.load_needles(environ={nd.ENV_NEEDLES_FILE: ""}) == nd.Needles()


def test_valid_file_loads_users_and_homes(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "n.json",
        {"schema_version": 1, "run_users": [FIXTURE_USER], "home_dirs": [FIXTURE_HOME]},
    )
    assert nd.load_needles(path) == nd.Needles(run_users=(FIXTURE_USER,), home_dirs=(FIXTURE_HOME,))
    assert nd.load_needles(environ={nd.ENV_NEEDLES_FILE: str(path)}).run_users == (FIXTURE_USER,)


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        [],
        {"schema_version": 2, "run_users": [], "home_dirs": []},
        {"schema_version": 1, "run_users": "fixture-runner", "home_dirs": []},
        {"schema_version": 1, "run_users": ["Not A User"], "home_dirs": []},
        {"schema_version": 1, "run_users": [], "home_dirs": ["relative/home"]},
        {"schema_version": 1, "run_users": [], "home_dirs": ["/trailing/"]},
    ],
)
def test_malformed_file_fails_closed(tmp_path: Path, payload: object) -> None:
    path = tmp_path / "n.json"
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        _write(path, payload)
    with pytest.raises(nd.NeedlesError):
        nd.load_needles(path)


def test_generic_home_pattern_is_the_fallback_and_skips_url_paths() -> None:
    generic = re.compile(nd.home_dir_pattern(nd.Needles()))
    assert generic.search(f'"{OTHER_HOME}/repo"')
    assert generic.search(f"file://{OTHER_HOME}/x")
    assert generic.search("/".join(("", "Users", "someone", "x")))
    assert not generic.search("https://example.org/home/page")
    assert not generic.search("/".join(("", "Users", "...")))
    assert not generic.search(FIXTURE_HOME)


def test_deployment_homes_extend_the_generic_pattern() -> None:
    pattern = re.compile(nd.home_dir_pattern(nd.Needles(home_dirs=(FIXTURE_HOME,))))
    assert pattern.search(f"{FIXTURE_HOME}/data")
    assert pattern.search(f" {OTHER_HOME}")
    assert not pattern.search(f"{FIXTURE_HOME}-other")


def test_run_user_aliases_only_come_from_the_deployment_file() -> None:
    assert nd.run_user_alias_pattern(nd.Needles()) is None
    without = ssh_or_host_re(nd.Needles())
    with_users = ssh_or_host_re(nd.Needles(run_users=(FIXTURE_USER,)))
    for text in (f"Host {FIXTURE_USER}", f"ssh {FIXTURE_USER}@box"):
        assert with_users.search(text)
        assert not without.search(text)
    for text in ("user@bastion:repo.git", f"{OTHER_HOME}/x"):
        assert without.search(text) and with_users.search(text)
