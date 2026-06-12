#!/usr/bin/env python3
"""Score one B1 writer output before promoting it into a V7 build.

This is a deterministic preflight for no-Claude writer bakeoffs. It does not
invoke any writer or reviewer. It reads a raw ``writer_output.md`` response,
parses it with the same strict parser used by ``v7_build.py``, then layers
B1 M01-specific workflow checks over the parsed artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit.wiki_coverage_gate import (
    check_wiki_coverage,
    parse_implementation_map,
    validate_obligations,
)
from scripts.build import linear_pipeline
from scripts.build.phases.implementation_map import read_implementation_map
from scripts.yaml_activities import ActivityParser

B1_M01_SLUG = "b1-baseline-past-present"

SOURCE_TOOL_NAMES = frozenset(
    {
        "get_chunk_context",
        "search_text",
        "verify_words",
        "query_pravopys",
        "search_style_guide",
        "check_modern_form",
        "search_heritage",
        "search_slovnyk_me",
        "query_wikipedia",
    }
)

EXPECTED_SECTION_KEYWORDS = (
    ("Теперішній час: дієвідміни", ("теперіш", "дієвідм")),
    ("Минулий час: утворення і вживання", ("минулий",)),
    ("Вид дієслова: доконаний і недоконаний", ("вид", "доконан")),
    ("Вид у розповіді: послідовність і тло", ("послідовн", "тло")),
    ("Дієслова на -ся: зворотні дієслова", ("дієслова на -ся", "зворотн")),
    ("Підсумок: від знання до вживання", ("підсумок",)),
)

PROSE_OBLIGATION_TOKENS = {
    "step-1": ("пишуть", "бачать", "основа"),
    "step-2": ("дієвідміна", "теперіш", "е", "и"),
    "step-3": ("основа інфінітива", "-в", "-л", "переміг"),
    "step-4": ("недоконаний", "доконаний", "читав", "прочитав"),
    "step-5": ("дієприслівник", "читаючи", "сказавши"),
    "step-6": ("дієприкметник", "-вш", "-ший", "-лий"),
}

FORBIDDEN_META_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("uk_this_module", re.compile(r"\b(?:цей|у цьому)\s+модул(?:ь|[ію])\b", re.I)),
    ("uk_this_lesson", re.compile(r"\b(?:цей|у цьому)\s+урок(?:|у|ці)\b", re.I)),
    ("uk_we_will_study", re.compile(r"\bми\s+(?:вивчимо|розглянемо|повторимо)\b", re.I)),
    ("en_this_module", re.compile(r"\bthis\s+module\b", re.I)),
    ("en_this_lesson", re.compile(r"\bthis\s+lesson\b", re.I)),
    ("ai_self_reference", re.compile(r"\bas\s+an\s+ai\b", re.I)),
)

TEACHER_VOICE_MARKERS = (
    "ти",
    "тобі",
    "твій",
    "запам'ятай",
    "пам'ятай",
    "поглянь",
    "порівняй",
    "спробуй",
    "візьми",
    "зверни",
)

EXPLANATION_MARKERS = (
    "тому",
    "бо",
    "саме",
    "логіка",
    "працює",
    "означає",
    "показує",
    "пояснює",
)

DECOLONIZATION_MARKERS = (
    "-вш",
    "-ший",
    "кальк",
    "суржик",
    "посивілий",
    "дівчина, яка",
    "той, що переміг",
)

BAD_FORM_MARKERS = ("<!-- bad -->", "<!-- /bad -->")
_LOOSE_FENCE_RE = re.compile(
    r"(?ms)^(?P<fence>`{3,})(?P<info>[^\n]*)\n(?P<body>.*?)^(?P=fence)\s*$"
)
_UK_WORD_RE = re.compile(r"[А-ЯІЇЄҐа-яіїєґ'ʼ-]+")
_RUSSIAN_SHADOW_TOKENS = ("вш", "ший", "чаюч", "ущ", "ящ")


def _check(
    name: str,
    passed: bool,
    *,
    severity: str = "hard",
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "severity": severity,
        "details": dict(details or {}),
    }


def _hard_failed(checks: Sequence[Mapping[str, Any]]) -> bool:
    return any(
        item.get("severity") == "hard" and item.get("passed") is not True
        for item in checks
    )


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_name_from_info(info: str) -> str | None:
    normalized = info.casefold()
    for name in linear_pipeline.WRITER_ARTIFACTS:
        if name in normalized:
            return name
    return None


def _best_effort_artifacts(raw_output: str) -> dict[str, str]:
    """Extract artifact fences without applying strict writer schemas.

    This keeps scorer output useful for rejected bakeoff artifacts: strict
    parse remains a hard failure, but section/voice/source diagnostics can
    still run when the four fences are present.
    """
    artifacts: dict[str, str] = {}
    for match in _LOOSE_FENCE_RE.finditer(raw_output):
        name = _artifact_name_from_info(match.group("info"))
        if name is None or name in artifacts:
            continue
        body = match.group("body").strip()
        if name == "module.md":
            artifacts[name] = body + "\n"
            continue
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            artifacts[name] = body + "\n"
        else:
            artifacts[name] = yaml.safe_dump(
                parsed,
                allow_unicode=True,
                sort_keys=False,
            )
    return artifacts


def _load_manifest(level: str, slug: str, path: Path | None) -> dict[str, Any]:
    if path and path.exists():
        data = _read_json(path)
        if isinstance(data, dict):
            return data
        raise ValueError(f"wiki manifest must be a JSON object: {path}")
    plan_path = linear_pipeline.plan_path_for(level, slug)
    plan = linear_pipeline.load_plan(plan_path)
    return linear_pipeline.build_wiki_manifest_data(level=level, slug=slug, plan=plan)


def _load_seeded_map(path: Path | None) -> dict[str, Any] | None:
    if not path or not path.exists():
        return None
    data = read_implementation_map(path)
    return dict(data) if isinstance(data, Mapping) else None


def _load_tool_calls(path: Path | None) -> list[dict[str, Any]]:
    if not path or not path.exists():
        return []
    data = _read_json(path)
    if not isinstance(data, list):
        return []
    return [dict(item) for item in data if isinstance(item, Mapping)]


def _yaml_list(text: str, artifact: str) -> list[dict[str, Any]]:
    data = yaml.safe_load(text)
    if not isinstance(data, list):
        raise ValueError(f"{artifact} must be a bare list")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError(f"{artifact} entries must be mappings")
    return data


def _strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _strip_tables(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("|")
    )


def _strip_bad_spans(text: str) -> str:
    return re.sub(
        r"<!--\s*bad\s*-->.*?<!--\s*/bad\s*-->",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )


def _normalize(text: str) -> str:
    lowered = text.casefold().replace("ʼ", "'").replace("’", "'")
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered


def _heading_text(module_md: str) -> list[str]:
    return [
        line.lstrip("#").strip()
        for line in module_md.splitlines()
        if line.startswith("## ")
    ]


def _check_sections(module_md: str, plan: Mapping[str, Any]) -> dict[str, Any]:
    headings = _heading_text(module_md)
    normalized_headings = [_normalize(heading) for heading in headings]
    missing: list[str] = []
    for title, keyword_options in EXPECTED_SECTION_KEYWORDS:
        if not any(
            all(keyword in normalized_heading for keyword in keyword_options)
            for normalized_heading in normalized_headings
        ):
            missing.append(title)

    expected_from_plan = [
        str(item.get("section") or "")
        for item in plan.get("content_outline", [])
        if isinstance(item, Mapping)
    ]
    return {
        "missing": missing,
        "headings": headings,
        "expected_from_plan": expected_from_plan,
    }


def _check_forbidden_voice(module_md: str) -> dict[str, Any]:
    body = _strip_comments(module_md)
    matches: list[dict[str, str]] = []
    for name, pattern in FORBIDDEN_META_PATTERNS:
        for match in pattern.finditer(body):
            matches.append(
                {
                    "pattern": name,
                    "match": match.group(0),
                }
            )
    return {"matches": matches}


def _check_teacher_voice(module_md: str) -> dict[str, Any]:
    prose = _normalize(_strip_comments(module_md))
    teacher_hits = sorted({marker for marker in TEACHER_VOICE_MARKERS if marker in prose})
    explanation_hits = sorted({marker for marker in EXPLANATION_MARKERS if marker in prose})
    english_words = [
        word
        for word in re.findall(r"\b[A-Za-z]{3,}\b", _strip_comments(module_md))
        if word.casefold() not in {"grade", "tip", "note"}
    ]
    bold_or_code_examples = len(re.findall(r"(?:\*\*[^*А-Яа-яІіЇїЄєҐґ]*[А-Яа-яІіЇїЄєҐґ][^*]*\*\*|`[^`]*[А-Яа-яІіЇїЄєҐґ][^`]*`)", module_md))
    passed = (
        len(teacher_hits) >= 3
        and len(explanation_hits) >= 4
        and len(english_words) <= 20
        and bold_or_code_examples >= 12
    )
    return {
        "passed": passed,
        "teacher_markers": teacher_hits,
        "explanation_markers": explanation_hits,
        "english_word_count": len(english_words),
        "english_words_sample": english_words[:10],
        "bold_or_code_uk_examples": bold_or_code_examples,
    }


def _check_implementation_map(raw_output: str, manifest: Mapping[str, Any]) -> dict[str, Any]:
    obligations = validate_obligations(manifest)
    obligation_ids = {
        str(item.get("id") or "")
        for item in obligations
        if str(item.get("id") or "")
    }
    parsed = parse_implementation_map(raw_output)
    parsed_ids = set(parsed)
    missing_from_parsed = sorted(obligation_ids - parsed_ids)
    missing_fields = sorted(
        obligation_id
        for obligation_id, entry in parsed.items()
        if obligation_id in obligation_ids
        and not all(str(entry.get(field) or "").strip() for field in ("artifact", "location", "treatment"))
    )
    audit_match = re.search(
        r"<implementation_map_audit>(?P<body>.*?)</implementation_map_audit>",
        raw_output,
        flags=re.IGNORECASE | re.DOTALL,
    )
    audit_body = audit_match.group("body").strip() if audit_match else ""
    audit_complete = bool(audit_body) and "missing=[]" in audit_body.replace(" ", "")
    return {
        "audit_present": audit_match is not None,
        "audit_complete": audit_complete,
        "audit_body": audit_body,
        "obligation_count": len(obligation_ids),
        "parsed_count": len(parsed_ids & obligation_ids),
        "missing_from_parsed": missing_from_parsed,
        "missing_fields": missing_fields,
    }


def _check_wiki_prose(module_md: str) -> dict[str, Any]:
    prose = _normalize(_strip_tables(_strip_comments(module_md)))
    missing: dict[str, list[str]] = {}
    for obligation_id, tokens in PROSE_OBLIGATION_TOKENS.items():
        absent = [token for token in tokens if token.casefold() not in prose]
        if absent:
            missing[obligation_id] = absent
    return {"missing": missing}


def _check_activity_markers(
    module_md: str,
    activities: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    markers = re.findall(r"<!--\s*INJECT_ACTIVITY:\s*([A-Za-z0-9_-]+)\s*-->", module_md)
    activity_ids = {
        str(item.get("id") or "")
        for item in activities
        if isinstance(item.get("id"), str) and str(item.get("id")).strip()
    }
    missing_ids = sorted(set(markers) - activity_ids)
    duplicate_markers = sorted(
        marker for marker in set(markers) if markers.count(marker) > 1
    )
    return {
        "markers": markers,
        "marker_count": len(markers),
        "activity_ids": sorted(activity_ids),
        "missing_activity_ids": missing_ids,
        "duplicate_markers": duplicate_markers,
    }


def _check_activity_parser(activities_yaml: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="b1-writer-score-") as tmp:
        path = Path(tmp) / "activities.yaml"
        path.write_text(activities_yaml, encoding="utf-8")
        parsed = ActivityParser().parse(path)
    return {"parsed_count": len(parsed)}


def _check_explanations(activities: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing: list[str] = []
    for activity in activities:
        activity_type = str(activity.get("type") or "")
        if activity_type not in {"quiz", "translate"}:
            continue
        activity_id = str(activity.get("id") or activity.get("title") or activity_type)
        items = activity.get("items")
        if not isinstance(items, list):
            missing.append(f"{activity_id}: items missing")
            continue
        for index, item in enumerate(items, start=1):
            if not isinstance(item, Mapping):
                missing.append(f"{activity_id}[{index}]: item not mapping")
                continue
            explanation = str(item.get("explanation") or "").strip()
            if not explanation:
                missing.append(f"{activity_id}[{index}]")
    return {"missing": missing}


def _extract_resource_chunk(resource: Mapping[str, Any]) -> str:
    for field in ("packet_chunk_id", "chunk_id", "source_ref", "notes", "description"):
        value = resource.get(field)
        if isinstance(value, str):
            match = re.search(r"\b[\w-]+_s\d+\b", value)
            if match:
                return match.group(0)
    return ""


def _check_resources(
    resources: Sequence[Mapping[str, Any]],
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    expected_count = len(plan.get("references") or [])
    textbook_resources = [
        item for item in resources if str(item.get("role") or "") == "textbook"
    ]
    textbook_without_chunk = [
        str(item.get("title") or f"resource-{index}")
        for index, item in enumerate(textbook_resources, start=1)
        if not _extract_resource_chunk(item)
    ]
    invalid_roles = sorted(
        {
            str(item.get("role") or "")
            for item in resources
            if str(item.get("role") or "") not in linear_pipeline.RESOURCE_ROLES
        }
    )
    chunks = sorted(
        {
            chunk
            for item in textbook_resources
            for chunk in [_extract_resource_chunk(item)]
            if chunk
        }
    )
    return {
        "count": len(resources),
        "expected_min_count": expected_count,
        "textbook_count": len(textbook_resources),
        "textbook_chunk_ids": chunks,
        "textbook_without_chunk": textbook_without_chunk,
        "invalid_roles": invalid_roles,
    }


def _check_verify_comments(module_md: str) -> dict[str, Any]:
    comments = re.findall(r"<!--\s*VERIFY:\s*(.*?)-->", module_md, flags=re.DOTALL)
    weak = [
        comment.strip()[:120]
        for comment in comments
        if "source=" not in comment and "chunk=" not in comment and "chunk_id" not in comment
    ]
    return {"count": len(comments), "weak": weak}


def _check_bad_forms(module_md: str, manifest: Mapping[str, Any]) -> dict[str, Any]:
    open_count = module_md.count(BAD_FORM_MARKERS[0])
    close_count = module_md.count(BAD_FORM_MARKERS[1])
    unmarked_text = _strip_bad_spans(module_md)
    l2_errors = manifest.get("l2_errors") or []
    bare_incorrect: list[str] = []
    shadow_candidates: set[str] = set()
    if isinstance(l2_errors, Sequence):
        for item in l2_errors:
            if not isinstance(item, Mapping):
                continue
            incorrect = str(item.get("incorrect") or "").strip()
            if incorrect and incorrect in unmarked_text:
                bare_incorrect.append(incorrect)
            for word in _UK_WORD_RE.findall(incorrect):
                folded = word.casefold()
                if any(token in folded for token in _RUSSIAN_SHADOW_TOKENS):
                    shadow_candidates.add(word)
    shadow_candidates.update(
        re.findall(
            r"\b[А-ЯІЇЄҐа-яіїєґ'ʼ-]+вш(?:ий|а|е|і|ого|ому|им|их|ими)\b",
            unmarked_text,
            flags=re.I,
        )
    )
    bare_shadow_forms = [
        word
        for word in sorted(shadow_candidates, key=str.casefold)
        if re.search(rf"\b{re.escape(word)}\b", unmarked_text, flags=re.I)
    ]
    return {
        "bad_open": open_count,
        "bad_close": close_count,
        "bare_incorrect": bare_incorrect,
        "bare_shadow_forms": sorted(set(bare_shadow_forms)),
    }


def _check_source_tool_evidence(
    raw_output: str,
    tool_calls: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    def normalized_tool_name(item: Mapping[str, Any]) -> str:
        raw_name = str(item.get("tool") or item.get("name") or "")
        return (
            raw_name.removeprefix("mcp__sources__")
            .removeprefix("mcp_sources_")
            .removeprefix("sources__")
        )

    telemetry_tools = sorted(
        {
            normalized_tool_name(item)
            for item in tool_calls
            if normalized_tool_name(item) in SOURCE_TOOL_NAMES
        }
    )
    raw_mentions = sorted(
        tool
        for tool in SOURCE_TOOL_NAMES
        if re.search(rf"\b(?:mcp_sources_)?{re.escape(tool)}\b", raw_output)
    )
    verify_word_calls = sum(
        1 for item in tool_calls if normalized_tool_name(item) == "verify_words"
    )
    return {
        "telemetry_tools": telemetry_tools,
        "raw_trace_tools": raw_mentions,
        "verify_words_telemetry_calls": verify_word_calls,
    }


def _check_decolonization(module_md: str) -> dict[str, Any]:
    prose = _normalize(_strip_comments(module_md))
    present = sorted({marker for marker in DECOLONIZATION_MARKERS if marker in prose})
    return {"present_markers": present}


def _artifact_report(
    raw_output: str,
    *,
    level: str,
    slug: str,
    candidate_dir: Path | None,
    wiki_manifest_path: Path | None,
    implementation_map_path: Path | None,
    tool_calls_path: Path | None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    plan_path = linear_pipeline.plan_path_for(level, slug)
    plan = linear_pipeline.load_plan(plan_path)
    manifest = _load_manifest(level, slug, wiki_manifest_path)
    seeded_map = _load_seeded_map(implementation_map_path)
    tool_calls = _load_tool_calls(tool_calls_path)

    try:
        artifacts = linear_pipeline.parse_writer_output(raw_output)
    except Exception as exc:
        checks.append(
            _check(
                "parse_writer_output",
                False,
                details={"error": str(exc)},
            )
        )
        artifacts = _best_effort_artifacts(raw_output)
        best_effort_missing = [
            name for name in linear_pipeline.WRITER_ARTIFACTS if name not in artifacts
        ]
        checks.append(
            _check(
                "best_effort_artifacts_present",
                not best_effort_missing,
                severity="advisory",
                details={"missing": best_effort_missing},
            )
        )
        if best_effort_missing:
            hard_failures = [
                str(item["name"])
                for item in checks
                if item.get("severity") == "hard" and item.get("passed") is not True
            ]
            return {
                "level": level,
                "slug": slug,
                "candidate_dir": str(candidate_dir) if candidate_dir else None,
                "summary": {
                    "passed": False,
                    "hard_failures": hard_failures,
                    "checks_total": len(checks),
                },
                "checks": checks,
            }
    else:
        checks.append(_check("parse_writer_output", True))
    missing = [name for name in linear_pipeline.WRITER_ARTIFACTS if name not in artifacts]
    checks.append(_check("artifacts_present", not missing, details={"missing": missing}))

    parsed_yaml: dict[str, list[dict[str, Any]]] = {}
    yaml_errors: dict[str, str] = {}
    for artifact_name in ("activities.yaml", "vocabulary.yaml", "resources.yaml"):
        try:
            parsed_yaml[artifact_name] = _yaml_list(
                artifacts[artifact_name],
                artifact_name,
            )
        except Exception as exc:
            yaml_errors[artifact_name] = str(exc)
    activities = parsed_yaml.get("activities.yaml", [])
    vocabulary = parsed_yaml.get("vocabulary.yaml", [])
    resources = parsed_yaml.get("resources.yaml", [])
    checks.append(
        _check(
            "artifact_yaml_shape",
            not yaml_errors,
            details={
                "errors": yaml_errors,
                "activities": len(activities),
                "vocabulary": len(vocabulary),
                "resources": len(resources),
            },
        )
    )

    module_md = artifacts["module.md"]
    section_details = _check_sections(module_md, plan)
    checks.append(
        _check(
            "expected_b1_m01_sections",
            not section_details["missing"],
            details=section_details,
        )
    )

    word_report = linear_pipeline._word_count_gate(
        module_md,
        int(plan["word_target"]),
    )
    checks.append(_check("b1_body_word_floor", word_report["passed"], details=word_report))

    forbidden_voice = _check_forbidden_voice(module_md)
    checks.append(
        _check(
            "forbidden_meta_voice",
            not forbidden_voice["matches"],
            details=forbidden_voice,
        )
    )

    teacher_voice = _check_teacher_voice(module_md)
    checks.append(
        _check(
            "anna_ohoiko_style_teacher_voice",
            teacher_voice.pop("passed"),
            details=teacher_voice,
        )
    )

    map_report = _check_implementation_map(raw_output, manifest)
    map_passed = (
        map_report["audit_present"]
        and map_report["audit_complete"]
        and map_report["parsed_count"] == map_report["obligation_count"]
        and not map_report["missing_from_parsed"]
        and not map_report["missing_fields"]
    )
    checks.append(
        _check(
            "implementation_map_audit",
            map_passed,
            details=map_report,
        )
    )

    try:
        wiki_report = check_wiki_coverage(
            manifest=manifest,
            implementation_map=raw_output,
            module_md=module_md,
            activities_yaml=artifacts["activities.yaml"],
            vocabulary_yaml=artifacts["vocabulary.yaml"],
            resources_yaml=artifacts["resources.yaml"],
            level=level,
            seeded_map=seeded_map,
        )
    except Exception as exc:
        checks.append(
            _check("wiki_coverage_gate", False, details={"error": str(exc)})
        )
    else:
        checks.append(
            _check(
                "wiki_coverage_gate",
                bool(wiki_report.get("passed")),
                details={
                    "covered": wiki_report.get("covered"),
                    "total": wiki_report.get("total"),
                    "coverage_pct": wiki_report.get("coverage_pct"),
                    "hard_fail": wiki_report.get("hard_fail"),
                    "failed_obligations": [
                        {
                            "id": item.get("obligation_id"),
                            "reason": item.get("reason"),
                        }
                        for item in wiki_report.get("obligations", [])
                        if item.get("status") == "FAIL"
                    ][:12],
                },
            )
        )

    prose_report = _check_wiki_prose(module_md)
    checks.append(
        _check(
            "wiki_obligations_in_prose",
            not prose_report["missing"],
            details=prose_report,
        )
    )

    try:
        parser_report = _check_activity_parser(artifacts["activities.yaml"])
    except Exception as exc:
        checks.append(
            _check("activity_parser_schema", False, details={"error": str(exc)})
        )
    else:
        checks.append(_check("activity_parser_schema", True, details=parser_report))

    marker_report = _check_activity_markers(module_md, activities)
    marker_passed = (
        5 <= marker_report["marker_count"] <= 7
        and not marker_report["missing_activity_ids"]
        and not marker_report["duplicate_markers"]
    )
    checks.append(
        _check("inline_activity_markers", marker_passed, details=marker_report)
    )

    explanation_report = _check_explanations(activities)
    checks.append(
        _check(
            "quiz_translate_explanations",
            not explanation_report["missing"],
            details=explanation_report,
        )
    )

    resource_report = _check_resources(resources, plan)
    resource_passed = (
        resource_report["count"] >= resource_report["expected_min_count"]
        and resource_report["textbook_count"] >= resource_report["expected_min_count"]
        and not resource_report["textbook_without_chunk"]
        and not resource_report["invalid_roles"]
    )
    checks.append(_check("resources_source_honesty", resource_passed, details=resource_report))

    verify_report = _check_verify_comments(module_md)
    verify_passed = verify_report["count"] >= len(EXPECTED_SECTION_KEYWORDS) and not verify_report["weak"]
    checks.append(_check("verify_source_comments", verify_passed, details=verify_report))

    bad_form_report = _check_bad_forms(module_md, manifest)
    bad_form_passed = (
        bad_form_report["bad_open"] == bad_form_report["bad_close"]
        and not bad_form_report["bare_incorrect"]
        and not bad_form_report["bare_shadow_forms"]
    )
    checks.append(_check("bad_form_marker_discipline", bad_form_passed, details=bad_form_report))

    tool_report = _check_source_tool_evidence(raw_output, tool_calls)
    tool_passed = (
        "verify_words" in tool_report["telemetry_tools"]
        or "verify_words" in tool_report["raw_trace_tools"]
    )
    checks.append(_check("vesum_word_verification_evidence", tool_passed, details=tool_report))

    decolonization_report = _check_decolonization(module_md)
    checks.append(
        _check(
            "decolonization_russianism_discipline",
            len(decolonization_report["present_markers"]) >= 4,
            details=decolonization_report,
        )
    )

    hard_failures = [
        str(item["name"])
        for item in checks
        if item.get("severity") == "hard" and item.get("passed") is not True
    ]
    return {
        "level": level,
        "slug": slug,
        "candidate_dir": str(candidate_dir) if candidate_dir else None,
        "summary": {
            "passed": not _hard_failed(checks),
            "hard_failures": hard_failures,
            "checks_total": len(checks),
        },
        "checks": checks,
    }


def score_writer_output(
    *,
    level: str,
    slug: str,
    writer_output_path: Path,
    candidate_dir: Path | None = None,
    wiki_manifest_path: Path | None = None,
    implementation_map_path: Path | None = None,
    tool_calls_path: Path | None = None,
) -> dict[str, Any]:
    raw_output = writer_output_path.read_text(encoding="utf-8")
    return _artifact_report(
        raw_output,
        level=level.lower(),
        slug=slug,
        candidate_dir=candidate_dir,
        wiki_manifest_path=wiki_manifest_path,
        implementation_map_path=implementation_map_path,
        tool_calls_path=tool_calls_path,
    )


def _defaulted_path(candidate_dir: Path | None, filename: str) -> Path | None:
    if candidate_dir is None:
        return None
    path = candidate_dir / filename
    return path if path.exists() else None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", default="b1")
    parser.add_argument("--slug", default=B1_M01_SLUG)
    parser.add_argument("--writer-output", type=Path, default=None)
    parser.add_argument("--candidate-dir", type=Path, default=None)
    parser.add_argument("--wiki-manifest", type=Path, default=None)
    parser.add_argument("--implementation-map", type=Path, default=None)
    parser.add_argument("--tool-calls", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    candidate_dir = args.candidate_dir.resolve() if args.candidate_dir else None
    writer_output = args.writer_output
    if writer_output is None:
        writer_output = _defaulted_path(candidate_dir, "writer_output.md")
    if writer_output is None:
        parser.error("provide --writer-output or --candidate-dir containing writer_output.md")
    writer_output = writer_output.resolve()

    report = score_writer_output(
        level=args.level,
        slug=args.slug,
        writer_output_path=writer_output,
        candidate_dir=candidate_dir,
        wiki_manifest_path=args.wiki_manifest or _defaulted_path(candidate_dir, "wiki_manifest.json"),
        implementation_map_path=args.implementation_map
        or _defaulted_path(candidate_dir, "implementation_map.json"),
        tool_calls_path=args.tool_calls or _defaulted_path(candidate_dir, "writer_tool_calls.json"),
    )
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if report["summary"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
