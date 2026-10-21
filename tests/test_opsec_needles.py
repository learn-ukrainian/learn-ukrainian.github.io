"""Deployment needles for the leak scanners: loading, fallback and patterns."""

from __future__ import annotations

import importlib
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
HOME_VALIDATORS = [
    ("v4_differential_soviet_miner", "PRIVATE_HOST_RE", "validate_no_private_host_paths"),
    ("v4_production_shards_assembly", "PRIVATE_HOST_RE", "assert_no_private_host_paths"),
    ("v4_verify_trajectory_claims", "PRIVATE_HOST_RE", "validate_no_private_host_paths"),
    ("v4_pilot_canary_evaluation", "_PRIVATE_HOME_RE", "validate_no_private_host_paths"),
]
ALL_VALIDATORS = [*HOME_VALIDATORS, ("v4_mine_stem_controls", "SSH_OR_HOST_RE", "assert_no_private_host_paths")]
SEPARATORS = ["\n", "\r", "\r\n", "\t", "\b", "\f", "\x1b", "\\n", "\\r", "\\t", "\\x1b", "\\u001b"]


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
    assert nd.load_needles(environ={"XDG_CONFIG_HOME": str(tmp_path)}) == nd.Needles()


def test_missing_explicit_override_fails_closed_and_is_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "missing.json"
    monkeypatch.setenv(nd.ENV_NEEDLES_FILE, str(target))
    for environ in (None, {nd.ENV_NEEDLES_FILE: str(target)}):
        with pytest.raises(nd.NeedlesError, match="configured override is absent") as caught:
            nd.load_needles(environ=environ)
        assert str(tmp_path) not in str(caught.value)


@pytest.mark.parametrize("base", [None, "", "relative/config"])
def test_invalid_xdg_config_home_uses_the_home_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, base: str | None,
) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    environ = {} if base is None else {"XDG_CONFIG_HOME": base}
    assert nd.needles_file(environ) == tmp_path / ".config" / "learn-ukrainian" / nd.NEEDLES_FILE_NAME


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
        {"schema_version": 1, "run_users": [FIXTURE_USER + "\n"], "home_dirs": []},
        {"schema_version": 1, "run_users": [], "home_dirs": ["relative/home"]},
        {"schema_version": 1, "run_users": [], "home_dirs": ["/trailing/"]},
        {"schema_version": 1, "homedirs": [FIXTURE_HOME]},
        {"schema_version": 1, "run_user": [FIXTURE_USER]},
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


@pytest.mark.parametrize("key", ["schema_version", "home_dirs", "run_users", FIXTURE_HOME])
def test_duplicate_keys_fail_closed_and_are_redacted(tmp_path: Path, key: str) -> None:
    target = tmp_path / "n.json"
    rendered_key = json.dumps(key)
    target.write_text(
        '{"schema_version":1,' + rendered_key + ':' + json.dumps([FIXTURE_HOME]) + ',' + rendered_key + ':[]}',
        encoding="utf-8",
    )
    with pytest.raises(nd.NeedlesError, match="duplicate object key") as caught:
        nd.load_needles(target)
    assert str(tmp_path) not in str(caught.value)
    assert FIXTURE_HOME not in str(caught.value)


def test_unknown_keys_fail_closed_without_echoing_them(tmp_path: Path) -> None:
    target = _write(tmp_path / "n.json", {"schema_version": 1, FIXTURE_HOME: [FIXTURE_USER]})
    with pytest.raises(nd.NeedlesError, match="unknown object key") as caught:
        nd.load_needles(target)
    assert str(tmp_path) not in str(caught.value)
    assert FIXTURE_HOME not in str(caught.value)
    assert FIXTURE_USER not in str(caught.value)


def test_dangling_link_at_the_location_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "n.json"
    target.symlink_to(tmp_path / "gone.json")
    with pytest.raises(nd.NeedlesError):
        nd.load_needles(target)


def test_errors_do_not_repeat_the_location_or_contents(tmp_path: Path) -> None:
    broken = tmp_path / "n.json"
    _write(broken, {"schema_version": 1, "run_users": ["Bad User"], "home_dirs": [FIXTURE_HOME]})
    malformed = tmp_path / "malformed.json"
    malformed.write_text(FIXTURE_HOME, encoding="utf-8")
    invalid_utf8 = tmp_path / "invalid-utf8.json"
    invalid_utf8.write_bytes(b"\xff" + FIXTURE_USER.encode())
    dangling = tmp_path / "dangling.json"
    dangling.symlink_to(tmp_path / "missing.json")
    directory = tmp_path / "d.json"
    directory.mkdir()
    for target in (broken, malformed, invalid_utf8, dangling, directory):
        with pytest.raises(nd.NeedlesError) as caught:
            nd.load_needles(target)
        message = str(caught.value)
        assert str(tmp_path) not in message
        assert "fixture" not in message and "Bad User" not in message


@pytest.mark.parametrize("operation", ["lstat", "read_text"])
def test_io_errors_are_redacted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str) -> None:
    target = _write(tmp_path / "n.json", {"schema_version": 1})

    def deny(*args: object, **kwargs: object) -> None:
        raise PermissionError(f"{target}: {FIXTURE_USER} {FIXTURE_HOME}")

    monkeypatch.setattr(Path, operation, deny)
    with pytest.raises(nd.NeedlesError) as caught:
        nd.load_needles(target)
    assert str(tmp_path) not in str(caught.value)
    assert FIXTURE_USER not in str(caught.value)
    assert FIXTURE_HOME not in str(caught.value)


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


@pytest.mark.parametrize("suffix", ["", "/file", ".", "...", ".\n", '"', ":", ";", ",", ")", "\n"])
@pytest.mark.parametrize(("module_name", "attribute", "function_name"), ALL_VALIDATORS)
def test_validators_reject_configured_homes_before_punctuation(
    monkeypatch: pytest.MonkeyPatch, suffix: str,
    module_name: str, attribute: str, function_name: str,
) -> None:
    needles = nd.Needles(home_dirs=(FIXTURE_HOME,))
    pattern = re.compile(nd.home_dir_pattern(needles))
    assert pattern.search(FIXTURE_HOME + suffix)
    module = importlib.import_module(f"scripts.projects.open_model_data.{module_name}")
    monkeypatch.setattr(module, attribute, ssh_or_host_re(needles) if attribute == "SSH_OR_HOST_RE" else pattern)
    leaked = f"ran in {FIXTURE_HOME}{suffix}"
    for payload in (leaked, [leaked], {"field": leaked}, {leaked: "value"}):
        with pytest.raises(ValueError) as caught:
            getattr(module, function_name)(payload)
        assert FIXTURE_HOME not in str(caught.value)


@pytest.mark.parametrize("suffix", ["x", "_other", "-other", ".bak", ".1", ".hidden/file"])
def test_configured_home_does_not_match_sibling_directories(suffix: str) -> None:
    pattern = re.compile(nd.home_dir_pattern(nd.Needles(home_dirs=(FIXTURE_HOME,))))
    assert not pattern.search(FIXTURE_HOME + suffix)


@pytest.mark.parametrize("character", ['"', "\\", "\x00", "\x7f"])
@pytest.mark.parametrize(("module_name", "attribute", "function_name"), ALL_VALIDATORS)
def test_configured_homes_with_json_escaping_are_detected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, character: str,
    module_name: str, attribute: str, function_name: str,
) -> None:
    home = FIXTURE_HOME + character + "suffix"
    config = _write(tmp_path / "n.json", {"schema_version": 1, "home_dirs": [home]})
    needles = nd.load_needles(config)
    pattern = re.compile(nd.home_dir_pattern(needles))
    assert pattern.search(home)
    assert pattern.search(json.dumps(home, ensure_ascii=False))
    module = importlib.import_module(f"scripts.projects.open_model_data.{module_name}")
    monkeypatch.setattr(module, attribute, ssh_or_host_re(needles) if attribute == "SSH_OR_HOST_RE" else pattern)
    for payload in (home, {"field": home}, {home: "value"}):
        with pytest.raises(ValueError) as caught:
            getattr(module, function_name)(payload)
        assert "fixture-runner-home" not in str(caught.value)


@pytest.mark.parametrize("home", [FIXTURE_HOME, OTHER_HOME])
@pytest.mark.parametrize("prefix", ["prefix", "https://example.org", "relative/path", "word-", "word.", "\\z"])
def test_home_boundaries_reject_arbitrary_prefixes(home: str, prefix: str) -> None:
    pattern = re.compile(nd.home_dir_pattern(nd.Needles(home_dirs=(FIXTURE_HOME,))))
    assert not pattern.search(f"{prefix}{home}/data")


@pytest.mark.parametrize("home", [FIXTURE_HOME, OTHER_HOME])
@pytest.mark.parametrize("separator", ["", " ", '"', "file://", *SEPARATORS])
def test_home_boundaries_match_raw_and_escaped_separators(home: str, separator: str) -> None:
    pattern = re.compile(nd.home_dir_pattern(nd.Needles(home_dirs=(FIXTURE_HOME,))))
    assert pattern.search(f"{separator}{home}/data")


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
    ALL_VALIDATORS,
)
def test_violation_messages_do_not_repeat_configured_values(
    monkeypatch: pytest.MonkeyPatch, module_name: str, attribute: str, function_name: str
) -> None:
    module = importlib.import_module(f"scripts.projects.open_model_data.{module_name}")
    needles = nd.Needles(home_dirs=(FIXTURE_HOME,))
    configured = ssh_or_host_re(needles) if attribute == "SSH_OR_HOST_RE" else re.compile(nd.home_dir_pattern(needles))
    monkeypatch.setattr(module, attribute, configured)
    for leaked in (f"{FIXTURE_HOME}/data", f"{OTHER_HOME}/data"):
        with pytest.raises(ValueError) as caught:
            getattr(module, function_name)({leaked: {"field": leaked}})
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
@pytest.mark.parametrize("separator", SEPARATORS)
def test_validators_reject_structured_samples(module_name: str, function_name: str, separator: str) -> None:
    module = importlib.import_module(f"scripts.projects.open_model_data.{module_name}")
    validate = getattr(module, function_name)
    for payload in (
        {"field": f"first line{separator}{OTHER_HOME}/data"},
        [f"first line{separator}{OTHER_HOME}/data"],
        f"first line{separator}{OTHER_HOME}/data",
    ):
        with pytest.raises(ValueError):
            validate(payload)


@pytest.mark.parametrize(("module_name", "attribute", "function_name"), ALL_VALIDATORS)
@pytest.mark.parametrize("home", [FIXTURE_HOME, OTHER_HOME])
@pytest.mark.parametrize("separator", ["", *SEPARATORS])
def test_validators_reject_configured_multiline_homes(
    monkeypatch: pytest.MonkeyPatch, module_name: str, attribute: str, function_name: str,
    home: str, separator: str,
) -> None:
    module = importlib.import_module(f"scripts.projects.open_model_data.{module_name}")
    needles = nd.Needles(home_dirs=(FIXTURE_HOME,))
    configured = ssh_or_host_re(needles) if attribute == "SSH_OR_HOST_RE" else re.compile(nd.home_dir_pattern(needles))
    monkeypatch.setattr(module, attribute, configured)
    leaked = f"{separator}{home}/data" if not separator else f"first line{separator}{home}/data"
    for payload in (leaked, [leaked], {"field": leaked}, {leaked: "value"}):
        with pytest.raises(ValueError) as caught:
            getattr(module, function_name)(payload)
        assert home not in str(caught.value)


@pytest.mark.parametrize("leaked", [FIXTURE_HOME, f"Host {FIXTURE_USER}", f"{FIXTURE_USER}@host"])
def test_stem_validator_rejects_keys_and_redacts_nested_diagnostics(
    monkeypatch: pytest.MonkeyPatch, leaked: str,
) -> None:
    module = importlib.import_module("scripts.projects.open_model_data.v4_mine_stem_controls")
    monkeypatch.setattr(module, "SSH_OR_HOST_RE", ssh_or_host_re(nd.Needles(
        run_users=(FIXTURE_USER,), home_dirs=(FIXTURE_HOME,),
    )))
    for payload in ({leaked: "value"}, {leaked: [leaked]}, {"safe": [{"field": leaked}]}):
        with pytest.raises(ValueError) as caught:
            module.assert_no_private_host_paths(payload)
        assert leaked not in str(caught.value)
        assert FIXTURE_USER not in str(caught.value)
