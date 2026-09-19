"""Minimal shared TypeSafe System One client.

About fourteen modules each re-load the key and POST ``/v1/systemone``.
This helper is the one place for that. Existing modules are not migrated
here (#8192); new callers should import these two functions instead of
copying the sketch in ``docs/best-practices/typesafe-jev.md`` §9.

Never log the API key or the expanded secret path. Error text uses the
tilde form ``~/.secrets/…`` only, or a fixed message that names neither
the key nor a path. A key that is not one printable-ASCII line is unusable.
A bad key file is skipped; a bad environment value, or a header the HTTP
stack rejects, raises ``TypeSafeError`` with that fixed message.
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
_UNUSABLE_KEY_MESSAGE = "TypeSafe API key is unusable"


class TypeSafeError(Exception):
    """HTTP error, timeout, malformed JSON, or a missing API key.

    ``str(self)`` never includes the key or an expanded secret path.
    """


def _api_key_is_usable(key: str) -> bool:
    """True when ``key`` is one non-empty printable-ASCII token with no whitespace."""
    return bool(key) and all(33 <= ord(char) <= 126 for char in key)


def load_typesafe_api_key() -> str:
    """Return the API key: env, then ``~/.secrets/typesafe-ai.key``, then the legacy misspelling.

    Precedence is ``TYPESAFE_API_KEY``, then ``~/.secrets/typesafe-ai.key``,
    then ``~/.secrets/typsafe-ai.key``. Empty env falls through. An empty,
    undecodable, or otherwise unusable file falls through to the next name.
    A non-empty env value that is not a usable key raises ``TypeSafeError``
    with the fixed message ``TypeSafe API key is unusable`` and does not
    fall through. That message contains neither the key nor a path.
    """
    env = os.environ.get("TYPESAFE_API_KEY", "")
    stripped = env.strip()
    if stripped:
        if not _api_key_is_usable(stripped):
            raise TypeSafeError(_UNUSABLE_KEY_MESSAGE) from None
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
    raise TypeSafeError(
        "TYPESAFE_API_KEY unset and neither ~/.secrets/typesafe-ai.key nor legacy ~/.secrets/typsafe-ai.key found"
    )


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
    """
    api_key = load_typesafe_api_key()
    payload = json.dumps(
        {"state": state, "model": model, "questions": questions},
        ensure_ascii=False,
    ).encode("utf-8")
    # Raise the sanitised error only after this handler has exited. Raising
    # inside the ``except`` reattaches the ``ValueError`` as ``__context__``,
    # and that message can contain the key.
    request_rejected = False
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
    except ValueError:
        request_rejected = True
    except urllib.error.HTTPError as exc:
        raise TypeSafeError(f"System One HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise TypeSafeError("System One request timed out") from exc
        raise TypeSafeError("System One request failed (URLError)") from exc
    except TimeoutError as exc:
        raise TypeSafeError("System One request timed out") from exc
    except http.client.HTTPException as exc:
        raise TypeSafeError(f"System One request failed ({type(exc).__name__})") from exc
    except OSError as exc:
        raise TypeSafeError(f"System One request failed ({type(exc).__name__})") from exc
    if request_rejected:
        raise TypeSafeError(_UNUSABLE_KEY_MESSAGE) from None
    try:
        text = raw.decode("utf-8")
        parsed = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TypeSafeError("System One returned malformed JSON") from exc
    if not isinstance(parsed, dict):
        raise TypeSafeError("System One returned malformed JSON")
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
