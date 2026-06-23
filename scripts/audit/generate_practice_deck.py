"""Generate the bounded Word Atlas practice deck."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from scripts.audit.lexeme_filter import is_practice_eligible

DEFAULT_MANIFEST = Path("site/src/data/lexicon-manifest.json")
DEFAULT_OUT = Path("site/src/data/lexicon-practice-deck.json")
DEFAULT_TARGET = 3000
DEFAULT_SOFT_CAP = 4000
CEFR_ORDER = ("A1", "A2", "B1", "B2", "C1", "C2")
CEFR_RANK = {level: index for index, level in enumerate(CEFR_ORDER)}


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _clean_text(value: Any) -> str | None:
    return value.strip() if _has_text(value) else None


def _stable_hash(entry: dict[str, Any]) -> str:
    key = "\x1f".join(
        str(part)
        for part in (
            entry.get("lemma") or "",
            entry.get("url_slug") or entry.get("slug") or "",
            entry.get("gloss") or "",
        )
    )
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def _course_usage(entry: dict[str, Any]) -> list[dict[str, Any]]:
    usage = entry.get("course_usage")
    if not isinstance(usage, list):
        return []
    return [item for item in usage if isinstance(item, dict)]


def _course_key(entry: dict[str, Any]) -> tuple[str, str, str]:
    first = _course_usage(entry)[0] if _course_usage(entry) else {}
    return (
        str(first.get("track") or ""),
        str(first.get("slug") or first.get("module") or ""),
        _stable_hash(entry),
    )


def _cefr_level(entry: dict[str, Any]) -> str | None:
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, dict):
        return None
    cefr = enrichment.get("cefr")
    level = cefr.get("level") if isinstance(cefr, dict) else cefr
    return level if isinstance(level, str) and level in CEFR_RANK else None


def _ipa(entry: dict[str, Any]) -> str | None:
    direct = _clean_text(entry.get("ipa"))
    if direct:
        return direct
    pronunciation = entry.get("pronunciation")
    if isinstance(pronunciation, dict):
        direct = _clean_text(pronunciation.get("ipa"))
        if direct:
            return direct
    enrichment = entry.get("enrichment")
    if isinstance(enrichment, dict):
        pronunciation = enrichment.get("pronunciation")
        if isinstance(pronunciation, dict):
            return _clean_text(pronunciation.get("ipa"))
        return _clean_text(enrichment.get("ipa"))
    return None


def _heritage(entry: dict[str, Any]) -> str | None:
    status = entry.get("heritage_status")
    if not isinstance(status, dict):
        return None
    for key in ("classification", "status", "label", "category"):
        value = _clean_text(status.get(key))
        if value:
            return value
    return None


def _example(entry: dict[str, Any]) -> str | None:
    for usage in _course_usage(entry):
        for key in ("context", "example", "sentence"):
            value = _clean_text(usage.get(key))
            if value:
                return value
    return None


def _practice_item(entry: dict[str, Any]) -> dict[str, Any] | None:
    lemma = _clean_text(entry.get("lemma"))
    slug = _clean_text(entry.get("url_slug")) or _clean_text(entry.get("slug"))
    gloss = _clean_text(entry.get("gloss"))
    if not lemma or not slug or not gloss:
        return None

    return {
        "lemma": lemma,
        "slug": slug,
        "gloss": gloss,
        "ipa": _ipa(entry),
        "pos": _clean_text(entry.get("pos")),
        "cefr": _cefr_level(entry),
        "heritage": _heritage(entry),
        "example": _example(entry),
        "audioKey": None,
    }


def build_practice_deck(
    entries: list[dict[str, Any]],
    target: int = DEFAULT_TARGET,
    soft_cap: int = DEFAULT_SOFT_CAP,
) -> tuple[list[dict[str, Any]], bool]:
    if target < 0:
        raise ValueError("target must be non-negative")
    if soft_cap < 0:
        raise ValueError("soft_cap must be non-negative")

    eligible = [entry for entry in entries if is_practice_eligible(entry)]
    course_entries = [entry for entry in eligible if _course_usage(entry)]
    fill_entries = [entry for entry in eligible if not _course_usage(entry)]

    course_entries.sort(key=_course_key)
    fill_entries.sort(
        key=lambda entry: (
            CEFR_RANK.get(_cefr_level(entry) or "", len(CEFR_RANK)),
            _stable_hash(entry),
        )
    )

    selected = list(course_entries)
    if len(selected) < target:
        selected.extend(fill_entries[: target - len(selected)])

    deck = [item for entry in selected if (item := _practice_item(entry)) is not None]
    return deck, len(deck) > soft_cap


def read_manifest(path: Path) -> list[dict[str, Any]]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError("manifest entries must be a list")
    return [entry for entry in entries if isinstance(entry, dict)]


def write_deck(deck: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(deck, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET)
    parser.add_argument("--soft-cap", type=int, default=DEFAULT_SOFT_CAP)
    args = parser.parse_args(argv)

    entries = read_manifest(args.manifest)
    deck, exceeded_soft_cap = build_practice_deck(
        entries,
        target=args.target,
        soft_cap=args.soft_cap,
    )
    if exceeded_soft_cap:
        print(
            f"WARNING: practice deck has {len(deck)} cards; soft cap is {args.soft_cap}",
            file=sys.stderr,
        )
    write_deck(deck, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
