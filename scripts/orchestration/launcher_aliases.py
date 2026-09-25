"""Compatibility selectors shared by the shell launcher and work API."""

from __future__ import annotations

import functools
import re
from pathlib import Path

ALIASES_PATH = Path(__file__).resolve().parents[1] / "config/launcher_stream_aliases.tsv"
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


@functools.lru_cache(maxsize=1)
def load_launcher_aliases() -> dict[str, str]:
    """Return selector-to-stream aliases, rejecting malformed or duplicate rows."""
    aliases: dict[str, str] = {}
    for line_number, line in enumerate(ALIASES_PATH.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 3 or any(_TOKEN.fullmatch(field) is None for field in fields):
            raise ValueError(f"invalid launcher alias row {line_number}")
        selector, stream, _lane = fields
        if selector in aliases:
            raise ValueError(f"duplicate launcher alias {selector!r}")
        aliases[selector] = stream
    return aliases
