"""Timeout and failure-shape tests for practice-deck GitHub Release calls."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.practice_deck import publish as publish_module


def test_release_subprocesses_use_operation_timeouts_and_preserve_clobber(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upload_path = tmp_path / publish_module.ASSET_NAME
    upload_path.write_bytes(b"gzip bytes")
    calls: list[dict[str, object]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        calls.append({"cmd": cmd, **kwargs})
        if cmd[:3] == ["gh", "release", "view"]:
            if "--json" in cmd:
                return subprocess.CompletedProcess(cmd, 0, stdout='{"assets":[]}', stderr="")
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")
        if cmd[:3] == ["gh", "release", "download"]:
            return subprocess.CompletedProcess(cmd, 0, stdout=b"gzip bytes", stderr=b"")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(publish_module.subprocess, "run", fake_run)

    publish_module.ensure_release("tag", "owner/repo")
    assert publish_module._release_asset_names(release_tag="tag", repo="owner/repo") == set()
    monkeypatch.setattr(publish_module, "ensure_release", lambda *_args, **_kwargs: None)
    publish_module.upload_release_asset(
        upload_path,
        release_tag="tag",
        repo="owner/repo",
        clobber=True,
    )
    assert publish_module._download_release_asset("asset.gz", release_tag="tag", repo="owner/repo") == b"gzip bytes"

    assert [call["timeout"] for call in calls] == [
        publish_module.GH_RELEASE_VIEW_TIMEOUT_SECONDS,
        publish_module.GH_RELEASE_CREATE_TIMEOUT_SECONDS,
        publish_module.GH_RELEASE_VIEW_TIMEOUT_SECONDS,
        publish_module.GH_RELEASE_ASSET_TIMEOUT_SECONDS,
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

    with pytest.raises(publish_module.PracticeDeckPublishError, match="Timed out"):
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
    upload_path = tmp_path / publish_module.ASSET_NAME
    upload_path.write_bytes(b"gzip bytes")
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(publish_module, "ensure_release", lambda *_args, **_kwargs: None)

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        calls.append({"cmd": cmd, **kwargs})
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(publish_module.subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        publish_module.upload_release_asset(upload_path, clobber=True)

    assert exc_info.value.returncode == 124
    assert calls[0]["timeout"] == publish_module.GH_RELEASE_ASSET_TIMEOUT_SECONDS
    assert "--clobber" in calls[0]["cmd"]


def test_release_asset_names_timeout_maps_to_called_process_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        calls.append({"cmd": cmd, **kwargs})
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(publish_module.subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        publish_module._release_asset_names()

    assert exc_info.value.returncode == 124
    assert calls[0]["timeout"] == publish_module.GH_RELEASE_VIEW_TIMEOUT_SECONDS


def test_download_release_asset_timeout_maps_to_called_process_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        calls.append({"cmd": cmd, **kwargs})
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(publish_module.subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        publish_module._download_release_asset("asset.gz")

    assert exc_info.value.returncode == 124
    assert calls[0]["timeout"] == publish_module.GH_RELEASE_ASSET_TIMEOUT_SECONDS
