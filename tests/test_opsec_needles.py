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
        {"schema_version": True, "run_users": [], "home_dirs": []},
        {"schema_version": 1.0, "run_users": [], "home_dirs": []},
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


def test_directory_at_the_location_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "n.json"
    target.mkdir()
    with pytest.raises(nd.NeedlesError):
        nd.load_needles(target)
    with pytest.raises(nd.NeedlesError):
        nd.load_needles(environ={nd.ENV_NEEDLES_FILE: str(target)})
    (tmp_path / "learn-ukrainian" / nd.NEEDLES_FILE_NAME).mkdir(parents=True)
    with pytest.raises(nd.NeedlesError):
        nd.load_needles(environ={"XDG_CONFIG_HOME": str(tmp_path)})


def test_dangling_link_at_the_location_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "n.json"
    target.symlink_to(tmp_path / "gone.json")
    with pytest.raises(nd.NeedlesError):
        nd.load_needles(target)


def test_errors_do_not_repeat_the_location_or_contents(tmp_path: Path) -> None:
    broken = tmp_path / "n.json"
    broken.write_text(json.dumps({"schema_version": 1, "run_users": ["Bad User"], "home_dirs": [FIXTURE_HOME]}))
    directory = tmp_path / "d.json"
    directory.mkdir()
    for target in (broken, directory):
        with pytest.raises(nd.NeedlesError) as caught:
            nd.load_needles(target)
        message = str(caught.value)
        assert str(tmp_path) not in message
        assert "fixture" not in message and "Bad User" not in message


def test_generic_home_pattern_is_the_fallback_and_skips_url_paths() -> None:
    generic = re.compile(nd.home_dir_pattern(nd.Needles()))
    assert generic.search(f'"{OTHER_HOME}/repo"')
    assert generic.search(f"file://{OTHER_HOME}/x")
    assert generic.search("/".join(("", "Users", "someone", "x")))
    assert not generic.search("https://example.org/home/page")
    assert not generic.search("/".join(("", "Users", "...")))
    assert not generic.search(FIXTURE_HOME)


@pytest.mark.parametrize("escape", ["\\n", "\\r", "\\t", "\\x1b", "\\u001b"])
def test_generic_home_pattern_extra_samples(escape: str) -> None:
    generic = re.compile(nd.home_dir_pattern(nd.Needles()))
    assert generic.search(f"first line{escape}{OTHER_HOME}/x")
    assert not generic.search("https://example.org/home/page")


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


@pytest.mark.parametrize(
    ("module_name", "attribute", "function_name"),
    [
        ("v4_differential_soviet_miner", "PRIVATE_HOST_RE", "validate_no_private_host_paths"),
        ("v4_production_shards_assembly", "PRIVATE_HOST_RE", "assert_no_private_host_paths"),
        ("v4_verify_trajectory_claims", "PRIVATE_HOST_RE", "validate_no_private_host_paths"),
        ("v4_pilot_canary_evaluation", "_PRIVATE_HOME_RE", "validate_no_private_host_paths"),
    ],
)
def test_violation_messages_do_not_repeat_configured_values(
    monkeypatch: pytest.MonkeyPatch, module_name: str, attribute: str, function_name: str
) -> None:
    module = pytest.importorskip(f"scripts.projects.open_model_data.{module_name}")
    configured = re.compile(nd.home_dir_pattern(nd.Needles(home_dirs=(FIXTURE_HOME,))))
    monkeypatch.setattr(module, attribute, configured)
    for leaked in (f"{FIXTURE_HOME}/data", f"{OTHER_HOME}/data"):
        with pytest.raises(ValueError) as caught:
            getattr(module, function_name)({"field": leaked})
        message = str(caught.value)
        assert "fixture" not in message
        assert "someone" not in message


@pytest.mark.parametrize(
    ("module_name", "function_name"),
    [
        ("v4_differential_soviet_miner", "validate_no_private_host_paths"),
        ("v4_production_shards_assembly", "assert_no_private_host_paths"),
        ("v4_verify_trajectory_claims", "validate_no_private_host_paths"),
        ("v4_pilot_canary_evaluation", "validate_no_private_host_paths"),
        ("v4_mine_stem_controls", "assert_no_private_host_paths"),
    ],
)
@pytest.mark.parametrize("separator", ["\n", "\r\n", "\t", "\x1b"])
def test_validators_reject_structured_samples(module_name: str, function_name: str, separator: str) -> None:
    module = pytest.importorskip(f"scripts.projects.open_model_data.{module_name}")
    validate = getattr(module, function_name)
    for payload in (
        {"field": f"first line{separator}{OTHER_HOME}/data"},
        [f"first line{separator}{OTHER_HOME}/data"],
        f"first line{separator}{OTHER_HOME}/data",
    ):
        with pytest.raises(ValueError):
            validate(payload)
