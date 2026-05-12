"""Deterministic gate for Wiki Obligations Manifest coverage."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

from scripts.config import (
    WIKI_COVERAGE_DEFAULT_MIN_PCT,
    WIKI_COVERAGE_HARD_FAIL,
    WIKI_COVERAGE_MIN_PCT_BY_LEVEL,
)

_IMPLEMENTATION_MAP_RE = re.compile(
    r"<implementation_map\b[^>]*>(?P<body>.*?)</implementation_map>",
    re.IGNORECASE | re.DOTALL,
)
_OBLIGATION_RE = re.compile(r"obligation_id\s*:\s*(?P<id>[-\w]+)", re.IGNORECASE)
_FIELD_RE = re.compile(r"^\s*-?\s*(?P<key>artifact|location|treatment)\s*:\s*(?P<value>.+?)\s*$", re.IGNORECASE)


def parse_implementation_map(text: str) -> dict[str, dict[str, str]]:
    """Parse the writer-visible implementation map from raw writer output."""
    match = _IMPLEMENTATION_MAP_RE.search(text)
    if not match:
        return {}
    body = match.group("body")
    entries: dict[str, dict[str, str]] = {}
    current_id: str | None = None
    for line in body.splitlines():
        id_match = _OBLIGATION_RE.search(line)
        if id_match:
            current_id = id_match.group("id").strip()
            entries.setdefault(current_id, {"obligation_id": current_id})
            continue
        if current_id is None:
            continue
        field_match = _FIELD_RE.match(line)
        if field_match:
            entries[current_id][field_match.group("key").casefold()] = field_match.group("value").strip()
    return entries


def validate_obligations(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Flatten manifest obligations in deterministic manifest order."""
    obligations: list[dict[str, Any]] = []
    for group in ("sequence_steps", "l2_errors", "phonetic_rules", "decolonization_bans"):
        raw_items = manifest.get(group) or []
        if not isinstance(raw_items, Sequence) or isinstance(raw_items, (str, bytes)):
            continue
        for item in raw_items:
            if not isinstance(item, Mapping):
                continue
            obligation = dict(item)
            obligation["type"] = group.removesuffix("s")
            obligations.append(obligation)
    return obligations


def check_wiki_coverage(
    *,
    manifest: Mapping[str, Any],
    implementation_map: Mapping[str, Mapping[str, str]] | str,
    module_md: str,
    activities_yaml: str,
    vocabulary_yaml: str = "",
    resources_yaml: str = "",
    level: str | None = None,
) -> dict[str, Any]:
    """Compare manifest obligations to claimed artifact evidence."""
    map_entries = (
        parse_implementation_map(implementation_map)
        if isinstance(implementation_map, str)
        else {str(key): dict(value) for key, value in implementation_map.items()}
    )
    artifacts = {
        "module.md": module_md,
        "activities.yaml": activities_yaml,
        "vocabulary.yaml": vocabulary_yaml,
        "resources.yaml": resources_yaml,
    }
    activities = _load_activity_items(activities_yaml)
    obligation_results: list[dict[str, Any]] = []

    for obligation in validate_obligations(manifest):
        obligation_id = str(obligation.get("id") or "")
        claim = map_entries.get(obligation_id)
        if not claim:
            obligation_results.append(_result(obligation, "FAIL", "implementation_map_missing"))
            continue

        artifact = str(claim.get("artifact") or "").strip()
        location = str(claim.get("location") or "").strip()
        if artifact not in artifacts:
            obligation_results.append(_result(obligation, "FAIL", "unknown_artifact", claim))
            continue

        target_text = (
            _activity_text(activities, location)
            if artifact == "activities.yaml"
            else _location_text(artifacts[artifact], location)
        )
        if not target_text.strip():
            obligation_results.append(_result(obligation, "FAIL", "claimed_location_missing", claim))
            continue

        status, reason = _check_obligation_text(obligation, target_text, artifact)
        obligation_results.append(_result(obligation, status, reason, claim))

    covered = sum(1 for item in obligation_results if item["status"] == "PASS")
    total = len(obligation_results)
    coverage_pct = covered / total if total else 1.0
    min_pct = WIKI_COVERAGE_MIN_PCT_BY_LEVEL.get(
        str(level or "").lower(),
        WIKI_COVERAGE_DEFAULT_MIN_PCT,
    )
    hard_failed = any(item["status"] == "FAIL" for item in obligation_results)
    passed = not hard_failed if WIKI_COVERAGE_HARD_FAIL else coverage_pct >= min_pct
    return {
        "passed": passed,
        "hard_fail": hard_failed and WIKI_COVERAGE_HARD_FAIL,
        "coverage_pct": round(coverage_pct, 4),
        "covered": covered,
        "total": total,
        "min_pct": min_pct,
        "obligations": obligation_results,
    }


def check_wiki_coverage_paths(
    *,
    manifest: Mapping[str, Any] | str | Path,
    implementation_map: Mapping[str, Mapping[str, str]] | str,
    module_dir: Path,
    level: str | None = None,
) -> dict[str, Any]:
    manifest_data = _load_manifest(manifest)
    return check_wiki_coverage(
        manifest=manifest_data,
        implementation_map=implementation_map,
        module_md=_read_optional(module_dir / "module.md"),
        activities_yaml=_read_optional(module_dir / "activities.yaml"),
        vocabulary_yaml=_read_optional(module_dir / "vocabulary.yaml"),
        resources_yaml=_read_optional(module_dir / "resources.yaml"),
        level=level,
    )


def _load_manifest(manifest: Mapping[str, Any] | str | Path) -> Mapping[str, Any]:
    if isinstance(manifest, Mapping):
        return manifest
    path = Path(manifest)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(str(manifest))


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _load_activity_items(activities_yaml: str) -> list[dict[str, Any]]:
    try:
        parsed = yaml.safe_load(activities_yaml) if activities_yaml.strip() else []
    except yaml.YAMLError:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def _activity_text(activities: list[dict[str, Any]], location: str) -> str:
    if not location:
        return yaml.safe_dump(activities, allow_unicode=True, sort_keys=False)
    for activity in activities:
        activity_id = str(activity.get("id") or "")
        if activity_id and activity_id in location:
            return yaml.safe_dump(activity, allow_unicode=True, sort_keys=False)
    return ""


def _location_text(text: str, location: str) -> str:
    if not location or location.casefold() in {"module.md", "whole file", "file"}:
        return text
    location_key = location.strip().lstrip("#§ ").casefold()
    heading_re = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$", re.MULTILINE)
    headings = list(heading_re.finditer(text))
    for index, heading in enumerate(headings):
        title = heading.group("title").strip().casefold()
        if location_key and location_key not in title and title not in location_key:
            continue
        start = heading.start()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        return text[start:end]
    return text if location_key in text.casefold() else ""


def _check_obligation_text(obligation: Mapping[str, Any], target_text: str, artifact: str) -> tuple[str, str]:
    obligation_type = str(obligation.get("type") or "")
    if obligation_type == "l2_error":
        treatment = str(obligation.get("treatment") or "")
        if treatment == "contrast_pair":
            missing = []
            if not _any_marker_present(str(obligation.get("incorrect") or ""), target_text):
                missing.append("incorrect")
            if not _any_marker_present(str(obligation.get("correct") or ""), target_text):
                missing.append("correct")
            if missing:
                return "FAIL", "missing_" + "_and_".join(missing)
            if artifact != "activities.yaml":
                return "FAIL", "contrast_pair_not_in_activity"
            return "PASS", "contrast_pair_present"
        if _has_substance(str(obligation.get("correct") or ""), str(obligation.get("why") or ""), target_text):
            return "PASS", "prose_substance_present"
        return "FAIL", "prose_substance_missing"

    if obligation_type == "phonetic_rule":
        written = str(obligation.get("written") or "")
        spoken = str(obligation.get("spoken") or "")
        if _contains(target_text, written) and _contains(target_text, spoken):
            return "PASS", "phonetic_rule_present"
        return "FAIL", "phonetic_rule_missing"

    if obligation_type == "sequence_step":
        claim = str(obligation.get("required_claim") or obligation.get("heading") or "")
        if _claim_markers_present(claim, target_text):
            return "PASS", "sequence_claim_present"
        return "FAIL", "sequence_claim_missing"

    if obligation_type == "decolonization_ban":
        rule = str(obligation.get("rule") or "")
        if _claim_markers_present(rule, target_text):
            return "PASS", "ban_substance_present"
        return "FAIL", "ban_substance_missing"

    return "FAIL", "unknown_obligation_type"


def _result(
    obligation: Mapping[str, Any],
    status: str,
    reason: str,
    claim: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "obligation_id": obligation.get("id"),
        "type": obligation.get("type"),
        "status": status,
        "reason": reason,
        "claim": dict(claim or {}),
    }


def _contains(text: str, marker: str) -> bool:
    return _normalize(marker) in _normalize(text)


def _normalize(text: str) -> str:
    text = re.sub(r"[`*_]", "", text.casefold())
    text = text.replace("’", "'").replace("ʼ", "'")
    return re.sub(r"\s+", " ", text)


def _marker_candidates(text: str) -> list[str]:
    cleaned = re.sub(r"^(?:Вимова|Pronunciation)\s*:\s*", "", text.strip(), flags=re.IGNORECASE)
    raw_parts = re.split(r"\s*/\s*|\s+або\s+|\s+чи\s+", cleaned)
    parts = []
    for part in raw_parts:
        part = re.sub(r"\[[SС]\d+\]", "", part)
        part = re.sub(r"[`*_]", "", part).strip(" .;:,")
        if part:
            parts.append(part)
    return parts


def _any_marker_present(markers: str, text: str) -> bool:
    candidates = _marker_candidates(markers)
    return bool(candidates) and any(_contains(text, candidate) for candidate in candidates)


def _claim_markers_present(claim: str, text: str) -> bool:
    markers = re.findall(r"`([^`]+)`|\*([^*]{2,80})\*", claim)
    flattened = [left or right for left, right in markers if (left or right)]
    if not flattened:
        flattened = _substance_terms(claim)
    present = sum(1 for marker in flattened if _contains(text, marker))
    return present >= min(3, max(1, len(flattened)))


def _has_substance(correct: str, why: str, text: str) -> bool:
    if correct and not _any_marker_present(correct, text):
        return False
    terms = _substance_terms(why)
    if not terms:
        return bool(correct)
    present = sum(1 for term in terms[:8] if _contains(text, term))
    return present >= min(2, len(terms))


def _substance_terms(text: str) -> list[str]:
    stop = {
        "учень",
        "учні",
        "англомовні",
        "українська",
        "українській",
        "помилка",
        "часто",
        "тому",
        "потрібно",
        "пояснити",
        "використання",
    }
    words = re.findall(r"[А-Яа-яІіЇїЄєҐґA-Za-z][\w'’ʼ-]{4,}", _normalize(text))
    result = []
    for word in words:
        if word in stop or word in result:
            continue
        result.append(word)
    return result
