"""Synthetic record and document builders for the resolver tests.

Every word is invented (checked absent from VESUM when written); every stressed
spelling is a placeholder. None claims dictionary attestation."""

from __future__ import annotations

from scripts.curriculum.resolver.inputs import Allowlist, ExpandedDocument

ACUTE = "\u0301"


def stressed(word: str, vowel_index: int) -> str:
    """Placeholder stress for an invented word: an acute after the given code point."""
    return word[: vowel_index + 1] + ACUTE + word[vowel_index + 1 :]


def form(text: str, tags: str, stressed_text: str | None, *, source: str = "ulif", markers=None, learner=None) -> dict:
    markers = list(markers or [])
    entry = {
        "form": text,
        "tags": tags,
        "stress_source": "pending" if stressed_text is None else source,
        "markers": markers,
        "learner": (not markers) if learner is None else learner,
    }
    if stressed_text is not None:
        entry["stressed"] = stressed_text
    return entry


def record(number: int, lemma: str, pos: str, forms: list[dict], gloss: str | None = None) -> dict:
    out = {
        "id": f"W-{number}",
        "lemma": lemma,
        "pos": pos,
        "entry": {"source": "vesum", "entry_id": 900000 + number},
        "ulif": "pending",
        "forms": forms,
    }
    if gloss:
        out["gloss_en"] = gloss
        out["gloss_source"] = {"table": "dmklinger_uk_en", "id": number}
    return out


def unit(
    text: str,
    role: str = "narration",
    *,
    tab: str = "urok",
    activity=None,
    item=None,
    block=0,
    step=None,
) -> dict:
    d = {"tab": tab, "activity": activity, "item": item, "block": block, "role": role, "text": text}
    if step is not None:
        d["step"] = step
    return d


def document(*units: dict, slug: str = "synthetic-module", n: int = 1) -> ExpandedDocument:
    return ExpandedDocument.from_data({"lesson": {"level": "a1", "slug": slug, "n": n}, "units": list(units)})


def allowlist(records: list[dict], **kwargs) -> Allowlist:
    kwargs.setdefault("label", "synthetic plan a1/synthetic-module lesson 1")
    return Allowlist.from_records(records, **kwargs)
