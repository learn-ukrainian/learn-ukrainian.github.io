"""Every lane resolves selectors through the launcher's single source of truth."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.session_canary import codex_lane, gemini_lane, glm_lane, grok_lane

ROOT = Path(__file__).resolve().parents[1]
LANES = (codex_lane, gemini_lane, glm_lane, grok_lane)


def _selectors() -> list[str]:
    keys = yaml.safe_load((ROOT / "scripts/config/issue_streams.yaml").read_text())["streams"]
    aliases = {
        line.split("\t")[0]
        for line in (ROOT / "scripts/config/launcher_stream_aliases.tsv").read_text().splitlines()
        if line and not line.startswith("#")
    }
    return sorted(set(keys) | {f"infra.{key}" for key in keys} | aliases)


def _shell_stream(selector: str) -> str:
    return subprocess.check_output(
        ["bash", "-c", 'source "$1" && launcher_selector_stream "$2"',
         "parity", str(ROOT / "scripts/lib/handoff_identity.sh"), selector],
        text=True, timeout=2,
    ).strip()


@pytest.mark.parametrize("selector", _selectors())
def test_all_selectors_match_shell(selector: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SESSION_STREAM_ID", raising=False)
    expected = _shell_stream(selector)
    for lane in LANES:
        assert lane._stream_id(argparse.Namespace(epic=selector, stream=None)) == expected
    assert grok_lane.EPIC_STREAM_DEFAULTS[selector] == expected


@pytest.mark.parametrize("lane", LANES, ids=lambda lane: lane.__name__.split(".")[-1])
@pytest.mark.parametrize("explicit,environment,expected", [
    ("epic:6321", "epic:7994", "epic:6321"),
    (None, "epic:7994", "epic:7994"),
    (None, "", "epic:6321"),
])
def test_stream_precedence(lane, explicit, environment, expected, monkeypatch) -> None:
    monkeypatch.setenv("SESSION_STREAM_ID", environment)
    assert lane._stream_id(argparse.Namespace(epic="open-model-data", stream=explicit)) == expected


@pytest.mark.parametrize("lane", LANES, ids=lambda lane: lane.__name__.split(".")[-1])
@pytest.mark.parametrize("selector", ["unknown-lane", "eval-harness", "infra.a1-upgrade", "$(exit 0)"])
def test_unknown_and_retired_selectors_raise_typed_error(lane, selector, monkeypatch) -> None:
    monkeypatch.delenv("SESSION_STREAM_ID", raising=False)
    with pytest.raises(grok_lane.StreamResolutionError, match="unresolved-stream-selector") as error:
        lane._stream_id(argparse.Namespace(epic=selector, stream=None))
    assert error.value.reason == "unresolved-stream-selector"


@pytest.mark.parametrize("lane", LANES, ids=lambda lane: lane.__name__.split(".")[-1])
def test_cli_reports_typed_selector_error(lane, monkeypatch, capsys) -> None:
    monkeypatch.delenv("SESSION_STREAM_ID", raising=False)
    assert lane.main(["hydrate", "--epic", "unknown-lane"]) == 2
    output = capsys.readouterr()
    assert "unresolved-stream-selector" in output.err
    assert "Traceback" not in output.err
    assert "epic:unknown-lane" not in output.out


def test_resolver_reads_registry_changes_and_new_keys(tmp_path, monkeypatch) -> None:
    registry = tmp_path / "streams.yaml"
    registry.write_text("streams:\n  open-model-data:\n    epics: [12345]\n  new-lane:\n    epics:\n      - 23456\n")
    monkeypatch.setenv("HANDOFF_ISSUE_STREAMS_YAML", str(registry))
    monkeypatch.delenv("SESSION_STREAM_ID", raising=False)
    for selector in ("open-model-data", "infra.open-model-data", "new-lane", "infra.new-lane"):
        assert grok_lane.resolve_stream_id(selector) == _shell_stream(selector)


@pytest.mark.parametrize("failure", [OSError("unavailable"), subprocess.TimeoutExpired("bash", 1)])
def test_unavailable_resolver_raises_typed_error(failure, monkeypatch) -> None:
    monkeypatch.delenv("SESSION_STREAM_ID", raising=False)

    def unavailable(*args, **kwargs):
        raise failure

    monkeypatch.setattr(grok_lane.subprocess, "run", unavailable)
    with pytest.raises(grok_lane.StreamResolutionError):
        grok_lane.resolve_stream_id("open-model-data")
