"""Deterministic gate for Wiki Obligations Manifest coverage.

Path 3 PR2 extends the gate from a pass/fail coverage report into a
deterministic repair input for the reviewer loop described in
docs/decisions/2026-05-17-path3-per-obligation-review-loop.md. When a
PR1 seeded ``implementation_map.json`` sidecar is available, callers can
pass it as ``seeded_map`` (or let ``check_wiki_coverage_paths`` auto-load
``module_dir/implementation_map.json``). On failure, the returned report
includes ``fix_proposals``: one bounded, JSON-serializable proposal per
failed obligation. Passing reports omit the key to keep success events
quiet.
"""

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
_FIELD_RE = re.compile(
    r"^\s*-?\s*(?P<key>artifact|location|treatment)\s*:\s*(?P<value>.+?)\s*$",
    re.IGNORECASE,
)
# Inline-field shape: writer emits all four fields on the SAME line as the
# obligation_id, separated by `;` (semicolons). Example:
#   - obligation_id: step-2; artifact: module.md; location: §Дiалоги; treatment: ...
# Captures each known field name + its value (up to the next `;` or end of
# string), regardless of position in the line.
_INLINE_FIELD_RE = re.compile(
    r"(?P<key>artifact|location|treatment)\s*:\s*(?P<value>[^;]+?)(?=\s*;\s*(?:obligation_id|artifact|location|treatment)\s*:|\s*$)",
    re.IGNORECASE,
)


def parse_implementation_map(text: str) -> dict[str, dict[str, str]]:
    """Parse the writer-visible implementation map from raw writer output.

    The writer-prompt template nests `<implementation_map>` inside each
    `<plan_reasoning>` section block (one per section, typically 4 per
    module). This parser MUST collect entries from ALL implementation_map
    blocks, not just the first — `re.findall` instead of `re.search`.

    The prompt's example format puts each field on its own line:

        <implementation_map>
        - obligation_id: step-2
          artifact: module.md
          location: §Діалоги
          treatment: ...
        </implementation_map>

    But writers (notably claude-tools) commonly emit the more compact
    single-line semicolon-delimited form:

        <implementation_map>
        - obligation_id: step-2; artifact: module.md; location: §Діалоги; treatment: ...
        </implementation_map>

    Both are valid markdown and pedagogically equivalent. Parser accepts
    BOTH shapes per-line: it captures any `obligation_id` mention, then
    captures any inline `key: value` triple after `;` separators in the
    same line, AND continues to consume bullet-list field lines below
    in the original multi-line shape.

    Per-obligation entries are merged across all implementation_map blocks
    by obligation_id; the LAST emission wins for a given field (mirrors
    the writer's intent if they restate a more refined claim later).
    """
    matches = list(_IMPLEMENTATION_MAP_RE.finditer(text))
    if not matches:
        return {}
    entries: dict[str, dict[str, str]] = {}
    for match in matches:
        body = match.group("body")
        current_id: str | None = None
        for line in body.splitlines():
            id_match = _OBLIGATION_RE.search(line)
            if id_match:
                current_id = id_match.group("id").strip()
                entries.setdefault(current_id, {"obligation_id": current_id})
                # Also capture inline fields on the same line (semicolon shape).
                for inline_match in _INLINE_FIELD_RE.finditer(line):
                    entries[current_id][inline_match.group("key").casefold()] = (
                        inline_match.group("value").strip()
                    )
                continue
            if current_id is None:
                continue
            # Multi-line bullet-list shape: field on its own line below the id.
            field_match = _FIELD_RE.match(line)
            if field_match:
                entries[current_id][field_match.group("key").casefold()] = (
                    field_match.group("value").strip()
                )
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
    seeded_map: Mapping[str, Any] | None = None,
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
            obligation_results.append(_result(obligation, "FAIL", "implementation_map_missing", evidence_text=""))
            continue

        artifact = str(claim.get("artifact") or "").strip()
        location = str(claim.get("location") or "").strip()
        if artifact not in artifacts:
            obligation_results.append(_result(obligation, "FAIL", "unknown_artifact", claim, evidence_text=""))
            continue

        target_text = (
            _activity_text(activities, location)
            if artifact == "activities.yaml"
            else _location_text(artifacts[artifact], location)
        )
        if not target_text.strip():
            obligation_results.append(_result(obligation, "FAIL", "claimed_location_missing", claim, evidence_text=""))
            continue

        status, reason = _check_obligation_text(obligation, target_text, artifact)
        obligation_results.append(_result(obligation, status, reason, claim, evidence_text=target_text))

    covered = sum(1 for item in obligation_results if item["status"] == "PASS")
    total = len(obligation_results)
    coverage_pct = covered / total if total else 1.0
    min_pct = WIKI_COVERAGE_MIN_PCT_BY_LEVEL.get(
        str(level or "").lower(),
        WIKI_COVERAGE_DEFAULT_MIN_PCT,
    )
    phonetic_hard_failed = any(
        item["category"] == "phonetic_rules" and item.get("spoken_present") is False
        for item in obligation_results
    )
    hard_failed = any(item["status"] == "FAIL" for item in obligation_results)
    passed = False if phonetic_hard_failed else (not hard_failed if WIKI_COVERAGE_HARD_FAIL else coverage_pct >= min_pct)
    report = {
        "passed": passed,
        "hard_fail": phonetic_hard_failed or (hard_failed and WIKI_COVERAGE_HARD_FAIL),
        "phonetic_hard_fail": phonetic_hard_failed,
        "coverage_pct": round(coverage_pct, 4),
        "covered": covered,
        "total": total,
        "min_pct": min_pct,
        "obligations": [_public_obligation_result(item) for item in obligation_results],
    }
    if not passed:
        seeded_index = _seeded_obligation_index(seeded_map)
        report["fix_proposals"] = [
            _build_fix_proposal(
                result,
                seeded_index.get(str(result["obligation_id"])),
                artifacts,
            )
            for result in obligation_results
            if result["status"] == "FAIL"
        ]
    return report


def check_wiki_coverage_paths(
    *,
    manifest: Mapping[str, Any] | str | Path,
    implementation_map: Mapping[str, Mapping[str, str]] | str,
    module_dir: Path,
    level: str | None = None,
    seeded_map: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    manifest_data = _load_manifest(manifest)
    implementation_map_path = module_dir / "implementation_map.json"
    if seeded_map is None and implementation_map_path.exists():
        from scripts.build.phases.implementation_map import read_implementation_map

        seeded_map = read_implementation_map(implementation_map_path)
    return check_wiki_coverage(
        manifest=manifest_data,
        implementation_map=implementation_map,
        module_md=_read_optional(module_dir / "module.md"),
        activities_yaml=_read_optional(module_dir / "activities.yaml"),
        vocabulary_yaml=_read_optional(module_dir / "vocabulary.yaml"),
        resources_yaml=_read_optional(module_dir / "resources.yaml"),
        level=level,
        seeded_map=seeded_map,
    )


def _seeded_obligation_index(seeded_map: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if not seeded_map:
        return {}
    raw_entries = seeded_map.get("entries") or []
    if not isinstance(raw_entries, Sequence) or isinstance(raw_entries, (str, bytes)):
        return {}
    entries: dict[str, Mapping[str, Any]] = {}
    for entry in raw_entries:
        if not isinstance(entry, Mapping):
            continue
        obligation_id = str(entry.get("obligation_id") or "")
        if obligation_id:
            entries[obligation_id] = entry
    return entries


def _build_fix_proposal(
    obligation_result: Mapping[str, Any],
    seeded_entry: Mapping[str, Any] | None,
    artifacts: Mapping[str, str],
) -> dict[str, Any]:
    """Return a structured fix proposal for one failed obligation."""
    reason = str(obligation_result.get("reason") or "")
    return {
        "obligation_id": str(obligation_result.get("obligation_id") or ""),
        "obligation_type": str(
            obligation_result.get("obligation_type")
            or obligation_result.get("type")
            or ""
        ),
        "failure_reason": reason,
        "current_artifact_state": _current_artifact_state(obligation_result),
        "expected_treatment": _seeded_dict(seeded_entry, "treatment_template"),
        "surgical_diff_hint": _surgical_diff_hint(obligation_result, seeded_entry),
        "manifest_payload": (
            {}
            if reason == "unknown_obligation_type"
            else _seeded_dict(seeded_entry, "manifest_payload")
        ),
    }


def _seeded_dict(seeded_entry: Mapping[str, Any] | None, key: str) -> dict[str, Any]:
    if not seeded_entry:
        return {}
    value = seeded_entry.get(key)
    return dict(value) if isinstance(value, Mapping) else {}


def _current_artifact_state(obligation_result: Mapping[str, Any]) -> str:
    reason = str(obligation_result.get("reason") or "")
    if reason == "implementation_map_missing":
        return "MISSING (no <implementation_map> entry from writer)"
    if reason in {"unknown_artifact", "claimed_location_missing"}:
        claim = _claim(obligation_result)
        return f"writer_claim={claim!r}; resolved_artifact_text=''"
    return _truncate_evidence(str(obligation_result.get("_evidence_text") or ""))


def _truncate_evidence(text: str, limit: int = 400) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _surgical_diff_hint(
    obligation_result: Mapping[str, Any],
    seeded_entry: Mapping[str, Any] | None,
) -> str:
    reason = str(obligation_result.get("reason") or "")
    oid = str(obligation_result.get("obligation_id") or "")
    claim = _claim(obligation_result)
    payload = _seeded_dict(seeded_entry, "manifest_payload")
    hint_by_reason = {
        "implementation_map_missing": _implementation_map_missing_hint(
            oid,
            obligation_result,
            seeded_entry,
        ),
        "unknown_artifact": (
            f"Writer claimed artifact={claim.get('artifact')}, "
            f"but obligation requires artifact={_seeded_value(seeded_entry, 'artifact', claim.get('artifact'))}"
        ),
        "claimed_location_missing": (
            f"Location {claim.get('location')!r} returns empty text in {claim.get('artifact')}. "
            "Verify the section heading or activities.yaml block exists "
            f"(expected: {_seeded_value(seeded_entry, 'location_hint', claim.get('location'))})"
        ),
        "missing_incorrect": _missing_incorrect_hint(payload, claim),
        "missing_correct": _missing_correct_hint(payload),
        "missing_incorrect_and_correct": (
            _missing_incorrect_hint(payload, claim)
            + "; "
            + _missing_correct_hint(payload)
        ),
        "contrast_pair_not_in_activity": (
            "Move contrast_pair to activities.yaml entry "
            f"- currently claimed in {claim.get('artifact')}"
        ),
        "prose_substance_missing": (
            "Add prose paragraph naming manifest_payload.correct "
            f"({payload.get('correct')!r}) and explaining manifest_payload.why ({payload.get('why')!r})"
        ),
        "phonetic_rule_missing": (
            f"Add prose stating written={payload.get('written')!r} -> "
            f"spoken={payload.get('spoken')!r} with at least one example pair"
        ),
        "sequence_claim_missing": (
            "Add section heading or step marker matching manifest_payload.heading "
            f"({payload.get('heading')!r}); required_claim: {payload.get('required_claim')!r}"
        ),
        "ban_substance_missing": (
            f"Remove phrasing matching manifest_payload.rule ({payload.get('rule')!r}) "
            "- negative obligation: absence required"
        ),
        "unknown_obligation_type": (
            f"Unknown obligation type {obligation_result.get('type')!r} "
            "- seeder bug, file follow-up issue"
        ),
    }
    hint = hint_by_reason.get(reason)
    if hint is None:
        hint = f"Unhandled wiki coverage failure reason {reason!r} - file follow-up issue"
    if seeded_entry is None:
        hint += " (no seeded sidecar - hint reduced; PR3 reviewer should run with --seeded-map)"
    return hint


def _implementation_map_missing_hint(
    oid: str,
    obligation_result: Mapping[str, Any],
    seeded_entry: Mapping[str, Any] | None,
) -> str:
    return (
        f"Add <implementation_map> entry: obligation_id={oid}; "
        f"artifact={_seeded_value(seeded_entry, 'artifact', 'UNKNOWN')}; "
        f"location={_seeded_value(seeded_entry, 'location_hint', 'UNKNOWN')}; "
        f"treatment={_seeded_value(seeded_entry, 'obligation_type', obligation_result.get('type'))}"
    )


def _missing_incorrect_hint(payload: Mapping[str, Any], claim: Mapping[str, str]) -> str:
    return (
        f"Insert manifest_payload.incorrect ({payload.get('incorrect')!r}) verbatim "
        f"into the activities.yaml entry at {claim.get('location')}"
    )


def _missing_correct_hint(payload: Mapping[str, Any]) -> str:
    return f"Insert manifest_payload.correct ({payload.get('correct')!r}) verbatim"


def _seeded_value(
    seeded_entry: Mapping[str, Any] | None,
    key: str,
    fallback: Any,
) -> Any:
    if seeded_entry is None:
        return fallback
    value = seeded_entry.get(key)
    return value if value not in (None, "") else fallback


def _claim(obligation_result: Mapping[str, Any]) -> dict[str, str]:
    claim = obligation_result.get("claim")
    if not isinstance(claim, Mapping):
        return {}
    return {str(key): str(value) for key, value in claim.items()}


def _public_obligation_result(result: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in result.items() if not str(key).startswith("_")}


def _load_manifest(manifest: Mapping[str, Any] | str | Path) -> Mapping[str, Any]:
    if isinstance(manifest, Mapping):
        return manifest
    # If the string clearly looks like a JSON blob, parse it directly. This
    # avoids passing the entire blob to `Path(...).exists()`, which on macOS
    # APFS raises `OSError: [Errno 63] ENAMETOOLONG` when the would-be
    # filename component exceeds 255 bytes. Linux returns False silently in
    # the same scenario, which is why the bug only surfaced on darwin
    # (2026-05-17 m20 build #12 — first build to reach the wiki_coverage_gate
    # phase via the macOS Dagger-less local path).
    text = str(manifest)
    if text.lstrip().startswith(("{", "[")):
        return json.loads(text)
    try:
        path = Path(manifest)
        if path.exists():
            if path.suffix.casefold() == ".md":
                from scripts.build.phases.wiki_manifest import extract_manifest

                return extract_manifest(path)
            return json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        # Defensive: any path-related OSError (ENAMETOOLONG, ENOENT in
        # an unusual form, EACCES) falls through to the json.loads path.
        pass
    return json.loads(text)


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
        if (
            bool(written)
            and bool(spoken)
            and _contains(target_text, written)
            and _contains(target_text, spoken)
            and _phonetic_examples_present(obligation, target_text)
        ):
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
    evidence_text: str | None = None,
) -> dict[str, Any]:
    obligation_type = str(obligation.get("type") or "")
    result = {
        "obligation_id": obligation.get("id"),
        "type": obligation_type,
        "category": _category_for_obligation_type(obligation_type),
        "status": status,
        "reason": reason,
        "claim": dict(claim or {}),
        "_evidence_text": evidence_text or "",
    }
    if obligation_type == "phonetic_rule":
        written = str(obligation.get("written") or "")
        spoken = str(obligation.get("spoken") or "")
        target_text = evidence_text or ""
        example_pairs = _phonetic_example_pairs(obligation)
        result.update(
            {
                "written": written,
                "spoken_target": spoken,
                "written_present": bool(written) and _contains(target_text, written),
                "spoken_present": bool(spoken) and _contains(target_text, spoken),
                "example_pairs_present": _phonetic_examples_present(obligation, target_text),
                "example_pairs_required": bool(example_pairs),
            }
        )
    return result


def _category_for_obligation_type(obligation_type: str) -> str:
    if obligation_type == "l2_error":
        return "l2_errors"
    if obligation_type == "phonetic_rule":
        return "phonetic_rules"
    if obligation_type == "sequence_step":
        return "sequence_steps"
    if obligation_type == "decolonization_ban":
        return "decolonization_bans"
    return obligation_type


def _contains(text: str, marker: str) -> bool:
    return _normalize(marker) in _normalize(text)


def _phonetic_examples_present(obligation: Mapping[str, Any], text: str) -> bool:
    pairs = _phonetic_example_pairs(obligation)
    if not pairs:
        return True
    return any(all(_contains(text, marker) for marker in pair) for pair in pairs)


def _phonetic_example_pairs(obligation: Mapping[str, Any]) -> list[tuple[str, ...]]:
    pairs: list[tuple[str, ...]] = []
    for key in ("example_pairs", "examples"):
        raw_examples = obligation.get(key) or []
        if not isinstance(raw_examples, Sequence) or isinstance(raw_examples, (str, bytes)):
            continue
        for raw_example in raw_examples:
            if isinstance(raw_example, str):
                example = raw_example.strip()
                if example:
                    pairs.append((example,))
                continue
            if not isinstance(raw_example, Mapping):
                continue
            written = str(
                raw_example.get("written")
                or raw_example.get("word")
                or raw_example.get("surface")
                or raw_example.get("example")
                or ""
            ).strip()
            spoken = str(raw_example.get("spoken") or raw_example.get("ipa") or raw_example.get("pronunciation") or "").strip()
            pair = tuple(marker for marker in (written, spoken) if marker)
            if pair:
                pairs.append(pair)
    return pairs


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
