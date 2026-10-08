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
# Documentation-range and loopback addresses, assembled like the other fixtures.
DOC_ADDRESS = ".".join(("198", "51", "100", "7"))
LOOPBACK_ADDRESS = ".".join(("127", "0", "0", "1"))


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


def test_generic_mode_extra_samples() -> None:
    assert guard.host_path_lines(f'"first\\n{guard.FIXTURE_HOME}/x"', needles=GENERIC) == [1]


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


def test_clean_text_passes_both_helpers() -> None:
    guard.assert_no_host_paths("relative/path only", needles=DEPLOYED)
    guard.assert_no_checkout_paths("relative/learn-ukrainian", needles=DEPLOYED)


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


def test_template_failure_reports_lines_without_matched_text() -> None:
    with pytest.raises(AssertionError) as caught:
        guard.assert_no_host_templates(f"x\n{DEPLOY_HOME}/<checkout>", "doc.md", needles=DEPLOYED)
    assert "line(s) 2" in str(caught.value)
    assert "fixture" not in str(caught.value)


def test_host_fact_lines_report_each_kind_by_line() -> None:
    alias = guard.HOST_ALIASES[0]
    text = "\n".join(
        (
            f"ssh {alias}",
            f"addr {DOC_ADDRESS}",
            f"loop {LOOPBACK_ADDRESS}",
            "/".join(("", "opt", "fixture-app")),
            "HostName example",
            "clean line",
        )
    )
    assert guard.host_fact_lines(text) == {
        guard.HOST_ALIAS: [1],
        guard.IPV4_LITERAL: [2],
        guard.INSTALL_TREE: [4],
        guard.HOSTNAME_LINE: [5],
    }
    assert guard.host_fact_lines(text, kinds=(guard.INSTALL_TREE,)) == {guard.INSTALL_TREE: [4]}


@pytest.mark.parametrize("escape", ["\\n", "\\t", "\\x1b", "\\u001b"])
def test_host_facts_match_after_an_escape_sequence(escape: str) -> None:
    text = f'"a{escape}{DOC_ADDRESS} b{escape}' + "/".join(("", "opt", "fixture-app")) + '"'
    assert guard.host_fact_lines(text, kinds=(guard.IPV4_LITERAL, guard.INSTALL_TREE)) == {
        guard.IPV4_LITERAL: [1],
        guard.INSTALL_TREE: [1],
    }


def test_host_fact_failure_names_kinds_and_lines_only() -> None:
    alias = guard.HOST_ALIASES[0]
    with pytest.raises(AssertionError) as caught:
        guard.assert_no_host_facts(f"ok\n{alias} at {DOC_ADDRESS}", "unit.service")
    message = str(caught.value)
    assert message.startswith("unit.service:")
    assert "line(s) 2" in message
    assert alias not in message and DOC_ADDRESS not in message
