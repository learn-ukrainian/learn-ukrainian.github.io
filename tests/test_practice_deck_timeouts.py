"""Timeout and failure-shape tests for practice-deck GitHub Release calls."""

from __future__ import annotations

import subprocess

import pytest

from scripts.practice_deck import publish as publish_module

pytestmark = pytest.mark.usefixtures("github_command_boundary")


def test_ensure_release_view_timeout_is_publish_error_and_never_creates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        calls.append({"cmd": cmd, **kwargs})
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(publish_module.subprocess, "run", fake_run)

    with pytest.raises(publish_module.PracticeDeckPublishError, match="Timed out"):
        publish_module.ensure_release("tag", "owner/repo")

    assert len(calls) == 1
    assert calls[0]["timeout"] == publish_module.GH_RELEASE_VIEW_TIMEOUT_SECONDS
    assert calls[0]["cmd"][:3] == ["gh", "release", "view"]


@pytest.fixture(autouse=True)
def _synthetic_publishing_rules(synthetic_opsec, publisher_transport, monkeypatch):
    """Use synthetic private tooling and an explicit destination for send spies."""
    monkeypatch.setenv("GH_REPO", "unit/public")
