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
# obligation_id, separated by EITHER `;` (semicolons) OR `|` (pipes).
# Examples (both accepted):
#   - obligation_id: step-2; artifact: module.md; location: §Дiалоги; treatment: ...
#   - obligation_id: step-2 | artifact: module.md | location: §Дiалоги | treatment: ...
# Captures each known field name + its value (up to the next `;`/`|` or end
# of string), regardless of position in the line. Pipe support added 2026-05-21
# after build-#9 a1/my-morning regression: writer-prompt template uses
# `<module.md | activities.yaml | vocabulary.yaml | resources.yaml>` to denote
# alternatives, and the writer copied the `|` pattern as a field separator
# across all four implementation_map fields. Coverage at 0/18 unknown_artifact
# because `artifact = "module.md | location: §... | treatment: ..."` did not
# match any artifact filename.
_INLINE_FIELD_RE = re.compile(
    r"(?P<key>artifact|location|treatment)\s*:\s*"
    r"(?P<value>[^;|]+?)"
    r"(?=\s*[;|]\s*(?:obligation_id|artifact|location|treatment)\s*:|\s*$)",
    re.IGNORECASE,
)
_COMPACT_PIPE_ENTRY_RE = re.compile(
    r"(?:^|\s)(?:\|\s*)?(?P<id>[-\w]+)\s*\|\s*"
    r"(?P<artifact>module\.md|activities\.yaml)\s*\|\s*"
    r"(?P<location>[^|<\n]+?)\s*\|\s*"
    r"(?P<treatment>.*?)(?=\s+(?:\|\s*)?[-\w]+\s*\|\s*(?:module\.md|activities\.yaml)\s*\||\s*$)",
    re.IGNORECASE | re.DOTALL,
)
# XML-attribute row shape: writer (codex-tools in particular) reads the
# `<implementation_map>` XML parent tag as a hint to nest `<row .../>` XML
# elements with quoted attributes. Both formats are present in the wild —
# claude-tools emits markdown bullets, codex-tools emits XML rows. Example:
#
#   <implementation_map>
#   <row obligation_id="ban-1" artifact="module.md" location="§Мій ранок"
#        treatment="No Russian-language explanation appears." />
#   <row obligation_id="step-2" artifact="module.md" location="§Дiалоги"
#        treatment="..." />
#   </implementation_map>
#
# Captures the full attribute body of any self-closing <row .../> tag inside
# an <implementation_map> block. Attribute extraction below pulls the four
# known fields (obligation_id, artifact, location, treatment). Discovered
# 2026-05-26 in m20 round #11 build a1-my-morning-20260526-200639, where
# codex-tools emitted all 18 obligations as <row .../> entries and the gate
# saw `implementation_map_missing` on every one (coverage 0/18) because the
# bullet/pipe parsers don't match the XML-attribute shape.
_ROW_XML_RE = re.compile(
    # Match `<row attr1="val1" attr2="val2" ... />` where values may contain
    # `/` and `>` characters (common in treatment text). The body is captured
    # as a sequence of one-or-more key="value" pairs, NOT as a free-form blob,
    # so the regex stops cleanly at the closing `/>` even when values contain
    # slashes (e.g. `treatment="Я прокидаюся. / Він прокидається."`).
    r"<row\b(?P<attrs>(?:\s+\w+\s*=\s*\"[^\"]*\")+)\s*/\s*>",
    re.IGNORECASE,
)
_ROW_XML_ATTR_RE = re.compile(
    r"(?P<key>obligation_id|artifact|location|treatment)\s*=\s*"
    r"\"(?P<value>[^\"]*)\"",
    re.IGNORECASE | re.DOTALL,
)
_INLINE_IMPLEMENTATION_MAP_XML_RE = re.compile(
    r"<implementation_map\b(?P<attrs>(?:\s+\w+\s*=\s*\"[^\"]*\")+)\s*/\s*>",
    re.IGNORECASE | re.DOTALL,
)
_WORKBOOK_AGGREGATE_ACTIVITY_TYPES = (
    "anagram",
    "authorial-intent",
    "cloze",
    "comparative-study",
    "count-syllables",
    "critical-analysis",
    "debate",
    "dialect-comparison",
    "divide-words",
    "error-correction",
    "essay-response",
    "etymology-trace",
    "fill-in",
    "grammar-identify",
    "group-sort",
    "highlight-morphemes",
    "mark-the-words",
    "match-up",
    "multiple-choice",
    "observe",
    "odd-one-out",
    "order",
    "paleography-analysis",
    "phrase-table",
    "pick-syllables",
    "quiz",
    "reading",
    "source-evaluation",
    "transcription",
    "translate",
    "translation-critique",
    "true-false",
    "unjumble",
)
_WORKBOOK_AGGREGATE_LOCATION_RE = re.compile(
    r"^workbook\b.*\b("
    + "|".join(re.escape(activity_type) for activity_type in _WORKBOOK_AGGREGATE_ACTIVITY_TYPES)
    + r")\b",
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
    entries: dict[str, dict[str, str]] = {}
    for match in matches:
        body = match.group("body")
        for pipe_match in _COMPACT_PIPE_ENTRY_RE.finditer(body):
            obligation_id = pipe_match.group("id").strip()
            entries[obligation_id] = {
                "obligation_id": obligation_id,
                "artifact": pipe_match.group("artifact").strip(),
                "location": pipe_match.group("location").strip(),
                "treatment": pipe_match.group("treatment").strip().rstrip("|").strip(),
            }
        # XML-row shape: `<row obligation_id="..." artifact="..." location="..."
        # treatment="..." />` — extract the attribute block, then pull each
        # known key=value pair out of it. Per-row obligation_id is required;
        # rows without it are silently skipped (matches the bullet/pipe
        # parser's tolerance for malformed lines).
        for row_match in _ROW_XML_RE.finditer(body):
            attrs_text = row_match.group("attrs")
            attrs: dict[str, str] = {}
            for attr_match in _ROW_XML_ATTR_RE.finditer(attrs_text):
                attrs[attr_match.group("key").casefold()] = (
                    attr_match.group("value").strip()
                )
            obligation_id = attrs.get("obligation_id", "").strip()
            if not obligation_id:
                continue
            existing = entries.setdefault(
                obligation_id, {"obligation_id": obligation_id}
            )
            for key in ("artifact", "location", "treatment"):
                value = attrs.get(key)
                if value:
                    existing[key] = value
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
    # During the V7.2 transition, accept both legacy nested-block maps and
    # V7.1 self-closing inline `<implementation_map ... />` tags. Step 6's
    # prompt-generator work will standardize on one canonical shape.
    for inline_map_match in _INLINE_IMPLEMENTATION_MAP_XML_RE.finditer(text):
        attrs_text = inline_map_match.group("attrs")
        attrs: dict[str, str] = {}
        for attr_match in _ROW_XML_ATTR_RE.finditer(attrs_text):
            attrs[attr_match.group("key").casefold()] = attr_match.group(
                "value"
            ).strip()
        obligation_id = attrs.get("obligation_id", "").strip()
        if not obligation_id:
            continue
        existing = entries.setdefault(obligation_id, {"obligation_id": obligation_id})
        for key in ("artifact", "location", "treatment"):
            value = attrs.get(key)
            if value is not None:
                existing[key] = value
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
    seeded_index = _seeded_obligation_index(seeded_map)

    for obligation in validate_obligations(manifest):
        obligation_id = str(obligation.get("id") or "")
        obligation = _enrich_obligation_from_seeded_map(
            obligation,
            seeded_index.get(obligation_id),
        )
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


def _enrich_obligation_from_seeded_map(
    obligation: Mapping[str, Any],
    seeded_entry: Mapping[str, Any] | None,
) -> dict[str, Any]:
    enriched = dict(obligation)
    if enriched.get("subtype") or not seeded_entry:
        return enriched
    subtype = str(seeded_entry.get("subtype") or "")
    if subtype in {"substance_required", "absence_required"}:
        enriched["subtype"] = subtype
    return enriched


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
            f"Add prose implementing the lexical substitution substance in manifest_payload.rule "
            f"({payload.get('rule')!r})"
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


def _flatten_strings(value: Any) -> list[str]:
    """Yield every string value reachable inside a YAML-decoded structure.

    Used by `_activity_text` so that the activity's content reaches the
    marker-match step as plain text. `yaml.safe_dump` would round-trip
    inner apostrophes inside single-quoted YAML strings as `''` (e.g.
    `Вимова: [прокидайес':а]` becomes `Вимова: [прокидайес'':а]`), which
    breaks `_contains` substring matching against the wiki-manifest
    marker. Concatenating raw string fields avoids that escape artifact.
    """

    out: list[str] = []
    stack: list[Any] = [value]
    while stack:
        node = stack.pop()
        if isinstance(node, str):
            out.append(node)
        elif isinstance(node, Mapping):
            stack.extend(node.values())
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes)):
            stack.extend(node)
    return out


def _activity_text(activities: list[dict[str, Any]], location: str) -> str:
    """Resolve a writer's claim ``location`` to flattened activity text.

    Resolution strategies (first match wins):

    1. Empty ``location`` → all activities flattened.
    2. ``location`` equals the bare artifact name ``activities.yaml`` (or
       an explicit ``all``/``any`` marker) → all activities flattened.
       This honours the seeded ``location_hint`` produced by
       ``seed_implementation_map`` for ``activities.yaml``-targeted
       obligations (see ``scripts/build/phases/implementation_map.py::
       _location_hint``: activity-targeted entries are seeded with the
       bare string ``"activities.yaml"``).
    3. An activity's ``id`` appears as a substring of ``location`` —
       canonical handle for **inline** activities targeted by
       ``<!-- INJECT_ACTIVITY: act-N -->`` markers.
    4. An activity's ``title`` overlaps ``location`` (either direction)
       — workbook activities legitimately **omit** ``id`` per
       ``scripts/build/phases/linear-write.md`` L700, so ``title`` is
       the next-most-stable handle when the writer's claim names a
       workbook activity. Codex-tools build-205831 regression: writer
       packed 6 ``err-N`` items into one workbook activity titled
       ``workbook error-correction item 5`` and wrote
       ``location: workbook error-correction item N``. Without title
       fallback, all 6 obligations hard-failed ``claimed_location_missing``
       even though the activity flattens to text containing every
       required contrast pair.
    5. No match → empty string (downstream gate FAILs the obligation
       with ``claimed_location_missing``).

    The flattened-text return is intentionally lenient: the downstream
    ``_check_obligation_text`` substance check validates that the
    required ``expected_error_value``/``expected_correction_value``
    markers are actually present. ``_activity_text``'s job is to give
    that substance check a sufficiently wide search window, not to
    enforce per-item exact-location accounting.
    """

    if not location:
        return "\n".join(s for activity in activities for s in _flatten_strings(activity))

    location_cf = location.casefold().strip()
    if location_cf in {
        "activities.yaml",
        "all",
        "any",
        "(any)",
        "(any activity)",
    } or _WORKBOOK_AGGREGATE_LOCATION_RE.search(location_cf):
        return "\n".join(s for activity in activities for s in _flatten_strings(activity))

    for activity in activities:
        activity_id = str(activity.get("id") or "")
        if activity_id and activity_id in location:
            return "\n".join(_flatten_strings(activity))

    for activity in activities:
        title = str(activity.get("title") or "")
        if not title:
            continue
        title_cf = title.casefold().strip()
        if not title_cf:
            continue
        if title_cf in location_cf or location_cf in title_cf:
            return "\n".join(_flatten_strings(activity))

    # Last-resort: strip a single trailing numeric index off both strings
    # and retry equality. Handles the codex-tools build-205831 pattern
    # where the writer packed 6 ``err-N`` items into ONE workbook activity
    # whose title happened to bake in one row's index (``workbook error-
    # correction item 5``) while every per-row claim location named a
    # different index (``workbook error-correction item 1``..``6``).
    # Pure substring matching can't unify them; stripping the trailing
    # ``\s*\d+\s*$`` from each yields the same stem and the activity (which
    # contains all 6 items as flattened text) covers every per-index claim.
    stripped_location = _TRAILING_INDEX_RE.sub("", location_cf).strip()
    if stripped_location:
        for activity in activities:
            title = str(activity.get("title") or "")
            if not title:
                continue
            stripped_title = _TRAILING_INDEX_RE.sub(
                "", title.casefold().strip()
            ).strip()
            if stripped_title and stripped_title == stripped_location:
                return "\n".join(_flatten_strings(activity))

    return ""


_TRAILING_INDEX_RE = re.compile(r"\s*\d+\s*$")


def _location_text(text: str, location: str) -> str:
    """Return the text of the heading section that best matches `location`.

    A module may legitimately repeat its title as a section heading
    (`# Мій ранок` for the module title and `## Мій ранок` for the
    matching section). Picking the first match in document order returns
    the H1 title-only block (a few lines of intro) instead of the H2
    section. Score candidates by heading depth (deeper = more specific)
    with title-length proximity as a tiebreaker so the deeper match
    wins, but degrade gracefully to the earlier behaviour when only one
    candidate exists.

    Multi-location locations (slash- or comma-joined, e.g. `§Діалоги/§Підсумок`
    or `§Діалоги, §Підсумок`) are treated as a UNION — the obligation is
    satisfied if its substance appears in ANY of the named sections, not
    only the tiebreaker-winner. Returns concatenated section text.
    Discovered 2026-05-27 in m20 round #15 build a1-my-morning-20260527-073054:
    codex's implementation_map row claimed `location="§Діалоги/§Підсумок"`
    for ban-4; the substance was at line 30 in §Діалоги but the title-gap
    tiebreaker picked §Підсумок (no substance) → ban_substance_missing →
    halt with 17/18 wiki coverage when actually 18/18 was achievable.
    """

    if not location or location.casefold() in {"module.md", "whole file", "file"}:
        return text
    parts = [
        part for part in re.split(r"\s*[/,;]\s*", location.strip()) if part.strip()
    ]
    if len(parts) > 1:
        chunks = [_location_text(text, part) for part in parts]
        # Deduplicate: a single section matching multiple location parts
        # (rare but possible if writer repeats themselves) shouldn't get
        # double-counted by substance matchers. Keep insertion order.
        seen: set[int] = set()
        out: list[str] = []
        for chunk in chunks:
            key = id(chunk) if chunk is text else hash(chunk[:200])
            if key in seen:
                continue
            seen.add(key)
            out.append(chunk)
        return "\n".join(out)
    location_key = location.strip().lstrip("#§ ").casefold()
    heading_re = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$", re.MULTILINE)
    headings = list(heading_re.finditer(text))
    candidates: list[tuple[int, int, int]] = []
    for index, heading in enumerate(headings):
        title = heading.group("title").strip().casefold()
        if location_key and location_key not in title and title not in location_key:
            continue
        depth = len(heading.group("marks"))
        title_gap = abs(len(title) - len(location_key))
        # Sort key: deeper first (negate depth), then closer title-length, then
        # earlier in the document — matches author intent that "§Мій ранок ..."
        # refers to the section, not the H1 module title.
        candidates.append((-depth, title_gap, index))

    if candidates:
        candidates.sort()
        chosen_index = candidates[0][2]
        heading = headings[chosen_index]
        start = heading.start()
        # End the section at the next heading whose depth is <= chosen
        # depth (sibling or shallower). Sub-headings (deeper) are
        # structurally INSIDE the chosen section and must stay in
        # `target_text`. Build-#8 a1/my-morning regression: chosen was
        # H2 `## Дієслова на -ся`, next-by-document was H3
        # `### Крок 1: ...`; without depth-aware boundary the returned
        # text was just the 620-char H2 intro, excluding every H3
        # paradigm block that carried the substance terms step-2 needed
        # to match. See `tests/audit/test_wiki_coverage_gate.py::
        # test_sequence_step_h2_section_includes_h3_subsection_content`.
        chosen_depth = len(heading.group("marks"))
        end = len(text)
        for next_idx in range(chosen_index + 1, len(headings)):
            next_depth = len(headings[next_idx].group("marks"))
            if next_depth <= chosen_depth:
                end = headings[next_idx].start()
                break
        return text[start:end]
    if location_key in text.casefold():
        return text
    # No heading match AND location isn't a literal substring of the text.
    # The writer's `location` field is a descriptive hint that doesn't
    # anchor cleanly (e.g. "same :::caution block, bullet 2" — observed
    # 2026-05-22 a1/my-morning build #14 phon-2/phon-3). Degrade
    # gracefully to whole-artifact matching so the obligation-specific
    # substance check below can still validate that the required content
    # is present somewhere in the artifact. The substance check is the
    # actual correctness gate (e.g. phonetic_rule requires both `written`
    # and `spoken` strings to appear in `target_text`); writer drift on
    # the `location` field's prose anchor must not silently fail
    # obligations whose content is genuinely present. If the content is
    # genuinely missing, the substance check will still fail and the
    # obligation will still report FAIL — just with a more accurate reason
    # than `claimed_location_missing` (e.g. `phonetic_rule_missing`).
    return text


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
        normalized_claim = _normalize_required_claim(claim)
        items = _extract_required_items(normalized_claim)

        # If we have extracted items, use item-level coverage.
        if items["vocabulary"] or items["examples"]:
            missing_items = []
            for word in items["vocabulary"]:
                if not _contains(target_text, word):
                    missing_items.append(word)
            for example in items["examples"]:
                if not _contains(target_text, example):
                    missing_items.append(f"«{example}»")

            if not missing_items:
                return "PASS", "sequence_claim_present"
            else:
                return "FAIL", f"sequence_claim_missing: missing {', '.join(missing_items)}"

        # DEPRECATED 2026-05-27: literal Крок N: substring match.
        # Replaced by _extract_required_items + per-item coverage.
        # Remove after one successful Phase 2a refire.
        if _claim_markers_present(claim, target_text):
            return "PASS", "sequence_claim_present"
        return "FAIL", "sequence_claim_missing"

    if obligation_type == "decolonization_ban":
        subtype = str(obligation.get("subtype") or "substance_required")
        if subtype == "substance_required":
            rule = str(obligation.get("rule") or "")
            if _claim_markers_present(rule, target_text):
                return "PASS", "ban_substance_present"
            return "FAIL", "ban_substance_missing"
        # Arbitrary prose prohibitions cannot be affirmatively verified here;
        # concrete violations belong to the russianism/shadow gates.
        return "PASS", "absence_obligation_assumed_satisfied"

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
    if obligation_type == "decolonization_ban" and obligation.get("subtype"):
        result["subtype"] = str(obligation.get("subtype"))
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
    text = text.replace("’", "\'").replace("ʼ", "\'")
    return re.sub(r"\s+", " ", text)


def _strip_step_prefix(text: str) -> str:
    """Strip leading 'Крок N:', 'Step N:', 'Урок N:' scaffolding labels."""
    return re.sub(
        r"^(?:Крок|Step|Урок)\s+\d+:\s*", "", text, flags=re.IGNORECASE
    ).strip()


def _strip_source_markers(text: str) -> str:
    """Strip inline source-reference markers like [S7] or [S1, S3]."""
    return re.sub(r"\[[SС]\d+(?:,\s*[SС]\d+)*\]", "", text).strip()


def _normalize_required_claim(text: str) -> str:
    """Apply both strip helpers, collapse whitespace, return pedagogical content."""
    text = _strip_step_prefix(text)
    text = _strip_source_markers(text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_required_items(claim_text: str) -> dict[str, list[str]]:
    """Extract item-level requirements (vocabulary, examples) from a claim."""
    vocabulary: list[str] = []
    # Vocabulary: find Ukrainian words inside parentheses.
    for match in re.findall(r"\(([^()]+)\)", claim_text):
        for token in match.split(","):
            token = token.strip().strip(" \t\r\n,;:.\"\'")
            if token and re.search(r"[А-Яа-яІіЇїЄєҐґ]", token):
                vocabulary.append(token)

    examples: list[str] = []

    def _add_item(val: str):
        val = val.strip()
        if not val or not re.search(r"[А-Яа-яІіЇїЄєҐґ]", val):
            return
        # If it's a single word, it might be vocabulary.
        if len(val.split()) > 1:
            examples.append(val)
        else:
            vocabulary.append(val)

    # Examples/Vocabulary: find Ukrainian text inside quotes.
    # 1. Guillemets «...»
    for match in re.findall(r"«([^»]+)»", claim_text):
        _add_item(match)
    # 2. Double quotes "..."
    for match in re.findall(r"\"([^\"]+)\"", claim_text):
        _add_item(match)
    # 3. Single quotes '...' (only if they look like quotes, not apostrophes)
    for match in re.findall(r"(?:\s|^)'([^']+)'(?=[\s.,;!?]|$)", claim_text):
        _add_item(match)

    # Deduplicate while preserving order.
    seen_vocab: set[str] = set()
    dedup_vocab = []
    for v in vocabulary:
        if v not in seen_vocab:
            dedup_vocab.append(v)
            seen_vocab.add(v)

    seen_examples: set[str] = set()
    dedup_examples = []
    for e in examples:
        if e not in seen_examples:
            dedup_examples.append(e)
            seen_examples.add(e)

    return {
        "vocabulary": dedup_vocab,
        "examples": dedup_examples,
        "key_phrases": [],  # Substantive content could go here if needed.
    }


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
