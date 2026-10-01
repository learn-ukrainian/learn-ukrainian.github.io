"""Publication rights from the existing textbook acquisition registry.

Pack provenance and inline ``publish`` claims never grant permission. Grounding
records remain usable without a right; only publication as a quote needs one.
"""

import re
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from . import codes

REGISTRY_PATH = Path(__file__).resolve().parents[3] / "docs/l2-uk-direct/textbook-selection.yaml"


@lru_cache(maxsize=8)
def _parse_registry(path: Path, fingerprint: tuple[int, int, int]) -> dict[str, Any]:
    """Parse once per file revision; the stat fingerprint invalidates withdrawals."""
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError):
        raise ValueError(f"{codes.PUBLICATION_REGISTRY_UNREADABLE}: cannot parse source registry") from None
    entries = document.get("sources") if isinstance(document, dict) else None
    if not isinstance(entries, dict) or any(not isinstance(entry, dict) for entry in entries.values()):
        raise ValueError(f"{codes.PUBLICATION_REGISTRY_UNREADABLE}: invalid sources mapping")
    return entries


def load_registry(path: Path | None = None) -> dict[str, Any]:
    """Load cached exact keys, preserving typed errors and isolating caller mutations."""
    path = path or REGISTRY_PATH
    try:
        stat = path.stat()
    except OSError:
        raise ValueError(f"{codes.PUBLICATION_REGISTRY_UNREADABLE}: cannot read source registry") from None
    return deepcopy(_parse_registry(path, (stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size)))


def source_attribution(record: dict, registry: dict | None = None) -> str:
    """One Ukrainian bibliographic citation for quotes and grounding resources.

    Metadata is registry-owned. This formats a citation, never grants quote rights.
    Grade ranges keep two positive integer endpoints rather than a string grade.
    """
    entries = load_registry() if registry is None else registry
    source = record.get("source") or {}
    entry = entries.get(source.get("file"))
    try:
        if (
            not isinstance(entry, dict)
            or entry.get("file") != source.get("file")
            or entry.get("kind") != source.get("kind")
        ):
            raise ValueError("unregistered source")
        author, title = entry.get("author"), entry.get("title")
        provenance = entry.get("title_provenance")
        if (
            not isinstance(author, str)
            or not author.strip()
            or not isinstance(title, str)
            or not title.strip()
            or re.search(r"[A-Za-z]", title + author)
            or title == source.get("file")
            or not isinstance(provenance, dict)
            or not (provenance.get("url") or provenance.get("chunk_id"))
        ):
            raise ValueError("unconfirmed bibliography")
        grade, year, page = entry.get("grade"), entry.get("year"), source.get("page")
        if any(type(value) is not int or value < 1 for value in (grade, year, page)):
            raise ValueError("invalid grade, year or page")
        grade_end, part = entry.get("grade_end"), entry.get("part")
        if grade_end is not None and (type(grade_end) is not int or grade_end < grade):
            raise ValueError("invalid grade range")
        if part is not None and (type(part) is not int or part < 1):
            raise ValueError("invalid part")
        grades = f"{grade}–{grade_end}" if grade_end is not None else str(grade)
        part_label = f", ч. {part}" if part is not None else ""
        return f"{author}, «{title}», {grades} клас{part_label}, {year}, с. {page}"
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"{codes.PUBLICATION_ATTRIBUTION}: {record.get('id')} incomplete source attribution") from exc


def quote_attribution(record: dict, registry: dict | None = None) -> str:
    """Validate one excerpt and return its required, source-bound attribution.

    limit_chars measures the original excerpt's Unicode characters, before
    normalization or stress annotation. No truncation or pack-provided policy.
    """
    entries = load_registry() if registry is None else registry
    source = record.get("source") or {}
    entry = entries.get(source.get("file"))
    right = entry.get("publish") if isinstance(entry, dict) else None
    if (
        not isinstance(right, dict)
        or right.get("allowed") is not True
        or entry.get("kind") != source.get("kind")
        or entry.get("file") != source.get("file")
    ):
        raise ValueError(f"{codes.PUBLICATION_RIGHT}: {record.get('id')} source has no publication right")
    limit = right.get("limit_chars")
    quote = record.get("quote")
    if type(limit) is not int or limit < 1 or not isinstance(quote, str) or not quote:
        raise ValueError(f"{codes.PUBLICATION_RIGHT}: {record.get('id')} invalid excerpt or publication limit")
    if len(quote) > limit:
        raise ValueError(
            f"{codes.PUBLICATION_LIMIT}: {record.get('id')} excerpt has {len(quote)} characters; limit {limit}"
        )
    if right.get("attribution") != "ukrainian-short":
        raise ValueError(f"{codes.PUBLICATION_ATTRIBUTION}: {record.get('id')} unsupported attribution format")
    return source_attribution(record, entries)


def quoted_records(plan: dict) -> dict[str, str]:
    """Map planned quote refs to step ids; explains-only citations are grounding."""
    refs = {}
    for lesson in plan.get("lessons", [plan]):
        for step in lesson.get("steps", []):
            if "quote" in (step.get("needs") or []):
                citations = [*(step.get("evidence") or []), *(step.get("explains") or [])]
                if step.get("ref"):
                    citations.append(step["ref"])
                refs.update({ref: step.get("id", "") for ref in citations if ref.startswith("T-")})
    return refs
