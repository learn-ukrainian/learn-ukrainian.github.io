"""Offline tests for scripts/typesafe/client.py (#8192)."""

from __future__ import annotations

import io
import json
import traceback
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from scripts.typesafe.client import TypeSafeError, load_typesafe_api_key, system_one

SECRET = "super-secret-key-value"
SENTINEL = "SENTINEL-CREDENTIAL-8192"


def _isolate_home(monkeypatch, tmp_path: Path) -> Path:
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    secrets = tmp_path / ".secrets"
    secrets.mkdir()
    return secrets


def test_env_beats_both_secret_files(monkeypatch, tmp_path):
    secrets = _isolate_home(monkeypatch, tmp_path)
    (secrets / "typesafe-ai.key").write_text("from-file\n", encoding="utf-8")
    (secrets / "typsafe-ai.key").write_text("from-legacy\n", encoding="utf-8")
    monkeypatch.setenv("TYPESAFE_API_KEY", "from-env")
    assert load_typesafe_api_key() == "from-env"


def test_canonical_file_beats_legacy_misspelling(monkeypatch, tmp_path):
    secrets = _isolate_home(monkeypatch, tmp_path)
    (secrets / "typesafe-ai.key").write_text("from-file\r\n", encoding="utf-8")
    (secrets / "typsafe-ai.key").write_text("from-legacy\n", encoding="utf-8")
    assert load_typesafe_api_key() == "from-file"


def test_legacy_file_used_when_canonical_missing(monkeypatch, tmp_path):
    secrets = _isolate_home(monkeypatch, tmp_path)
    (secrets / "typsafe-ai.key").write_text("from-legacy\n", encoding="utf-8")
    assert load_typesafe_api_key() == "from-legacy"


def test_empty_canonical_file_falls_through_to_legacy(monkeypatch, tmp_path):
    secrets = _isolate_home(monkeypatch, tmp_path)
    (secrets / "typesafe-ai.key").write_text("\n", encoding="utf-8")
    (secrets / "typsafe-ai.key").write_text("from-legacy\n", encoding="utf-8")
    assert load_typesafe_api_key() == "from-legacy"


def test_missing_key_error_names_neither_the_secret_nor_the_expanded_path(monkeypatch, tmp_path):
    _isolate_home(monkeypatch, tmp_path)
    with pytest.raises(TypeSafeError) as caught:
        load_typesafe_api_key()
    message = str(caught.value)
    assert caught.value.category == "no_key"
    assert caught.value.status is None
    assert SECRET not in message
    assert str(tmp_path) not in message
    assert "typesafe-ai.key" not in message
    assert "~/.secrets" not in message
    assert message == "no_key"


class _Body:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_system_one_returns_parsed_json(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", SECRET)
    seen: dict = {}

    def _open(request, timeout=None):
        seen["timeout"] = timeout
        seen["auth"] = request.get_header("Authorization")
        seen["body"] = json.loads(request.data.decode("utf-8"))
        return _Body(b'{"model":"jev-1","answers":{}}')

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    parsed = system_one({"ping": 1}, {"ok": {"type": "noul", "instructions": "Is this a check?"}}, timeout=12)
    assert parsed == {"model": "jev-1", "answers": {}}
    assert seen["timeout"] == 12
    assert seen["auth"] == f"Bearer {SECRET}"
    assert seen["body"]["model"] == "jev-latest"
    assert seen["body"]["state"] == {"ping": 1}


@pytest.mark.parametrize(
    "raiser",
    [
        urllib.error.HTTPError("https://api.typesafe.ai/v1/systemone", 500, "nope", hdrs=None, fp=None),
        urllib.error.URLError(TimeoutError("slow")),
        TimeoutError("slow"),
    ],
)
def test_http_and_timeout_raise_typesafe_error_without_the_key(monkeypatch, raiser):
    monkeypatch.setenv("TYPESAFE_API_KEY", SECRET)

    def _open(request, timeout=None):
        raise raiser

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    with pytest.raises(TypeSafeError) as caught:
        system_one("state", {})
    assert SECRET not in str(caught.value)
    assert "Bearer" not in str(caught.value)


def test_malformed_json_raises_typesafe_error(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", SECRET)
    monkeypatch.setattr(urllib.request, "urlopen", lambda request, timeout=None: _Body(b"not-json"))
    with pytest.raises(TypeSafeError) as caught:
        system_one("state", {})
    assert caught.value.category == "malformed_json"
    assert str(caught.value) == "malformed_json"
    assert SECRET not in str(caught.value)


def test_non_object_json_raises_typesafe_error(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", SECRET)
    monkeypatch.setattr(urllib.request, "urlopen", lambda request, timeout=None: _Body(b"[1]"))
    with pytest.raises(TypeSafeError):
        system_one("state", {})


def _assert_key_not_in_error(exc: BaseException, key: str) -> None:
    assert key not in str(exc)
    assert key not in repr(exc.__cause__)
    assert key not in repr(exc.__context__)


def test_key_with_embedded_newline_does_not_leak(monkeypatch):
    key = "super-secret-key-value\ninjected"
    monkeypatch.setenv("TYPESAFE_API_KEY", key)
    calls = {"n": 0}

    def _open(request, timeout=None):
        calls["n"] += 1
        raise ValueError(f"Invalid header value: {key}")

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    with pytest.raises(TypeSafeError) as caught:
        system_one("state", {})
    _assert_key_not_in_error(caught.value, key)
    assert calls["n"] == 0

    monkeypatch.setattr("scripts.typesafe.client.load_typesafe_api_key", lambda: key)
    with pytest.raises(TypeSafeError) as wrapped:
        system_one("state", {})
    _assert_key_not_in_error(wrapped.value, key)
    assert calls["n"] == 1


def test_invalid_utf8_key_file_falls_through_to_the_next_location(monkeypatch, tmp_path):
    secrets = _isolate_home(monkeypatch, tmp_path)
    (secrets / "typesafe-ai.key").write_bytes(b"\xff\xfe not utf-8")
    (secrets / "typsafe-ai.key").write_text("from-legacy\n", encoding="utf-8")
    assert load_typesafe_api_key() == "from-legacy"


def _assert_sentinel_absent(exc: BaseException, sentinel: str) -> None:
    rendered = "".join(traceback.format_exception(exc))
    assert sentinel not in str(exc)
    assert sentinel not in repr(exc.__cause__)
    assert sentinel not in repr(exc.__context__)
    assert sentinel not in rendered
    assert exc.__cause__ is None
    assert exc.__context__ is None


def test_http_401_does_not_chain_reason_or_body(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", SECRET)
    body = io.BytesIO(f"body {SENTINEL}".encode())
    error = urllib.error.HTTPError(
        f"https://api.typesafe.ai/v1/systemone?api_key={SENTINEL}",
        401,
        f"Unauthorized {SENTINEL}",
        hdrs=None,
        fp=body,
    )

    def _open(request, timeout=None):
        raise error

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    with pytest.raises(TypeSafeError) as caught:
        system_one("state", {})
    exc = caught.value
    _assert_sentinel_absent(exc, SENTINEL)
    assert exc.category == "http_error"
    assert exc.status == 401
    assert str(exc) == "http_error 401"


def test_timeout_urlerror_does_not_chain_the_reason(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", SECRET)
    raisers = (
        (urllib.error.URLError(TimeoutError(f"timed out {SENTINEL}")), "timeout"),
        (urllib.error.URLError(f"network {SENTINEL}"), "network_error"),
    )
    for raiser, category in raisers:

        def _open(request, timeout=None, raiser=raiser):
            raise raiser

        monkeypatch.setattr(urllib.request, "urlopen", _open)
        with pytest.raises(TypeSafeError) as caught:
            system_one("state", {})
        exc = caught.value
        _assert_sentinel_absent(exc, SENTINEL)
        assert exc.category == category
        assert exc.status is None
        assert str(exc) == category
