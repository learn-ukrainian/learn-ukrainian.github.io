"""Direct coverage for tests/_host_path_guard.py in both configuration modes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.opsec import needles as nd
from tests import _host_path_guard as guard

# Fictional deployment home outside the generic roots; only its shape matters.
DEPLOY_HOME = "/".join(("", "srv", "fixture-deploy"))
DEPLOYED = nd.Needles(run_users=("fixture-deploy",), home_dirs=(DEPLOY_HOME,))
GENERIC = nd.Needles()
MAC_HOME = "/".join(("", "Users", "fixture-user"))


def test_generic_mode_finds_home_directories_by_line() -> None:
    text = f"intro\n{guard.FIXTURE_HOME}/data\nok\nfile://{MAC_HOME}/x\n"
    assert guard.host_path_lines(text, needles=GENERIC) == [2, 4]


@pytest.mark.parametrize(
    "text",
    [
        "https://example.org/home/page",
        "/".join(("", "Users", "...")),
        f"{DEPLOY_HOME}/data",
        "no paths at all",
    ],
)
def test_generic_mode_ignores_non_home_text(text: str) -> None:
    assert guard.host_path_lines(text, needles=GENERIC) == []


def test_deployment_mode_adds_the_configured_home() -> None:
    text = f"{DEPLOY_HOME}/data\n{guard.FIXTURE_HOME}\n{DEPLOY_HOME}-other\n"
    assert guard.host_path_lines(text, needles=DEPLOYED) == [1, 2]
    assert guard.host_path_lines(text, needles=GENERIC) == [2]


def test_checkout_lines_cover_both_layouts_and_filter_by_root() -> None:
    text = "\n".join(
        (
            f"{guard.FIXTURE_HOME}/learn-ukrainian/scripts",
            f"{MAC_HOME}/projects/learn-ukrainian",
            f"{guard.FIXTURE_HOME}/elsewhere",
            f"{DEPLOY_HOME}/learn-ukrainian",
        )
    )
    assert guard.checkout_path_lines(text, needles=GENERIC) == [1, 2]
    assert guard.checkout_path_lines(text, needles=DEPLOYED) == [1, 2, 4]
    assert guard.checkout_path_lines(text, home_root="/Users", needles=GENERIC) == [2]


@pytest.mark.parametrize(
    ("helper", "text"),
    [
        (guard.assert_no_host_paths, f"a\n{DEPLOY_HOME}/x"),
        (guard.assert_no_checkout_paths, f"a\n{DEPLOY_HOME}/learn-ukrainian"),
    ],
)
def test_failures_report_lines_without_matched_text(helper, text: str) -> None:
    with pytest.raises(AssertionError) as caught:
        helper(text, "sample.py", needles=DEPLOYED)
    message = str(caught.value)
    assert message.startswith("sample.py:")
    assert "line(s) 2" in message
    assert "fixture" not in message and "srv" not in message


def test_default_mode_reads_the_deployment_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "n.json"
    path.write_text(json.dumps({"schema_version": 1, "run_users": [], "home_dirs": [DEPLOY_HOME]}))
    monkeypatch.setenv(nd.ENV_NEEDLES_FILE, str(path))
    for cached in (guard._deployment_needles, guard.host_path_re, guard.checkout_path_re):
        cached.cache_clear()
    try:
        assert guard.host_path_lines(f"{DEPLOY_HOME}/x") == [1]
        monkeypatch.setenv(nd.ENV_NEEDLES_FILE, "")
        for cached in (guard._deployment_needles, guard.host_path_re, guard.checkout_path_re):
            cached.cache_clear()
        assert guard.host_path_lines(f"{DEPLOY_HOME}/x") == []
    finally:
        for cached in (guard._deployment_needles, guard.host_path_re, guard.checkout_path_re):
            cached.cache_clear()


def test_template_lines_cover_named_and_placeholder_homes() -> None:
    text = "\n".join(
        (
            f"{guard.FIXTURE_HOME}/<checkout>",
            "/".join(("", "home", "<user>", "repo")),
            f"{MAC_HOME}/<project>",
            f"{DEPLOY_HOME}/<checkout>",
            f"{guard.FIXTURE_HOME}/plain",
            "<home>/<checkout>",
        )
    )
    assert guard.host_template_lines(text, needles=GENERIC) == [1, 2, 3]
    assert guard.host_template_lines(text, needles=DEPLOYED) == [1, 2, 3, 4]


def test_host_facts_report_all_kinds_and_deduplicate_lines() -> None:
    aliases = sorted(guard.HOST_ALIASES)
    ip = ".".join(("192", "0", "2", "10"))
    addon = "/".join(("", "opt", aliases[0], "bin"))
    text = f"intro\n{' '.join(aliases)}\n{ip} {ip}\n\tHostName fixture.example\n{addon}\n{aliases[0]}"
    assert guard.host_fact_lines(text) == {
        "host alias": [2, 5, 6],
        "non-loopback IPv4": [3],
        "SSH HostName": [4],
        "add-on install tree": [5],
    }


@pytest.mark.parametrize("octets", [("10", "0", "0", "1"), ("0", "0", "0", "0"), ("203", "0", "113", "5")])
def test_host_facts_reject_valid_non_loopback_ipv4(octets: tuple[str, ...]) -> None:
    ip = ".".join(octets)
    assert guard.host_fact_lines(f"first\nhttps://{ip}:8000/path\n{ip}.") == {"non-loopback IPv4": [2, 3]}


@pytest.mark.parametrize(
    "octets",
    [
        ("127", "0", "0", "1"),
        ("127", "255", "255", "255"),
        ("999", "0", "0", "1"),
        ("10", "000", "0", "1"),
        ("1", "2", "3", "4", "5"),
    ],
)
def test_host_facts_ignore_loopback_and_invalid_ipv4(octets: tuple[str, ...]) -> None:
    text = ".".join(octets)
    assert guard.host_fact_lines(text) == {}
    guard.assert_no_host_facts(text)


def test_host_facts_ignore_clean_text_and_hostname_mentions() -> None:
    text = "relative/path\n# HostName placeholder\nexplain HostName here\nHostNameSuffix value\n/opt/fixture-addon/bin"
    assert guard.host_fact_lines(text) == {}
    guard.assert_no_host_facts(text)
