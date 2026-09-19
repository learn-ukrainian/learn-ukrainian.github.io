"""Minimal shared TypeSafe System One client.

About fourteen modules each re-load the key and POST ``/v1/systemone``.
This helper is the one place for that. Existing modules are not migrated
here (#8192); new callers should import these two functions instead of
copying the sketch in ``docs/best-practices/typesafe-jev.md`` §9.

Never log the API key or a secret path. Every client ``TypeSafeError`` is
raised ``from None`` after the handler has exited, so ``__cause__`` and
``__context__`` cannot echo a header, URL, reason phrase, or body. The
message is only a category (``http_error``, ``timeout``, ``network_error``,
``malformed_json``, ``invalid_key``, ``no_key``) plus the integer HTTP
status when the category is ``http_error``. A key that is not one
printable-ASCII line is unusable. A bad key file is skipped; a bad
environment value, or a header the HTTP stack rejects, raises
``invalid_key``.
"""

from __future__ import annotations

import http.client
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_URL = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
DEFAULT_TIMEOUT = 60.0

_KEY_FILENAMES = ("typesafe-ai.key", "typsafe-ai.key")


class TypeSafeError(Exception):
    """HTTP error, timeout, malformed JSON, or a missing or unusable API key.

    ``category`` is one of ``http_error``, ``timeout``, ``network_error``,
    ``malformed_json``, ``invalid_key``, ``no_key``. ``status`` is the integer
    HTTP status for ``http_error`` and ``None`` otherwise. ``str(self)`` is
    built only from those fields. It never includes a key, key path, URL,
    header, reason phrase, or response body.
    """

    def __init__(self, message: str, *, category: str | None = None, status: int | None = None) -> None:
        super().__init__(message)
        self.category = category
        self.status = status


def _client_error(category: str, status: int | None = None) -> TypeSafeError:
    """Build an error whose text is the category and, for HTTP, the status code."""
    safe_status = status if isinstance(status, int) and not isinstance(status, bool) else None
    if category == "http_error" and safe_status is not None:
        return TypeSafeError(f"http_error {safe_status}", category=category, status=safe_status)
    return TypeSafeError(category, category=category, status=None)


def _api_key_is_usable(key: str) -> bool:
    """True when ``key`` is one non-empty printable-ASCII token with no whitespace."""
    return bool(key) and all(33 <= ord(char) <= 126 for char in key)


def load_typesafe_api_key() -> str:
    """Return the API key: env, then ``~/.secrets/typesafe-ai.key``, then the legacy misspelling.

    Precedence is ``TYPESAFE_API_KEY``, then ``~/.secrets/typesafe-ai.key``,
    then ``~/.secrets/typsafe-ai.key``. Empty env falls through. An empty,
    undecodable, or otherwise unusable file falls through to the next name.
    A non-empty env value that is not a usable key raises ``TypeSafeError``
    with category ``invalid_key`` and does not fall through. No key at all
    raises category ``no_key``. Neither message names the key or a path.
    """
    env = os.environ.get("TYPESAFE_API_KEY", "")
    stripped = env.strip()
    if stripped:
        if not _api_key_is_usable(stripped):
            raise _client_error("invalid_key") from None
        return stripped
    secrets = Path.home() / ".secrets"
    for name in _KEY_FILENAMES:
        path = secrets / name
        if not path.is_file():
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if len(lines) == 1 and _api_key_is_usable(lines[0]):
            return lines[0]
    raise _client_error("no_key") from None


def system_one(
    state: Any,
    questions: Any,
    *,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """POST one System One request and return the parsed JSON object.

    Raises ``TypeSafeError`` on HTTP failure, timeout, or a body that is not
    a JSON object. The key is loaded inside this call and is not returned.
    The raised error is built only from a category and, for HTTP, the integer
    status. It is raised after the handler exits, ``from None``, so the
    server reason, body, and URL are not attached as ``__cause__`` or
    ``__context__``.
    """
    api_key = load_typesafe_api_key()
    payload = json.dumps(
        {"state": state, "model": model, "questions": questions},
        ensure_ascii=False,
    ).encode("utf-8")
    # Capture only the safe fields, then raise after this handler has exited.
    # Raising inside ``except`` attaches the raw error as ``__context__``, and
    # that text can contain a credential, a URL, or a response body.
    failure: tuple[str, int | None] | None = None
    raw = b""
    try:
        request = urllib.request.Request(
            API_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "learn-ukrainian-typesafe-client/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        code = exc.code
        status = code if isinstance(code, int) and not isinstance(code, bool) else None
        failure = ("http_error", status)
    except urllib.error.URLError as exc:
        failure = ("timeout", None) if isinstance(exc.reason, TimeoutError) else ("network_error", None)
    except TimeoutError:
        failure = ("timeout", None)
    except http.client.HTTPException:
        failure = ("network_error", None)
    except OSError:
        failure = ("network_error", None)
    except ValueError:
        failure = ("invalid_key", None)
    if failure is not None:
        raise _client_error(failure[0], failure[1]) from None
    malformed = False
    parsed: Any = None
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        malformed = True
    if malformed or not isinstance(parsed, dict):
        raise _client_error("malformed_json") from None
    return parsed


class HttpSystemOneClient:
    """Object wrapper so verifiers can inject a fake with the same method."""

    def system_one(
        self,
        state: Any,
        questions: Any,
        *,
        model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        return system_one(state, questions, model=model, timeout=timeout)
