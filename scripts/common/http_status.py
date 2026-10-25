"""Recognize HTTP status tokens in untrusted diagnostic text, using stdlib only."""

from __future__ import annotations

import re
from collections.abc import Collection

_STATUS_TOKEN = re.compile(
    r"(?<![\w.])"
    r"(?:(?:HTTP(?:/[0-9]+(?:\.[0-9]+)*[ \t]+)?|status(?:[ \t]+code)?|error(?:[ \t]+code)?)"
    r"[ \t]*[:=]?[ \t]*)?"
    r"([1-5][0-9]{2})(?!\w|\.\d)",
    re.IGNORECASE,
)


def has_http_status(text: str, codes: Collection[int], *, start: int = 0) -> bool:
    """Match selected codes as standalone tokens or HTTP/status/error markers.

    Letters, digits, underscores and decimal/version runs cannot contain a
    standalone status. ASCII digits are required. ``start`` limits the code's
    position while retaining the original text for boundary and marker context,
    so callers inspecting a tail never turn a partial identifier into a status.
    Pass output streams separately to preserve their independent boundaries.
    """
    return any(
        match.start(1) >= start and int(match[1]) in codes
        for match in _STATUS_TOKEN.finditer(text)
    )
