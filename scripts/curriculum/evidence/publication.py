"""Publication rights from the existing textbook acquisition registry.

Pack provenance and inline ``publish`` claims never grant permission. Grounding
records remain usable without a right; only publication as a quote needs one.
"""

from pathlib import Path
from string import Formatter
from typing import Any

import yaml

from . import codes

REGISTRY_PATH = Path(__file__).resolve().parents[3] / "docs/l2-uk-direct/textbook-selection.yaml"


def load_registry(path: Path | None = None) -> dict[str, Any]:
    """Load exact source_file keys; unavailable or malformed rights fail closed."""
    try:
        document = yaml.safe_load((path or REGISTRY_PATH).read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError):
        return {}
    entries = document.get("sources") if isinstance(document, dict) else None
    return entries if isinstance(entries, dict) else {}


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
    template = right.get("attribution")
    values = {key: entry.get(key) for key in ("author", "title", "grade", "year")}
    values["page"] = source.get("page")
    try:
        fields = {field for _, field, _, _ in Formatter().parse(template) if field is not None}
        if fields != set(values) or any(value is None or value == "" for value in values.values()):
            raise ValueError("incomplete attribution")
        attribution = template.format(**values)
    except (TypeError, ValueError, KeyError, AttributeError, IndexError) as exc:
        raise ValueError(f"{codes.PUBLICATION_ATTRIBUTION}: {record.get('id')} incomplete source attribution") from exc
    return attribution


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
