"""Compatibility selectors shared by the shell launcher and work API."""

from __future__ import annotations

import functools
import re
from pathlib import Path

ALIASES_PATH = Path(__file__).resolve().parents[1] / "config/launcher_stream_aliases.tsv"
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


def load_launcher_bindings() -> dict[str, tuple[str, str]]:
    """Return selector-to-(stream, lane) bindings, rejecting malformed or duplicate rows."""
    aliases: dict[str, tuple[str, str]] = {}
    for line_number, line in enumerate(ALIASES_PATH.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 3 or any(_TOKEN.fullmatch(field) is None for field in fields):
            raise ValueError(f"invalid launcher alias row {line_number}")
        selector, stream, lane = fields
        if selector in aliases:
            raise ValueError(f"duplicate launcher alias {selector!r}")
        aliases[selector] = (stream, lane)
    return aliases


@functools.lru_cache(maxsize=1)
def load_launcher_aliases() -> dict[str, str]:
    """Return the existing selector-to-stream view of the validated bindings."""
    return {selector: stream for selector, (stream, _lane) in load_launcher_bindings().items()}
