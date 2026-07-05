"""Canonical quality-gate evidence schema helpers for the UA eval harness.

The schema in this module is additive. It does not migrate existing
``curriculum_ua_qg_evidence.v1`` or ``llm_qg_evidence.v1`` payloads; those stay
valid as projection profiles while new calque, grammar, and LLM-review adapters
normalize their findings into this shared shape.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "ua_contact_quality_evidence.v1"
LEGACY_EVIDENCE_SCHEMA_VERSIONS = frozenset(
    {
        "curriculum_ua_qg_evidence.v1",
        "llm_qg_evidence.v1",
    }
)

PROFILES = frozenset(
    {
        "curriculum_deterministic",
        "curriculum_llm_compact",
        "ua_gec_eval",
        "leaderboard",
    }
)
EVIDENCE_KINDS = frozenset({"module", "fixture", "eval_item"})
VERDICTS = frozenset({"PASS", "WARN", "FAIL"})
SOURCE_LANGS = frozenset({"ru", "pl", "en", "unknown", "other"})
TRACK_L1S = frozenset({"uk", "en", "pl", "ru", "unknown", "other"})
ISSUE_CLASSES = frozenset(
    {
        "calque",
        "grammar",
        "collocation",
        "false_friend",
        "register",
        "leakage",
        "pedagogy",
        "fluency",
        "mechanics",
        "other",
    }
)
DIMENSIONS = frozenset(
    {
        "contact_calque",
        "contact_grammar",
        "ukrainian_style",
        "level_policy",
        "surface_leakage",
        "naturalness",
        "pedagogical",
        "decolonization",
        "engagement",
        "tone",
        "seminar_sensitivity",
        "mechanics",
    }
)
SEVERITIES = frozenset({"critical", "warning", "info"})
CONFIDENCE_LEVELS = frozenset({"deterministic", "lookup_heuristic", "llm_judgment"})
DISPOSITIONS = frozenset(
    {
        "defect",
        "teaching_contrast",
        "quoted_bad_form",
        "heritage_allowed",
        "suppressed_fp",
    }
)
FACT_CHECK_VERDICTS = frozenset(
    {
        "CONFIRMED",
        "REFUTED_BY_CONTRADICTION",
        "UNATTESTED_AFTER_SEARCH",
        "CONTESTED",
        "UNVERIFIED_INSUFFICIENT_SEARCH",
    }
)
MAX_REVIEWER_FACT_CHECKS = 40
GROUNDING_REQUIRED_DIMENSIONS = frozenset({"seminar_sensitivity", "decolonization"})
GROUNDING_REQUIRED_SEMINAR_CLASSES = frozenset({"calque", "false_friend"})
GROUNDING_KEYS = frozenset({"tool", "query", "evidence_excerpt", "tool_call_id"})

DEFAULT_ATTRIBUTION = {
    "corpus": None,
    "license": None,
    "doc_id": None,
    "pair_id": None,
    "evidence": None,
}


@dataclass(frozen=True, slots=True)
class UaGecTagMapping:
    """Canonical mapping from one UA-GEC tag family to harness fields."""

    tag: str
    issue_id: str
    issue_class: str
    dimension: str
    severity: str
    default_source_lang: str

    def asdict(self) -> dict[str, str]:
        return {
            "tag": self.tag,
            "issue_id": self.issue_id,
            "issue_class": self.issue_class,
            "dimension": self.dimension,
            "severity": self.severity,
            "default_source_lang": self.default_source_lang,
        }


UA_GEC_TAG_MAPPINGS: dict[str, UaGecTagMapping] = {
    "F/Calque": UaGecTagMapping(
        tag="F/Calque",
        issue_id="CONTACT_CALQUE_UA_GEC",
        issue_class="calque",
        dimension="contact_calque",
        severity="info",
        default_source_lang="ru",
    ),
    "F/Collocation": UaGecTagMapping(
        tag="F/Collocation",
        issue_id="UNNATURAL_COLLOCATION",
        issue_class="collocation",
        dimension="contact_calque",
        severity="warning",
        default_source_lang="ru",
    ),
    "G/Case": UaGecTagMapping(
        tag="G/Case",
        issue_id="UKRAINIAN_GRAMMAR_CASE",
        issue_class="grammar",
        dimension="contact_grammar",
        severity="warning",
        default_source_lang="ru",
    ),
    "G/Gender": UaGecTagMapping(
        tag="G/Gender",
        issue_id="UKRAINIAN_GRAMMAR_GENDER",
        issue_class="grammar",
        dimension="contact_grammar",
        severity="warning",
        default_source_lang="ru",
    ),
}
UA_GEC_SUPPORTED_TAGS = frozenset(UA_GEC_TAG_MAPPINGS)

_SOURCE_LANG_ALIASES = {
    "": "unknown",
    "russian": "ru",
    "rus": "ru",
    "ru": "ru",
    "polish": "pl",
    "pol": "pl",
    "pl": "pl",
    "english": "en",
    "eng": "en",
    "en": "en",
    "unknown": "unknown",
    "unk": "unknown",
    "other": "other",
}


def _stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_hash(value: object) -> str:
    """Return a stable SHA-256 hex digest for schema ids and config hashes."""
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def normalize_source_lang(value: str | None, *, default: str = "unknown") -> str:
    """Normalize a source/contact language code into the schema enum."""
    raw = (value if value is not None else default).strip().lower()
    normalized = _SOURCE_LANG_ALIASES.get(raw, raw)
    if normalized not in SOURCE_LANGS:
        raise ValueError(f"unsupported contact source language: {value!r}")
    return normalized


def normalize_track_l1(value: str | None, *, default: str = "unknown") -> str:
    """Normalize the learner track L1 separately from the contact-error source."""
    raw = (value if value is not None else default).strip().lower()
    normalized = _SOURCE_LANG_ALIASES.get(raw, raw)
    if normalized not in TRACK_L1S:
        raise ValueError(f"unsupported track L1: {value!r}")
    return normalized


def map_ua_gec_tag(tag: str, *, source_lang: str | None = None) -> dict[str, str]:
    """Map a UA-GEC tag into the canonical finding fields.

    ``source_lang`` here means the contact source of the error. When UA-GEC does
    not provide a useful value, the high-signal F/G tags default to Russian
    because #2156 prioritizes Russian-contact harm first.
    """
    if tag in UA_GEC_TAG_MAPPINGS:
        mapping = UA_GEC_TAG_MAPPINGS[tag]
        out = mapping.asdict()
        out["source_lang"] = normalize_source_lang(source_lang, default=mapping.default_source_lang)
        out["contact_source_lang"] = out["source_lang"]
        return out

    if tag.startswith("G/"):
        source = normalize_source_lang(source_lang, default="ru")
        return {
            "tag": tag,
            "issue_id": "UKRAINIAN_GRAMMAR_UA_GEC",
            "issue_class": "grammar",
            "dimension": "contact_grammar",
            "severity": "warning",
            "default_source_lang": "ru",
            "source_lang": source,
            "contact_source_lang": source,
        }
    if tag.startswith("F/"):
        source = normalize_source_lang(source_lang, default="unknown")
        return {
            "tag": tag,
            "issue_id": "UA_GEC_FLUENCY_OTHER",
            "issue_class": "fluency",
            "dimension": "naturalness",
            "severity": "info",
            "default_source_lang": "unknown",
            "source_lang": source,
            "contact_source_lang": source,
        }
    raise ValueError(f"unsupported UA-GEC tag: {tag!r}")


def make_span(start: int | None, end: int | None) -> dict[str, int | None]:
    """Return a normalized span object and validate ordering when both ends exist."""
    if start is not None and not isinstance(start, int):
        raise ValueError("span start must be an integer or None")
    if end is not None and not isinstance(end, int):
        raise ValueError("span end must be an integer or None")
    if start is not None and start < 0:
        raise ValueError("span start must be non-negative")
    if end is not None and end < 0:
        raise ValueError("span end must be non-negative")
    if start is not None and end is not None and end < start:
        raise ValueError("span end must be greater than or equal to start")
    return {"start": start, "end": end}


def make_finding_id(finding: Mapping[str, Any]) -> str:
    """Build a stable finding id from locator and issue fields."""
    detector = finding.get("detector")
    detector_id = None
    if isinstance(detector, Mapping):
        detector_id = detector.get("rule_id") or detector.get("pattern_id") or detector.get("adapter")
    payload = {
        "issue_id": finding.get("issue_id"),
        "file": finding.get("file"),
        "line": finding.get("line"),
        "span": finding.get("span"),
        "excerpt": finding.get("excerpt"),
        "detector": detector_id,
    }
    return stable_hash(payload)[:24]


def build_finding(
    *,
    issue_id: str,
    issue_class: str,
    dimension: str,
    severity: str,
    file: str,
    line: int | None,
    span: Mapping[str, int | None] | None,
    excerpt: str,
    message: str,
    contact_source_lang: str | None = None,
    source_lang: str | None = None,
    track_l1: str | None = "en",
    ua_gec_tag: str | None = None,
    confidence: str = "deterministic",
    disposition: str = "defect",
    suggested_replacement: str | Sequence[str] | None = None,
    detector: Mapping[str, Any] | None = None,
    attribution: Mapping[str, Any] | None = None,
    grounding: Mapping[str, Any] | None = None,
    sense_context: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build and validate one canonical finding."""
    normalized_source = normalize_source_lang(contact_source_lang or source_lang)
    normalized_span = dict(span) if span is not None else make_span(None, None)
    replacement: list[str] = []
    if isinstance(suggested_replacement, str):
        replacement = [suggested_replacement]
    elif suggested_replacement:
        replacement = [str(item) for item in suggested_replacement]

    finding: dict[str, Any] = {
        "issue_id": issue_id,
        "issue_class": issue_class,
        "dimension": dimension,
        "severity": severity,
        "contact_source_lang": normalized_source,
        "source_lang": normalized_source,
        "track_l1": normalize_track_l1(track_l1),
        "ua_gec_tag": ua_gec_tag,
        "confidence": confidence,
        "disposition": disposition,
        "file": file,
        "line": line,
        "span": normalized_span,
        "excerpt": excerpt[:160],
        "message": message,
        "suggested_replacement": replacement,
        "detector": dict(detector or {}),
        "attribution": {**DEFAULT_ATTRIBUTION, **dict(attribution or {})},
    }
    if sense_context:
        finding["sense_context"] = dict(sense_context)
    if metadata:
        finding["metadata"] = dict(metadata)
    if grounding:
        finding["grounding"] = dict(grounding)
    finding["finding_id"] = make_finding_id(finding)
    validate_finding(finding)
    return finding


def build_deterministic_curriculum_finding(
    *,
    issue_id: str,
    rule_id: str,
    dimension: str,
    severity: str,
    file: str,
    line: int,
    span: Mapping[str, int | None],
    excerpt: str,
    message: str,
    contact_source_lang: str | None = "unknown",
    suggested_replacement: str | Sequence[str] | None = None,
) -> dict[str, Any]:
    """Build a curriculum deterministic finding such as the B1-27 canaries."""
    return build_finding(
        issue_id=issue_id,
        issue_class="calque" if "CALQUE" in issue_id or "PASSIVE" in issue_id else "register",
        dimension=dimension,
        severity=severity,
        file=file,
        line=line,
        span=span,
        excerpt=excerpt,
        message=message,
        contact_source_lang=contact_source_lang,
        confidence="deterministic",
        suggested_replacement=suggested_replacement,
        detector={
            "adapter": "curriculum_qg_harness",
            "rule_id": rule_id,
            "pattern_id": rule_id,
        },
        attribution={
            "corpus": "curriculum_phrase_rules",
            "license": None,
            "evidence": "B1-27 calibration fixture",
        },
    )


def build_ua_gec_finding(
    *,
    error: str,
    correction: str,
    tag: str,
    file: str,
    line: int | None,
    span: Mapping[str, int | None] | None,
    source_lang: str | None = None,
    doc_id: str | None = None,
    pair_id: str | None = None,
    frequency: int | None = None,
    severity: str | None = None,
    message: str | None = None,
    adapter: str = "ua_gec_lookup",
) -> dict[str, Any]:
    """Build a canonical finding from one UA-GEC error/correction pair."""
    mapped = map_ua_gec_tag(tag, source_lang=source_lang)
    effective_severity = severity or mapped["severity"]
    if effective_severity not in SEVERITIES:
        raise ValueError(f"unsupported severity: {effective_severity!r}")
    frequency_note = f" (frequency {frequency})" if frequency is not None else ""
    default_message = f"UA-GEC {tag} pair: {error} -> {correction}{frequency_note}."
    return build_finding(
        issue_id=mapped["issue_id"],
        issue_class=mapped["issue_class"],
        dimension=mapped["dimension"],
        severity=effective_severity,
        file=file,
        line=line,
        span=span,
        excerpt=error,
        message=message or default_message,
        contact_source_lang=mapped["contact_source_lang"],
        ua_gec_tag=tag,
        confidence="lookup_heuristic",
        suggested_replacement=correction,
        detector={
            "adapter": adapter,
            "rule_id": tag,
            "pattern_id": pair_id or doc_id or error,
        },
        attribution={
            "corpus": "UA-GEC v2",
            "license": "CC-BY-4.0",
            "doc_id": doc_id,
            "pair_id": pair_id,
            "evidence": "Syvokon et al., UNLP 2023",
        },
        metadata={
            "ua_gec": {
                "error": error,
                "correction": correction,
                "tag": tag,
                "frequency": frequency,
            }
        },
    )


def build_semantic_false_friend_finding(
    *,
    word: str,
    russian_meaning: str,
    ukrainian_meaning: str,
    replacement: str | None,
    matched_gloss_pattern: str,
    file: str,
    line: int | None,
    span: Mapping[str, int | None] | None,
    excerpt: str,
    severity: str = "critical",
) -> dict[str, Any]:
    """Build the #912 semantic false-friend finding shape."""
    suggested = [replacement] if replacement else []
    return build_finding(
        issue_id="SEMANTIC_FALSE_FRIEND",
        issue_class="false_friend",
        dimension="contact_calque",
        severity=severity,
        file=file,
        line=line,
        span=span,
        excerpt=excerpt,
        message=(
            f"{word!r} is valid Ukrainian as {ukrainian_meaning!r}, "
            f"but this gloss uses the Russian meaning {russian_meaning!r}."
        ),
        contact_source_lang="ru",
        ua_gec_tag=None,
        confidence="deterministic",
        suggested_replacement=suggested,
        detector={
            "adapter": "semantic_false_friends",
            "rule_id": "SEMANTIC_FALSE_FRIEND",
            "pattern_id": word,
        },
        attribution={
            "corpus": "scripts.pipeline.semantic_russianisms",
            "license": None,
            "evidence": "Issue #912 semantic false-friend list",
        },
        sense_context={
            "word": word,
            "calque_sense": russian_meaning,
            "authentic_sense": ukrainian_meaning,
            "matched_gloss_pattern": matched_gloss_pattern,
        },
    )


def build_dimension(
    *,
    verdict: str,
    findings: Iterable[Mapping[str, Any]],
    score: float | None = None,
) -> dict[str, Any]:
    """Build a dimension record with nested canonical findings."""
    if verdict not in VERDICTS:
        raise ValueError(f"unsupported verdict: {verdict!r}")
    finding_list = [dict(item) for item in findings]
    for item in finding_list:
        validate_finding(item)
    out: dict[str, Any] = {"score": score, "verdict": verdict, "findings": finding_list}
    return out


def build_evidence_record(
    *,
    profile: str,
    evidence_kind: str,
    module_id: str | None = None,
    eval_item_id: str | None = None,
    fixture_id: str | None = None,
    level_policy: Mapping[str, Any] | None = None,
    dimensions: Mapping[str, Mapping[str, Any]] | None = None,
    checker_runs: Sequence[Mapping[str, Any]] | None = None,
    content_sha: str | None = None,
    provenance: Mapping[str, Any] | None = None,
    verdict: str = "PASS",
    terminal_verdict: str = "PASS",
    aggregate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build and validate one canonical evidence record."""
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "profile": profile,
        "evidence_kind": evidence_kind,
        "module_id": module_id,
        "eval_item_id": eval_item_id,
        "fixture_id": fixture_id,
        "level_policy": dict(level_policy or {}),
        "content_sha": content_sha,
        "verdict": verdict,
        "terminal_verdict": terminal_verdict,
        "aggregate": dict(aggregate or {}),
        "dimensions": {key: dict(value) for key, value in (dimensions or {}).items()},
        "checker_runs": [dict(run) for run in (checker_runs or [])],
        "provenance": dict(provenance or {}),
        "compatibility": {
            "legacy_projection_versions": sorted(LEGACY_EVIDENCE_SCHEMA_VERSIONS),
            "migration_required": False,
        },
    }
    validate_record(record)
    return record


def validate_finding(finding: Mapping[str, Any]) -> None:
    """Validate a canonical finding and raise ``ValueError`` on mismatch."""
    required = {
        "finding_id",
        "issue_id",
        "issue_class",
        "dimension",
        "severity",
        "contact_source_lang",
        "source_lang",
        "track_l1",
        "confidence",
        "disposition",
        "file",
        "line",
        "span",
        "excerpt",
        "message",
        "detector",
        "attribution",
    }
    missing = sorted(key for key in required if key not in finding)
    if missing:
        raise ValueError(f"finding missing required fields: {', '.join(missing)}")
    _require_member("issue_class", finding["issue_class"], ISSUE_CLASSES)
    _require_member("dimension", finding["dimension"], DIMENSIONS)
    _require_member("severity", finding["severity"], SEVERITIES)
    _require_member("contact_source_lang", finding["contact_source_lang"], SOURCE_LANGS)
    _require_member("source_lang", finding["source_lang"], SOURCE_LANGS)
    _require_member("track_l1", finding["track_l1"], TRACK_L1S)
    _require_member("confidence", finding["confidence"], CONFIDENCE_LEVELS)
    _require_member("disposition", finding["disposition"], DISPOSITIONS)

    span = finding["span"]
    if not isinstance(span, Mapping):
        raise ValueError("span must be a mapping")
    make_span(span.get("start"), span.get("end"))
    if not str(finding["issue_id"]).strip():
        raise ValueError("issue_id must be non-empty")
    if not str(finding["file"]).strip():
        raise ValueError("file must be non-empty")
    line = finding["line"]
    if line is not None and (not isinstance(line, int) or line < 1):
        raise ValueError("line must be a positive integer or None")
    if not str(finding["excerpt"]).strip():
        raise ValueError("excerpt must be non-empty")
    if len(str(finding["excerpt"])) > 160:
        raise ValueError("excerpt must be bounded to 160 characters")
    if not isinstance(finding["detector"], Mapping):
        raise ValueError("detector must be a mapping")
    if not isinstance(finding["attribution"], Mapping):
        raise ValueError("attribution must be a mapping")
    grounding = finding.get("grounding")
    if grounding is not None:
        validate_grounding(grounding)


def finding_requires_grounding(finding: Mapping[str, Any], policy_family: str | None) -> bool:
    """Return True when the D1 grounding matrix requires this finding to cite tools."""
    family = str(policy_family or "").strip().lower()
    dimension = str(finding.get("dimension") or "")
    issue_class = str(finding.get("issue_class") or "")
    if dimension in GROUNDING_REQUIRED_DIMENSIONS:
        return True
    return family == "seminar" and issue_class in GROUNDING_REQUIRED_SEMINAR_CLASSES


def validate_grounded_finding(finding: Mapping[str, Any], policy_family: str | None) -> None:
    """Validate one reviewer finding plus the D1 grounding requirement."""
    validate_finding(finding)
    if finding_requires_grounding(finding, policy_family) and not finding.get("grounding"):
        raise ValueError("finding requires grounding")


def validate_grounding(grounding: Mapping[str, Any]) -> None:
    """Validate the traceable reviewer grounding object."""
    if not isinstance(grounding, Mapping):
        raise ValueError("grounding must be a mapping")
    missing = sorted(key for key in GROUNDING_KEYS if key not in grounding)
    if missing:
        raise ValueError(f"grounding missing required fields: {', '.join(missing)}")
    for key in sorted(GROUNDING_KEYS):
        value = grounding.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"grounding.{key} must be a non-empty string")


def validate_fact_check(fact_check: Mapping[str, Any]) -> None:
    """Validate one reviewer fact-check row."""
    if not isinstance(fact_check, Mapping):
        raise ValueError("fact_check must be a mapping")
    claim = fact_check.get("claim")
    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("fact_check.claim must be a non-empty string")
    _require_member("fact_check.verdict", fact_check.get("verdict"), FACT_CHECK_VERDICTS)
    if "original_verdict" in fact_check:
        _require_member("fact_check.original_verdict", fact_check.get("original_verdict"), FACT_CHECK_VERDICTS)
    grounding = fact_check.get("grounding")
    if grounding is not None:
        validate_grounding(grounding)
    if fact_check.get("verdict") in {"CONFIRMED", "REFUTED_BY_CONTRADICTION", "CONTESTED"} and grounding is None:
        raise ValueError("fact_check verdict requires grounding")
    for bool_key in ("deep_read_attempted", "budget_exhausted", "admissibility_downgraded"):
        if bool_key in fact_check and not isinstance(fact_check[bool_key], bool):
            raise ValueError(f"fact_check.{bool_key} must be a boolean")
    searches = fact_check.get("searches")
    if searches is not None:
        _validate_string_list(searches, "fact_check.searches")


def validate_evidence_gap(evidence_gap: Mapping[str, Any]) -> None:
    """Validate one reviewer evidence-gap row."""
    if not isinstance(evidence_gap, Mapping):
        raise ValueError("evidence_gap must be a mapping")
    for key in ("claim", "suspected_issue", "status", "reason"):
        value = evidence_gap.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"evidence_gap.{key} must be a non-empty string")
    _validate_string_list(evidence_gap.get("searches"), "evidence_gap.searches")


def validate_reviewer_payload(payload: Mapping[str, Any], policy_family: str | None) -> None:
    """Validate an LLM reviewer payload before cache write or cache reuse."""
    if not isinstance(payload, Mapping):
        raise ValueError("reviewer payload must be a mapping")
    findings = payload.get("findings", [])
    if not isinstance(findings, list):
        raise ValueError("reviewer payload findings must be a list")
    for finding in findings:
        if not isinstance(finding, Mapping):
            raise ValueError("reviewer payload findings entries must be mappings")
        validate_grounded_finding(finding, policy_family)
    fact_checks = payload.get("fact_checks", [])
    if not isinstance(fact_checks, list):
        raise ValueError("reviewer payload fact_checks must be a list")
    if len(fact_checks) > MAX_REVIEWER_FACT_CHECKS:
        raise ValueError(
            f"reviewer payload fact_checks exceeds cap: {len(fact_checks)} > {MAX_REVIEWER_FACT_CHECKS}"
        )
    for fact_check in fact_checks:
        if not isinstance(fact_check, Mapping):
            raise ValueError("reviewer payload fact_checks entries must be mappings")
        validate_fact_check(fact_check)
    evidence_gaps = payload.get("evidence_gaps", [])
    if not isinstance(evidence_gaps, list):
        raise ValueError("reviewer payload evidence_gaps must be a list")
    for evidence_gap in evidence_gaps:
        if not isinstance(evidence_gap, Mapping):
            raise ValueError("reviewer payload evidence_gaps entries must be mappings")
        validate_evidence_gap(evidence_gap)


def validate_record(record: Mapping[str, Any]) -> None:
    """Validate a canonical evidence record and all nested findings."""
    if record.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version: {record.get('schema_version')!r}")
    _require_member("profile", record.get("profile"), PROFILES)
    _require_member("evidence_kind", record.get("evidence_kind"), EVIDENCE_KINDS)
    _require_member("verdict", record.get("verdict"), VERDICTS)
    _require_member("terminal_verdict", record.get("terminal_verdict"), VERDICTS)

    dimensions = record.get("dimensions")
    if not isinstance(dimensions, Mapping):
        raise ValueError("dimensions must be a mapping")
    for dim, entry in dimensions.items():
        _require_member("dimension key", dim, DIMENSIONS)
        if not isinstance(entry, Mapping):
            raise ValueError(f"dimension {dim!r} must be a mapping")
        _require_member(f"{dim}.verdict", entry.get("verdict"), VERDICTS)
        findings = entry.get("findings", [])
        if not isinstance(findings, list):
            raise ValueError(f"{dim}.findings must be a list")
        for finding in findings:
            if not isinstance(finding, Mapping):
                raise ValueError(f"{dim}.findings entries must be mappings")
            validate_finding(finding)


def _require_member(name: str, value: object, allowed: frozenset[str]) -> None:
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(f"unsupported {name}: {value!r}")


def _validate_string_list(value: object, name: str) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{name} entries must be non-empty strings")
