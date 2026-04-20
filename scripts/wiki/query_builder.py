"""Build section-retrieval query buckets from discovery + plan data."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .config import CURRICULUM_DIR

_CYRILLIC_RE = re.compile(r"[А-Яа-яІіЇїЄєҐґ]")
_TOKEN_RE = re.compile(r"[А-Яа-яІіЇїЄєҐґ'’ʼ`-]{4,}")


def build_query_buckets(discovery_yaml_path: str | Path, track: str) -> tuple[list[str], set[str]]:
    """Return bucket-A phrases and bucket-B keywords for section retrieval.

    Bucket A keeps exact Ukrainian phrases from discovery/plan text.
    Bucket B is the flattened 4+ char Cyrillic token set used for broad recall.
    """
    discovery_path = Path(discovery_yaml_path)
    discovery = _load_yaml(discovery_path)
    plan = _load_yaml(_plan_path_for(discovery_path, track))

    phrase_candidates = [
        *(_normalize_phrase(value) for value in discovery.get("query_keywords", [])),
        *(_normalize_phrase(value) for value in plan.get("objectives", [])),
    ]
    bucket_a = _dedupe_preserving_order(
        _quote_phrase(phrase)
        for phrase in phrase_candidates
        if _is_bucket_a_phrase(phrase)
    )

    bucket_b: set[str] = set()
    for value in [*discovery.get("query_keywords", []), *plan.get("objectives", [])]:
        bucket_b.update(_extract_bucket_b_keywords(str(value)))

    return bucket_a, bucket_b


def _plan_path_for(discovery_path: Path, track: str) -> Path:
    return CURRICULUM_DIR / "plans" / track / f"{discovery_path.stem}.yaml"


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _normalize_phrase(value: object) -> str:
    return _normalize_text(str(value or ""))


def _is_bucket_a_phrase(phrase: str) -> bool:
    if not phrase or not _CYRILLIC_RE.search(phrase):
        return False
    words = phrase.split()
    return len(words) >= 3 or len(phrase) >= 10


def _quote_phrase(phrase: str) -> str:
    clean = phrase.replace('"', " ").strip()
    return f'"{clean}"'


def _extract_bucket_b_keywords(value: str) -> set[str]:
    normalized = _normalize_text(value)
    if not _CYRILLIC_RE.search(normalized):
        return set()

    keywords: set[str] = set()
    for token in _TOKEN_RE.findall(normalized):
        cleaned = token.strip("-'’ʼ`")
        if len(cleaned) >= 4 and _CYRILLIC_RE.search(cleaned):
            keywords.add(cleaned)
    return keywords


def _dedupe_preserving_order(values: list[str] | tuple[str, ...] | object) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        ordered.append(value)
        seen.add(value)
    return ordered


def _normalize_text(text: str) -> str:
    from .diagnostics.retrieval_playback import normalize_text

    return normalize_text(text)
