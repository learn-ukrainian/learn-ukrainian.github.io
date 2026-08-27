"""Atlas Wikipedia intro policy (#7379).

uk.wikipedia REST may return an exact-title hit whose *lead* still teaches the
wrong identity. For берегиня the title is Берегиня (#7376 does not apply), but
the REST extract introduces her as a rusalka-kin lesser spirit. That contradicts
the locked СУМ-20 sense 1 (goddess-protectress). Do not invent a replacement
excerpt: refuse the card.

This is Atlas encyclopedia attach/render policy, not a generic Wikipedia query
filter. Wiki writers may still fetch the article via ``wikipedia_summary``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

# Lemmas whose Wikipedia lead *should* identify them as rusalka-class beings.
_RUSALKA_CLASS_LEMMAS = frozenset(
    {
        "русалка",
        "русалки",
        "мавка",
        "мавки",
        "нявка",
        "нявки",
    }
)

# Explicit rusalka-identity / kinship in the encyclopedia lead.
_WIKI_RUSALKA_KIN_RE = re.compile(
    r"(?:"
    r"спор[іі]днен\w{0,8}\s+(?:із|з)\s+русалк"
    r"|інш(?:а|ою)\s+назва(?:ою)?\s+русалк"
    r"|тотожн\w{0,8}\s+(?:із|з)\s+русалк"
    r")",
    re.IGNORECASE,
)
_WIKI_LESSER_SPIRIT_RE = re.compile(r"нижч(?:ий|а|і)\s+дух", re.IGNORECASE)
_WIKI_RUSALKA_STEM_RE = re.compile(r"русалк", re.IGNORECASE)
_LEAD_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _strip_stress(text: str) -> str:
    return str(text or "").replace("\u0301", "")


def normalize_atlas_lemma(lemma: str) -> str:
    return _strip_stress(lemma).strip().casefold()


def is_rusalka_class_lemma(lemma: str) -> bool:
    return normalize_atlas_lemma(lemma) in _RUSALKA_CLASS_LEMMAS


def wikipedia_lead_text(*parts: object) -> str:
    """First-sentence lead plus optional description, stress-stripped."""
    chunks: list[str] = []
    for part in parts:
        raw = _strip_stress(str(part or "")).strip()
        if not raw:
            continue
        chunks.append(_LEAD_SPLIT_RE.split(raw, maxsplit=1)[0].strip())
    return " ".join(chunks)


def wikipedia_lead_has_rusalka_kin_framing(*parts: object) -> bool:
    """True when the encyclopedia intro teaches rusalka / lesser-spirit kinship."""
    lead = wikipedia_lead_text(*parts)
    if not lead:
        return False
    if _WIKI_RUSALKA_KIN_RE.search(lead):
        return True
    return bool(_WIKI_LESSER_SPIRIT_RE.search(lead) and _WIKI_RUSALKA_STEM_RE.search(lead))


def atlas_wikipedia_ok_as_intro(lemma: str, wiki_data: Mapping[str, Any] | None) -> bool:
    """Whether an exact-title Wikipedia summary may be the Atlas encyclopedia intro."""
    if not wiki_data:
        return False
    if is_rusalka_class_lemma(lemma):
        return True
    extract = wiki_data.get("extract") or wiki_data.get("summary") or ""
    description = wiki_data.get("description") or ""
    return not wikipedia_lead_has_rusalka_kin_framing(description, extract)
