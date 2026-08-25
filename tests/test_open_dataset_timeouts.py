"""Timeout and failure-shape tests for open-dataset GitHub Release calls (#7213 slice 15)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.request import Request

import pytest

from scripts.open_dataset import hydrate as hydrate_module
from scripts.open_dataset import publish as publish_module


def test_release_subprocesses_use_operation_timeouts_and_preserve_clobber(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upload_path = tmp_path / "lexicon-open-dataset.json.gz"
    upload_path.write_bytes(b"gzip bytes")
    calls: list[dict[str, object]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        calls.append({"cmd": cmd, **kwargs})
        if cmd[:3] == ["gh", "release", "view"]:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(publish_module.subprocess, "run", fake_run)

    publish_module.ensure_release("tag", "owner/repo")
    monkeypatch.setattr(publish_module, "ensure_release", lambda *_args, **_kwargs: None)
    publish_module.upload_release_asset(upload_path, release_tag="tag", repo="owner/repo")

    assert [call["timeout"] for call in calls] == [
        publish_module.GH_RELEASE_VIEW_TIMEOUT_SECONDS,
        publish_module.GH_RELEASE_CREATE_TIMEOUT_SECONDS,
        publish_module.GH_RELEASE_ASSET_TIMEOUT_SECONDS,
    ]
    upload_call = next(call for call in calls if call["cmd"][:3] == ["gh", "release", "upload"])
    assert "--clobber" in upload_call["cmd"]


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


def test_ensure_release_create_timeout_maps_to_called_process_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        calls.append({"cmd": cmd, **kwargs})
        if cmd[:3] == ["gh", "release", "view"]:
            return subprocess.CompletedProcess(cmd, 1, stdout=None, stderr=None)
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(publish_module.subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        publish_module.ensure_release("tag", "owner/repo")

    assert exc_info.value.returncode == 124
    assert [call["timeout"] for call in calls] == [
        publish_module.GH_RELEASE_VIEW_TIMEOUT_SECONDS,
        publish_module.GH_RELEASE_CREATE_TIMEOUT_SECONDS,
    ]
    assert calls[1]["cmd"][:3] == ["gh", "release", "create"]


def test_upload_release_asset_timeout_maps_to_called_process_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upload_path = tmp_path / "lexicon-open-dataset.json.gz"
    upload_path.write_bytes(b"gzip bytes")
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(publish_module, "ensure_release", lambda *_args, **_kwargs: None)

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        calls.append({"cmd": cmd, **kwargs})
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(publish_module.subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        publish_module.upload_release_asset(upload_path, release_tag="tag", repo="owner/repo")

    assert exc_info.value.returncode == 124
    assert calls[0]["timeout"] == publish_module.GH_RELEASE_ASSET_TIMEOUT_SECONDS
    assert "--clobber" in calls[0]["cmd"]


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

    monkeypatch.setattr(hydrate_module, "urlopen", fake_urlopen)

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
