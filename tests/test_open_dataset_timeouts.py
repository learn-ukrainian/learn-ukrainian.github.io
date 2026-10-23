"""Timeout and failure-shape tests for open-dataset GitHub Release calls (#7213 slice 15)."""

from __future__ import annotations

import subprocess
from urllib.request import Request

import pytest

from scripts.open_dataset import hydrate as hydrate_module
from scripts.open_dataset import publish as publish_module

pytestmark = pytest.mark.usefixtures("github_command_boundary")


def test_ensure_release_view_timeout_is_publish_error_and_never_creates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        calls.append({"cmd": cmd, **kwargs})
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(publish_module.subprocess, "run", fake_run)

    with pytest.raises(publish_module.OpenDatasetPublishError, match="Timed out"):
        publish_module.ensure_release("tag", "owner/repo")

    assert len(calls) == 1
    assert calls[0]["timeout"] == publish_module.GH_RELEASE_VIEW_TIMEOUT_SECONDS
    assert calls[0]["cmd"][:3] == ["gh", "release", "view"]


def test_download_with_gh_timeout_maps_to_none_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []
    pointer = {"release_tag": "atlas-open-dataset"}

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        calls.append({"cmd": cmd, **kwargs})
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(hydrate_module.subprocess, "run", fake_run)

    assert hydrate_module._download_with_gh(pointer, repo="owner/repo") is None

    assert len(calls) == 1
    assert calls[0]["timeout"] == hydrate_module.GH_RELEASE_DOWNLOAD_TIMEOUT_SECONDS
    assert calls[0]["cmd"][:3] == ["gh", "release", "download"]


def test_download_with_gh_timeout_falls_back_to_asset_url(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeResponse:
        def __init__(self, payload: bytes) -> None:
            self._payload = payload

        def __enter__(self) -> _FakeResponse:
            return self

        def __exit__(self, *_args: object) -> bool:
            return False

        def read(self) -> bytes:
            return self._payload

    gh_calls: list[dict[str, object]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        gh_calls.append({"cmd": cmd, **kwargs})
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(hydrate_module.subprocess, "run", fake_run)
    url_calls: list[Request] = []

    def fake_urlopen(request: Request, timeout: float) -> _FakeResponse:
        url_calls.append(request)
        assert timeout > 0
        return _FakeResponse(b"url bytes")

    monkeypatch.setattr(hydrate_module.github_client, "http_open", fake_urlopen)

    pointer = {"release_tag": "atlas-open-dataset", "asset_url": "https://example.com/asset.gz"}
    assert hydrate_module.download_asset(pointer, repo="owner/repo") == b"url bytes"

    assert len(gh_calls) == 1
    assert len(url_calls) == 1


def test_download_with_gh_success_returns_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        calls.append({"cmd": cmd, **kwargs})
        return subprocess.CompletedProcess(cmd, 0, stdout=b"gzip bytes", stderr=b"")

    monkeypatch.setattr(hydrate_module.subprocess, "run", fake_run)

    pointer = {"release_tag": "atlas-open-dataset"}
    assert hydrate_module._download_with_gh(pointer, repo="owner/repo") == b"gzip bytes"
    assert calls[0]["timeout"] == hydrate_module.GH_RELEASE_DOWNLOAD_TIMEOUT_SECONDS


@pytest.fixture(autouse=True)
def _synthetic_publishing_rules(synthetic_opsec, publisher_transport, monkeypatch):
    """Use synthetic private tooling and an explicit destination for send spies."""
    monkeypatch.setenv("GH_REPO", "unit/public")
