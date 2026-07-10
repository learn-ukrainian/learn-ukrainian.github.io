#!/usr/bin/env python3
"""Validate the final, deterministic schema for seminar reading records.

The validator is deliberately separate from build and promotion gates. It
checks only the checked-in reading-record contract and emits stable,
machine-readable ``RDR_*`` diagnostics. Legacy aliases are normalized so
migration work has actionable field-level evidence, but they can never make a
record pass the version-2 contract.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlparse

import yaml

READINGS_CONTRACT_VERSION = 2
HOSTING_VALUES = frozenset({"link-only", "excerpt-only", "hosted"})
HOSTED_RIGHTS_BASES = frozenset({"public-domain", "open-license", "permission"})
EXCERPT_RIGHTS_BASES = HOSTED_RIGHTS_BASES | frozenset({"approved-exception"})
_PLACEHOLDER_VALUES = frozenset(
    {
        "n/a",
        "none",
        "not applicable",
        "not-applicable",
        "tbd",
        "todo",
        "pending",
        "reading-needed",
        "reading needed",
        "unresolved",
        "unknown",
        "потрібно уточнити",
        "підлягає уточненню",
        "потрібен матеріал",
        "не визначено",
        "невідомо",
    }
)
_READING_SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_PLACEHOLDER_SEPARATOR_RE = re.compile(r"[\s_\-‐‑‒–—―]+")
_MISSING = object()


def _is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_http_url(value: object) -> bool:
    if not _is_nonempty_string(value):
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_placeholder(value: object) -> bool:
    if not _is_nonempty_string(value):
        return False
    normalized = _PLACEHOLDER_SEPARATOR_RE.sub(" ", value.strip()).casefold()
    return normalized in _PLACEHOLDER_VALUES


def _normalized_title(value: object) -> str | None:
    """Return the conservative normalization used for hosted title matching."""
    if not _is_nonempty_string(value):
        return None
    return " ".join(value.split()).casefold()


def _diagnostic(
    code: str,
    *,
    entry: int | None = None,
    field: str | None = None,
    detail: str | None = None,
) -> dict[str, object]:
    """Return one stable machine-readable diagnostic in deterministic key order."""
    result: dict[str, object] = {"code": code}
    if entry is not None:
        result["entry"] = entry
    if field is not None:
        result["field"] = field
    if detail is not None:
        result["detail"] = detail
    return result


def _record_alias(
    normalized: dict[str, object],
    diagnostics: list[dict[str, object]],
    *,
    alias: str,
    canonical: str,
    value: object,
) -> None:
    """Normalize one legacy alias without allowing it to become contract-valid."""
    if canonical in normalized and normalized[canonical] != value:
        diagnostics.append(
            _diagnostic(
                "RDR_NORMALIZATION_CONFLICT",
                field=canonical,
                detail=f"legacy {alias!r} conflicts with {canonical!r}",
            )
        )
        return
    normalized.setdefault(canonical, value)
    diagnostics.append(
        _diagnostic(
            "RDR_LEGACY_FIELD",
            field=alias,
            detail=f"migrate {alias!r} to {canonical!r}",
        )
    )


def normalize_legacy_entry(entry: Mapping[str, object]) -> dict[str, object]:
    """Return a diagnostic-only normalization of known pre-v2 aliases.

    Only explicit aliases are normalized: ``url``, ``source``, and ``task``.
    Hosting and missing semantic values are never inferred.
    """
    normalized = dict(entry)
    diagnostics: list[dict[str, object]] = []
    if "url" in entry:
        _record_alias(
            normalized,
            diagnostics,
            alias="url",
            canonical="source_url",
            value=entry["url"],
        )
    if "source" in entry:
        source = entry["source"]
        canonical = "source_url" if _is_http_url(source) else "source_name"
        _record_alias(
            normalized,
            diagnostics,
            alias="source",
            canonical=canonical,
            value=source,
        )
    if "task" in entry:
        _record_alias(
            normalized,
            diagnostics,
            alias="task",
            canonical="learner_task",
            value=entry["task"],
        )
    return {"entry": normalized, "diagnostics": diagnostics}


def _public_reading_page_frontmatter(reading_slug: str, readings_dir: Path) -> Mapping[str, object] | None:
    """Return frontmatter for an enabled public reading page, else ``None``."""
    if not _READING_SLUG_RE.fullmatch(reading_slug):
        return None
    path = readings_dir / f"{reading_slug}.mdx"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    try:
        frontmatter = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(frontmatter, Mapping):
        return None
    if frontmatter.get("published", True) is False or frontmatter.get("canonical", True) is False:
        return None
    return frontmatter


def _validate_entry(
    entry: object,
    *,
    entry_number: int,
    readings_dir: Path,
    version_is_final: bool,
) -> dict[str, object]:
    if not isinstance(entry, Mapping):
        diagnostic = _diagnostic("RDR_ENTRY_TYPE", entry=entry_number, detail="reading entry must be a mapping")
        return {"status": "fail", "diagnostics": [diagnostic]}

    normalization = normalize_legacy_entry(entry)
    normalized = normalization["entry"]
    diagnostics = [{**diagnostic, "entry": entry_number} for diagnostic in normalization["diagnostics"]]
    for field in ("title", "source_name", "learner_task"):
        value = normalized.get(field)
        if not _is_nonempty_string(value):
            diagnostics.append(_diagnostic("RDR_REQUIRED", entry=entry_number, field=field))
        elif _is_placeholder(value):
            diagnostics.append(_diagnostic("RDR_PLACEHOLDER", entry=entry_number, field=field))

    language = normalized.get("language")
    if language != "uk":
        diagnostics.append(_diagnostic("RDR_LANGUAGE", entry=entry_number, field="language"))

    source_url = normalized.get("source_url")
    if not _is_http_url(source_url):
        diagnostics.append(_diagnostic("RDR_SOURCE_URL", entry=entry_number, field="source_url"))

    hosting = normalized.get("hosting")
    if hosting not in HOSTING_VALUES:
        diagnostics.append(_diagnostic("RDR_HOSTING", entry=entry_number, field="hosting"))

    rights = normalized.get("rights")
    if not isinstance(rights, Mapping):
        diagnostics.append(_diagnostic("RDR_RIGHTS_TYPE", entry=entry_number, field="rights"))
        rights = {}
    rights_basis = rights.get("basis")
    rights_evidence_url = rights.get("evidence_url")
    for field, value in (
        ("basis", rights_basis),
        ("evidence_url", rights_evidence_url),
        ("note", rights.get("note")),
    ):
        if not _is_nonempty_string(value):
            diagnostics.append(_diagnostic("RDR_RIGHTS_REQUIRED", entry=entry_number, field=f"rights.{field}"))
        elif _is_placeholder(value):
            diagnostics.append(_diagnostic("RDR_PLACEHOLDER", entry=entry_number, field=f"rights.{field}"))
    if _is_nonempty_string(rights_evidence_url) and not _is_http_url(rights_evidence_url):
        diagnostics.append(_diagnostic("RDR_RIGHTS_EVIDENCE_URL", entry=entry_number, field="rights.evidence_url"))

    if hosting == "link-only":
        if rights_basis != "external-link":
            diagnostics.append(_diagnostic("RDR_LINK_RIGHTS_BASIS", entry=entry_number, field="rights.basis"))
        if _is_http_url(source_url) and rights_evidence_url != source_url:
            diagnostics.append(_diagnostic("RDR_LINK_EVIDENCE_MISMATCH", entry=entry_number, field="rights.evidence_url"))
        if "reading_slug" in normalized:
            diagnostics.append(_diagnostic("RDR_LINK_READING_SLUG", entry=entry_number, field="reading_slug"))
        for field in ("locator", "excerpt_locator"):
            if field in normalized:
                diagnostics.append(_diagnostic("RDR_LINK_LOCATOR", entry=entry_number, field=field))
    elif hosting == "excerpt-only":
        locator = normalized.get("locator")
        if not _is_nonempty_string(locator) or _is_placeholder(locator):
            diagnostics.append(_diagnostic("RDR_EXCERPT_LOCATOR", entry=entry_number, field="locator"))
        if rights_basis not in EXCERPT_RIGHTS_BASES:
            diagnostics.append(_diagnostic("RDR_EXCERPT_RIGHTS_BASIS", entry=entry_number, field="rights.basis"))
    elif hosting == "hosted":
        reading_slug = normalized.get("reading_slug")
        if not _is_nonempty_string(reading_slug) or not _READING_SLUG_RE.fullmatch(reading_slug):
            diagnostics.append(_diagnostic("RDR_HOSTED_READING_SLUG", entry=entry_number, field="reading_slug"))
        else:
            reading_frontmatter = _public_reading_page_frontmatter(reading_slug, readings_dir)
            if reading_frontmatter is None:
                diagnostics.append(_diagnostic("RDR_HOSTED_READING_PAGE", entry=entry_number, field="reading_slug"))
            elif _normalized_title(reading_frontmatter.get("title")) != _normalized_title(normalized.get("title")):
                diagnostics.append(_diagnostic("RDR_HOSTED_READING_TITLE", entry=entry_number, field="title"))
        if rights_basis not in HOSTED_RIGHTS_BASES:
            diagnostics.append(_diagnostic("RDR_HOSTED_RIGHTS_BASIS", entry=entry_number, field="rights.basis"))

    unmigrated = bool(normalization["diagnostics"]) or not version_is_final
    status = "pass" if not diagnostics and not unmigrated else "unmigrated" if unmigrated else "fail"
    return {"status": status, "diagnostics": diagnostics}


def validate_readings_contract(
    plan: Mapping[str, object],
    *,
    readings_dir: Path,
) -> dict[str, object]:
    """Validate one plan's readings against the final version-2 contract."""
    diagnostics: list[dict[str, object]] = []
    version = plan.get("readings_contract_version")
    version_is_final = type(version) is int and version == READINGS_CONTRACT_VERSION
    if version is None:
        diagnostics.append(_diagnostic("RDR_VERSION_MISSING", field="readings_contract_version"))
    elif type(version) is not int:
        diagnostics.append(_diagnostic("RDR_VERSION_TYPE", field="readings_contract_version"))
    elif version != READINGS_CONTRACT_VERSION:
        diagnostics.append(_diagnostic("RDR_VERSION_UNSUPPORTED", field="readings_contract_version"))

    readings_present = "readings" in plan
    raw_readings = plan.get("readings")
    reading_disposition = plan.get("reading_disposition", _MISSING)
    if not readings_present:
        if reading_disposition is _MISSING:
            diagnostics.append(_diagnostic("RDR_READINGS_TYPE", field="readings"))
        elif not isinstance(reading_disposition, Mapping):
            diagnostics.append(_diagnostic("RDR_READING_DISPOSITION_TYPE", field="reading_disposition"))
        else:
            status = reading_disposition.get("status")
            if status != "not-applicable":
                diagnostics.append(_diagnostic("RDR_READING_DISPOSITION_STATUS", field="reading_disposition.status"))
            reason = reading_disposition.get("reason")
            if not _is_nonempty_string(reason) or _is_placeholder(reason):
                diagnostics.append(_diagnostic("RDR_READING_DISPOSITION_REASON", field="reading_disposition.reason"))
            evidence_url = reading_disposition.get("evidence_url")
            if not _is_http_url(evidence_url):
                diagnostics.append(
                    _diagnostic("RDR_READING_DISPOSITION_EVIDENCE_URL", field="reading_disposition.evidence_url")
                )
        raw_readings = []
    elif not isinstance(raw_readings, list):
        diagnostics.append(_diagnostic("RDR_READINGS_TYPE", field="readings"))
        raw_readings = []
    else:
        if not raw_readings:
            diagnostics.append(_diagnostic("RDR_READINGS_EMPTY", field="readings"))
        if reading_disposition is not _MISSING:
            diagnostics.append(_diagnostic("RDR_READING_DISPOSITION_CONFLICT", field="reading_disposition"))

    entries = [
        _validate_entry(
            entry,
            entry_number=index,
            readings_dir=readings_dir,
            version_is_final=version_is_final,
        )
        for index, entry in enumerate(raw_readings, start=1)
    ]
    diagnostics.extend(diagnostic for entry in entries for diagnostic in entry["diagnostics"])
    entry_counts = Counter(str(entry["status"]) for entry in entries)
    has_unmigrated = not version_is_final or entry_counts["unmigrated"] > 0
    status = "pass" if not diagnostics else "unmigrated" if has_unmigrated else "fail"
    return {
        "status": status,
        "passed": status == "pass",
        "readings_contract_version": version,
        "entry_count": len(entries),
        "entry_counts": {
            "pass": entry_counts["pass"],
            "unmigrated": entry_counts["unmigrated"],
            "fail": entry_counts["fail"],
        },
        "diagnostic_counts": dict(sorted(Counter(diagnostic["code"] for diagnostic in diagnostics).items())),
        "diagnostics": diagnostics,
    }
