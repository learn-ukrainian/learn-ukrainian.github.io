"""Registered exemptions for seminar primary-reading quotes that fail corpus auto-match."""

from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

_EXEMPTIONS_PATH = Path(__file__).with_name("seminar_quote_exemptions.json")


def normalize_seminar_quote_text(text: str) -> str:
    return re.sub(r"[^а-яіїєґА-ЯІЇЄҐ0-9]", "", text.lower())


def seminar_quote_exemption_key(module_slug: str, quote_text: str) -> str:
    normalized = normalize_seminar_quote_text(quote_text)
    payload = f"{module_slug.strip().lower()}\n{normalized}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def load_seminar_quote_exemptions() -> dict[str, dict[str, Any]]:
    if not _EXEMPTIONS_PATH.is_file():
        return {}
    data = json.loads(_EXEMPTIONS_PATH.read_text(encoding="utf-8"))
    exemptions = data.get("exemptions", {})
    if not isinstance(exemptions, dict):
        return {}
    return {
        str(key): entry
        for key, entry in exemptions.items()
        if isinstance(entry, dict)
    }


def lookup_seminar_quote_exemption(
    module_slug: str,
    quote_text: str,
    *,
    exemptions: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    registry = load_seminar_quote_exemptions() if exemptions is None else exemptions
    return registry.get(seminar_quote_exemption_key(module_slug, quote_text))
