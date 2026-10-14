"""Record boundaries of JSON Lines text (#9532).

A JSON Lines record ends at a physical LF; a CR before it is tolerated
(https://jsonlines.org/). ``str.splitlines()`` also breaks at U+000B, U+000C,
U+001C-U+001E, U+0085, U+2028 and U+2029, and a JSON serializer may emit the
last three unescaped inside string values, so it would cut one valid record
into two malformed fragments. The same holds for other LF-framed records whose
fields carry free text: Git object headers and log lines, HTTP header fields.
"""

from __future__ import annotations


def jsonl_lines(text: str) -> list[str]:
    """Split ``text`` into records at LF only, dropping one trailing CR from each."""
    return [line.removesuffix("\r") for line in text.split("\n")]


def physical_lines(text: str) -> list[str]:
    """``str.splitlines()`` shape (no empty record after a final LF), split at LF only (#9556)."""
    return jsonl_lines(text.removesuffix("\n")) if text else []
